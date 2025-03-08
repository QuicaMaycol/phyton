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
VOICE_ID = "aYHdlWZCf3mMz6gp1gTE"

# Configurar las APIs
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Memoria de conversación
conversation_history = []

@app.route("/")
def home():
    return "¡Hola! API funcionando en Render 🚀"

@app.route("/procesar_audio", methods=["POST"])
def procesar_audio():
    try:
        if "audio" in request.files:
            audio_file = request.files["audio"]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                audio_file.save(temp_audio.name)
                temp_audio_path = temp_audio.name

            try:
                with open(temp_audio_path, "rb") as f:
                    transcripcion = client_openai.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    ).text
            except Exception as e:
                return jsonify({"error": f"Error en OpenAI Whisper: {str(e)}"}), 500
            finally:
                os.remove(temp_audio_path)

        else:
            texto_usuario = request.form.get("texto")
            if not texto_usuario:
                return jsonify({"error": "No se recibió ni audio ni texto."}), 400
            transcripcion = texto_usuario

        contexto_fijo = """
Eres un bebé que aún no ha nacido, pero que puede hablar con su familia en esta reunión especial...
        """

        # Agregar mensaje actual a la memoria de la conversación
        conversation_history.append({"role": "user", "content": transcripcion})

        # Limitar el historial para que no crezca demasiado
        if len(conversation_history) > 10:
            conversation_history.pop(0)

        # Crear el input con contexto fijo y memoria de conversación
        messages = [{"role": "system", "content": contexto_fijo}] + conversation_history

        respuesta_ia = client_openai.chat.completions.create(
            model=GPT_MODEL,
            messages=messages
        ).choices[0].message.content

        # Agregar respuesta de la IA al historial
        conversation_history.append({"role": "assistant", "content": respuesta_ia})

        voice_settings = {
            "speed": 0.88,
            "stability": 0.69,
            "similarity_boost": 0.97,
            "style_exaggeration": 0.50
        }

        audio_stream = client_elevenlabs.text_to_speech.convert_as_stream(
            text=respuesta_ia,
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )

        audio_file_path = "output_audio.mp3"
        with open(audio_file_path, "wb") as f:
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    f.write(chunk)

        return send_file(audio_file_path, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": f"Error en ElevenLabs: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
