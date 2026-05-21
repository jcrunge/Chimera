import chromadb
import shutil
import os
import time
import datetime
import re
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

console = Console()
DB_PATH = "./BaseDatos_Vectorial"

def obtener_coleccion():
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        return client.get_collection(name="memoria_neuronal")
    except Exception:
        return None

def mostrar_estado():
    coleccion = obtener_coleccion()
    if not coleccion:
        console.print("[yellow]⚠️ La memoria está vacía o no ha sido inicializada aún.[/yellow]")
        return

    cantidad = coleccion.count()
    console.print(f"\n[bold cyan]📊 Total de recuerdos almacenados:[/bold cyan] [bold magenta]{cantidad}[/bold magenta]")

def listar_recuerdos():
    coleccion = obtener_coleccion()
    if not coleccion:
        console.print("[yellow]⚠️ La memoria está vacía.[/yellow]")
        return
        
    # Obtener todos los datos de la colección
    datos = coleccion.get()
    
    if not datos['ids']:
        console.print("[yellow]📭 No hay recuerdos almacenados.[/yellow]")
        return
        
    # Organizar datos para ordenarlos
    lista_recuerdos = []
    for i in range(len(datos['ids'])):
        mem_id = datos['ids'][i]
        meta = datos['metadatas'][i]
        texto = datos['documents'][i]
        
        # Extraer timestamp del ID usando Regex
        timestamp = 0
        match = re.search(r'_(\d+)(_|$)', mem_id)
        if match:
            ts_str = match.group(1)
            # Si tiene 13 dígitos o más es en milisegundos, si no, es en segundos
            if len(ts_str) >= 13:
                timestamp = int(ts_str) / 1000.0
            else:
                timestamp = int(ts_str)
                
        fecha_hora = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp > 0 else "Fecha Desconocida"
        
        lista_recuerdos.append({
            'id': mem_id,
            'meta': meta,
            'texto': texto,
            'timestamp': timestamp,
            'fecha_hora': fecha_hora
        })
        
    # Ordenar de mayor a menor timestamp (Los más nuevos arriba)
    lista_recuerdos.sort(key=lambda x: x['timestamp'], reverse=True)
    
    table = Table(title="🧠 Detalles de la Memoria (Subconsciente)")
    table.add_column("Fecha/Hora", style="yellow")
    table.add_column("ID del Recuerdo", style="cyan", no_wrap=True)
    table.add_column("Autor/Origen", style="green")
    table.add_column("Contenido (Fragmento)", style="white")
    
    for r in lista_recuerdos:
        origen = r['meta'].get('autor', r['meta'].get('origen', 'Desconocido')) if r['meta'] else 'Desconocido'
        # Recortar el texto para que no desborde la pantalla
        fragmento = r['texto'][:60].replace("\n", " ") + "..." if len(r['texto']) > 60 else r['texto'].replace("\n", " ")
        table.add_row(r['fecha_hora'], r['id'], origen, fragmento)
        
    console.print(table)

def borrar_recuerdo_especifico():
    coleccion = obtener_coleccion()
    if not coleccion:
        return
        
    listar_recuerdos()
    id_borrar = Prompt.ask("\n[bold yellow]🗑️ Escribe el ID exacto del recuerdo que quieres eliminar (o 'cancelar')[/bold yellow]")
    
    if id_borrar.lower() == 'cancelar':
        return
        
    try:
        coleccion.delete(ids=[id_borrar])
        console.print(f"[bold green]✅ Recuerdo '{id_borrar}' borrado para siempre.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al borrar (verifica que el ID sea correcto):[/bold red] {e}")

def reiniciar_memoria():
    confirmacion = Prompt.ask("\n[bold red]⚠️ PELIGRO: ¿Estás seguro de que quieres borrar TODA la memoria (AMNESIA TOTAL)? (s/n)[/bold red]")
    if confirmacion.lower() == 's':
        try:
            if os.path.exists(DB_PATH):
                shutil.rmtree(DB_PATH)
                console.print("[bold green]✅ Memoria borrada con éxito. Jarvis no recordará nada la próxima vez.[/bold green]")
            else:
                console.print("[yellow]La base de datos no existe actualmente.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]❌ Error al intentar borrar la memoria:[/bold red] {e}")
    else:
        console.print("[blue]Operación cancelada.[/blue]")

if __name__ == "__main__":
    while True:
        console.print("\n[bold reverse white]  >>> PANEL DE CONTROL PSICOLÓGICO DE JARVIS <<<  [/bold reverse white]")
        console.print("1. Ver cantidad de recuerdos (Estado)")
        console.print("2. Leer los recuerdos detallados (Lista)")
        console.print("3. Borrar un recuerdo específico (Cirugía de memoria)")
        console.print("4. Formatear memoria (Amnesia total)")
        console.print("5. Salir")
        
        opcion = Prompt.ask("\n[cyan]Selecciona una acción[/cyan]", choices=["1", "2", "3", "4", "5"])
        
        if opcion == "1":
            mostrar_estado()
        elif opcion == "2":
            listar_recuerdos()
        elif opcion == "3":
            borrar_recuerdo_especifico()
        elif opcion == "4":
            reiniciar_memoria()
        elif opcion == "5":
            console.print("[magenta]Cerrando panel de control...[/magenta]")
            break
