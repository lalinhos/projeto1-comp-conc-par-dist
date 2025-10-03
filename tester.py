import socket
import threading
import random
import time
import json

HOST = '127.0.0.1'
PORT = 65432
NUM_CLIENTS = 20
OPS_PER_CLIENT = 50 

expected_final_state = {}
state_lock = threading.Lock()

def run_test_client(client_id: int):
    print(f"[Cliente de Teste {client_id}] Iniciando...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            for i in range(OPS_PER_CLIENT):
                # now include both POST (create-only) and PUT (update-only)
                op = random.choice(['POST', 'PUT', 'GET', 'DELETE'])
                key = f"key_{client_id}_{(i % 10)}"
                
                command = ""
                
                if op == 'POST':
                    # create-only: will succeed only if key not present on server
                    value = f"val_{client_id}_{i}"
                    command = f"POST {key} {value}"

                elif op == 'PUT':
                    # update-only: will succeed only if key already present
                    value = f"val_{client_id}_{i}_up"
                    command = f"PUT {key} {value}"

                elif op == 'GET':
                    command = f"GET {key}"

                elif op == 'DELETE':
                    command = f"DELETE {key}"
                    with state_lock:
                        if key in expected_final_state:
                            del expected_final_state[key]
                
                s.sendall(command.encode('utf-8'))
                resp = s.recv(1024).decode('utf-8')

                # Update local expected_final_state only when server confirmed OK
                with state_lock:
                    if command.startswith('POST') and resp == 'OK':
                        # extract value from command
                        _, k, v = command.split()
                        expected_final_state[k] = v
                    elif command.startswith('PUT') and resp == 'OK':
                        _, k, v = command.split()
                        expected_final_state[k] = v
                    elif command.startswith('DELETE') and resp == 'OK':
                        _, k = command.split()
                        if k in expected_final_state:
                            del expected_final_state[k]
                
                time.sleep(random.uniform(0.01, 0.05))

    except Exception as e:
        print(f"[Cliente de Teste {client_id}] Erro: {e}")
    
    print(f"[Cliente de Teste {client_id}] Concluído.")


def main():
    print("--- Testador de Concorrência e Consistência ---")
    
    threads = []
    
    print(f"Iniciando {NUM_CLIENTS} clientes concorrentes...")
    start_time = time.time()

    for i in range(NUM_CLIENTS):
        thread = threading.Thread(target=run_test_client, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    total_ops = NUM_CLIENTS * OPS_PER_CLIENT
    print(f"\nFase de operações concluída em {end_time - start_time:.2f} segundos.")
    print(f"Total de operações: {total_ops}")
    print(f"Throughput: {total_ops / (end_time - start_time):.2f} ops/segundo.")

    print("\n--- Fase de Validação ---")
    print("Buscando o estado final do servidor...")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(b'DUMP')
            full_response = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                full_response += chunk
            
            server_state = json.loads(full_response.decode('utf-8'))
            
            print(f"Itens esperados: {len(expected_final_state)}")
            print(f"Itens no servidor: {len(server_state)}")

            expected_sorted = sorted(expected_final_state.items())
            server_sorted = sorted(server_state.items())

            if expected_sorted == server_sorted:
                print("\n✅ SUCESSO: O estado final do servidor é consistente com o esperado!")
            else:
                print("\n❌ FALHA: Inconsistência detectada no estado final do servidor!")
                

    except Exception as e:
        print(f"Erro durante a validação: {e}")


if __name__ == '__main__':
    main()
