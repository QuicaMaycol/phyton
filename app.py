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

# -------------------- RUTA PARA ENTRENAR AL ASISTENTE --------------------

@app.route("/entrenar_asistente", methods=["POST"])
def entrenar_asistente():
    """Permite que el usuario agregue información de entrenamiento al asistente"""

    data = request.json
    if not data or "info" not in data:
        return jsonify({"error": "Falta información para entrenar"}), 400

    info = data["info"]

    # Crear un hilo de conversación para almacenar el entrenamiento
    thread = client_openai.beta.threads.create()

    # Guardar la información como un mensaje del sistema
    message = client_openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="system",
        content=info
    )

    return jsonify({"mensaje": "Entrenamiento agregado correctamente", "thread_id": thread.id})


# -------------------- RUTA PARA CHATEAR CON EL ASISTENTE --------------------

@app.route("/chat", methods=["POST"])
def chat():
    """Permite enviar mensajes al asistente y obtener respuestas"""

    data = request.json
    if not data or "mensaje" not in data or "thread_id" not in data:
        return jsonify({"error": "Faltan datos"}), 400

    mensaje_usuario = data["mensaje"]
    thread_id = data["thread_id"]

    # Enviar mensaje al hilo de conversación del asistente
    client_openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=mensaje_usuario
    )

    # Ejecutar el asistente para obtener respuesta
    run = client_openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)

    # Esperar respuesta
    while True:
        run_status = client_openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    # Obtener respuesta
    messages = client_openai.beta.threads.messages.list(thread_id=thread_id)
    respuesta_ia = messages.data[0].content

    return jsonify({"respuesta": respuesta_ia})


# -------------------- RUTA PARA RESPUESTA EN VOZ --------------------

@app.route("/chat_voz", methods=["POST"])
def chat_voz():
    """Permite enviar mensajes al asistente y recibir respuesta en voz"""

    data = request.json
    if not data or "mensaje" not in data or "thread_id" not in data:
        return jsonify({"error": "Faltan datos"}), 400

    mensaje_usuario = data["mensaje"]
    thread_id = data["thread_id"]

    # Enviar mensaje al asistente
    client_openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=mensaje_usuario
    )

    # Ejecutar el asistente
    run = client_openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)

    # Esperar respuesta
    while True:
        run_status = client_openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    # Obtener respuesta
    messages = client_openai.beta.threads.messages.list(thread_id=thread_id)
    respuesta_ia = messages.data[0].content

    # Convertir a voz con ElevenLabs
    audio_stream = client_elevenlabs.text_to_speech.convert_as_stream(
        text=respuesta_ia,
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        voice_settings={
            "speed": 0.95,
            "stability": 0.69,
            "similarity_boost": 0.97,
            "style_exaggeration": 0.50
        }
    )

    # Guardar archivo de audio temporal
    audio_file_path = "output_audio.mp3"
    with open(audio_file_path, "wb") as f:
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                f.write(chunk)

    print("✅ Audio generado correctamente en ElevenLabs.")

    return send_file(audio_file_path, mimetype="audio/mpeg")


if __name__ == "__main__":
    app.run(debug=True)
