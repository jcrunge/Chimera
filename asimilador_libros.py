import os
import pypdf
import chromadb
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

# Conectar a la base de datos que usa el Motor Neuronal
chroma_client = chromadb.PersistentClient(path="./BaseDatos_Vectorial")
memoria_colectiva = chroma_client.get_or_create_collection(name="memoria_neuronal")

CHUNK_SIZE = 2000
OVERLAP = 200

def procesar_libros(directorio):
    if not os.path.exists(directorio):
        console.print(f"[red]❌ El directorio {directorio} no existe.[/red]")
        return
        
    archivos_pdf = [f for f in os.listdir(directorio) if f.lower().endswith('.pdf')]
    if not archivos_pdf:
        console.print(f"[yellow]⚠️ No se encontraron archivos PDF en {directorio}.[/yellow]")
        return
        
    console.print(f"[bold cyan]📚 Encontrados {len(archivos_pdf)} libros para asimilar.[/bold cyan]")
    
    libros_asimilados = []
    
    for archivo in archivos_pdf:
        ruta = os.path.join(directorio, archivo)
        nombre_libro = os.path.splitext(archivo)[0]
        console.print(f"\n[bold yellow]📖 Procesando:[/bold yellow] {nombre_libro}")
        
        try:
            reader = pypdf.PdfReader(ruta)
            texto_completo = ""
            for i, pagina in enumerate(reader.pages):
                texto = pagina.extract_text()
                if texto:
                    texto_completo += texto + "\n"
                    
            if not texto_completo:
                console.print(f"[red]❌ No se pudo extraer texto de {archivo}.[/red]")
                continue
                
            # Chunking básico
            chunks = []
            for i in range(0, len(texto_completo), CHUNK_SIZE - OVERLAP):
                chunks.append(texto_completo[i:i + CHUNK_SIZE])
                
            console.print(f"   [cyan]🧩 Dividido en {len(chunks)} fragmentos.[/cyan]")
            
            # Vectorizar e insertar
            ids = [f"book_{nombre_libro.replace(' ', '_')}_{j}_{int(time.time())}" for j in range(len(chunks))]
            metadatas = [{"autor": "AsimiladorLibros", "origen": nombre_libro} for _ in range(len(chunks))]
            
            # Insertar en lotes para evitar sobrecarga de memoria
            lote_tam = 100
            for i in range(0, len(chunks), lote_tam):
                memoria_colectiva.add(
                    documents=chunks[i:i+lote_tam],
                    metadatas=metadatas[i:i+lote_tam],
                    ids=ids[i:i+lote_tam]
                )
            
            console.print(f"[green]✅ {nombre_libro} asimilado correctamente en ChromaDB.[/green]")
            libros_asimilados.append(nombre_libro)
            
        except Exception as e:
            console.print(f"[red]❌ Error procesando {archivo}: {e}[/red]")
            
    # Escribir el chip cognitivo
    if libros_asimilados:
        chip_path = "Chips_Cognitivos/chip_biblioteca.txt"
        os.makedirs("Chips_Cognitivos", exist_ok=True)
        with open(chip_path, "w", encoding="utf-8") as f:
            f.write("# CHIP COGNITIVO: BIBLIOTECA (MEMORIA LOCAL)\n")
            f.write("Tienes acceso instantáneo al contenido de los siguientes libros guardados en tu memoria ChromaDB. ")
            f.write("Si el usuario te pregunta algo relacionado a estos temas, prioriza hacer búsquedas en la memoria local con palabras clave y sin usar comillas:\n\n")
            for libro in libros_asimilados:
                f.write(f"- {libro}\n")
        
        console.print(Panel(f"[bold green]🎉 PROCESO COMPLETADO[/bold green]\nSe han asimilado {len(libros_asimilados)} libros.\nSe generó el 'Mapa Mental' en {chip_path}", border_style="green"))

if __name__ == "__main__":
    console.print("\n[bold reverse white]  >>> ASIMILADOR DE LIBROS PDF <<<  [/bold reverse white]\n")
    procesar_libros("Biblioteca")
