import re
from rich.console import Console
from rich.panel import Panel
from mlx_lm import generate

console = Console()

class Neurona:
    """Un agente especializado con un rol y prompt de sistema fijo."""
    
    def __init__(self, nombre, rol, instrucciones, modelo=None, tokenizer=None):
        self.nombre = nombre
        self.rol = rol
        self.instrucciones = instrucciones
        self.modelo = modelo
        self.tokenizer = tokenizer

    def pensar(self, tarea, contexto="", max_tokens=1500):
        """
        Genera una respuesta usando el LLM.
        Args:
            tarea: La pregunta o instrucción para la neurona.
            contexto: Información adicional (RAG, feedback, etc).
            max_tokens: Máximo de tokens a generar.
        Returns:
            str: La respuesta generada (texto limpio, sin bloques de código).
        """
        # Construir prompt con formato ChatML
        prompt = f"""<|im_start|>system
Eres {self.nombre}, {self.rol}.
{self.instrucciones}
{contexto}
<|im_end|>
<|im_start|>user
{tarea}<|im_end|>
<|im_start|>assistant
"""
        if not self.modelo or not self.tokenizer:
            raise ValueError(f"Neurona '{self.nombre}' no tiene modelo asignado. Usa set_modelo() primero.")
        
        with console.status(f"[bold magenta]{self.nombre} pensando...[/bold magenta]"):
            respuesta = generate(self.modelo, self.tokenizer, prompt=prompt, max_tokens=max_tokens, verbose=False)
        
        texto = respuesta.strip()
        # Limpiar bloques de código markdown si los hay
        if "```python" in texto:
            texto = texto.split("```python")[1].split("```")[0].strip()
        elif "```json" in texto:
            texto = texto.split("```json")[1].split("```")[0].strip()
        elif "```" in texto:
            texto = texto.split("```")[1].strip()
        
        console.print(Panel(f"[italic]{texto[:500]}{'...' if len(texto) > 500 else ''}[/italic]", 
                           title=f"🧠 {self.nombre}", border_style="blue"))
        return texto
    
    def set_modelo(self, modelo, tokenizer):
        """Asigna un modelo y tokenizer a esta neurona."""
        self.modelo = modelo
        self.tokenizer = tokenizer


# ==========================================
# REGISTRY DE NEURONAS PREDEFINIDAS
# ==========================================
REGISTRY = {
    "investigador": {
        "nombre": "Investigador-Alpha",
        "rol": "Especialista en Investigación y Análisis de Información",
        "instrucciones": """Tu trabajo es investigar temas a fondo.
1. Analiza la pregunta del usuario y genera sub-preguntas específicas.
2. Evalúa la información que recibes como contexto.
3. Identifica qué información falta o es insuficiente.
4. Sintetiza hallazgos de forma clara y estructurada.
5. SIEMPRE indica la fuente de cada dato que mencionas.
6. PROTOCOLO DE EVALUACIÓN DE COMPLETITUD (cuando se te pida juzgar si una síntesis responde a una pregunta): Tu última línea SIEMPRE debe ser `<resultado>EXITO</resultado>` si responde por completo, o `<resultado>INCOMPLETO</resultado>` con explicación encima."""
    },
    "coder": {
        "nombre": "Coder-X",
        "rol": "Programador Python Experto",
        "instrucciones": """Generas código Python limpio y funcional.
1. Escribe código que se ejecute en un contenedor Docker con Python 3.11.
2. Incluye manejo de errores básico.
3. Los archivos de entrada/salida van en /workspace/.
4. Responde SOLO con el código Python, sin explicaciones.
5. Usa solo librerías estándar o las que se indiquen como disponibles."""
    },
    "tester": {
        "nombre": "Tester-Y",
        "rol": "Auditor de Calidad (QA)",
        "instrucciones": """Evalúas resultados de ejecución de código.
1. Analiza la salida del programa y los errores si los hay.
2. Verifica que el resultado cumple con la tarea original.
3. Si hay errores, describe EXACTAMENTE qué falló y por qué.
4. PROTOCOLO DE RESULTADO: Tu última línea SIEMPRE debe ser `<resultado>EXITO</resultado>` o `<resultado>FALLO</resultado>`. Encima describe la razón."""
    },
    "citation": {
        "nombre": "CitationAgent",
        "rol": "Verificador de Fuentes y Referencias",
        "instrucciones": """Tu trabajo es verificar y citar fuentes.
1. Recibes un texto y una lista de documentos fuente.
2. Para cada afirmación importante, busca la evidencia en los documentos.
3. Inserta referencias numeradas [1], [2], etc.
4. Al final, genera una sección de REFERENCIAS con las fuentes.
5. Si una afirmación no tiene fuente, márcala con [FALTA_FUENTE].
6. PROTOCOLO DE RESULTADO: Tu última línea SIEMPRE debe ser `<resultado>EXITO</resultado>` (todo verificado) o `<resultado>FALLO</resultado>` (hubo [FALTA_FUENTE] u otra inconsistencia)."""
    },
    "sintetizador": {
        "nombre": "Synth-Omega",
        "rol": "Sintetizador de Información",
        "instrucciones": """Combinas múltiples fragmentos de información en un reporte coherente.
1. Recibe resultados parciales de diferentes investigaciones.
2. Elimina redundancias y organiza la información lógicamente.
3. Escribe en español claro y profesional.
4. Estructura: Resumen > Hallazgos > Conclusión.
5. Mantén un tono objetivo y basado en datos."""
    },
    "planner": {
        "nombre": "Planner-Zero",
        "rol": "Planificador Global Dinámico",
        "instrucciones": """Eres el Planificador Global del sistema. Analizas la tarea del usuario y la divides en pasos atómicos y secuenciales.
Debes devolver ÚNICAMENTE un array JSON válido, sin Markdown (sin ```json), con este formato:
[
  {"tipo": "INVESTIGACION", "tarea": "Lo que se debe investigar..."},
  {"tipo": "CODIGO", "tarea": "Lo que se debe programar..."}
]
Los tipos válidos son: INVESTIGACION, CODIGO. Si la tarea es simple o solo charla, puedes usar "INVESTIGACION" como único paso.
Asegúrate de que la salida sea puro JSON analizable."""
    }
}


def crear_neurona(tipo, chips_extra=None, tarea_contextual=""):
    """
    Crea una Neurona del tipo especificado desde el REGISTRY.
    Si existe un chip cognitivo en Chips_Cognitivos/chip_<tipo>.txt,
    se anexa dinámicamente a sus instrucciones.

    Args:
        tipo: str - Una clave del REGISTRY ('investigador', 'coder', 'tester', etc.)
        chips_extra: list[str] | None - Nombres de chips swappable a inyectar
                     ENCIMA del chip base (ej: ['chip_red_team', 'chip_experto_python']).
        tarea_contextual: str - Texto de la tarea, usado para RAG cuando un chip_extra
                          esté en modo 'rag'.

    Returns:
        Neurona configurada (sin modelo asignado, hay que llamar set_modelo() después).

    Raises:
        KeyError si el tipo no existe en el REGISTRY.
    """
    if tipo not in REGISTRY:
        raise KeyError(f"Tipo de neurona '{tipo}' no encontrado. Disponibles: {list(REGISTRY.keys())}")

    config = REGISTRY[tipo]
    instrucciones = config["instrucciones"]

    # Carga dinámica de Chip Cognitivo base
    chip_base_nombre = f"chip_{tipo}"
    try:
        from herramientas import cargar_chip
        chip_extra_base = cargar_chip(chip_base_nombre)
        if chip_extra_base:
            instrucciones += f"\n\n--- DIRECTRICES ADICIONALES (CHIP COGNITIVO) ---\n{chip_extra_base}"

        # Si es el investigador, añadir también el mapa de la biblioteca
        if tipo == "investigador":
            chip_biblio = cargar_chip("chip_biblioteca")
            if chip_biblio:
                instrucciones += f"\n\n{chip_biblio}"
    except ImportError:
        pass

    # Layer de chips swappable adicionales (Matrix-style)
    if chips_extra:
        try:
            from herramientas import cargar_chip_completo
        except ImportError:
            cargar_chip_completo = None
        for nombre in chips_extra:
            # Evitar duplicar el chip base si fue seleccionado por similaridad.
            if nombre == chip_base_nombre:
                continue
            contenido = ""
            if cargar_chip_completo is not None:
                contenido = cargar_chip_completo(nombre, tarea_contextual=tarea_contextual)
            if contenido:
                instrucciones += f"\n\n--- CHIP ADICIONAL ({nombre}) ---\n{contenido}"

    return Neurona(
        nombre=config["nombre"],
        rol=config["rol"],
        instrucciones=instrucciones
    )
