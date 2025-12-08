import requests
import os
import time
from scipy.io.wavfile import read

# Configuração do servidor FastAPI
BASE_URL = 'http://127.0.0.1:5000'

def send_wav_file(filepath):
    """Envia um arquivo WAV para o servidor"""
    try:
        # Ler arquivo WAV
        sample_rate, audio_data = read(filepath)
        
        # Abrir arquivo em modo binário para envio
        with open(filepath, 'rb') as audio_file:
            files = {'file': (os.path.basename(filepath), audio_file, 'audio/wav')}
            
            # Enviar para servidor FastAPI
            response = requests.post(f"{BASE_URL}/audio", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Áudio enviado com sucesso")
                print(f"    User ID: {result.get('user_id')}")
                print(f"    Sample Rate: {result.get('sample_rate')}")
                print(f"    Shape: {result.get('shape')}")
                return result
            else:
                print(f"  ✗ Erro no áudio: {response.status_code} - {response.text}")
                return None
        
    except Exception as e:
        print(f"  ✗ Erro ao enviar áudio: {e}")
        return None

def send_text(message):
    """Envia uma mensagem de texto para o servidor"""
    try:
        payload = {"text": message}
        response = requests.post(f"{BASE_URL}/texto", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Texto enviado: {message}")
            print(f"    User ID: {result.get('user_id')}")
            print(f"    Processado: {result.get('message_processado')}")
            return result
        else:
            print(f"  ✗ Erro no texto: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ✗ Erro ao enviar texto: {e}")
        return None

def main():
    """Função principal do pipeline de teste"""
    print("=== Pipeline de Teste: Texto + Áudio ===\n")
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Servidor online: {response.json()}\n")
    except requests.exceptions.ConnectionError:
        print(f"Erro: Servidor não está respondendo em {BASE_URL}")
        return
    
    # Verificar se arquivo de áudio existe
    audio_file = "0-0-xtts.wav"
    if not os.path.exists(audio_file):
        print(f"Erro: O arquivo {audio_file} não foi encontrado.")
        return
    
    try:
        # Pipeline: repetir 5 vezes
        for i in range(1, 6):
            print(f"[Iteração {i}/5]")
            
            # 1. Enviar texto
            print(f"→ Enviando texto...")
            text_message = f"Teste de mensagem #{i}"
            send_text(text_message)
            
            time.sleep(0.2)  # Pequena pausa entre texto e áudio
            
            # 2. Enviar áudio
            print(f"→ Enviando áudio...")
            send_wav_file(audio_file)
            
            print()
            
            if i < 5:
                time.sleep(2)  # Pausa entre iterações
        
        # Encerrar sessão
        print("→ Encerrando sessão...")
        close_response = requests.post(f"{BASE_URL}/session/close")
        print(f"  ✓ Sessão encerrada: {close_response.json()}\n")
        
        # Consultar informações finais da sessão
        print("→ Informações da sessão:")
        info_response = requests.get(f"{BASE_URL}/session/info")
        info_data = info_response.json()
        for key, value in info_data.items():
            print(f"  {key}: {value}")
            
    except requests.exceptions.ConnectionError:
        print("\nErro: Conexão perdida com o servidor.")
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário. Tentando encerrar sessão...")
        try:
            requests.post(f"{BASE_URL}/session/close")
            print("Sessão encerrada.")
            
        except:
            pass
    except Exception as e:
        print(f"\nErro inesperado: {e}")
    finally:
        print("\n=== Pipeline de teste concluído ===")

if __name__ == "__main__":
    main()
