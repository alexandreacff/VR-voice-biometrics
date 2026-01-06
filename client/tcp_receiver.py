import socket

TCP_HOST = "127.0.0.1"
TCP_PORT = 5555

def start_tcp_server():
    """Inicia servidor TCP para receber resultados de verificação"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((TCP_HOST, TCP_PORT))
    server_socket.listen(5)
    
    print(f"=== Servidor TCP Receptor ===")
    print(f"Escutando em {TCP_HOST}:{TCP_PORT}")
    print("Aguardando resultados de verificação...\n")
    
    try:
        while True:
            client_socket, address = server_socket.accept()
            print(f"\n[Conexão recebida de {address}]")
            
            try:
                # Receber dados
                data = client_socket.recv(1024).decode('utf-8')
                
                if data:
                    print(f"→ Resultado recebido: {data}")
                    
                    # Processar resultado
                    if data == "INVALIDO":
                        print("  ✗ Usuário NÃO verificado")
                    else:
                        print(f"  ✓ Usuário verificado: {data}")
                    
                    # Enviar confirmação
                    client_socket.sendall("OK".encode('utf-8'))
                
            except Exception as e:
                print(f"✗ Erro ao processar dados: {e}")
            finally:
                client_socket.close()
                
    except KeyboardInterrupt:
        print("\n\n→ Encerrando servidor...")
    finally:
        server_socket.close()
        print("=== Servidor encerrado ===")

if __name__ == "__main__":
    start_tcp_server()
