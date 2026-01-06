import numpy as np
from typing import List
import json
import torch
import torchaudio.functional as F

class ReDimNetModel:
    def __init__(self, model_name: str = 'M', train_type: str = 'ft_mix', dataset: str = 'vb2+vox2+cnc'):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = torch.hub.load('IDRnD/ReDimNet', 'ReDimNet', model_name=model_name, train_type=train_type, dataset=dataset)
        model = model.to(device)
        self.model = model
        self.model.eval()

    def model_infer(self, audio):

        self.model.eval()
        
        # Verificar o dispositivo do modelo
        device = next(self.model.parameters()).device

        # Garantir que não serão calculados gradientes
        with torch.no_grad():

            # Transferir o tensor de áudio para o mesmo dispositivo do modelo
            audio = audio.to(device)

            emb = self.model(audio)

        return emb.cpu().numpy()
    
    def load_process_audio(self, audio_array: np.ndarray, sample_rate: int = 22100) -> torch.Tensor:

        audio = torch.tensor(audio_array, dtype=torch.float32).unsqueeze(0)  # Adiciona dimensão de batch
        print(f"Audio tensor shape before resample: {audio.shape}, Sample rate: {sample_rate}")

        if sample_rate != 16000:
            print("Realizando resample")
            audio = F.resample(audio, sample_rate, 16000)
        
        return audio

class tmp_model_test:
    def __init__(self):
        pass

    def load_process_audio(self, audio_array: np.ndarray, sample_rate: int = 22100) -> np.ndarray:
        # Retorna o áudio como array numpy
        print(f"Audio array shape: {audio_array.shape}, Sample rate: {sample_rate}")
        
        if sample_rate != 16000:
            print("Resample seria necessário (não implementado sem torch)")
        
        return audio_array

    def model_infer(self, audio):
        # Retorna um embedding fixo para teste como numpy array
        emb = np.zeros((1, 256), dtype=np.float32)  # Embedding fixo
        return emb

model = ReDimNetModel()


def extract_audio_features(audio_array: np.ndarray, sample_rate: int = 22100) -> np.ndarray:
    """
    Extrai embeddings utilizando speaker models.
    
    Returns:
        np.ndarray: Array de features (embedding)
    """

    audio = model.load_process_audio(audio_array, sample_rate)
    features = model.model_infer(audio)
    
    return features


def concatenate_audio_arrays(audio_list: List[str]) -> np.ndarray:
    """
    Concatena múltiplos arrays de áudio serializados em JSON.
    
    Args:
        audio_list: Lista de strings JSON contendo arrays numpy
        
    Returns:
        Array numpy concatenado
    """
    arrays = []
    for audio_json in audio_list:
        audio_array = np.array(json.loads(audio_json), dtype=np.int16)
        arrays.append(audio_array)
    
    if not arrays:
        return np.array([], dtype=np.int16)
    
    return np.concatenate(arrays)


def generate_session_embedding(audio_arrays: List[str], sample_rate: int = 22100) -> List[float]:
    """
    Gera embedding único concatenando todos os áudios da sessão.
    
    Args:
        audio_arrays: Lista de arrays de áudio serializados em JSON
        sample_rate: Taxa de amostragem
        
    Returns:
        Lista de features que representa o embedding da sessão
    """
    # Concatenar todos os áudios
    concatenated_audio = concatenate_audio_arrays(audio_arrays)
    
    if len(concatenated_audio) == 0:
        return []
    
    # Extrair features do áudio concatenado
    return extract_audio_features(concatenated_audio, sample_rate)