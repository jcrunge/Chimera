"""
Indexador de Chips Cognitivos.

Recorre Chips_Cognitivos/, lee la metadata declarada en _metadata.json
(con fallback automático para chips sin entrada), e inserta cada chip
en la colección ChromaDB `indice_chips`. Para chips marcados como modo
'rag', además trocea el contenido y lo asimila en `memoria_neuronal`
para que pueda recuperarse luego por similaridad con filtro de origen.
"""
import os
import json
import time
import chromadb
from rich.console import Console
from rich.panel import Panel

console = Console()

CHIPS_PATH = "./Chips_Cognitivos"
METADATA_FILE = os.path.join(CHIPS_PATH, "_metadata.json")
DB_PATH = "./BaseDatos_Vectorial"

CHUNK_SIZE = 2000
OVERLAP = 200
TAMANO_INLINE_MAX = 8192  # 8KB; chips más grandes pasan a modo rag por defecto


def cargar_metadata_declarada():
    if not os.path.exists(METADATA_FILE):
        return {}
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]⚠️ No se pudo leer {METADATA_FILE}: {e}[/yellow]")
        return {}


def listar_chips():
    if not os.path.exists(CHIPS_PATH):
        return []
    return [
        f for f in os.listdir(CHIPS_PATH)
        if f.endswith(".txt") and not f.startswith("_")
    ]


def inferir_metadata(ruta, contenido):
    """Fallback para chips sin entrada en _metadata.json."""
    tamano = os.path.getsize(ruta)
    modo = "inline" if tamano <= TAMANO_INLINE_MAX else "rag"
    descripcion = contenido.strip()[:200].replace("\n", " ") or "Chip sin descripción declarada."
    return {
        "descripcion": descripcion,
        "keywords": [],
        "requiere_autorizacion": False,
        "modo": modo
    }


def chunkear(texto, tamano=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    paso = tamano - overlap
    for i in range(0, len(texto), paso):
        chunk = texto[i:i + tamano]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def indexar():
    metadata_declarada = cargar_metadata_declarada()
    archivos = listar_chips()
    if not archivos:
        console.print(f"[yellow]⚠️ No hay chips en {CHIPS_PATH}.[/yellow]")
        return

    client = chromadb.PersistentClient(path=DB_PATH)
    indice = client.get_or_create_collection(name="indice_chips")
    memoria = client.get_or_create_collection(name="memoria_neuronal")

    # Borrar índice previo para reindexación idempotente.
    existentes = indice.get()
    if existentes["ids"]:
        indice.delete(ids=existentes["ids"])
        console.print(f"[cyan]🧹 Limpiado índice previo ({len(existentes['ids'])} entradas).[/cyan]")

    indexados = 0
    rag_troceados = 0

    for archivo in archivos:
        ruta = os.path.join(CHIPS_PATH, archivo)
        nombre_chip = os.path.splitext(archivo)[0]

        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()

        meta = metadata_declarada.get(nombre_chip) or inferir_metadata(ruta, contenido)
        documento = meta["descripcion"] + " " + " ".join(meta.get("keywords", []))

        indice.add(
            documents=[documento],
            metadatas=[{
                "requiere_autorizacion": bool(meta.get("requiere_autorizacion", False)),
                "modo": meta.get("modo", "inline"),
                "ruta_archivo": ruta,
                "autor": "IndexadorChips"
            }],
            ids=[nombre_chip]
        )
        indexados += 1
        console.print(f"[green]✅ Indexado {nombre_chip} (modo={meta.get('modo')})[/green]")

        if meta.get("modo") == "rag":
            # Asimilar el contenido a memoria_neuronal con metadata de origen.
            # Limpiar fragmentos previos del mismo chip para evitar duplicados.
            previos = memoria.get(where={"origen": nombre_chip})
            if previos["ids"]:
                memoria.delete(ids=previos["ids"])
            chunks = chunkear(contenido)
            ts = int(time.time())
            ids = [f"chip_rag_{nombre_chip}_{j}_{ts}" for j in range(len(chunks))]
            metadatas = [
                {"origen": nombre_chip, "tipo": "chip_rag", "autor": "IndexadorChips"}
                for _ in chunks
            ]
            lote = 100
            for i in range(0, len(chunks), lote):
                memoria.add(
                    documents=chunks[i:i + lote],
                    metadatas=metadatas[i:i + lote],
                    ids=ids[i:i + lote]
                )
            rag_troceados += 1
            console.print(f"   [cyan]🧩 Troceado en {len(chunks)} fragmentos RAG.[/cyan]")

    console.print(Panel(
        f"[bold green]🎉 Indexación completada[/bold green]\n"
        f"Chips indexados: {indexados}\n"
        f"Chips troceados (modo rag): {rag_troceados}\n"
        f"Colección: indice_chips ({indice.count()} entradas)",
        border_style="green"
    ))


if __name__ == "__main__":
    console.print("\n[bold reverse white]  >>> INDEXADOR DE CHIPS COGNITIVOS <<<  [/bold reverse white]\n")
    indexar()
