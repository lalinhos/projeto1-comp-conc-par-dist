import socket
import threading
import multiprocessing
import json
import time
import os

HOST = '127.0.0.1'
PORT = 65432
NUM_WORKERS = 2
cadastro_produtos = {}

cadastro_lock = threading.Lock()

def worker_tarefa_pesada(fila_tarefas: multiprocessing.Queue, worker_id: int):
    print(f"[Worker {worker_id}] Processo iniciado (PID: {os.getpid()}). Aguardando tarefas.")
    while True:
        try:
            tarefa = fila_tarefas.get()
            if tarefa is None:
                print(f"[Worker {worker_id}] Encerrando.")
                break

            operacao, id_produto, nome_produto = tarefa
            print(f"[Worker {worker_id}] Processando '{operacao}' para produto '{id_produto}'...")
            time.sleep(1.5)
            print(f"[Worker {worker_id}] Concluído: '{operacao}' para produto '{id_produto}'.")

        except Exception as e:
            print(f"[Worker {worker_id}] Erro: {e}")

def lidar_com_cliente(conn: socket.socket, addr, fila_tarefas: multiprocessing.Queue):
    print(f"[Thread {threading.get_ident()}] Conectado por {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                comando_str = data.decode('utf-8').strip()
                partes = comando_str.split()
                resposta = ""

                if not partes:
                    continue

                comando = partes[0].upper()

                # --- Comandos em português ---

                # Criar produto
                if comando == 'CRIAR' and len(partes) >= 3 and partes[1].upper() == 'PRODUTO':
                    id_produto, nome_produto = partes[2], partes[3]
                    with cadastro_lock:
                        if id_produto in cadastro_produtos:
                            resposta = "JA_EXISTE"
                        else:
                            cadastro_produtos[id_produto] = nome_produto
                            fila_tarefas.put(('SALVAR', id_produto, nome_produto))
                            resposta = "OK"

                # Editar produto
                elif comando == 'EDITAR' and len(partes) >= 3 and partes[1].upper() == 'PRODUTO':
                    id_produto, nome_produto = partes[2], partes[3]
                    with cadastro_lock:
                        if id_produto in cadastro_produtos:
                            cadastro_produtos[id_produto] = nome_produto
                            fila_tarefas.put(('SALVAR', id_produto, nome_produto))
                            resposta = "OK"
                        else:
                            resposta = "NAO_ENCONTRADO"

                # Ver produto
                elif comando == 'VER' and len(partes) == 3 and partes[1].upper() == 'PRODUTO':
                    id_produto = partes[2]
                    with cadastro_lock:
                        resposta = cadastro_produtos.get(id_produto, "NAO_ENCONTRADO")

                # Deletar produto
                elif comando == 'DELETAR' and len(partes) == 3 and partes[1].upper() == 'PRODUTO':
                    id_produto = partes[2]
                    with cadastro_lock:
                        if id_produto in cadastro_produtos:
                            del cadastro_produtos[id_produto]
                            fila_tarefas.put(('REMOVER', id_produto, None))
                            resposta = "OK"
                        else:
                            resposta = "NAO_ENCONTRADO"

                # Histórico (listar todos)
                elif comando == 'HISTÓRICO':
                    with cadastro_lock:
                        resposta = json.dumps(cadastro_produtos)

                else:
                    resposta = "COMANDO_INVALIDO"

                conn.sendall(resposta.encode('utf-8'))

            except ConnectionResetError:
                print(f"[Thread {threading.get_ident()}] Conexão com {addr} perdida.")
                break
            except Exception as e:
                print(f"[Thread {threading.get_ident()}] Erro: {e}")
                break
    print(f"[Thread {threading.get_ident()}] Conexão encerrada com {addr}")

def main():
    print("--- Servidor de Cadastro de Produtos ---")
    fila_tarefas = multiprocessing.Queue()
    workers = []
    for i in range(NUM_WORKERS):
        processo = multiprocessing.Process(target=worker_tarefa_pesada, args=(fila_tarefas, i+1))
        workers.append(processo)
        processo.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[Servidor] Ouvindo em {HOST}:{PORT}")

        try:
            while True:
                conn, addr = s.accept()
                threading.Thread(target=lidar_com_cliente, args=(conn, addr, fila_tarefas)).start()
        except KeyboardInterrupt:
            print("\n[Servidor] Encerrando...")
        finally:
            for _ in workers:
                fila_tarefas.put(None)
            for p in workers:
                p.join()
            print("[Servidor] Finalizado.")

if __name__ == '__main__':
    main()
