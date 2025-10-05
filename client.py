import socket

HOST = '127.0.0.1'
PORT = 65432

def main():
    print("--- Cliente Interativo de Produtos ---")
    print("Comandos disponíveis:")
    print("CRIAR PRODUTO <id> <nome>")
    print("EDITAR PRODUTO <id> <nome>")
    print("VER PRODUTO <id>")
    print("DELETAR PRODUTO <id>")
    print("HISTÓRICO")
    print("SAIR")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"Conectado ao servidor {HOST}:{PORT}")
        except ConnectionRefusedError:
            print("Erro: servidor não encontrado.")
            return

        while True:
            comando = input("> ")
            if not comando or comando.lower() == 'sair':
                break

            s.sendall(comando.encode('utf-8'))
            resposta = s.recv(4096).decode('utf-8')
            print(f"Resposta: {resposta}")

    print("Conexão encerrada.")

if __name__ == '__main__':
    main()
