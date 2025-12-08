import requests
import time

def main():
    """Função principal do cliente"""
    print("=== Cliente de Envio de Texto ===")

    # Configuração do servidor FastAPI
    base_url = "http://localhost:5000"
    
    try:
        # Verificar se servidor está rodando
        response = requests.get(f"{base_url}/")
        print(f"Servidor online: {response.json()}")
        print()

        # Loop de envio de mensagens
        contador = 1
        while True:
            message = f"Teste de mensagem #{contador}"
            
            # Enviar para rota /texto
            payload = {"text": message}
            response = requests.post(f"{base_url}/texto", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Mensagem enviada: {message}")
                print(f"  User ID: {result.get('user_id')}")
                print(f"  Processado: {result.get('message_processado')}")
            else:
                print(f"✗ Erro: {response.status_code} - {response.text}")
            
            print()
            
            contador += 1
            time.sleep(2)  # Aguarda 2 segundos antes da próxima mensagem
            
            # Parar após 5 mensagens (exemplo)
            if contador > 5:
                print("Encerrando sessão...")
                close_response = requests.post(f"{base_url}/session/close")
                print(f"Sessão encerrada: {close_response.json()}")
                
                # Consultar informações da sessão
                print("\nInformações da sessão:")
                info_response = requests.get(f"{base_url}/session/info")
                print(info_response.json())
                break

    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar ao servidor.")
        print(f"Certifique-se de que o FastAPI está rodando em {API_URL}")
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário. Encerrando sessão...")
        try:
            requests.post(f"{base_url}/session/close")
        except:
            pass
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        print("Cliente encerrado.")

if __name__ == "__main__":
    main()