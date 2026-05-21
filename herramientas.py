"""
Herramientas disponibles para el Harness de Jarvis.
Cada función es un wrapper simple que las Neuronas pueden usar.
"""
import os
import chromadb
from rich.console import Console

console = Console()

# ==========================================
# 1. MEMORIA VECTORIAL (ChromaDB)
# ==========================================
DB_PATH = "./BaseDatos_Vectorial"

def obtener_coleccion():
    """Obtiene o crea la colección principal de memoria."""
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(name="memoria_neuronal")

def buscar_memoria(query, n=3):
    """
    Busca en la memoria vectorial de Jarvis.
    
    Args:
        query: Texto a buscar.
        n: Número de resultados.
    
    Returns:
        str: Documentos encontrados concatenados, o cadena vacía.
    """
    try:
        coleccion = obtener_coleccion()
        if coleccion.count() == 0:
            return ""
        res = coleccion.query(query_texts=[query], n_results=min(n, coleccion.count()))
        if res['documents'] and res['documents'][0]:
            return "\n---\n".join(res['documents'][0])
        return ""
    except Exception as e:
        console.print(f"[yellow]⚠️ Error buscando en memoria: {e}[/yellow]")
        return ""

def guardar_en_memoria(texto, metadata=None, doc_id=None):
    """
    Guarda un documento en la memoria vectorial.
    
    Args:
        texto: El texto a guardar.
        metadata: dict con metadatos (autor, fuente, etc).
        doc_id: ID único del documento. Si no se da, se genera uno.
    """
    import time
    coleccion = obtener_coleccion()
    doc_id = doc_id or f"harness_{int(time.time())}"
    metadata = metadata or {"autor": "JarvisHarness"}
    coleccion.add(documents=[texto], metadatas=[metadata], ids=[doc_id])
    console.print(f"[green]💾 Guardado en memoria: {doc_id}[/green]")


# ==========================================
# 2. BÚSQUEDA WEB (DuckDuckGo)
# ==========================================
def buscar_web(query, max_resultados=5):
    """
    Busca en internet usando DuckDuckGo.
    
    Args:
        query: Texto a buscar en internet.
        max_resultados: Máximo de resultados a devolver.
    
    Returns:
        list[dict]: Lista de resultados con keys: 'title', 'url', 'body'
                    Lista vacía si falla.
    """
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=max_resultados))
        
        console.print(f"[cyan]🌐 Encontrados {len(resultados)} resultados web para: '{query}'[/cyan]")
        return resultados
    except ImportError:
        console.print("[red]❌ ddgs no instalado. Ejecuta: pip install ddgs[/red]")
        return []
    except Exception as e:
        console.print(f"[yellow]⚠️ Error en búsqueda web: {e}[/yellow]")
        return []

def formatear_resultados_web(resultados):
    """
    Convierte resultados de búsqueda web a texto plano para inyectar como contexto.
    
    Args:
        resultados: Lista de dicts de buscar_web().
    
    Returns:
        str: Texto formateado con título, URL y snippet de cada resultado.
    """
    if not resultados:
        return "No se encontraron resultados."
    
    lineas = []
    for i, r in enumerate(resultados, 1):
        lineas.append(f"[{i}] {r.get('title', 'Sin título')}")
        lineas.append(f"    URL: {r.get('href', r.get('url', r.get('link', 'N/A')))}")
        lineas.append(f"    {r.get('body', r.get('snippet', 'Sin descripción'))}")
        lineas.append("")
    return "\n".join(lineas)


# ==========================================
# 3. SANDBOX DOCKER
# ==========================================
def ejecutar_en_sandbox(codigo, sandbox_instance=None):
    """
    Ejecuta código Python en el sandbox Docker.
    
    Args:
        codigo: String con el código Python a ejecutar.
        sandbox_instance: Instancia de DockerSandbox ya creada (opcional).
    
    Returns:
        tuple: (exito: bool, salida: str)
    """
    if sandbox_instance:
        return sandbox_instance.ejecutar_codigo(codigo)
    
    # Si no hay instancia, crear una temporal
    try:
        from docker_sandbox import DockerSandbox
        sandbox = DockerSandbox()
        resultado = sandbox.ejecutar_codigo(codigo)
        sandbox.apagar()
        return resultado
    except Exception as e:
        return False, f"Error creando sandbox: {e}"


# ==========================================
# 4. SISTEMA DE ARCHIVOS (WORKSPACE)
# ==========================================
WORKSPACE_PATH = "./workspace"

def leer_archivo(path):
    """
    Lee un archivo del workspace.
    
    Args:
        path: Ruta relativa al workspace, o absoluta.
    
    Returns:
        str: Contenido del archivo, o mensaje de error.
    """
    # Si es ruta relativa, construir desde workspace
    if not os.path.isabs(path):
        path = os.path.join(WORKSPACE_PATH, path)
    
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"[ERROR] Archivo no encontrado: {path}"
    except Exception as e:
        return f"[ERROR] No se pudo leer {path}: {e}"

def listar_workspace():
    """Lista los archivos en el workspace."""
    try:
        archivos = os.listdir(WORKSPACE_PATH)
        return archivos
    except:
        return []


# ==========================================
# 5. CHIPS COGNITIVOS
# ==========================================
CHIPS_PATH = "./Chips_Cognitivos"

def cargar_chip(nombre_chip):
    """
    Carga un chip cognitivo por nombre.
    
    Args:
        nombre_chip: Nombre del archivo sin extensión (ej: 'chip_investigador')
    
    Returns:
        str: Contenido del chip, o cadena vacía si no existe.
    """
    path = os.path.join(CHIPS_PATH, f"{nombre_chip}.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""
