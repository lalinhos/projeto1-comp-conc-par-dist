import socket

HOST = '127.0.0.1'
PORT = 65432

def main():
    
    print("--- Cliente Interativo Chave-Valor ---")
    print("Comandos disponíveis: PUT <chave> <valor> | GET <chave> | DELETE <chave> | DUMP | exit")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"Conectado ao servidor em {HOST}:{PORT}")
        except ConnectionRefusedError:
            print(f"Erro: Não foi possível conectar ao servidor. Ele está em execução?")
            return

        while True:
            try:
                command = input("> ")
                if not command or command.lower() == 'exit':
                    break

                s.sendall(command.encode('utf-8'))

                response = s.recv(4096).decode('utf-8')
                print(f"Resposta do servidor: {response}")

            except KeyboardInterrupt:
                print("\nEncerrando o cliente.")
                break
            except Exception as e:
                print(f"Ocorreu um erro: {e}")
                break
    
    print("Conexão fechada.")


if __name__ == '__main__':
    main()
