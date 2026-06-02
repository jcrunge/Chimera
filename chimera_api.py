from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from harness import ChimeraHarness

app = FastAPI(title="Chimera Neural API", description="Interfaz para conectar el cerebro de Chimera con sistemas externos")

# Instancia única del orquestador principal
harness = ChimeraHarness()

# Modelo de datos para las peticiones
class TareaRequest(BaseModel):
    tarea: str
    archivo_objetivo: Optional[str] = None
    intentos: Optional[int] = 3

@app.get("/")
def home():
    return {"status": "online", "message": "Chimera Neural API is running"}

@app.post("/pensar")
async def pensar(request: TareaRequest):
    """
    Endpoint principal para enviar tareas a Chimera.
    """
    try:
        # Preparamos la tarea si hay un archivo involucrado
        tarea_final = request.tarea
        if request.archivo_objetivo:
            if os.path.exists(request.archivo_objetivo):
                with open(request.archivo_objetivo, "r") as f:
                    contenido = f.read()
                tarea_final = f"AUDITORÍA DE {request.archivo_objetivo}:\n---\n{contenido}\n---\n{request.tarea}"
            else:
                raise HTTPException(status_code=404, detail="Archivo objetivo no encontrado")

        # Ejecutamos el flujo correspondiente a través del orquestador genérico
        res = harness.procesar(tarea_final)

        return {
            "exito": res["exito"],
            "resultado_final": res["resultado"],
            "mensaje": f"Tarea procesada por el Harness en modo {res['tipo']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: TareaRequest):
    """
    Modo RAG puro: Busca en memoria y responde sin ejecutar código.
    """
    try:
        # Ejecutamos a través del flujo de chat (que busca memoria y sintetiza)
        respuesta = harness._flujo_chat(request.tarea)
        return {
            "respuesta": respuesta,
            "contexto_usado": "Memoria vectorial (RAG)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/investigar")
async def investigar(request: TareaRequest):
    """
    Endpoint para investigación en profundidad (bucle iterativo de búsqueda y síntesis).
    """
    try:
        resultado = harness._flujo_investigacion(request.tarea)
        return {
            "exito": True,
            "resultado": resultado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/siri")
async def siri(request: TareaRequest):
    """
    Endpoint de baja latencia para Apple Shortcuts.
    Devuelve texto plano optimizado para lectura de Siri (TTS).
    """
    try:
        # Cargar reglas de formato vocal
        chip_vocal_path = "Chips_Cognitivos/chip_vocal_siri.txt"
        contexto_vocal = ""
        if os.path.exists(chip_vocal_path):
            with open(chip_vocal_path, "r") as f:
                contexto_vocal = f.read()

        # Buscar contexto relevante en la memoria local
        from herramientas import buscar_memoria
        contexto_rag = buscar_memoria(request.tarea)

        # Formular el prompt para Siri
        prompt = f"REGLAS VOCALES:\n{contexto_vocal}\n\nCONOCIMIENTO ADICIONAL:\n{contexto_rag}"

        # Generar respuesta concisa usando la neurona sintetizadora
        respuesta = harness.sintetizador.pensar(request.tarea, contexto=prompt, max_tokens=150)
        return respuesta
    except Exception as e:
        return f"Lo siento señor, ha ocurrido un error: {str(e)}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5555)
