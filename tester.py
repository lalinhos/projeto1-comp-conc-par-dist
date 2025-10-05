import socket
import threading
import random
import time
import json

HOST = '127.0.0.1'
PORT = 65432
NUM_CLIENTES = 20
OPS_POR_CLIENTE = 50

estado_esperado = {}
estado_lock = threading.Lock()

def cliente_teste(id_cliente: int):
    print(f"[ClienteTeste {id_cliente}] Iniciando...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            for i in range(OPS_POR_CLIENTE):
                operacao = random.choice(['CRIAR', 'EDITAR', 'VER', 'DELETAR'])
                id_produto = f"P{id_cliente}_{i % 10}"
                comando = ""

                if operacao == 'CRIAR':
                    nome = f"Produto_{id_cliente}_{i}"
                    comando = f"CRIAR PRODUTO {id_produto} {nome}"

                elif operacao == 'EDITAR':
                    nome = f"Produto_{id_cliente}_{i}_editado"
                    comando = f"EDITAR PRODUTO {id_produto} {nome}"

                elif operacao == 'VER':
                    comando = f"VER PRODUTO {id_produto}"

                elif operacao == 'DELETAR':
                    comando = f"DELETAR PRODUTO {id_produto}"
                    with estado_lock:
                        estado_esperado.pop(id_produto, None)

                s.sendall(comando.encode('utf-8'))
                resp = s.recv(1024).decode('utf-8')

                with estado_lock:
                    if comando.startswith('CRIAR') and resp == 'OK':
                        _, _, pid, nome = comando.split()
                        estado_esperado[pid] = nome
                    elif comando.startswith('EDITAR') and resp == 'OK':
                        _, _, pid, nome = comando.split()
                        estado_esperado[pid] = nome
                    elif comando.startswith('DELETAR') and resp == 'OK':
                        _, _, pid = comando.split()
                        estado_esperado.pop(pid, None)

                time.sleep(random.uniform(0.01, 0.05))
    except Exception as e:
        print(f"[ClienteTeste {id_cliente}] Erro: {e}")
    print(f"[ClienteTeste {id_cliente}] Concluído.")

def main():
    print("--- Testador de Concorrência do Cadastro de Produtos ---")
    threads = []
    inicio = time.time()

    for i in range(NUM_CLIENTES):
        t = threading.Thread(target=cliente_teste, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    fim = time.time()
    total_ops = NUM_CLIENTES * OPS_POR_CLIENTE
    print(f"\nConcluído em {fim - inicio:.2f}s ({total_ops/(fim - inicio):.2f} ops/s)")

    print("\n--- Validação do Estado Final ---")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(b'HISTORICO')
            resposta = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                resposta += chunk
            servidor_estado = json.loads(resposta.decode('utf-8'))

            print(f"Itens esperados: {len(estado_esperado)}")
            print(f"Itens no servidor: {len(servidor_estado)}")

            if sorted(estado_esperado.items()) == sorted(servidor_estado.items()):
                print("\n SUCESSO: Estado do servidor consistente!")
            else:
                print("\n FALHA: Estado inconsistente!")
    except Exception as e:
        print(f"Erro na validação: {e}")

if __name__ == '__main__':
    main()
