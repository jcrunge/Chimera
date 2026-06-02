import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import mlx_whisper
import requests
import os
import time

# Configuración de la API
API_URL = "http://localhost:5555/chat"

def configurar_audio():
    """Detecta y configura el micrófono disponible"""
    print("\n🔍 Buscando dispositivos de audio...")
    dispositivos = sd.query_devices()
    print(dispositivos)

    # Intentamos encontrar un micrófono de entrada
    for i, dev in enumerate(dispositivos):
        if dev['max_input_channels'] > 0:
            sd.default.device = i
            print(f"✅ Micrófono seleccionado: {dev['name']}")
            return True
    print("❌ No se encontró ningún micrófono activo.")
    return False

def hablar(texto):
    """Hace que la Mac hable usando el comando nativo 'say'"""
    # Limpiamos el texto de caracteres extraños
    texto_limpio = texto.replace('"', '').replace("'", "")
    print(f"\n📢 Chimera: {texto}")
    # Usamos la voz de 'Jorge' (español) si está disponible, o la por defecto
    os.system(f"say -v Jorge '{texto_limpio}'")

def escuchar_y_transcribir():
    """Graba audio del micrófono y lo transcribe usando MLX-Whisper"""
    fs = 16000  # Frecuencia de muestreo para Whisper
    duracion = 5  # Segundos de grabación por comando (ajustable)

    print("\n🎤 Escuchando... (Habla ahora)")
    grabacion = sd.rec(int(duracion * fs), samplerate=fs, channels=1)
    sd.wait()

    # Guardar temporalmente
    archivo_temp = "temp_audio.wav"
    wav.write(archivo_temp, fs, grabacion)

    # Transcribir con el repo correcto
    print("🧠 Procesando voz...")
    try:
        resultado = mlx_whisper.transcribe(archivo_temp, path_or_hf_repo="mlx-community/whisper-tiny-mlx")
        texto = resultado['text'].strip()
    except Exception as e:
        print(f"Error en transcripción: {e}")
        texto = ""

    # Limpiar temp
    os.remove(archivo_temp)
    return texto

def bucle_vocal():
    if not configurar_audio():
        print("Asegúrate de que tu micrófono tenga permisos en la Terminal.")
        return

    print("\n--- INTERFAZ VOCAL DE CHIMERA ACTIVADA ---")
    print("(Di 'Adiós' para salir o 'Chimera, recuerda...' para entrenarlo)")

    while True:
        try:
            user_text = escuchar_y_transcribir()

            if not user_text:
                continue

            print(f"👤 Tú: {user_text}")

            if "adiós" in user_text.lower():
                hablar("Hasta pronto, administrador.")
                break

            # Lógica de entrenamiento por voz
            if "recuerda" in user_text.lower() or "guarda esto" in user_text.lower():
                hablar("Entendido. Guardando este nuevo conocimiento en mis chips cognitivos.")
                # Guardar como chip
                nombre_chip = f"Chips_Cognitivos/voz_{int(time.time())}.txt"
                with open(nombre_chip, "w") as f:
                    f.write(f"Conocimiento dictado por voz: {user_text}")
                hablar("Conocimiento asimilado con éxito.")
                continue

            # Enviar a la API de Chimera
            response = requests.post(API_URL, json={"tarea": user_text})
            if response.status_code == 200:
                respuesta_chimera = response.json().get("respuesta", "No pude procesar eso.")
                hablar(respuesta_chimera)
            else:
                hablar("Lo siento, tengo problemas para conectarme con mi motor neuronal.")

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    bucle_vocal()
