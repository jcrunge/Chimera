import httpx
import argparse
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import chromadb
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

# Conectar a la misma base de datos que usa el Motor Neuronal
chroma_client = chromadb.PersistentClient(path="./BaseDatos_Vectorial")
memoria_colectiva = chroma_client.get_or_create_collection(name="memoria_neuronal")

def limpiar_html(html_content):
    """Extrae solo el texto útil de un HTML y lo convierte a Markdown."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Eliminar scripts, estilos, header, nav y footer
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()
        
    # Obtener el contenido principal (intentando adivinar dónde está)
    main_content = soup.find('main') or soup.find('article') or soup.body
    
    if not main_content:
        return ""
        
    # Convertir a Markdown limpio
    markdown_text = md(str(main_content), heading_style="ATX", escape_asterisks=False)
    
    # Limpiar saltos de línea excesivos
    lineas = [linea for linea in markdown_text.split('\n') if linea.strip() != '']
    return '\n'.join(lineas)

def asimilar_url(url):
    console.print(f"\n[bold yellow]📡 Iniciando descarga desde:[/bold yellow] {url}")
    
    try:
        # 1. Descargar
        response = httpx.get(url, timeout=15.0)
        response.raise_for_status()
        console.print("[green]✔️ HTML descargado con éxito.[/green]")
        
        # 2. Limpiar y convertir a Markdown
        console.print("[cyan]🧹 Limpiando ruido y convirtiendo a formato Neuronal (Markdown)...[/cyan]")
        markdown_puro = limpiar_html(response.text)
        
        if not markdown_puro or len(markdown_puro) < 50:
            console.print("[red]❌ No se pudo extraer contenido útil de la página.[/red]")
            return

        # 3. Guardar en el Subconsciente (Vector DB)
        # Cortamos el documento si es inmenso, o lo guardamos entero (Chroma maneja internamente los límites del modelo de embeddings, pero es mejor asegurarnos).
        # Por simplicidad, guardamos todo el markdown.
        id_memoria = f"web_{int(time.time())}"
        
        console.print(f"[magenta]🧠 Vectorizando y guardando en ChromaDB ({len(markdown_puro)} caracteres)...[/magenta]")
        memoria_colectiva.add(
            documents=[markdown_puro],
            metadatas=[{"autor": "AsimiladorWeb", "url": url}],
            ids=[id_memoria]
        )
        
        console.print(Panel(f"[bold green]✅ CONOCIMIENTO ASIMILADO[/bold green]\nLa URL [blue]{url}[/blue] ha sido indexada.\nLas Neuronas ahora tienen acceso inmediato a esta información en sus próximos ciclos.", border_style="green"))
        
    except httpx.HTTPError as exc:
        console.print(f"[bold red]❌ Error de conexión al descargar la web:[/bold red] {exc}")
    except Exception as e:
        console.print(f"[bold red]❌ Ocurrió un error inesperado:[/bold red] {e}")

if __name__ == "__main__":
    console.print("\n[bold reverse white]  >>> ASIMILADOR DE CONOCIMIENTO EXTERNO <<<  [/bold reverse white]\n")
    console.print("Ingresa una URL técnica (documentación, tutorial, artículo) para descargarla y enviarla al subconsciente del motor.")
    
    while True:
        url_input = Prompt.ask("\n[bold cyan]🔗 URL a asimilar[/bold cyan] (o 'q' para salir)")
        if url_input.lower() in ['q', 'quit', 'exit']:
            break
        
        if url_input.startswith("http"):
            asimilar_url(url_input)
        else:
            console.print("[yellow]⚠️ Por favor, ingresa una URL válida que empiece con http o https.[/yellow]")
