from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
from elevenlabs.client import ElevenLabs
import os
import tempfile
import time

app = Flask(__name__)
CORS(app)

# Configurar API Keys desde variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
    raise ValueError("❌ ERROR: Faltan las claves API en las variables de entorno.")

GPT_MODEL = "gpt-4-turbo"
VOICE_ID = "aYHdlWZCf3mMz6gp1gTE"

# Inicializar clientes de OpenAI y ElevenLabs
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# -------------------- CREAR ASISTENTE --------------------

# Crear un asistente en OpenAI
assistant = client_openai.beta.assistants.create(
    name="MagicVoice AI",
    instructions="Eres un asistente especializado en ayudar con MagicVoice y MagicMemory. Responde con empatía y claridad.",
    model=GPT_MODEL
)

ASSISTANT_ID = assistant.id
print(f"✅ Asistente creado con ID: {ASSISTANT_ID}")

@app.route("/")
def home():
    return "¡Hola! API funcionando en Render 🚀"

@app.route("/procesar_audio", methods=["POST"])
def procesar_audio():
    """Procesa texto o audio y devuelve respuesta en audio"""

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

        # Enviar el texto al asistente
        respuesta_ia = client_openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": transcripcion}
            ]
        ).choices[0].message.content

        print("✅ Respuesta generada por GPT:", respuesta_ia)

        # Configuración de voz
        voice_settings = {
            "speed":0.95,
            "stability": 0.69,
            "similarity_boost": 0.97,
            "style_exaggeration": 0.50
        }

        print("🔹 Enviando solicitud a ElevenLabs...")

        # Generar audio con ElevenLabs utilizando convert_as_stream
        audio_stream = client_elevenlabs.text_to_speech.convert_as_stream(
            text=respuesta_ia,
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )

        # Guardar archivo de audio temporal
        audio_file_path = "output_audio.mp3"
        with open(audio_file_path, "wb") as f:
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    f.write(chunk)

        print("✅ Audio generado correctamente en ElevenLabs.")

        return send_file(audio_file_path, mimetype="audio/mpeg")

    except Exception as e:
        print(f"🚨 ERROR en ElevenLabs: {str(e)}")
        return jsonify({"error": f"Error en ElevenLabs: {str(e)}"}), 500

# -------------------- RUTA PARA PROCESAR IMÁGENES --------------------

@app.route("/procesar_imagen", methods=["POST"])
def procesar_imagen():
    """Procesa una imagen y devuelve una respuesta en texto o voz"""

    try:
        if "imagen" not in request.files:
            return jsonify({"error": "No se recibió una imagen."}), 400

        imagen_file = request.files["imagen"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_imagen:
            imagen_file.save(temp_imagen.name)
            imagen_path = temp_imagen.name

        # Enviar imagen a GPT-4 Turbo Vision
        response = client_openai.chat.completions.create(
            model="gpt-4-turbo-vision",
            messages=[
                {"role": "system", "content": "Describe la imagen con empatía."},
                {"role": "user", "content": [
                    {"type": "text", "text": "¿Qué ves en esta imagen?"},
                    {"type": "image_url", "image_url": {"url": f"file://{imagen_path}"}}
                ]}
            ]
        )

        respuesta_ia = response.choices[0].message.content
        os.remove(imagen_path)  # Borrar imagen después de procesarla

        print("✅ Respuesta generada por GPT Vision:", respuesta_ia)

        return jsonify({"respuesta": respuesta_ia})

    except Exception as e:
        print(f"🚨 ERROR: {str(e)}")
        return jsonify({"error": f"Error procesando imagen: {str(e)}"}), 500

# -------------------- CONFIGURAR EL PUERTO EN RENDER --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usar el puerto que asigna Render
    app.run(host="0.0.0.0", port=port, debug=True)
