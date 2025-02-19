import openai
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import simpleaudio as sa  # Librería para reproducir audio en tiempo real

# 🔹 CONFIGURA TUS CLAVES API 🔹
OPENAI_API_KEY = "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"
ELEVENLABS_API_KEY = "sk_0388b0594628d734ecccfbae85168b3082e444884fd41403"
GPT_MODEL = "gpt-3.5-turbo"  # Usa "gpt-4" si tienes acceso
VOICE_ID = "sd1ju7WLrhatskFTLPsP"  # ID de la voz en ElevenLabs

# 🔹 Configurar las APIs
client_openai = OpenAI(api_key=OPENAI_API_KEY)
client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def generar_respuesta(texto_usuario):
    """Genera respuesta con la IA"""
    respuesta = client_openai.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": texto_usuario}]
    )
    return respuesta.choices[0].message.content

def reproducir_audio_en_vivo(texto):
    """Reproduce el audio directamente desde ElevenLabs sin descargarlo"""
    print("🎵 Reproduciendo en vivo desde ElevenLabs...")

    # Generar el audio en stream
    audio_stream = client_elevenlabs.text_to_speech.convert(text=texto, voice_id=VOICE_ID)

    # Leer y reproducir el stream de audio
    audio_data = b"".join(audio_stream)  # Convertir el generador en bytes
    wave_obj = sa.WaveObject(audio_data, num_channels=1, bytes_per_sample=2, sample_rate=44100)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # Espera a que termine de reproducirse

if __name__ == "__main__":
    print("💬 Escribe algo para que la IA responda:")
    entrada_usuario = input("Tú: ")
    
    respuesta_ia = generar_respuesta(entrada_usuario)
    print(f"🤖 IA: {respuesta_ia}")
    
    print("🔊 Reproduciendo directamente desde ElevenLabs...")
    reproducir_audio_en_vivo(respuesta_ia)
