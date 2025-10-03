import socket
import threading
import multiprocessing
import json
import time
import os

HOST = '127.0.0.1'
PORT = 65432
NUM_WORKERS = 2
db_data = {}

db_lock = threading.Lock()

def heavy_task_worker(task_queue: multiprocessing.Queue, worker_id: int):

    print(f"[Worker {worker_id}] Processo iniciado (PID: {os.getpid()}). Aguardando tarefas.")
    while True:
        try:
            task = task_queue.get()
            if task is None:
                print(f"[Worker {worker_id}] Sinal de término recebido. Encerrando.")
                break

            operation, key, value = task
            print(f"[Worker {worker_id}] Processando tarefa '{operation}' para a chave '{key}'...")

            time.sleep(1.5)

            print(f"[Worker {worker_id}] Tarefa '{operation}' para a chave '{key}' concluída.")

        except Exception as e:
            print(f"[Worker {worker_id}] Erro: {e}")

def handle_client(conn: socket.socket, addr, task_queue: multiprocessing.Queue):
    
    print(f"[Thread {threading.get_ident()}] Conectado por {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                command_str = data.decode('utf-8').strip()
                parts = command_str.split()
                command = parts[0].upper()
                
                response = ""

                # POST: criar somente (falha se a chave já existir)
                if command == 'POST' and len(parts) == 3:
                    key, value = parts[1], parts[2]
                    with db_lock:
                        if key in db_data:
                            response = "ALREADY_EXISTS"
                        else:
                            db_data[key] = value
                            # Enfileira tarefa de persistência/assíncrona
                            task_queue.put(('PERSIST', key, value))
                            response = "OK"

                # PUT: atualizar somente (falha se a chave não existir)
                elif command == 'PUT' and len(parts) == 3:
                    key, value = parts[1], parts[2]
                    with db_lock:
                        if key in db_data:
                            db_data[key] = value
                            task_queue.put(('PERSIST', key, value))
                            response = "OK"
                        else:
                            response = "NOT_FOUND"

                elif command == 'GET' and len(parts) == 2:
                    key = parts[1]
                    with db_lock:
                        value = db_data.get(key, "NULL")
                    response = value

                elif command == 'DELETE' and len(parts) == 2:
                    key = parts[1]
                    with db_lock:
                        if key in db_data:
                            del db_data[key]
                            response = "OK"
                            task_queue.put(('DELETE_PERSIST', key, None))
                        else:
                            response = "NOT_FOUND"
                
                elif command == 'DUMP' and len(parts) == 1:
                    with db_lock:
                        response = json.dumps(db_data)
                
                else:
                    response = "INVALID_COMMAND"

                conn.sendall(response.encode('utf-8'))

            except ConnectionResetError:
                print(f"[Thread {threading.get_ident()}] Conexão com {addr} reiniciada.")
                break
            except Exception as e:
                print(f"[Thread {threading.get_ident()}] Erro ao lidar com {addr}: {e}")
                break
    
    print(f"[Thread {threading.get_ident()}] Conexão com {addr} fechada.")


def main():
    print("--- Servidor Chave-Valor Distribuído ---")

    task_queue = multiprocessing.Queue()
    workers = []
    for i in range(NUM_WORKERS):
        process = multiprocessing.Process(target=heavy_task_worker, args=(task_queue, i + 1))
        workers.append(process)
        process.start()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[Servidor Principal] Ouvindo em {HOST}:{PORT}")
        print(f"[Servidor Principal] PID do processo principal: {os.getpid()}")

        try:
            while True:
                conn, addr = s.accept()
                # Para cada nova conexão, uma nova thread é criada para lidar com ela
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, task_queue)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\n[Servidor Principal] Encerrando o servidor...")
        finally:
            # Envia sinal de término para todos os workers
            for _ in workers:
                task_queue.put(None)
            
            # Aguarda o término dos processos workers
            for p in workers:
                p.join()
            
            print("[Servidor Principal] Todos os workers foram encerrados.")
            print("[Servidor Principal] Servidor desligado.")


if __name__ == '__main__':
    main()
