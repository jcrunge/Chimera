# Changelog

Todos los cambios notables del proyecto **Sistema de Jarvis** serán documentados en este archivo.

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
