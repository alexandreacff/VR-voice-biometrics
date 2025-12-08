# 🎤 VR Voice Biometrics

Voice biometric authentication system for VR applications. Processes audio in real-time, generates voice embeddings using deep learning (ReDimNet), and manages user sessions for voice recognition.

## 🚀 Features

- 🎯 Voice authentication using biometric embeddings
- 📊 Audio and metadata storage in SQLite
- 🔄 Automatic session management by IP
- 🐳 Ready to run with Docker
- 🎙️ Support for multiple audio formats

## 📋 Requirements

- Docker and Docker Compose

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/alexandreacff/VR-voice-biometrics.git
cd VR-voice-biometrics
```

### 2. Start the server with Docker

```bash
docker-compose up -d
```

### 3. Check if it's running

```bash
# Check logs
docker-compose logs -f api

```

### 4. Test by sending audio

```bash
# With Python client
cd client
docker exec -it biometria-api bash
cd ../client
python client_pipeline.py

# Or with cURL
curl -X POST "http://localhost:5000/audio" \
  -F "file=@your_audio.wav"
```

## 📡 Main API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/audio` | POST | Send audio file |
| `/texto` | POST | Send text (username) |
| `/session/info` | GET | Session information |
| `/session/close` | POST | End session and generate embedding |
| `/health` | GET | API status |


## 🛠️ Local Development (without Docker)

```bash
# Python 3.9

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Run server
cd api
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## 📂 Structure

```
VR-voice-biometrics/
├── api/                    # FastAPI backend
│   ├── main.py            # Main server
│   ├── database.py        # Database models
│   └── embeddings.py      # Embedding generation
├── client/                # Test clients
│   ├── client.py          # Audio client
│   └── client_text.py     # Text client
├── data/                  # Database and audio files
├── docker-compose.yml     # Docker configuration
└── requirements.txt       # Python dependencies
```

## 🔧 Useful Commands

```bash
# Stop containers
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Check API health
curl http://localhost:5000/health
```


## 👤 Author

**Alexandre Ferro** - [@alexandreacff](https://github.com/alexandreacff)

---
