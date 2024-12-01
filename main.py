import os
from fastapi import FastAPI, UploadFile
from vosk import Model, KaldiRecognizer
import wave
import json
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

app = FastAPI()

# Загрузка модели VOSK
MODEL_PATH = "vosk-model-small-ru-0.22"  # Укажите путь к вашей модели
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("VOSK model not found!")
model = Model(MODEL_PATH)


# Функция для анализа аудио
def analyze_audio(file_path):
    audio = AudioSegment.from_file(file_path, format="mp3")
    audio = audio.set_channels(1)  # Преобразование в моно
    audio.export("temp.wav", format="wav")  # Сохранение как WAV

    # Открытие WAV файла для анализа
    # wf = wave.open("temp.wav", "rb")
    audio.export("temp.wav", format="wav")  # Конвертация в WAV
    wf = wave.open("temp.wav", "rb")

    if wf.getnchannels() != 1:
        raise ValueError("Audio must be mono channel.")
    if wf.getsampwidth() != 2:
        raise ValueError("Audio must be 16-bit.")
    if wf.getframerate() not in [8000, 16000]:
        raise ValueError("Audio sample rate must be 8k or 16k Hz.")

    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    dialog = []
    receiver_duration = 0
    transmitter_duration = 0

    # Обработка аудио через VOSK
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "")
            if text:
                # Условно разделяем на стороны receiver/transmitter
                side = "receiver" if len(dialog) % 2 == 0 else "transmitter"
                duration = len(audio) // 1000  # пример оценки длительности
                raised_voice = audio.dBFS > -20  # простая логика для определения громкости
                gender = "male" if side == "receiver" else "female"  # условно
                dialog.append({
                    "source": side,
                    "text": text,
                    "duration": duration,
                    "raised_voice": raised_voice,
                    "gender": gender,
                })
                if side == "receiver":
                    receiver_duration += duration
                else:
                    transmitter_duration += duration

    wf.close()
    os.remove("temp.wav")

    return {
        "dialog": dialog,
        "result_duration": {
            "receiver": receiver_duration,
            "transmitter": transmitter_duration
        }
    }


# POST-эндпоинт для обработки аудиофайла
@app.post("/asr")
async def asr(file: UploadFile):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        result = analyze_audio(file_path)
    finally:
        os.remove(file_path)

    return result

# Запуск приложения
# Используйте команду:
