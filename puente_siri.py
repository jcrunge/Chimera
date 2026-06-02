import requests
import sys
import json

# Configuración de la API local
API_URL = "http://localhost:5555/siri"

def consultar_chimera(pregunta):
    """
    Se conecta a la API de Chimera que ya tiene el modelo en memoria.
    Esto permite una respuesta instantánea para Siri.
    """
    try:
        payload = {"tarea": pregunta}
        response = requests.post(API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            # La API ahora devuelve texto plano para /siri
            return response.text.strip().strip('"')
        else:
            return f"Error de conexión con el motor neuronal: {response.status_code}"
    except Exception as e:
        return f"Chimera no está disponible en este momento, señor. (Error: {str(e)})"

if __name__ == "__main__":
    # Soporte para argumentos (Siri envía el texto aquí)
    if len(sys.argv) > 1:
        entrada_usuario = " ".join(sys.argv[1:])
    else:
        # Fallback para entrada manual si se corre en terminal
        entrada_usuario = input("Dime algo: ").strip()

    if entrada_usuario:
        print(consultar_chimera(entrada_usuario))
    else:
        print("Chimera está listo. ¿En qué puedo ayudarle?")
