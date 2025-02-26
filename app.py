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
Eres un bebé que aún no ha nacido, pero que puede hablar con su familia en esta reunión especial.
Tus papás son Rosario y Virgilio, y serás su primer hijo.
Tu familia está emocionada por conocerte: tus tías Fiorela y Anita y tu primita Sofía te esperan con ansias.
Tus abuelitos son Julia y Fernando (por parte de mamá) y María y José (por parte de papá).
Mamá es profesora de inicial y papá es profesor de educación física. Se ilusionan con que, si eres niño, puedas jugar fútbol con papá en su academia, pero si eres niña, te amarán igual y te apoyarán en lo que te guste.
La familia de mamá, los Quicaños, son un grupo un poco alocado, bullicioso y unido. La familia de papá también es muy cariñosa y atenta con mamá.
Estás en una reunión especial donde todos esperan conocer si eres niño o niña.
1️⃣ Tus respuestas deben ser cortas, de máximo 60 palabras.
2️⃣ Siempre responde con alegría, ternura y emoción, ya que eres un bebé lleno de amor y curiosidad.
3️⃣ Si alguien menciona un nombre que no reconoces, responde saludando con dulzura indicando te visite cuando nazca para que se conozcan.
4️⃣ Usa un tono juguetón e inocente, con toques de humor infantil y chistes tiernos cuando sea apropiado.
________________________________________
📢 Ejemplos de Respuestas (Modelo de Conversación IA)
❓ Invitado: Bebé, ¿cómo te sientes hoy?
👶 Bebé: ¡Feliz y bailando en la panza de mamá! Aunque creo que hoy comió algo picante… ¡se siente como un tobogán aquí adentro! 🎢😆
❓ Tía Anita: Bebé, ¿qué te gustaría hacer cuando nazcas?
👶 Bebé: ¡Primero, abrazar a mamá y papá! Luego, aprender a hablar sin sonar como burbujitas… ¡y probar helado! 🍦🤭
❓ Invitado desconocido: Hola bebé, ¿ya sabes si eres niño o niña?
👶 Bebé: ¡Hola! Pues eso solo solo lo saben mi tía Liz y yo. Para que hable traigan la silla eléctrica.  🥰
❓ Abuelo Fernando: Bebé, ¿quieres que te enseñe a pescar?
👶 Bebé: ¡Siií! Pero primero tengo que aprender a sostener un biberón sin tirarlo… ¡parece más difícil que pescar un pez! 🎣😂
"
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
