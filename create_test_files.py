import shutil
import time
from pathlib import Path

# Define source and destination paths
source_txt = "/home/alexandre/akcit/humano_digital/biometria_vr/a.txt"
source_audio = "/home/alexandre/akcit/humano_digital/biometria_vr/VR-voice-biometrics/data/0-0-xtts.wav"
destination_folder = "/home/alexandre/akcit/humano_digital/biometria_vr/VR-voice-biometrics/data/input"

# Create destination folder if it doesn't exist
Path(destination_folder).mkdir(parents=True, exist_ok=True)

# Repeat 3 times
for i in range(3):
    # Copy txt file
    txt_dest = Path(destination_folder)/f"file_{i+1}.txt"
    shutil.copy(source_txt, txt_dest)
    
    # Copy audio file
    audio_dest = Path(destination_folder)/f"audio_{i+1}.wav"
    shutil.copy(source_audio, audio_dest)
    
    print(f"Iteration {i+1}: Files copied")
    
    # Wait 2 seconds (skip on last iteration)
    if i < 2:
        time.sleep(2)

print("All files copied successfully")