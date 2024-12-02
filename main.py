import os
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
import wave
import json
import random

MODEL_PATH = "model/vosk-model-small-ru-0.22"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Please download the VOSK model and place it in the 'model' folder.")

model = Model(MODEL_PATH)


def convert_mp3_to_wav(input_file, output_file):
    """Конвертирует MP3 в WAV формат."""
    audio = AudioSegment.from_mp3(input_file)
    audio.export(output_file, format="wav")


def process_audio(file_path):
    """Обрабатывает аудио файл и возвращает список реплик."""
    wf = wave.open(file_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        raise ValueError("Audio file must be WAV format mono PCM with 16kHz sample rate.")

    recognizer = KaldiRecognizer(model, wf.getframerate())
    recognizer.SetWords(True)
    results = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            results.append(result)

    final_result = json.loads(recognizer.FinalResult())
    results.append(final_result)
    return results


def analyze_text(result):
    """Анализирует текстовые данные для формирования JSON-ответа."""
    dialog = []
    receiver_duration = 0
    transmitter_duration = 0

    for res in result:
        if "text" in res and res["text"].strip():
            text = res["text"]
            duration = random.randint(5, 10)  # Заменить на реальную длительность, если возможно
            raised_voice = random.choice([True, False])  # Пример: определить тональность
            gender = random.choice(["male", "female"])  # Пример: определить пол

            source = "receiver" if random.choice([True, False]) else "transmitter"
            if source == "receiver":
                receiver_duration += duration
            else:
                transmitter_duration += duration

            dialog.append({
                "source": source,
                "text": text,
                "duration": duration,
                "raised_voice": raised_voice,
                "gender": gender
            })

    return {
        "dialog": dialog,
        "result_duration": {
            "receiver": receiver_duration,
            "transmitter": transmitter_duration
        }
    }


def main(audio_path):
    try:
        if not os.path.exists(audio_path):
            return {"error": f"File '{audio_path}' not found."}

        local_wav = "temp.wav"
        convert_mp3_to_wav(audio_path, local_wav)

        results = process_audio(local_wav)
        response = analyze_text(results)

        os.remove(local_wav)
        return response

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Пример использования
    input_audio = "test2.mp3"  # Укажите путь к локальному MP3 файлу
    output = main(input_audio)
    print(json.dumps(output, ensure_ascii=False, indent=4))
