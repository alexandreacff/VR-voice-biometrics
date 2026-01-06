import requests
import os
import time
from scipy.io.wavfile import read
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuração do servidor FastAPI
BASE_URL = "https://brett-unpieced-bud.ngrok-free.dev"
WATCHED_FOLDER = "../data/input"  # Pasta a ser monitorada
MAX_QUESTIONS = 3  # Número de perguntas a processar

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

def send_text_from_file(filepath):
    """Lê e envia o conteúdo de um arquivo de texto"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            message = f.read().strip()
        
        if not message:
            print(f"  ⚠ Arquivo vazio: {os.path.basename(filepath)}")
            return None
        
        payload = {"text": message}
        response = requests.post(f"{BASE_URL}/texto", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Texto enviado: {message[:50]}...")
            print(f"    User ID: {result.get('user_id')}")
            return result
        else:
            print(f"  ✗ Erro no texto: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ✗ Erro ao enviar texto: {e}")
        return None

class FileHandler(FileSystemEventHandler):
    """Handler para processar arquivos novos na pasta monitorada"""
    
    def __init__(self):
        super().__init__()
        self.questions_count = 0
        self.txt_processed = 0
        self.wav_processed = 0
    
    def on_created(self, event):
        """Chamado quando um arquivo é criado"""
        if event.is_directory:
            return
        
        # Verificar se já atingiu o limite
        if self.questions_count >= MAX_QUESTIONS:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Aguardar um pouco para garantir que o arquivo foi completamente escrito
        time.sleep(0.5)
        
        # Processar arquivos .txt
        if filepath.lower().endswith('.txt'):
            print(f"\n[{time.strftime('%H:%M:%S')}] Novo arquivo TXT detectado: {filename}")
            result = send_text_from_file(filepath)
            
            if result:
                self.txt_processed += 1
                try:
                    os.remove(filepath)
                    print(f"  ✓ Arquivo removido: {filename}")
                except Exception as e:
                    print(f"  ✗ Erro ao remover arquivo: {e}")
                
                # Atualizar contador se já recebeu o áudio correspondente
                self._check_question_complete()
        
        # Processar arquivos .wav
        elif filepath.lower().endswith('.wav'):
            print(f"\n[{time.strftime('%H:%M:%S')}] Novo arquivo WAV detectado: {filename}")
            result = send_wav_file(filepath)
            
            if result:
                self.wav_processed += 1
                try:
                    os.remove(filepath)
                    print(f"  ✓ Arquivo removido: {filename}")
                except Exception as e:
                    print(f"  ✗ Erro ao remover arquivo: {e}")
                
                # Atualizar contador se já recebeu o texto correspondente
                self._check_question_complete()
    
    def _check_question_complete(self):
        """Verifica se uma pergunta completa foi processada"""
        min_processed = min(self.txt_processed, self.wav_processed)
        if min_processed > self.questions_count:
            self.questions_count = min_processed
            print(f"\n>>> Pergunta {self.questions_count}/{MAX_QUESTIONS} completa <<<\n")

def main():
    """Função principal - monitora pasta continuamente"""
    print("=== Monitor de Pasta: Texto + Áudio ===\n")
    print(f"Configurado para processar {MAX_QUESTIONS} perguntas e encerrar\n")
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Servidor online: {response.json()}")
    except requests.exceptions.ConnectionError:
        print(f"✗ Erro: Servidor não está respondendo em {BASE_URL}")
        return
    
    # Criar pasta monitorada se não existir
    if not os.path.exists(WATCHED_FOLDER):
        os.makedirs(WATCHED_FOLDER)
        print(f"✓ Pasta criada: {WATCHED_FOLDER}")
    
    print(f"✓ Monitorando pasta: {os.path.abspath(WATCHED_FOLDER)}")
    print(f"\nAguardando arquivos .txt e .wav...")
    print("Pressione Ctrl+C para encerrar manualmente\n")
    
    # Configurar observador de arquivos
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCHED_FOLDER, recursive=False)
    observer.start()
    
    try:
        while event_handler.questions_count < MAX_QUESTIONS:
            time.sleep(1)
        
        # Perguntas completas - encerrar automaticamente
        print(f"\n✓ {MAX_QUESTIONS} perguntas processadas com sucesso!")
        print("→ Encerrando automaticamente...")
        
    except KeyboardInterrupt:
        print("\n\n→ Encerrando monitor (interrompido pelo usuário)...")
    finally:
        observer.stop()
        observer.join()
        
        # Encerrar sessão no servidor
        try:
            close_response = requests.post(f"{BASE_URL}/session/close")
            print(f"✓ Sessão encerrada: {close_response.json()}")
        except:
            pass
        
        print("\n=== Monitor encerrado ===")
        print(f"Total processado: {event_handler.txt_processed} textos, {event_handler.wav_processed} áudios")

if __name__ == "__main__":
    main()
