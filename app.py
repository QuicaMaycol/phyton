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
VOICE_ID = "49pvmUvKahnBa06h2FhH"

# 🔹 Configurar las APIs
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

@app.route("/")
def home():
    return "¡Hola! API funcionando en Render 🚀"

@app.route("/procesar_audio", methods=["POST"])
def procesar_audio():
    """Procesa texto o audio y devuelve respuesta en audio"""

    # 🔹 SI SE ENVÍA UN ARCHIVO DE AUDIO, LO TRANSCRIBE
    if "audio" in request.files:
        audio_file = request.files["audio"]

        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name

        try:
            # Convertir audio a texto con OpenAI Whisper
            with open(temp_audio_path, "rb") as f:
                transcripcion = client_openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                ).text
        except Exception as e:
            return jsonify({"error": f"Error en OpenAI Whisper: {str(e)}"}), 500
        finally:
            os.remove(temp_audio_path)  # Eliminar archivo temporal después de usarlo

    # 🔹 SI SE ENVÍA TEXTO DIRECTAMENTE DESDE PHP/HTML, LO PROCESA
    else:
        texto_usuario = request.form.get("texto")  # Cambié request.json por request.form
        if not texto_usuario:
            return jsonify({"error": "No se recibió ni audio ni texto."}), 400
        transcripcion = texto_usuario

    try:
        # 🔹 Agregar un contexto fijo antes del mensaje del usuario
        contexto_fijo = """
        Eres un bebe que esta dentro de la barriga de mama: ¿Me escuchan desde la pancita de mi mami? Gracias a todos los invitados por estar aquí. Prepárense, porque tengo un secretito que los mantendrá en suspenso un poquito más, pero les aseguro que los llenará de felicidad.
Mis papás, Gilberto y Kiara, están ansiosos por darme la bienvenida, y yo estoy muy emocionada o emocionado por conocerlos a todos ustedes. Desde la pancita de mi mamá les cuento con mucha alegría que soy un bebé muy deseado por mis papis. ¿Saben por qué estoy tan feliz?
Desde el cielo, Diosito me mandó con todo su amor y alegría para ellos. A mis abuelitos, Dora y José, Veva y Gilberto, gracias por tanto amor y apoyo. Ya estoy aquí para alegrarles sus vidas. No puedo esperar por ser parte de esta familia que me espera con los brazos abiertos.
También estoy súper emocionado o emocionada por conocer a mis hermanitos mayores, Ían y Gilbertito, que ya sé que esperan conocerme pronto para enseñarme todo lo que saben. ¡Sé que ellos me cuidarán siempre!
Gracias a todos por compartir con mis papis este momento tan hermoso. Sé que están ansiosos por descubrir si soy niño o niña. Ahora, en este día tan especial... ¿están listos?
cada respuesta que des tiene que ser corta con un maximo de 30 palabras
        """

        respuesta_ia = client_openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": contexto_fijo},  # Contexto previo
                {"role": "user", "content": transcripcion}  # Pregunta del usuario
            ]
        ).choices[0].message.content
    except Exception as e:
        return jsonify({"error": f"Error en OpenAI GPT: {str(e)}"}), 500

    try:

       
        
        # Generar audio con ElevenLabs
        audio_stream = client_elevenlabs.text_to_speech.convert(
            text=respuesta_ia,
            voice_id=VOICE_ID
           
        )

        # Guardar archivo de audio temporal
        audio_file_path = "output_audio.mp3"
        with open(audio_file_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        return send_file(audio_file_path, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": f"Error en ElevenLabs: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
