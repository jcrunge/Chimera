# 🌌 Sistema de Jarvis: Red Neuronal Multi-Agente

> **Arquitectura de Inteligencia Artificial Autónoma integrada a nivel de sistema operativo. Diseñada con latencia ultra-baja para hardware Apple Silicon, utilizando RAG (ChromaDB), Ejecución Segura (Docker) y Auto-Corrección Recursiva.**

---

## 🚀 Resumen del Proyecto

El **Sistema de Jarvis** ha evolucionado de un simple script a un **Clúster Neuronal Multi-Agente**. En lugar de tener un solo modelo de lenguaje, Jarvis se divide en "Neuronas" especializadas (ej. Programador, Tester, Asimilador) que comparten una memoria central y trabajan en equipo para resolver tareas complejas.

El sistema no solo genera código, sino que lo **ejecuta en un Sandbox real**, evalúa los resultados, y si falla, **se auto-corrige** iterativamente hasta tener éxito.

---

## 🏗️ Arquitectura del Motor (Capas Lógicas)

### 1. 🛡️ El Sandbox Físico (Docker)
Para garantizar la seguridad del Host (tu Mac), las Neuronas ejecutan su código dentro de un contenedor Docker persistente y aislado.
- **Volúmenes Montados:** El código se escribe en un directorio `workspace` local que se refleja instantáneamente en Docker.
- **Seguridad:** Evita que el LLM ejecute comandos destructivos en el sistema principal.
- **Script responsable:** `docker_sandbox.py`

### 2. 🧠 La Sinapsis (Memoria Vectorial Compartida)
El "Subconsciente" del sistema. Utiliza **ChromaDB** para almacenar conocimiento.
- Todas las Neuronas leen y escriben en esta base de datos.
- Actúa como una pizarra compartida: El Coder guarda su código, y el Tester lo lee.
- Permite inyectar conocimiento externo (RAG) instantáneamente a las Neuronas.

### 3. 🔄 Motor Neuronal Multi-Agente (Auto-Corrección)
Implementación avanzada de agentes especializados que colaboran entre sí.
- **Paso de Testigo:** El Coder-X programa -> Docker ejecuta -> Tester-Y evalúa.
- **Auto-Corrección Recursiva:** Si el código en Docker falla, el Tester le devuelve el error exacto al Coder, creando un bucle infinito de retroalimentación hasta alcanzar el Éxito.
- **Script responsable:** `motor_neuronal.py`

### 4. 🌐 El Asimilador (Aprendizaje Externo)
Permite a Jarvis aprender de internet bajo demanda.
- Extrae el HTML de cualquier URL, elimina la basura (scripts, estilos) y lo convierte a **Markdown puro**.
- Lo inyecta matemáticamente en la base de datos vectorial para que las Neuronas lo usen en el futuro.
- **Script responsable:** `asimilador_web.py`

---

## ⚡ Infraestructura Técnica y Core

- **Hardware Base:** Mac Mini M4 con 16GB de RAM (Unified Memory).
- **El Cerebro (LLM):** `Llama-3.2-3B-Instruct-4bit` cuantizado y ejecutado vía **MLX** para latencia casi cero.
- **Base de Datos Vectorial:** ChromaDB (100% Local).
- **Entorno de Ejecución:** Contenedores efímeros de Docker.
- **Interfaz (UI):** Librería `rich` para una visualización premium de los logs en terminal.

---

## 🛠️ Estructura del Proyecto

- `motor_neuronal.py`: **[NÚCLEO]** Orquestador multi-agente y bucle de auto-corrección.
- `docker_sandbox.py`: Controlador de los contenedores para ejecución segura.
- `asimilador_web.py`: Script para inyectar conocimiento (URLs) a la memoria.
- `gestor_memoria.py`: **Panel de Control Psicológico**. Permite ver, auditar y borrar los recuerdos vectoriales de Jarvis.
- `Jarvis.py`: (Legacy) Prueba de concepto original con sandbox simulado.

## 🚦 Cómo Ejecutar el Motor Principal

1. Asegúrate de tener Docker abierto en tu Mac.
2. Inicia la red neuronal:
   ```bash
   python motor_neuronal.py
   ```
3. (Opcional) Para alimentar a Jarvis con nueva información de internet:
   ```bash
   python asimilador_web.py
   ```
4. (Opcional) Para gestionar o borrar su memoria:
   ```bash
   python gestor_memoria.py
   ```

---

> **Filosofía:** Un Agente Autónomo real no es el que nunca falla, sino el que es capaz de leer su propio error, aprender de él y volver a intentarlo en milisegundos.
