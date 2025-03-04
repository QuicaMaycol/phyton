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

# Crear un nuevo hilo para recordar la conversación
thread = client_openai.beta.threads.create()
THREAD_ID = thread.id
print(f"✅ Conversación iniciada con ID: {THREAD_ID}")

@app.route("/")
def home():
    return "¡Hola! API funcionando en Render 🚀"

@app.route("/procesar_audio", methods=["POST"])
def procesar_audio():
    """Procesa texto o audio y devuelve respuesta en audio"""

    try:
        transcripcion = ""

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
                os.remove(temp_audio_path)  # Asegurar eliminación del archivo en caso de error
                return jsonify({"error": f"Error en OpenAI Whisper: {str(e)}"}), 500
            finally:
                os.remove(temp_audio_path)  # Eliminar archivo después de procesarlo

        else:
            texto_usuario = request.form.get("texto")
            if not texto_usuario:
                return jsonify({"error": "No se recibió ni audio ni texto."}), 400
            transcripcion = texto_usuario

        # Enviar el mensaje al mismo `thread_id`
        client_openai.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=transcripcion
        )

        # Ejecutar el asistente en el mismo hilo para recordar la conversación
        run = client_openai.beta.threads.runs.create(thread_id=THREAD_ID, assistant_id=GPT_MODEL)

        # Esperar respuesta
        while True:
            run_status = client_openai.beta.threads.runs.retrieve(thread_id=THREAD_ID, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)

        # Obtener la respuesta
        messages = client_openai.beta.threads.messages.list(thread_id=THREAD_ID)
        respuesta_ia = messages.data[0].content

        print("✅ Respuesta generada por GPT:", respuesta_ia)

        # Configuración de voz para ElevenLabs
        voice_settings = {
            "speed": 0.95,
            "stability": 0.69,
            "similarity_boost": 0.97,
            "style_exaggeration": 0.50
        }

        print("🔹 Enviando solicitud a ElevenLabs...")

        # Generar audio con ElevenLabs
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

        return send_file(audio_file_path, mimetype="audio/mpeg", as_attachment=False)

    except Exception as e:
        print(f"🚨 ERROR en procesar_audio: {str(e)}")
        return jsonify({"error": f"Error en procesar_audio: {str(e)}"}), 500

# -------------------- CONFIGURAR EL PUERTO EN RENDER --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usar el puerto que asigna Render
    app.run(host="0.0.0.0", port=port, debug=True)
