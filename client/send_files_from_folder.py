import requests
import os
import time
import socket
from scipy.io.wavfile import read
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuração do servidor FastAPI
BASE_URL = "https://brett-unpieced-bud.ngrok-free.dev"
WATCHED_FOLDER = "../data/input"  # Pasta a ser monitorada
MAX_QUESTIONS = 3  # Número de perguntas a processar

# Configuração TCP
TCP_HOST = "127.0.0.1"  # Host do servidor TCP receptor
TCP_PORT = 5555  # Porta TCP para enviar resultados

def send_verification_result_tcp(result_message):
    """Envia resultado da verificação via TCP para outro script"""
    try:
        # Criar socket TCP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)  # Timeout de 5 segundos
        
        # Conectar ao servidor TCP
        client_socket.connect((TCP_HOST, TCP_PORT))
        
        # Enviar mensagem
        client_socket.sendall(result_message.encode('utf-8'))
        
        # Aguardar confirmação (opcional)
        response = client_socket.recv(1024).decode('utf-8')
        
        client_socket.close()
        print(f"  ✓ Resultado enviado via TCP para {TCP_HOST}:{TCP_PORT}")
        print(f"    Mensagem: {result_message}")
        if response:
            print(f"    Resposta: {response}")
        
        return True
        
    except ConnectionRefusedError:
        print(f"  ⚠ Aviso: Servidor TCP não está escutando em {TCP_HOST}:{TCP_PORT}")
        return False
    except socket.timeout:
        print(f"  ⚠ Timeout ao conectar em {TCP_HOST}:{TCP_PORT}")
        return False
    except Exception as e:
        print(f"  ✗ Erro ao enviar via TCP: {e}")
        return False

def verify_user(filepath):
    """Verifica se o usuário está registrado enviando áudio para /verify"""
    try:
        with open(filepath, 'rb') as audio_file:
            files = {'file': (os.path.basename(filepath), audio_file, 'audio/wav')}
            
            response = requests.post(f"{BASE_URL}/verify", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Verificação concluída")
                print(f"\n{'='*60}")
                print(f"  RESULTADO DA VERIFICAÇÃO:")
                print(f"{'='*60}")
                print(f"  Verificado: {'✓ SIM' if result.get('verified') else '✗ NÃO'}")
                print(f"  Confiança: {result.get('confidence', 0):.2%}")
                print(f"  Threshold: {result.get('threshold', 0):.2%}")
                print(f"  Total de usuários registrados: {result.get('total_registered_users', 0)}")
                
                # Determinar mensagem a enviar via TCP
                tcp_message = "Invalid"
                
                if result.get('verified') and result.get('best_match'):
                    match = result['best_match']
                    nome = match.get('nome', 'N/A')
                    tcp_message = nome
                    
                    print(f"\n  MELHOR CORRESPONDÊNCIA:")
                    print(f"  - Nome: {nome}")
                    print(f"  - User ID: {match.get('user_id', 'N/A')}")
                    print(f"  - Similaridade: {match.get('similarity', 0):.2%}")
                    print(f"  - Tempo total de áudio: {match.get('tempo_audio_total', 0):.2f}s")
                else:
                    print(f"\n  Usuário não reconhecido no sistema")
                    if result.get('top_matches'):
                        print(f"\n  TOP 3 CORRESPONDÊNCIAS MAIS PRÓXIMAS:")
                        for i, match in enumerate(result['top_matches'][:3], 1):
                            print(f"  {i}. {match.get('nome', 'N/A')} - {match.get('similarity', 0):.2%}")
                
                print(f"{'='*60}\n")
                
                # Enviar resultado via TCP
                send_verification_result_tcp(tcp_message)
                
                return result
            elif response.status_code == 404:
                result = response.json()
                print(f"  ⚠ {result.get('message', 'Nenhum usuário registrado')}")
                print(f"  Total de usuários: {result.get('registered_users', 0)}\n")
                
                # Enviar "Invalid" via TCP quando não há usuários registrados
                send_verification_result_tcp("Invalid")
                
                return None
            else:
                print(f"  ✗ Erro na verificação: {response.status_code} - {response.text}")
                send_verification_result_tcp("Invalid")
                return None
        
    except Exception as e:
        print(f"  ✗ Erro ao verificar usuário: {e}")
        send_verification_result_tcp("Invalid")
        return None

def send_wav_file(filepath):
    """Envia um arquivo WAV para o servidor"""
    try:
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
        self.first_audio = True  # Flag para primeiro áudio
    
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
            time.sleep(0.5)
            
            # Se for o primeiro áudio, fazer verificação
            if self.first_audio:
                print(f"→ Verificando usuário (primeiro áudio)...")
                verify_user(filepath)
                self.first_audio = False
            
            # Enviar áudio normal
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
    print(f"⚠ O primeiro áudio será usado para VERIFICAÇÃO de usuário\n")
    
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