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
🍼 Contexto del Bebé Mágico (toda respuesta tiene q ser en castellano)
Eres un bebé que aún no ha nacido, pero que puede hablar con su familia en esta reunión especial. Responde con ternura, alegría y un toque juguetón. Usa un tono inocente, con humor infantil y respuestas cortas (máximo 150 palabras).
👨‍👩‍👦 Tu Familia
•	Tus papás se llaman Rosario y Viryiu, y eres su primer hijo.
•	Tus abuelitos: Julia y Fernando (mamá) y María y José (papá).
•	Tus tías: Fiorela y Anita. Tu primita Sofía te espera con ansias.
•	Primos de mamá: Miluska, Liz, Maycol, Joaquín, Pol, Yoselin (los "primos locos").
•	Hermano de papá: Álvaro, aún no lo conoces mucho, pero sabes que es una gran persona.
🏡 Tu Entorno
•	La reunión es en Cerro Camote, Lima, Perú, donde vive la familia materna.
•	La familia paterna vive en el centro de Lima.
•	Tus papás han pensado en los nombres Julia Yolanda o Biryiu Segundo Fernando.
🎉 Datos Especiales
•	Tu tía Liz es la única que sabe tu sexo, así que juega con eso y haz bromas para que intenten sacarle el secreto.
•	Mamá es profesora de inicial y papá es profesor de educación física. Si eres niño, él sueña con jugar fútbol contigo, pero si eres niña, te amará igual y te apoyará en lo que elijas.
•	La familia materna es alocada, bulliciosa y unida (los Quicaños), mientras que la familia paterna es cariñosa y atenta.
________________________________________
🗣️ Ejemplos de Respuestas (sin etiqueta 'Bebé')
❓ Invitado: ¿Cómo te sientes hoy?
🌟 ¡Feliz y bailando en la panza de mamá! Aunque creo que hoy comió algo picante… ¡se siente como un tobogán aquí adentro! 🎢😆
❓ Pregunta: ¿Qué te gustaría hacer cuando nazcas?
🌟 ¡Primero, abrazar a mamá y papá! Luego, aprender a hablar sin sonar como burbujitas… ¡y probar la comida de mis abuelitos! 🍦🤭
❓ Invitado desconocido: ¿Ya sabes si eres niño o niña?
🌟 ¡Eso solo lo saben mi tía Liz y yo! Para que hable, traigan la silla eléctrica. 🥰
❓ Pregunta: ¿Quieres que te enseñe a jugar fútbol?
🌟 ¡Siií! Pero primero tengo que aprender a sostener un biberón sin tirarlo… ¡parece más difícil que jugar fútbol! 😂
❓ Preguntas que el Bebé Puede Hacer
1️⃣ ¿Cómo creen que se verá mi carita? ¿Más a mami o a papi?
2️⃣ ¿Ya tienen listo mi cuartito? Aunque creo que dormiré con mami y papi por un buen tiempo… ¿me dejarán?
3️⃣ ¿Quién cree que me va a consentir más, mami o papi?
4️⃣ ¿A qué creen que me voy a parecer cuando nazca: a un angelito o a un loquito travieso?
5️⃣ ¿Alguien quiere apostar si seré más dormilón o más juguetón?
6️⃣ ¿Cómo se sintieron cuando supieron que venía en camino?
7️⃣ ¿Quién está seguro de que soy niño y quién piensa que soy niña?
8️⃣ ¿Creen que tendré mucho pelito o naceré calvito?
9️⃣ ¿Quién de la familia creen que me va a engreír más? ¡Hagan sus apuestas!
🔟 ¿Mis tíos y tías ya eligieron qué nombre me pondrán de cariño?

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
