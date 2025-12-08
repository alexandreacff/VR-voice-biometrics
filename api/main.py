import uuid
import os
import numpy as np
import json
from fastapi import FastAPI, UploadFile, File, Request, Depends
from fastapi.responses import JSONResponse
from scipy.io.wavfile import write
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DBSession

from database import init_db, get_db, Session, Audio, Texto
from embeddings import generate_session_embedding

app = FastAPI()
SAMPLE_RATE = 48000

# Inicializar banco de dados
init_db()

class AccessManager:
    """Gerencia acessos por IP e sessões de usuários."""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}  # key = IP, value = dados da sessão

    
    def get_or_create_session(self, ip: str, db: DBSession) -> dict:
        """Retorna sessão existente ou cria nova se necessário."""
        if ip not in self.sessions or self.sessions[ip]["closed"]:
            # Verificar se existe sessão aberta no banco
            db_session = db.query(Session).filter(
                Session.ip == ip, 
                Session.closed == 0
            ).first()
            
            if db_session:
                # Carregar sessão existente do banco
                self.sessions[ip] = {
                    "user_id": db_session.id,
                    "ip": db_session.ip,
                    "nome": db_session.nome,
                    "tempo_audio_total": db_session.tempo_audio_total,
                    "closed": False,
                    "created_at": db_session.created_at.isoformat()
                }
            else:
                # Criar nova sessão
                user_id = str(uuid.uuid4())
                new_session = Session(
                    id=user_id,
                    ip=ip,
                    created_at=datetime.now()
                )
                db.add(new_session)
                db.commit()
                
                self.sessions[ip] = {
                    "user_id": user_id,
                    "ip": ip,
                    "nome": None,
                    "tempo_audio_total": 0.0,
                    "closed": False,
                    "created_at": datetime.now().isoformat()
                }
        
        return self.sessions[ip]
    
    def add_audio(self, ip: str, audio_array: np.ndarray, duration: float, db: DBSession):
        """Adiciona áudio à sessão do IP."""
        session = self.get_or_create_session(ip, db)
        
        # Salvar áudio bruto (sem embeddings) no banco
        db_audio = Audio(
            session_id=session["user_id"],
            audio_data=json.dumps(audio_array.tolist()),  # Serializar como JSON
            duration=duration,
            timestamp=datetime.now()
        )
        db.add(db_audio)
        
        # Atualizar tempo total
        db_session = db.query(Session).filter(Session.id == session["user_id"]).first()
        db_session.tempo_audio_total += duration
        session["tempo_audio_total"] += duration
        
        db.commit()
    
    def add_texto(self, ip: str, texto: str, db: DBSession):
        """Adiciona texto à sessão do IP."""
        session = self.get_or_create_session(ip, db)
        
        # Se é o primeiro texto, definir como nome
        db_session = db.query(Session).filter(Session.id == session["user_id"]).first()
        if not db_session.nome:
            db_session.nome = texto
            session["nome"] = texto
        
        # Salvar texto no banco
        db_texto = Texto(
            session_id=session["user_id"],
            texto=texto,
            timestamp=datetime.now()
        )
        db.add(db_texto)
        db.commit()
    
    def close_session(self, ip: str, db: DBSession) -> bool:
        """Encerra a sessão do IP e gera embedding concatenado."""
        if ip in self.sessions and not self.sessions[ip]["closed"]:
            session_id = self.sessions[ip]["user_id"]
            
            # Buscar sessão no banco
            db_session = db.query(Session).filter(Session.id == session_id).first()
            if db_session:
                # Gerar embedding concatenando todos os áudios
                audio_arrays = [audio.audio_data for audio in db_session.audios]
                
                if audio_arrays:
                    print(f"Gerando embedding de {len(audio_arrays)} áudios concatenados...")
                    embedding = generate_session_embedding(audio_arrays)
                    db_session.embedding = json.dumps(embedding.tolist() if isinstance(embedding, np.ndarray) else embedding)
                    print(f"Embedding gerado com {len(embedding)} features")
                else:
                    print("Nenhum áudio encontrado para gerar embedding")
                
                # Marcar como fechada
                db_session.closed = 1
                db_session.closed_at = datetime.now()
                db.commit()
            
            self.sessions[ip]["closed"] = True
            self.sessions[ip]["closed_at"] = datetime.now().isoformat()
            print(f"Sessão encerrada para IP {ip}: {session_id}")
            return True
        return False
    
    def get_session(self, ip: str, db: DBSession) -> Optional[dict]:
        """Retorna dados da sessão do IP."""
        session = self.sessions.get(ip)
        if session and not session["closed"]:
            # Enriquecer com dados do banco
            db_session = db.query(Session).filter(Session.id == session["user_id"]).first()
            if db_session:
                result = {
                    "user_id": db_session.id,
                    "ip": db_session.ip,
                    "nome": db_session.nome,
                    "tempo_audio_total": db_session.tempo_audio_total,
                    "total_audios": len(db_session.audios),
                    "total_textos": len(db_session.textos),
                    "created_at": db_session.created_at.isoformat()
                }
                
                # Incluir embedding se sessão estiver fechada
                if db_session.closed and db_session.embedding:
                    result["embedding_size"] = len(json.loads(db_session.embedding))
                
                return result
        return None


# Instanciar gerenciadores
access_manager = AccessManager()

def is_text_data(data: bytes) -> bool:
    """Verifica se os dados são texto UTF-8."""
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

# ================================
#   ROTA PARA ÁUDIO
# ================================
@app.post("/audio")
async def upload_audio(request: Request, file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    """Recebe e processa um arquivo de áudio."""
    
    client_ip = request.client.host
    
    # Ler bytes
    audio_bytes = await file.read()

    # Converter bytes => array numpy
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    sample_rate = SAMPLE_RATE
    
    # Calcular duração do áudio (em segundos)
    duration = len(audio_array) / sample_rate
    
    # Adicionar à sessão (salva áudio bruto, SEM embedding)
    access_manager.add_audio(client_ip, audio_array, duration, db)

    return {
        "message": "Áudio salvo (embedding será gerado ao fechar sessão)",
        "user_id": access_manager.get_session(client_ip, db)["user_id"],
        "sample_rate": sample_rate,
        "shape": audio_array.shape,
        "duration": duration
    }


# ================================
#   ROTA PARA TEXTO
# ================================
@app.post("/texto")
async def upload_text(request: Request, payload: dict, db: DBSession = Depends(get_db)):
    """Recebe dados de texto JSON."""
    
    client_ip = request.client.host
    
    if "text" not in payload:
        return JSONResponse({"error": "campo 'text' ausente"}, status_code=400)

    message = payload["text"]

    # Log da mensagem recebida
    print(f"Mensagem recebida de {client_ip}: {message}")
    
    # Adicionar à sessão
    access_manager.add_texto(client_ip, message, db)
    
    session = access_manager.get_session(client_ip, db)
    
    return {
        "message_processado": message,
        "user_id": session["user_id"],
        "is_nome": session["nome"] == message
    }


# ================================
#   ROTA GENÉRICA
# ================================
@app.post("/raw")
async def raw_receiver(request: Request):
    """Recebe qualquer dado e tenta detectar tipo."""
    
    client_ip = request.client.host
    data = await request.body()

    if is_text_data(data):
        message = data.decode("utf-8")
        access_manager.add_texto(client_ip, message)
        return {
            "tipo": "texto",
            "conteúdo": message,
            "user_id": access_manager.get_session(client_ip)["user_id"]
        }

    # Caso binário → tratar como áudio
    audio_array = np.frombuffer(data, dtype=np.int16)
    sample_rate = SAMPLE_RATE

    audio_dir = "../data/audios_files"
    os.makedirs(audio_dir, exist_ok=True)

    filename = f"audio_{uuid.uuid4()}.wav"
    filepath = os.path.join(audio_dir, filename)

    write(filepath, sample_rate, audio_array)
    
    duration = len(audio_array) / sample_rate
    
    access_manager.add_audio(client_ip, {
        "filename": filename,
        "filepath": filepath,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "tipo": "audio",
        "file": filename,
        "user_id": access_manager.get_session(client_ip)["user_id"]
    }


# ================================
#   NOVAS ROTAS PARA GERENCIAR SESSÕES
# ================================
@app.post("/session/close")
async def close_session(request: Request, db: DBSession = Depends(get_db)):
    """Encerra a sessão do usuário e gera embedding concatenado."""
    client_ip = request.client.host
    success = access_manager.close_session(client_ip, db)
    print(f"Fechando sessão para IP {client_ip}: {success}")
    
    if success:
        # Buscar sessão para retornar info do embedding
        db_session = db.query(Session).filter(
            Session.ip == client_ip,
            Session.closed == 1
        ).order_by(Session.closed_at.desc()).first()
        
        embedding_info = {}
        if db_session and db_session.embedding:
            embedding = json.loads(db_session.embedding)
            embedding_info = {
                "embedding_generated": True,
                "embedding_size": len(embedding),
                "total_audios_concatenated": len(db_session.audios)
            }
        
        return {
            "message": "Sessão encerrada e embedding gerado",
            "ip": client_ip,
            **embedding_info
        }
    return JSONResponse({"error": "Sessão não encontrada ou já encerrada"}, status_code=404)


@app.get("/session/info")
async def session_info(request: Request, db: DBSession = Depends(get_db)):
    """Retorna informações da sessão atual."""
    client_ip = request.client.host
    session = access_manager.get_session(client_ip, db)
    
    if session:
        return session
    return JSONResponse({"error": "Sessão não encontrada"}, status_code=404)


# ================================
#   HEALTH CHECK
# ================================
@app.get("/")
def root():
    return {"status": "OK", "message": "Servidor FastAPI rodando!"}
