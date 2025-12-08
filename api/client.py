import requests
import numpy as np
from scipy.io.wavfile import read
import os

# Configuração do servidor FastAPI
BASE_URL = 'http://127.0.0.1:5000'

def send_wav_file(filepath):
    """Envia um arquivo WAV para o servidor"""
    try:
        # Ler arquivo WAV
        sample_rate, audio_data = read(filepath)
        print(f"Arquivo carregado: {filepath}")
        print(f"Taxa de amostragem: {sample_rate}, Shape: {audio_data.shape}")
        
        # Abrir arquivo em modo binário para envio
        with open(filepath, 'rb') as audio_file:
            files = {'file': (os.path.basename(filepath), audio_file, 'audio/wav')}
            
            # Enviar para servidor FastAPI
            response = requests.post(f"{BASE_URL}/audio", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Áudio enviado com sucesso")
                print(f"  User ID: {result.get('user_id')}")
                print(f"  Sample Rate: {result.get('sample_rate')}")
                print(f"  Shape: {result.get('shape')}")
                print(f"  Processado: {result.get('message')}")
                return result
            else:
                print(f"✗ Erro: {response.status_code} - {response.text}")
                return None
        
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar ao servidor.")
        print(f"Certifique-se de que o FastAPI está rodando em {BASE_URL}")
    except Exception as e:
        print(f"Erro ao enviar arquivo: {e}")
        return None
    
def main():
    """Função principal do cliente"""
    print("=== Cliente de Envio de Áudio ===")
    
    try:
        # Verificar se servidor está rodando
        response = requests.get(f"{BASE_URL}/")
        print(f"Servidor online: {response.json()}")
        print()
    except requests.exceptions.ConnectionError:
        print(f"Erro: Servidor não está respondendo em {BASE_URL}")
        return
    
    audio_file = "../../0-0-xtts.wav"
    if os.path.exists(audio_file):
        try:
            result = send_wav_file(audio_file)
            
            if result:
                print("\nConsultando informações da sessão:")
                info_response = requests.get(f"{BASE_URL}/session/info")
                print(info_response.json())

        except ValueError:
            print("Entrada inválida")
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuário.")
    else:
        print(f"Erro: O arquivo {audio_file} não foi encontrado.")

if __name__ == "__main__":
    main()