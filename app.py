from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
from elevenlabs.client import ElevenLabs
import os
import tempfile

app = Flask(__name__)
CORS(app)

# Configurar API Keys desde variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
    raise ValueError("❌ ERROR: Faltan las claves API en las variables de entorno.")

GPT_MODEL = "gpt-3.5-turbo"
VOICE_ID = "MlvaOZdX5RhuFeF0WNFz"

client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

@app.route("/")
def home():
    return "¡Hola! API funcionando en Render 🚀"

@app.route("/procesar_audio", methods=["POST"])
def procesar_audio():
    """Convierte audio en texto, genera respuesta y devuelve audio"""
    if "audio" not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo de audio"}), 400

    audio_file = request.files["audio"]

    # Guardar el audio temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        audio_file.save(temp_audio.name)
        temp_audio_path = temp_audio.name

    # Convertir audio a texto con OpenAI Whisper
    with open(temp_audio_path, "rb") as f:
        transcripcion = client_openai.audio.transcriptions.create(
            model="whisper-1", file=f
        ).text

    # Generar respuesta con OpenAI GPT
    respuesta_ia = client_openai.chat.completions.create(
        model=GPT_MODEL, messages=[{"role": "user", "content": transcripcion}]
    ).choices[0].message.content

    # Generar audio con ElevenLabs
    audio = client_elevenlabs.text_to_speech.convert(text=respuesta_ia, voice_id=VOICE_ID)

    # Guardar audio generado
    output_audio_path = "output_audio.mp3"
    with open(output_audio_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Eliminar el archivo temporal de entrada
    os.remove(temp_audio_path)

    return send_file(output_audio_path, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
