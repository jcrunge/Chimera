# Changelog

Todos los cambios notables del proyecto **Sistema de Jarvis** serán documentados en este archivo.

## [v0.4.0] - Biblioteca de Chips Swappable + Protocolo Estructurado

### Añadido (Added)
- **Biblioteca swappable de Chips Cognitivos**: Nuevo `indexador_chips.py` que indexa todos los chips de `Chips_Cognitivos/` en una colección ChromaDB independiente (`indice_chips`). El `Planner` ahora consulta el índice por similaridad semántica y, por cada paso, instala los chips relevantes ENCIMA del chip base del agente (analogía Matrix: "load skills on demand"). Esto rescata los 11 chips huérfanos (`chip_filosofia`, `chip_red_team`, `chip_experto_python`, etc.) que antes nunca se cargaban.
- **Metadata declarativa (`Chips_Cognitivos/_metadata.json`)**: descripción, keywords, `requiere_autorizacion` y `modo` (`inline` | `rag`) por chip. Los book-chips grandes (`chip_teoria_musical`, `chip_linux_master`) se indexan solo por descripción y su contenido se trae por RAG bajo demanda.
- **Gate de chips autorizados**: chips marcados `requiere_autorizacion: true` (ej. `chip_red_team`) requieren un umbral de similaridad más alto (`0.65` vs `0.45` para chips normales) — solo se instalan cuando la tarea del usuario lo pide semánticamente.
- **Helpers `buscar_chips_relevantes` y `cargar_chip_completo`** en `herramientas.py`.

### Modificado (Changed)
- **Protocolo estructurado de evaluadores**: `tester`, `citation` y `investigador` ahora terminan su salida con `<resultado>EXITO|FALLO|INCOMPLETO</resultado>`. El harness parsea ese token con `_extraer_resultado()` en vez de hacer matching por substring. Esto cierra la contradicción documentada en `CLAUDE.md` (`EXITO` vs `EXITO_TOTAL`).
- **`crear_neurona(tipo, chips_extra=None, tarea_contextual="")`**: nuevo parámetro `chips_extra` para layer de chips encima del chip base sin romper el comportamiento por defecto.
- **`config_jarvis.json`**: nuevos campos `umbral_chip_normal`, `umbral_chip_autorizado`, `max_chips_por_paso`.

---

## [v0.2.0] - Evolución Multi-Agente y Sandbox Real

### Añadido (Added)
- **Arquitectura Multi-Agente (`motor_neuronal.py`)**: Se reemplazó el bucle secuencial simple por un sistema de agentes especializados (Clase `Neurona`). Actualmente implementando `Coder-X` y `Tester-Y`.
- **Bucle de Auto-Corrección Recursiva**: Las neuronas ahora pueden pasarse retroalimentación. Si la ejecución falla, el Tester devuelve el error al Coder para re-escribir el código.
- **Sandbox en Docker (`docker_sandbox.py`)**: Implementación nativa del SDK de Docker para ejecutar código generado por IA de forma 100% aislada usando un volumen local (`workspace`).
- **Asimilador Web (`asimilador_web.py`)**: Nueva herramienta para realizar scraping de URLs, limpiar el HTML a Markdown e inyectar el conocimiento en ChromaDB.
- **Panel de Control Psicológico (`gestor_memoria.py`)**: CLI interactivo para listar memorias con fecha/hora, leer el contenido de los recuerdos y borrar vectores específicos de ChromaDB.
- **UI Premium**: Integración de la librería `rich` en todos los scripts para mejorar la legibilidad y estética de la terminal.

### Modificado (Changed)
- **Base de Datos Vectorial**: Se migró de la memoria temporal simulada en `Jarvis.py` a una implementación robusta y centralizada usando `ChromaDB` (Sinapsis Compartida).

---

## [v0.1.0] - Prueba de Concepto (PoC) Inicial

### Añadido (Added)
- Bucle Cognitivo ReAct básico (Observación -> Pensamiento -> Acción).
- Integración de `mlx-lm` para ejecución ultra-rápida del modelo Llama-3.2-3B en hardware Apple Silicon (M4).
- Sistema de Archivos Virtual (Simulado vía diccionario Python) para probar permisos y manejo de errores estáticos.
- Creación del archivo `Jarvis.py`.
