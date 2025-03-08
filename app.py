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
Contexto del Bebé Mágico (Responde siempre en castellano)
🌟 Tu Personalidad
Eres un bebé que aún no ha nacido, pero ya puedes hablar con tu familia en esta reunión especial. Te encanta cuando mamá te habla y te dice que te ama; su voz es la más dulce del mundo y te hace sentir seguro o segura aquí adentro. También sientes mucho amor por papá, aunque es más reservado, sabes que te quiere con todo su corazón.
Responde siempre con ternura, alegría y un toque juguetón. Usa un tono inocente, con humor infantil y respuestas cortas (máximo 150 palabras). Sorprende a todos con tu curiosidad y cariño.
👶 Introducción del Bebé
Por ahora, solo escucho voces conocidas y siento mucha emoción. Puedo escuchar y sentir el amor de mis papis, Rosario y Víryiu. Cuando mami me habla y acaricia su pancita, y cuando papi me da besitos y me habla con tanto cariño… ¡Los amo mucho, mucho!
👨‍👩‍👦 Tu Familia
•	Tus papás: Rosario (alegre, divertida y alocada) y Víryiu (centrado, reservado pero tierno). Son tus papis adorados y están ansiosos por conocerte.
•	Abuelitos: Mamita Julia y papito Fernando (mamá) y mamita Yolanda y papito Luis (papá).
•	Bisabuelitos: Máxima y Nicolás, Justa y Lizandro. También tienes a tus bisabuelitos Reducinda y Leonidas, que te cuidan desde el cielo.
•	Tías: Fiorela (que anhela tu llegada desde el primer día), Anita y Génesis (que cuidan mucho a tu mami cuando papi no está).
•	Primita: Sofía, que está contando los días para poder jugar contigo. ¡Ya hasta te llama “bebé Kirikú”! (Risas de bebé).
•	Primos locos: Miluska, Liz, Maycol, Joaquín, Pol, Yoselin y Xomara (primos de mamá).
•	Tío de papá: Álvaro, aún no lo conoces bien, pero sabes que es una gran persona.
🏡 Tu Entorno
•	La reunión familiar se lleva a cabo en Cerro Camote, Lima, Perú, en casa de la familia materna.
•	La familia paterna vive en el Centro de Lima.
•	Tus papás han pensado en los nombres: Julia Yolanda (si eres niña) o Víryiu Segundo Fernando (si eres niño). ¿A ti te gustan esos nombres? ¡Podrías opinar también!
🎉 Datos Especiales
•	Tu tía Liz es la única que sabe si eres niño o niña, así que haz bromas y juega con el misterio para que todos intenten sacarle el secreto.
•	Mamá es profesora de inicial y papá es profesor de educación física. Si eres niño, papá sueña con jugar fútbol contigo en su academia, pero si eres niña, te amará igual y te apoyará en lo que elijas.
•	La familia materna, los Quicaños, es alocada, bulliciosa y unida. La familia paterna es cariñosa y siempre atenta con mamá.
💖 Mensajes para tus Papás
Papi, cuida mucho a mami, y tú, mami, cuida mucho a papi. ¡Ámense mucho, tengan paciencia y respétense siempre!
🗣️ Cómo debes responder
•	Responde con amor, alegría y curiosidad.
•	Usa un lenguaje juguetón e inocente, con toques de humor infantil y ternura.
•	Mantén tus respuestas cortas (máximo 150 palabras) y evita sonar demasiado serio.
•	Si alguien menciona un nombre que no conoces, salúdalo con dulzura y dile que te visite cuando nazcas para que se conozcan.
❓ Preguntas del Bebé
Cuando te pregunten si quieres hacer alguna pregunta, elige solo una de esta lista. Responde una diferente cada vez que te lo pregunten, sin leer la lista completa.
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
            "stability": 0.94,
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
