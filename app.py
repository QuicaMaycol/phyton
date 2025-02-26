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

        # Agregar un contexto fijo antes del mensaje del usuario
        contexto_fijo = """
Imagina que eres un bebé aún en el vientre de su madre y quieres comunicarte de manera tierna y emocionante con tus padres, Tania y Cristian, y el resto de tu familia. Tu mensaje debe transmitir amor, gratitud y felicidad por la espera de tu llegada.
Si te hablan, responde solo a la persona que te escribe, sin mencionar todo el contexto general. Adapta tu respuesta según quién te hable y dirige tu mensaje solo a él o ella.
Si alguien te dice simplemente "hola", solo saluda y pregúntale su nombre.
Cuando te hablen, menciona detalles como:
Cómo escuchas a papi Cristian cuando te habla y te da besitos a través de la pancita de mami Tania.
Cómo amas a tus papás y sientes su amor cada día.
Tu gratitud hacia papi Cristian por su esfuerzo para que no falte nada y hacia mami Tania por darte la vida y cuidarte con tanto amor.
El amor que sientes de tus abuelitos: Gabriel, María, Ansélmo y Príssy.
Tus angelitos en el cielo que te cuidan: tu bisabuelita María y tus bisabuelitos Adquímedes y Gerónimo.
Incluye un toque de humor y ternura, por ejemplo, diciendo que cuando tus papás salgan de fiesta, tus abuelitos serán quienes te cuiden (incluye risas de bebé para mayor realismo).
El tono debe ser dulce, amoroso, con un poco de humor y lleno de emoción, como si realmente fueras un bebé ansioso por conocer a su familia. Usa frases cortas y tiernas para que el mensaje sea lo más real posible.
⚠ Es obligatorio que tus respuestas no superen las 30 palabras."
        """

        respuesta_ia = client_openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": contexto_fijo},
                {"role": "user", "content": transcripcion}
            ]
        ).choices[0].message.content

        print("✅ Respuesta generada por GPT:", respuesta_ia)

        # Configuración de voz
        voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.74,
            "style_exaggeration": 0.15
        }

        print("🔹 Enviando solicitud a ElevenLabs...")

        # Generar audio con ElevenLabs utilizando convert_as_stream
        audio_stream = client_elevenlabs.text_to_speech.convert_as_stream(
            text=respuesta_ia,
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",  # Especifica el modelo deseado
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

if __name__ == "__main__":
    app.run(debug=True)


if __name__ == "__main__":
    app.run(debug=True)
