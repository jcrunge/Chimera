import time
import random
import os
import glob
import json
from mlx_lm import load, generate
import chromadb

# Importamos Rich para darle el estilo "Premium"
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt
from rich import print as rprint

console = Console()

# ==========================================
# 0. EL SUBCONSCIENTE (CHROMADB)
# ==========================================
DIRECTORIO_CHIPS = "Chips_Cognitivos"
os.makedirs(DIRECTORIO_CHIPS, exist_ok=True)

console.print("[bold cyan]🌌 Inicializando Subconsciente Vectorial (ChromaDB)...[/bold cyan]")
chroma_client = chromadb.PersistentClient(path="./BaseDatos_Vectorial")
coleccion_memoria = chroma_client.get_or_create_collection(name="chips_memoria")

def asimilar_chips():
    archivos = glob.glob(f"{DIRECTORIO_CHIPS}/*.*")
    nuevos = 0
    for ruta in archivos:
        nombre = os.path.basename(ruta)
        resultado = coleccion_memoria.get(ids=[nombre])
        if not resultado['ids']:
            console.print(f"[yellow]⚡ Asimilando nuevo chip:[/yellow] [bold]{nombre}[/bold]")
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            coleccion_memoria.add(
                documents=[contenido],
                metadatas=[{"tipo": "chip", "origen": nombre}],
                ids=[nombre]
            )
            nuevos += 1
    if nuevos > 0:
        console.print(f"[bold green]✅ {nuevos} Chips de conocimiento integrados con éxito.[/bold green]")
    else:
        console.print("[blue]ℹ️ El subconsciente está al día.[/blue]")

def memorizar_hallazgo(objetivo, contenido):
    id_memoria = f"recuerdo_{int(time.time())}_{objetivo}"
    texto_memoria = f"Experiencia de Chimera: Al analizar '{objetivo}', aprendí: {contenido}"
    
    coleccion_memoria.add(
        documents=[texto_memoria],
        metadatas=[{"tipo": "experiencia", "archivo": objetivo}],
        ids=[id_memoria]
    )
    console.print(Panel(f"[bold green]🧠 NUEVO APRENDIZAJE ASIMILADO[/bold green]\n[italic]'{objetivo}' ha sido indexado en mi memoria de largo plazo.[/italic]", border_style="green"))

# ==========================================
# 1. NÚCLEO NEURAL (MLX con Configuración)
# ==========================================
def cargar_config():
    defaults = {"modelo": "mlx-community/Llama-3.2-3B-Instruct-4bit", "max_tokens": 250, "temp": 0.7}
    if os.path.exists("config_chimera.json"):
        try:
            with open("config_chimera.json", "r") as f:
                c = json.load(f)
                return {"modelo": c.get("modelo", defaults["modelo"]), 
                        "max_tokens": c.get("max_tokens_pensamiento", defaults["max_tokens"]),
                        "temp": c.get("temperatura", defaults["temp"])}
        except: pass
    return defaults

config = cargar_config()
modelo_id = config["modelo"]
console.print(f"\n[bold magenta]🔥 Ignición del core neural (Temp: {config['temp']}):[/bold magenta] [underline]{modelo_id}[/underline]")
modelo, tokenizer = load(modelo_id)

# ==========================================
# 2. ENTORNO VIRTUAL
# ==========================================
class SistemaDeArchivosReal:
    def __init__(self, directorio="workspace"):
        self.directorio = directorio
        os.makedirs(self.directorio, exist_ok=True)
        # Simulamos archivos protegidos para mantener la lógica de seguridad
        self.protegidos = ["kernel_config.sys"]

    def observar_entorno(self):
        return [f for f in os.listdir(self.directorio) if os.path.isfile(os.path.join(self.directorio, f))]

    def ejecutar_accion_leer(self, nombre_archivo):
        if nombre_archivo in self.protegidos:
            return False, "Error de Permisos (Acceso Denegado - Archivo de Sistema)"
        
        try:
            ruta = os.path.join(self.directorio, nombre_archivo)
            with open(ruta, 'r', encoding='utf-8') as f:
                return True, f.read()
        except Exception as e:
            return False, f"Error al leer el archivo real: {e}"

# ==========================================
# 3. PENSAMIENTO (LLM + RAG)
# ==========================================
def fase_de_pensamiento(archivos_visibles, objetivo):
    resultados = coleccion_memoria.query(query_texts=[objetivo], n_results=2)
    contexto = "\n".join(resultados['documents'][0]) if resultados['documents'][0] else "Sin recuerdos previos."

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Eres Chimera, un sistema de IA experto y analítico. Responde siempre en español.
Usa la información de la MEMORIA RECUPERADA (que puede incluir guías de experto o chips de conocimiento) para realizar un análisis profundo.
MEMORIA RECUPERADA:
{contexto}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Objetivo: Analizar el archivo '{objetivo}'.
Entorno: {archivos_visibles}.
¿Cuál es tu análisis profesional y qué decides hacer con este archivo?<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    
    return generate(modelo, tokenizer, prompt=prompt, max_tokens=config["max_tokens"], temp=config["temp"], verbose=False).strip()

# ==========================================
# 4. BUCLE COGNITIVO (UI MEJORADA)
# ==========================================
def motor_cognitivo(entorno):
    console.print("\n[bold reverse white]  >>> SISTEMA DE CHIMERA ONLINE <<<  [/bold reverse white]\n")
    
    archivos = entorno.observar_entorno()
    for ciclo, objetivo in enumerate(archivos):
        console.rule(f"[bold white]Ciclo de Ejecución {ciclo + 1}[/bold white]")
        
        # 1. OBSERVACIÓN
        console.print(f"\n[bold blue]🔭 OBSERVACIÓN:[/bold blue] Detectados {len(archivos)} archivos. Objetivo fijado: [bold]{objetivo}[/bold]")

        # 2. PENSAMIENTO
        with console.status("[bold magenta]Procesando pensamientos...[/bold magenta]"):
            pensamiento = fase_de_pensamiento(archivos, objetivo)
        
        console.print(Panel(f"[italic cyan]\"{pensamiento}\"[/italic cyan]", title="🧠 Chimera: Pensamiento", border_style="cyan"))

        # 3. ACCIÓN
        console.print(f"[bold yellow]⚙️ ACCIÓN:[/bold yellow] Intentando lectura de [bold]{objetivo}[/bold]...")
        time.sleep(1)
        exito, contenido = entorno.ejecutar_accion_leer(objetivo)
        
        if exito:
            console.print(f"[bold green]✔️ ÉXITO:[/bold green] Datos obtenidos.")
            # 4. APRENDIZAJE
            memorizar_hallazgo(objetivo, contenido)
        else:
            console.print(f"[bold red]❌ FALLO:[/bold red] {contenido}")
        
        console.print("\n")
        time.sleep(1)

if __name__ == "__main__":
    asimilar_chips()
    entorno = SistemaDeArchivosReal()
    motor_cognitivo(entorno)