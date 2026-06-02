# Análisis riguroso: Jerarquía Hubel-Wiesel aplicada a Chimera

## Context

El usuario propone reorganizar las neuronas de Chimera siguiendo la **jerarquía Hubel-Wiesel** del córtex visual:

> Células **simples** (responden a orientaciones específicas) → células **complejas** (agrupan simples) → **hipercomplejas de bajo orden** → **hipercomplejas de alto orden**. La hipercompleja terminal "contiene en su patrón de respuesta todas las orientaciones" y el manejo convergente "incrementa varios órdenes de magnitud el contenido informativo".

Pregunta: ¿es apto para este sistema o existe una solución mejor?

**Estado del sistema** (Fase 3 completa):
- Pipeline lineal: `Planner → [steps] → resultado`
- 6 agentes especializados ([neuronas.py:66](neuronas.py#L66-L130))
- 15 chips cognitivos seleccionados por similaridad ChromaDB ([harness.py:141-166](harness.py#L141-L166))
- Hasta 2 chips/paso inyectados en el system prompt del agente
- Modelos: Qwen 7B (orquestador) + Llama 3.2 3B (worker)

---

## 1. Análisis rigoroso de la propuesta

### 1.1 Dónde la analogía es válida

| Propiedad del córtex visual | Tiene análogo válido en LLMs |
|---|---|
| Composición jerárquica | ✅ CNNs, ToT, multi-judge ensembles funcionan |
| Diversidad → robustez | ✅ Self-consistency (Wang 2022) sube exactitud 15-30% |
| Especialización por rol | ✅ Los chips ya demuestran que prompts especializados mejoran resultados |
| Pooling reduce ruido | ✅ Ensembling de evaluadores reduce falsos positivos/negativos |

### 1.2 Dónde la analogía se rompe (problemas críticos)

**Problema A — "Orientación" no es una primitiva bien definida en lenguaje.**
En visión, una orientación es un ángulo (0°-180°) y un conjunto de células simples forma una **base completa** del espacio local. La hipercompleja sí puede afirmar "contengo todas las orientaciones" porque el espacio es finito y conocido.
En lenguaje, ¿qué es una orientación? ¿Tema? ¿Estilo lógico (deductivo/inductivo)? ¿Granularidad? ¿Tipo de fuente? No existe base completa. Sin ella, la "hipercompleja terminal" no contiene **todas** las orientaciones — solo las que el ingeniero diseñó como prompts. La afirmación de "incrementar varios órdenes de magnitud" carece de fundamento formal.

**Problema B — La amplificación informativa del córtex es aprendida, no estructural.**
V1→V2 amplifica información porque los campos receptivos fueron **entrenados** sobre estadísticas de imágenes naturales (sparse coding, Olshausen-Field 1996). La estructura jerárquica per se no genera información; descubre código eficiente. Las neuronas de Chimera son LLMs **estáticos prompted** — no aprenden campos receptivos. Apilar 4 capas no multiplica información; solo combina streams de tokens. La ganancia depende **enteramente** de qué tan bien estén ingenierizados los prompts.

**Problema C — Presupuesto de latencia es prohibitivo en M4.**
- Una inferencia Qwen 7B en M4 ≈ 3-8 s (500-1000 tokens).
- Jerarquía propuesta: ~4 simples + 2 complejas + 1 hipercompleja baja + 1 hipercompleja alta = **8 inferencias/paso**.
- M4 tiene memoria unificada ~273 GB/s. Dos modelos 7B en paralelo saturan el bus → en práctica corren serial.
- Mejor caso: 8 × 4 s = **32 s/paso**. Tareas multi-paso pasan de 30-90 s actuales a **3-5 minutos**.
- Esto rompe el caso de uso de Siri/voz, que tolera <10 s.

**Problema D — Retornos decrecientes empíricos.**
Self-consistency satura en N=5 muestras (~85-90% del beneficio de N=40). Apilar 4 capas con 8 neuronas reproduce el efecto de N=8 ensembling — gasto de cómputo enorme para ~5% adicional de exactitud.

**Problema E — El sistema YA hace convergencia, pero dentro de UNA inferencia.**
Cuando un agente se ejecuta con `chips_extra=["chip_filosofia", "chip_red_team"]`, esas dos "orientaciones" se concatenan al system prompt y el LLM las integra **en una sola pasada** ([neuronas.py:174-188](neuronas.py#L174-L188)). La atención del transformer hace el pooling gratis. Externalizar este pooling a una capa hipercompleja paga el costo de N inferencias adicionales sin ganancia clara.

**Problema F — Quién decide qué orientaciones disparan.**
En el córtex, la convergencia es anatómica. En agentes LLM se necesita un **router** que escoja qué neuronas simples activar. Ese router se vuelve el cuello de botella y el modo de fallo principal. Sin un router robusto, dispararías todas las orientaciones → costo combinatorio.

### 1.3 Lo que sí tiene mérito de la idea

A pesar de los problemas, hay un núcleo válido:

> **Para tareas críticas y ambiguas**, evaluadores diversos en paralelo SÍ mejoran outcomes. Esto es bien establecido (multi-judge, devil's advocate, red-team patterns).

El error es el **alcance** y la **granularidad**: una jerarquía de 4 capas universal es excesiva; un panel de 2-3 evaluadores aplicado **selectivamente** es óptimo.

---

## 2. Decisión final: "Convergent Council" (2 capas, on-demand)

**Decisiones confirmadas por el usuario:**
- ✅ Arquitectura: Council 2-capas (no Hubel-Wiesel literal de 4 capas)
- ✅ Roadmap: construir DESPUÉS de Fase 1 (Quick Wins) + Fase 4 (Benchmarks)
- ✅ Activación: solo cuando Router (Fase 2.2) clasifica `COMPLEJO`

En lugar de 4 capas Hubel-Wiesel, esta arquitectura **híbrida** rescata la intuición central sin pagar el costo prohibitivo:

```
                    Router (clasifica TRIVIAL / SIMPLE / COMPLEJO)
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     TRIVIAL        SIMPLE        COMPLEJO
     (1 agente)    (pipeline      (Council activo)
                    actual)
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                  Simple-1        Simple-2      Simple-3
                  chip A          chip B        chip C
                  (paralelo)      (paralelo)    (paralelo)
                          └────────────┼────────────┘
                                       ▼
                               Integrator (hipercompleja)
                                  síntesis convergente
```

**Capa simple (paralela):** 2-3 instancias del mismo agente con **chips distintos** activos. Para una auditoría de código: una con `chip_experto_python`, otra con `chip_auditor_datos`, otra con `chip_red_team`. Cada chip = "orientación".

**Capa integradora (hipercompleja):** Un único agente con prompt diseñado para reconciliar perspectivas divergentes. NO necesita ser una capa nueva — puede ser el `sintetizador` existente con un chip nuevo `chip_integrador_convergente`.

### Por qué esta es la mejor solución

1. **Rescata el núcleo válido:** diversidad → robustez en tareas COMPLEJAS.
2. **Reutiliza infraestructura existente:** los chips ya son las "orientaciones"; solo falta correr varios agentes en paralelo con chips distintos.
3. **Latencia controlada:** 3 simples paralelos + 1 integrador = 4 inferencias, pero las 3 simples corren en paralelo → tiempo de pared ≈ 2 inferencias (~10 s).
4. **Activación condicional:** Router (ya planeado en Fase 2.2) gatea cuándo invocar el Council. Tareas triviales no pagan el costo.
5. **Falsable:** Phase 4 (benchmarks) permite verificar empíricamente si el Council mejora sobre pipeline+chips, antes de comprometerse arquitectónicamente.

### Mapping conceptual a la propuesta original

| Propuesta original | Equivalente en Council |
|---|---|
| Células simples | Agentes paralelos con un chip cada uno |
| Células complejas | Pooling lo hace la atención del integrador en un único paso |
| Hipercomplejas bajo/alto orden | Colapsadas en una sola capa "Integrador"; la distinción táctica/estratégica se logra con prompt engineering |
| "Patrón con todas las orientaciones" | El integrador recibe los N outputs como contexto y emite la síntesis convergente |

---

## 3. Archivos críticos a tocar (si se aprueba)

| Archivo | Cambio |
|---|---|
| [harness.py:174-181](harness.py#L174-L181) `_neurona_con_chips` | Extender para devolver una **lista** de neuronas con chips distintos (modo "council") |
| [harness.py:202-256](harness.py#L202-L256) `_flujo_planificador` | Añadir rama "council" disparada por el Router cuando `clasificacion == "COMPLEJO"` + tarea ambigua |
| [neuronas.py:108-116](neuronas.py#L108-L116) `sintetizador` | Añadir variante con instrucciones de integración convergente (o crear `chip_integrador_convergente`) |
| [Chips_Cognitivos/_metadata.json](Chips_Cognitivos/_metadata.json) | Nuevo chip `chip_integrador_convergente` + flag `usable_en_council: true` en chips diversificadores |
| `config_chimera.json` | `"council_min_chips": 3`, `"council_max_chips": 5`, `"council_activo": false` (feature flag) |

**Reutilizable existente:** `buscar_chips_relevantes()` ya devuelve top-K candidatos ordenados ([harness.py:149-166](harness.py#L141-L166)) — el Council puede tomar los top-3 en lugar de top-2 cuando se active.

**Paralelización en M4:** Inferencias paralelas reales en MLX requieren `asyncio` + sesiones separadas o `multiprocessing.Pool`. Recomendado empezar con paralelización **secuencial-aparente** (todas con el mismo modelo, llamadas seriadas pero rápidas) y migrar a paralelo real solo si los benchmarks justifican.

---

## 4. Integración con roadmap existente (ULTRAPLAN_PENDIENTE.md)

| Fase actual | Relación con Council |
|---|---|
| **Fase 1 (Quick Wins)** | PRE-REQUISITO. Sin Docker singleton + Qwen-Coder, el Council multiplica un sistema lento. Hacer primero. |
| **Fase 4 (Benchmarks)** | PRE-REQUISITO. Sin baseline no se puede demostrar que el Council mejora. Hacer ANTES del Council. |
| **Fase 2.2 (Router)** | DEPENDENCIA DIRECTA. El Council solo se activa cuando Router clasifica `COMPLEJO`. Construir Router primero. |
| **Fase 5 (Council)** | Nueva fase propuesta, tras Fase 4. |

**Orden recomendado:** Fase 1 → Fase 4 → Fase 2.2 → Fase 5 (Council). El Council es la corona del sistema, no la base.

---

## 5. Verificación end-to-end

1. **Benchmark previo (sin Council):** correr `bench.py` con suite completa para baseline. Métricas: tasa éxito, latencia, tokens.
2. **Implementar Council con feature flag** desactivado por defecto.
3. **Test A/B sobre `tareas_complejas` de la suite:**
   ```bash
   python bench.py complejas --council=off > baseline.json
   python bench.py complejas --council=on  > council.json
   diff <(jq '.exito_pct' baseline.json) <(jq '.exito_pct' council.json)
   ```
4. **Criterio go/no-go:**
   - GO si Council mejora >10% exactitud en tareas complejas con <3× latencia.
   - NO-GO si la mejora es marginal — el costo no se justifica.
5. **Test cualitativo manual:** correr una auditoría compleja (`"audita seguridad y calidad de chimera_api.py"`) con y sin Council; comparar profundidad.

---

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Latencia >3× hace inutilizable Siri/voz | Alta | Feature flag + Router solo activa en COMPLEJO; Siri sigue usando `/siri` que ignora Council |
| Integrador alucina al reconciliar contradicciones | Media | Prompt explícito: "si las perspectivas contradicen, reportar la contradicción explícitamente; no inventar consenso" |
| Selección de chips diversos da chips redundantes | Media | Añadir penalización por similaridad inter-chip al seleccionar el panel |
| Memoria saturada por contexto inflado | Baja-Media | Truncar outputs de simples a 500 tokens antes de pasar al integrador |
| Sobre-ingeniería: las quick wins de Fase 1 dan más ROI | **Alta** | **Hacer Fase 1 + 4 primero**. Decidir Council solo si los benchmarks muestran que el cuello no es velocidad sino diversidad de razonamiento. |

---

## 7. Veredicto

**¿Es apta la propuesta literal de 4 capas Hubel-Wiesel?** **No** para este sistema, por los problemas A-F (especialmente latencia y ausencia de base completa).

**¿Hay núcleo válido?** **Sí**: convergencia de perspectivas diversas para tareas críticas.

**¿Solución recomendada?** **Convergent Council**: 2 capas, on-demand, gatillado por Router, construido sobre el sistema de chips existente.

**¿Cuándo construirla?** **Después** de Fase 1 (velocidad) y Fase 4 (benchmarks). Sin baseline no podemos validar la mejora; sin Quick Wins, el costo se duplica.

---

## 8. Próximos pasos (cuando retomemos)

1. Confirmar que Fase 1 (Quick Wins) y Fase 4 (Benchmarks) están completas con baseline registrado.
2. Implementar Fase 2.2 (Router) — pre-requisito directo.
3. Diseñar `chip_integrador_convergente` (prompt + metadata).
4. Añadir flags `council_activo`, `council_min_chips`, `council_max_chips` a `config_chimera.json`.
5. Implementar rama `_flujo_council()` en `harness.py` paralela a `_flujo_investigacion`.
6. Correr A/B sobre suite `tareas_complejas` y decidir GO/NO-GO según criterio del §5.
