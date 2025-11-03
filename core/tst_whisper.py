import torch
from faster_whisper import WhisperModel

print("🧠 Torch CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("🚀 Using GPU:", torch.cuda.get_device_name(0))
else:
    print("🐢 Using CPU")

model_name = "base"  # or "small", "medium", etc.
model = WhisperModel(model_name, device="cuda" if torch.cuda.is_available() else "cpu")

print(f"✅ Faster-Whisper '{model_name}' model loaded successfully on",
      "CUDA" if torch.cuda.is_available() else "CPU")

# Optional quick test
# segments, info = model.transcribe("sample.wav")
# print("Transcript:", " ".join([s.text for s in segments]))
