import time
import os
import argparse
import chromadb
import json
from rich.console import Console
from rich.panel import Panel
from mlx_lm import load, generate
from docker_sandbox import DockerSandbox
import glob
import re

console = Console()

# ==========================================
# 1. LA SINAPSIS
# ==========================================
chroma_client = chromadb.PersistentClient(path="./BaseDatos_Vectorial")
coleccion_chips = chroma_client.get_or_create_collection(name="chips_memoria")

def buscar_conocimiento(query, n=3):
    res = coleccion_chips.query(query_texts=[query], n_results=n)
    return "\n".join(res['documents'][0]) if res['documents'] and res['documents'][0] else ""

# ==========================================
# 2. EL CEREBRO
# ==========================================
CONFIG_FILE = "config_jarvis.json"
def cargar_config():
    defaults = {"modelo": "mlx-community/Llama-3.2-3B-Instruct-4bit", "max_tokens_pensamiento": 1500, "temperatura": 0.1}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return {**defaults, **json.load(f)}
        except: pass
    return defaults

config = cargar_config()
modelo, tokenizer = load(config["modelo"])

# ==========================================
# 3. LA NEURONA
# ==========================================
class Neurona:
    def __init__(self, nombre, rol, instrucciones):
        self.nombre = nombre
        self.rol = rol
        self.instrucciones = instrucciones

    def pensar(self, tarea, contexto=""):
        prompt = f"""<|im_start|>system
Eres {self.nombre}, {self.rol}.
{self.instrucciones}
{contexto}
<|im_end|>
<|im_start|>user
{tarea}<|im_end|>
<|im_start|>assistant
"""
        with console.status(f"[bold magenta]{self.nombre} pensando...[/bold magenta]"):
            respuesta = generate(modelo, tokenizer, prompt=prompt, max_tokens=config["max_tokens_pensamiento"], verbose=False)
        
        texto = respuesta.strip()
        if "```python" in texto:
            texto = texto.split("```python")[1].split("```")[0].strip()
        elif "```" in texto:
            texto = texto.split("```")[1].strip()
        
        console.print(Panel(f"[italic]{texto}[/italic]", title=f"🧠 {self.nombre}", border_style="blue"))
        return texto

# ==========================================
# 4. BUCLE DE AUTO-CORRECCIÓN
# ==========================================
def ejecutar_red_neuronal(tarea, max_intentos=3):
    console.print("\n[bold reverse white]  >>> JARVIS NEURAL ENGINE ACTIVE <<<  [/bold reverse white]\n")
    
    if "mlx-whisper" in tarea.lower() or "mlx_whisper" in tarea.lower():
        tarea = tarea.replace("mlx-whisper", "whisper").replace("mlx_whisper", "whisper")

    sandbox = DockerSandbox()
    archivos = os.listdir("workspace")

    neurona_coder = Neurona(
        nombre="Coder-X", 
        rol="Audio AI Specialist", 
        instrucciones=f"""Genera código Python para análisis de audio en Docker.
1. Metadatos: Usa 'mutagen.flac' para obtener Artista y Título.
2. Transcripción: Usa 'whisper' con language='es'. Imprime [inicio - fin] texto.
3. Música: Usa 'librosa.feature.chroma_cqt' para Tonalidad (MAPEA A NOTA: C, C#, etc) y 'librosa.beat.beat_track' para BPM.
4. Salida: Escribe todo en '/workspace/resultado_analisis.txt'.
Archivos: {archivos}"""
    )
    
    neurona_tester = Neurona(
        nombre="Tester-Y", 
        rol="QA Auditor", 
        instrucciones="""Analiza la salida.
1. ¿La tonalidad es una NOTA (ej: C#) o un número feo? Si es número, es FALLO.
2. ¿La transcripción está en español?
3. ¿Están los metadatos (Artista/Título)?
4. Solo EXITO si todo es correcto y humano-legible."""
    )

    feedback = ""
    for intento in range(1, max_intentos + 1):
        console.rule(f"Ciclo {intento}/{max_intentos}")
        contexto = buscar_conocimiento(tarea)
        if feedback: contexto += f"\nFEEDBACK QA: {feedback}\n"
            
        codigo = neurona_coder.pensar(tarea, contexto)
        exito, salida = sandbox.ejecutar_codigo(codigo)
        
        # Leer el archivo de resultados para que el Tester lo vea
        try:
            with open("workspace/resultado_analisis.txt", "r") as f:
                contenido_final = f.read()
        except:
            contenido_final = "Archivo no encontrado o vacío."

        console.print(f"[bold cyan]📄 Contenido de resultado_analisis.txt:[/bold cyan]\n{contenido_final}")

        eval_qa = neurona_tester.pensar(f"Resultado:\n{contenido_final}\nError terminal: {salida if not exito else 'Ninguno'}")
        
        if "EXITO" in eval_qa.upper() and exito:
            console.print("[bold green]✅ COMPLETADO CON ÉXITO.[/bold green]")
            return True, codigo
        feedback = eval_qa
        time.sleep(1)

    sandbox.apagar()
    return False, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tarea", type=str, nargs='?')
    args = parser.parse_args()
    ejecutar_red_neuronal(args.tarea if args.tarea else "Saluda.")
