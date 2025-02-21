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

# 🔹 Configurar las APIs
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

@app.route("/")
def home():
    return "¡Hola! API funcionando en Render 🚀"

@app.route("/procesar_audio", methods=["POST"])
def generar_audio():
    """Genera una respuesta con OpenAI y un audio con ElevenLabs"""
    data = request.json

    if not data or "texto" not in data:
        return jsonify({"error": "Falta el parámetro 'texto' en la solicitud."}), 400

    texto_usuario = data["texto"]

    # Generar respuesta con OpenAI
    respuesta_ia = client_openai.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": texto_usuario}]
    ).choices[0].message.content

    # Generar audio con ElevenLabs
    audio = client_elevenlabs.text_to_speech.convert(text=respuesta_ia, voice_id=VOICE_ID)

    # Guardar archivo de audio temporal
    audio_file = "output_audio.mp3"
    with open(audio_file, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Devolver el archivo de audio para reproducir en el navegador
    return send_file(audio_file, mimetype="audio/mpeg")
