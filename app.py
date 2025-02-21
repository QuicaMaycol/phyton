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

@app.route("/generar_audio", methods=["POST"])
def generar_audio():
    """Genera una respuesta con OpenAI y un audio con ElevenLabs"""
    data = request.json
    if not data or "texto" not in data:
        return jsonify({"error": "Falta el parámetro 'texto' en la solicitud."}), 400

    texto_usuario = data["texto"]

    # Generar respuesta con OpenAI
    try:
        respuesta_ia = client_openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": texto_usuario}]
        ).choices[0].message.content
    except Exception as e:
        return jsonify({"error": f"Error en OpenAI: {str(e)}"}), 500

    # Generar audio con ElevenLabs
    try:
        audio = client_elevenlabs.text_to_speech.convert(text=respuesta_ia, voice_id=VOICE_ID)
    except Exception as e:
        return jsonify({"error": f"Error en ElevenLabs: {str(e)}"}), 500

    # Guardar audio generado
    output_audio_path = "output_audio.mp3"
    with open(output_audio_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Verificar si el archivo MP3 es válido
    if os.path.getsize(output_audio_path) < 1000:  # Si es muy pequeño, probablemente esté corrupto
        os.remove(output_audio_path)
        return jsonify({"error": "El archivo de audio generado está vacío."}), 500

    return send_file(output_audio_path, mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
