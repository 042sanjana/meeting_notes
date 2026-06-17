from faster_whisper import WhisperModel

print("LOADING WHISPER")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("WHISPER LOADED")

segments, info = model.transcribe(
    "uploads/meeting1.wav"
)

for segment in segments:
    print(segment.text)