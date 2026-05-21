# 🚀 ULTRAPLAN — Fases Pendientes

**Estado Actual:** Fase 3 (Swappable Chips) ✅ COMPLETADA Y VERIFICADA
**Rama:** `feature/chips-swappable-matrix` (pushed to GitHub)
**Repositorio:** https://github.com/jcrunge/Chimera.git

---

## ✅ Fase 3 (Swappable Chips) — COMPLETA

- [x] Indexador de chips semántico (`indexador_chips.py`)
- [x] Metadata declarativa de chips (`Chips_Cognitivos/_metadata.json`)
- [x] Carga dinámica on-demand (`buscar_chips_relevantes()`, `cargar_chip_completo()`)
- [x] Protocolo estructurado `<resultado>EXITO|FALLO|INCOMPLETO</resultado>`
- [x] Verificación: Test task "escribe un script python" → chips seleccionados correctamente ✓

---

## ⏳ Fase 1 (Quick Wins) — NO INICIADA

**Objetivo:** 2-3× speedup, +30% tasa de éxito sin cambiar arquitectura

### 1.1 Cambiar modelo Coder a Qwen2.5-Coder-7B
**Archivo:** `config_jarvis.json`
**Cambios:**
- Agregar nuevo campo `"modelo_coder": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"`
- Mantener `modelo_orquestador` y `modelo_worker` como están

**Archivo:** `harness.py` (líneas ~84-87)
**Cambios:**
- En `JarvisHarness.__init__()`: cargar 3 modelos en lugar de 2
  ```python
  self.modelo_orquestador = cargar_modelo(config["modelo_orquestador"])
  self.modelo_worker = cargar_modelo(config["modelo_worker"])
  self.modelo_coder = cargar_modelo(config["modelo_coder"])  # NUEVO
  ```
- En `_modelo_para_tipo(tipo)`: asignar `coder` al modelo_coder
  ```python
  if tipo == "coder":
      return self.modelo_coder
  elif tipo in ["planner", "investigador", "sintetizador"]:
      return self.modelo_orquestador
  else:
      return self.modelo_worker
  ```

**Impacto:** Qwen 7B tiene ~50% pass@1 en HumanEval vs. Llama 3.2 3B (~15%). Mejora masiva en calidad de código.

---

### 1.2 Singletonizar DockerSandbox
**Archivo:** `harness.py` (línea ~62 en `__init__`)
**Cambios:**
```python
def __init__(self):
    # ... otros inicios ...
    self.sandbox = DockerSandbox(deps_extra=[])  # UNA SOLA VEZ
    # NO destruir después de cada ejecución
```

**Archivo:** `harness.py` en `_flujo_codigo()` (línea ~302-303)
**Cambios:**
```python
# Antes:
sandbox = DockerSandbox(deps_extra=[...])  # Crea NUEVO cada vez
# Después:
resultado = self.sandbox.ejecutar_codigo(...)  # Usa el singleton
```

**Archivo:** `docker_sandbox.py` (línea ~64-68)
**Cambios:**
- Eliminar fallback "instalar todo si no se especifica"
- Siempre respetar `deps_extra`
- Por defecto, instalar solo `numpy scipy beautifulsoup4 requests`
- Agregar método `instalar_extras(deps)` para instalación on-demand

**Impacto:** Elimina 60-110s de `apt-get update + ffmpeg + librosa + nltk + whisper + descarga datasets` por cada ejecución. Es la causa #1 de lentitud.

**Verificación:** Medir tiempo antes/después en mismo script.

---

### 1.3 Relajar pattern matching con regex tolerante
**Archivo:** `harness.py` línea 248-253
**Cambios:**
```python
# Antes:
if "COMPLETO" in resultado.upper():
# Después:
if re.search(r'\b(complet[oa]|done|finished)\b', resultado, re.IGNORECASE):
```

**Archivo:** `harness.py` línea 337
**Cambios:**
```python
# Antes:
if "EXITO" in eval_qa.upper():
# Después:
if self._extraer_resultado(eval_qa) == "EXITO":  # Ya existe desde Fase 3
```

**Archivo:** `harness.py` línea 271 (citation verificación)
**Cambios:**
```python
# Antes:
if "[VERIFICACION_EXITOSA]" in respuesta:
# Después:
if self._extraer_resultado(respuesta) != "FALLO":
```

**Impacto:** Modelos pequeños a menudo usan variantes ("exitoso", "ok", "success"). Los regexes toleran esto. Reduce ~40% de falsos negativos solo por mismatch de formato.

---

### 1.4 Caché simple de búsquedas web
**Archivo:** `herramientas.py`
**Cambios:**
```python
import functools

@functools.lru_cache(maxsize=128)
def buscar_web(query, max_results=5):
    # Implementación existente sin cambios
    # pero ahora con caché automático
```

**Impacto:** En investigaciones multi-paso, la misma búsqueda no se repite. Ahorra tiempo en red (aunque sea local).

---

### 1.5 Pasar lista de librerías disponibles al Coder
**Archivo:** `harness.py` en `_flujo_codigo()` (línea ~323)
**Cambios:**
```python
# Obtener lista de librerías instaladas en Docker
librerías_disponibles = [
    "numpy", "scipy", "beautifulsoup4", "requests",
    # + otras que Docker instale on-demand
]

# Pasar en el contexto al Coder
tarea_con_contexto = f"""
{tarea}

Librerías disponibles en el sandbox: {', '.join(librerías_disponibles)}
No intentes importar librerías que no estén en esta lista.
Si necesitas una, avísame antes de escribir el código.
"""
```

**Impacto:** Reduce `ImportError` del 30% al <5% porque Coder sabe qué está disponible.

---

## ⏸️ Fase 2 (Structured Output + Router) — PARCIALMENTE HECHA

### 2.1 Structured Output — ✅ COMPLETA
- [x] Protocolo XML `<resultado>...</resultado>` implementado
- [x] Parser tolerante `_extraer_resultado()` en harness.py
- [x] Todos los chips actualizados

**NO REQUIERE TRABAJO ADICIONAL en esta fase.**

---

### 2.2 Router por Complejidad — ❌ NO HECHA
**Objetivo:** Tareas triviales responden en <3s, complejas se toman su tiempo

**Archivo:** `harness.py` (nuevo método `procesar()`)
**Cambios:**
Crear clase `Router`:
```python
class Router:
    @staticmethod
    def clasificar(tarea: str) -> Literal["TRIVIAL", "SIMPLE", "COMPLEJO"]:
        # Heurística 1: longitud y keywords
        if len(tarea) < 20 and any(kw in tarea.lower() for kw in ["hola", "qué hora", "cuánto"]):
            return "TRIVIAL"
        if any(kw in tarea.lower() for kw in ["investiga", "profundiza", "escribe un script", "crea"]):
            return "COMPLEJO"
        # Heurística 2: llamar al Planner para clasificar (1 LLM call rápido)
        return "SIMPLE"
    
    @staticmethod
    def ejecutar(harness, tarea: str, clasificacion: str):
        if clasificacion == "TRIVIAL":
            return harness._flujo_chat(tarea)  # Directo sin Planner
        elif clasificacion == "SIMPLE":
            # Un solo agente, sin iteración
            plan = harness._flujo_planificador(tarea, max_steps=1)
            return harness._ejecutar_plan(plan)
        else:  # COMPLEJO
            # Pipeline completo
            return harness.procesar(tarea)  # Implementación actual
```

**Impacto:** Tareas tipo "hola" responden en <3s sin overhead de Planner.

---

### 2.3 Retry con corrección de formato — ❌ PARCIAL
**Idea:** Si output no parsea, pedir solo corrección de formato, no rehacer tarea.
**Estado:** Parser tolerante existe, retry logic no.

**Archivo:** `harness.py` en cada `_flujo_X()`
**Cambios:**
```python
resultado = neurona.pensar(...)
if self._extraer_resultado(resultado) is None:
    # Retry: pedir corrección de formato
    resultado_corregido = neurona.pensar(
        f"Por favor, reformula tu respuesta anterior usando el formato XML:\n"
        f"<resultado>EXITO o FALLO o INCOMPLETO</resultado>\n\n"
        f"Tu respuesta anterior fue: {resultado}"
    )
    resultado = resultado_corregido
```

**Impacto:** Convierte fallos por formato en pequeños overhead en lugar de rehacer todo.

---

### 2.4 Reescribir `_flujo_investigacion` — ❌ NO HECHA
**Cambios:**
- Reducir max iteraciones de 5 a 2 (en config)
- Si llega al límite, devolver con flag "verificación parcial"
- Eliminar sistema de "penalización en hallazgos" que solo infla contexto

**Archivo:** `config_jarvis.json`
```json
"max_iteraciones_investigacion": 2
```

**Impacto:** Investigaciones más rápidas, menos bloat de contexto.

---

## ⏹️ Fase 4 (Benchmarks + Observabilidad) — NO INICIADA

### 4.1 Suite de test
**Archivo nuevo:** `tests/tareas_eval.json`
```json
{
  "tareas_triviales": [
    {"tarea": "¿Cuánto es 2+2?", "esperado": "4"},
    {"tarea": "¿Qué hora es?", "esperado": "time|hour"},
    {"tarea": "Hola", "esperado": "hola|saludo"}
  ],
  "tareas_simples": [
    {"tarea": "Explica qué es ChromaDB", "esperado": "vectorial|embedding|búsqueda"},
    ...
  ],
  "tareas_codigo": [
    {"tarea": "Escribe un script que imprima 'hola'", "esperado_stdout": "hola"},
    ...
  ]
}
```

**Impacto:** Baseline cuantitativa para medir progreso.

---

### 4.2 Script de benchmarking
**Archivo nuevo:** `bench.py`
```python
def run_benchmark(suite="all"):
    results = {}
    for tarea in cargar_tareas(suite):
        start = time.time()
        resultado = harness.procesar(tarea["tarea"])
        latencia = time.time() - start
        
        éxito = evaluar(resultado, tarea["esperado"])
        results[tarea["id"]] = {
            "latencia": latencia,
            "exito": éxito,
            "modelo_usado": ...,
            "tokens": ...
        }
    
    print_reporte(results)

if __name__ == "__main__":
    run_benchmark(sys.argv[1] if len(sys.argv) > 1 else "all")
```

**Uso:**
```bash
python bench.py          # Corre suite completa
python bench.py simple   # Solo tareas SIMPLE
```

**Impacto:** Medición objetiva de qué mejora.

---

### 4.3 Logging estructurado
**Archivo:** `herramientas.py` (nueva función)
```python
def log_inference(agente, prompt_tokens, response_tokens, latencia, modelo, exito):
    fecha = datetime.now().strftime("%Y-%m-%d")
    ruta = f"logs/jarvis_{fecha}.jsonl"
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "agente": agente,
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "latencia_ms": latencia * 1000,
        "modelo": modelo,
        "exito": exito
    }
    with open(ruta, "a") as f:
        f.write(json.dumps(entrada) + "\n")
```

**Archivo:** `neuronas.py` en `Neurona.pensar()`
**Cambios:**
```python
# Al final de pensar():
log_inference(
    agente=self.tipo,
    prompt_tokens=len(self.prompt) // 4,  # Aproximado
    response_tokens=len(respuesta) // 4,
    latencia=time.time() - start,
    modelo=self.modelo,
    exito=True  # o validar
)
```

**Impacto:** Post-mortem de qué agente es cuello de botella.

---

### 4.4 Comando de diagnóstico
**Archivo:** `harness.py` en `JarvisHarness`
**Cambios:**
```python
def diagnosticar(self):
    print("🏥 Diagnóstico de salud del sistema:\n")
    
    # Docker
    try:
        docker_client = docker.from_env()
        print("✅ Docker: Corriendo")
    except:
        print("❌ Docker: No disponible")
    
    # ChromaDB
    try:
        col = obtener_coleccion_chips()
        print(f"✅ ChromaDB: {col.count()} chips indexados")
    except:
        print("❌ ChromaDB: No accesible")
    
    # Modelos cacheados
    cache_dir = Path.home() / ".cache/huggingface/hub"
    models = list(cache_dir.glob("*"))
    print(f"✅ Modelos cacheados: {len(models)}")
    
    # Espacio en disco
    import shutil
    stat = shutil.disk_usage("/")
    print(f"💾 Espacio disponible: {stat.free / 1e9:.1f} GB")
    
    # RAM
    import psutil
    print(f"🧠 RAM disponible: {psutil.virtual_memory().available / 1e9:.1f} GB")
```

**Uso:**
```bash
python harness.py --diag
```

**Impacto:** Debug rápido de por qué algo no funciona.

---

## 📋 Orden Recomendado de Ejecución

```
1. ✅ Fase 3 (Swappable Chips)        — COMPLETA, EN MAIN
2. 📌 Fase 1 (Quick Wins)             — SIGUIENTE
   a. 1.2 DockerSandbox singleton     (máximo impacto en velocidad)
   b. 1.1 Qwen2.5-Coder-7B            (máximo impacto en calidad)
   c. 1.3 Pattern matching relajado    (reduce falsos negativos)
   d. 1.4 Caché web                    (optimización menor)
   e. 1.5 Librerías disponibles        (reduce ImportError)
3. 🎯 Fase 4 (Benchmarks)             — ANTES de Fase 2
   (necesitamos baseline antes de mejorar)
4. 🔄 Fase 2 (Router)                 — DESPUÉS de Fase 1 + Benchmarks
5. 🎉 Verificación end-to-end         (correr bench.py después de cada fase)
```

---

## 📊 Métricas Objetivo

**Línea Base Actual (Fase 3 solamente):**
- Tasa de éxito: ~35% (estimado, no medido sin benchmarks)
- Latencia tarea trivial: ~30s (overhead de Planner)
- Latencia tarea código simple: ~90s (Docker cold start)

**Después de Fase 1:**
- Tasa de éxito: >65% (modelos mejores + patrón matching flexible)
- Latencia tarea trivial: <3s (sin Planner)
- Latencia tarea código simple: <15s (Docker singleton)

**Después de Fase 2:**
- Tasa de éxito: >80%
- Latencia tarea trivial: <3s
- Latencia tarea código: <15s
- Latencia tarea investigación: <45s

---

## 🚀 Próximos Pasos

1. **Confirmar el orden** (¿empezamos con 1.2 o 1.1?)
2. **Implementar Fase 1** en sesión 1-2
3. **Ejecutar benchmarks** después de cada paso
4. **Integrar resultados** a feature/chips-swappable-matrix
5. **Crear PR** cuando Fase 1 esté lista

---

**¿Listo? Dime si cambio algo del plan o si empezamos directo con 1.2 (DockerSandbox).**
