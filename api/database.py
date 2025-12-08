from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Configuração do banco de dados SQLite
DATABASE_URL = "sqlite:///./biometria_sessions.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Session(Base):
    """Tabela de sessões de usuário"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    ip = Column(String, index=True)
    nome = Column(String, nullable=True)  # Primeiro texto recebido
    embedding = Column(Text, nullable=True)  # JSON string com embedding concatenado
    tempo_audio_total = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    closed_at = Column(DateTime, nullable=True)
    closed = Column(Integer, default=0)  # 0 = aberta, 1 = fechada
    
    # Relacionamentos
    audios = relationship("Audio", back_populates="session", cascade="all, delete-orphan")
    textos = relationship("Texto", back_populates="session", cascade="all, delete-orphan")


class Audio(Base):
    """Tabela de áudios coletados"""
    __tablename__ = "audios"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    audio_data = Column(Text)  # JSON string com array numpy serializado
    duration = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    
    session = relationship("Session", back_populates="audios")


class Texto(Base):
    """Tabela de textos enviados"""
    __tablename__ = "textos"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    texto = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    
    session = relationship("Session", back_populates="textos")


def init_db():
    """Inicializa o banco de dados"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Retorna sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
