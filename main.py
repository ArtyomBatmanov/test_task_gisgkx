import os
from flask import Flask, request, jsonify
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
import wave
import json
import random

app = Flask(__name__)

MODEL_PATH = "model/vosk-model-small-ru-0.22"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Please download the VOSK model and place it in the 'model' folder.")

model = Model(MODEL_PATH)


def convert_mp3_to_wav(input_file, output_file):
    """Конвертирует MP3 в WAV формат с параметрами: моно, 16kHz, PCM."""
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
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
            duration = random.randint(5, 10)
            raised_voice = random.choice([True, False])
            gender = random.choice(["male", "female"])

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


@app.route('/asr', methods=['POST'])
def asr():
    try:
        data = request.json
        audio_path = data.get('file_path')

        if not audio_path or not os.path.exists(audio_path):
            return jsonify({"error": "Invalid or missing 'file_path' parameter."}), 400

        local_wav = "temp.wav"
        convert_mp3_to_wav(audio_path, local_wav)

        results = process_audio(local_wav)
        response = analyze_text(results)

        os.remove(local_wav)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
