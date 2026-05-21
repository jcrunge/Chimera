"""
JarvisHarness v0.3 — Orquestador principal del sistema multi-agente.

Este módulo coordina todas las neuronas, herramientas y flujos de trabajo.
Reemplaza a motor_neuronal.py.
"""

import os
# Necesario en macOS para evitar segfault con Metal/MLX y procesos hijos
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

import json
import time
import multiprocessing as mp
from rich.console import Console
from rich.panel import Panel
from mlx_lm import load

from neuronas import crear_neurona
from herramientas import (
    buscar_memoria, guardar_en_memoria, 
    buscar_web, formatear_resultados_web,
    ejecutar_en_sandbox, leer_archivo, listar_workspace,
    cargar_chip
)

console = Console()

# ==========================================
# CONFIGURACIÓN
# ==========================================
CONFIG_FILE = "config_jarvis.json"

def cargar_config():
    """Carga la configuración desde config_jarvis.json."""
    defaults = {
        "modelo_orquestador": "mlx-community/Qwen2.5-7B-Instruct-4bit",
        "modelo_worker": "mlx-community/Llama-3.2-3B-Instruct-4bit",
        "max_tokens_pensamiento": 1500,
        "max_tokens_codigo": 2000,
        "max_intentos_correccion": 3,
        "max_iteraciones_investigacion": 5,
        "temperatura": 0.1
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return {**defaults, **json.load(f)}
        except:
            pass
    return defaults


class JarvisHarness:
    """
    Orquestador principal del sistema Jarvis.
    
    Gestiona el ciclo completo:
    Router → Planificación → Ejecución → Evaluación → Síntesis → Citación
    """
    
    def __init__(self):
        console.print("\n[bold reverse white]  >>> JARVIS HARNESS v0.3 INICIANDO <<<  [/bold reverse white]\n")
        self.config = cargar_config()
        
        # Cargar modelos
        console.print("[bold cyan]🧠 Cargando modelo orquestador...[/bold cyan]")
        self.modelo_orq, self.tokenizer_orq = load(self.config["modelo_orquestador"])
        
        console.print("[bold cyan]⚡ Cargando modelo worker...[/bold cyan]")
        self.modelo_worker, self.tokenizer_worker = load(self.config["modelo_worker"])
        
        # Crear neuronas y asignar modelos
        self.planner = crear_neurona("planner")
        self.planner.set_modelo(self.modelo_orq, self.tokenizer_orq)
        
        self.investigador = crear_neurona("investigador")
        self.investigador.set_modelo(self.modelo_orq, self.tokenizer_orq)
        
        self.sintetizador = crear_neurona("sintetizador")
        self.sintetizador.set_modelo(self.modelo_orq, self.tokenizer_orq)
        
        self.coder = crear_neurona("coder")
        self.coder.set_modelo(self.modelo_worker, self.tokenizer_worker)
        
        self.tester = crear_neurona("tester")
        self.tester.set_modelo(self.modelo_worker, self.tokenizer_worker)
        
        self.citation = crear_neurona("citation")
        self.citation.set_modelo(self.modelo_worker, self.tokenizer_worker)
        
        console.print("[bold green]✅ Harness inicializado. Todas las neuronas activas.[/bold green]\n")
    
    # ------------------------------------------
    # PLANNER: Planificador Dinámico
    # ------------------------------------------
    def planificar_tarea(self, tarea):
        """
        Usa la neurona Planner para dividir la tarea en pasos.
        Returns:
            list: Lista de diccionarios con 'tipo' y 'tarea'.
        """
        import json
        resultado = self.planner.pensar(tarea, max_tokens=300)
        try:
            # Buscar array JSON en la respuesta
            inicio = resultado.find("[")
            fin = resultado.rfind("]") + 1
            if inicio != -1 and fin != 0:
                json_str = resultado[inicio:fin]
                plan = json.loads(json_str)
                console.print(f"[bold yellow]📋 Plan Dinámico Generado: {len(plan)} pasos[/bold yellow]")
                return plan
        except Exception as e:
            console.print(f"[red]Error parseando plan JSON: {e}[/red]")
        
        # Fallback a un solo paso si falla el parseo
        console.print("[yellow]🔀 Fallback: Tarea interpretada como INVESTIGACION simple.[/yellow]")
        return [{"tipo": "INVESTIGACION", "tarea": tarea}]

    def limpiar_query(self, query):
        import re
        query = query.strip()
        lineas = query.split("\n")
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            # Quitar prefijos comunes
            linea = re.sub(r'^(búsqueda|query|términos|duckduckgo|google|búsqueda concisa|término de búsqueda|búsqueda concisa en español para google/duckduckgo):\s*', '', linea, flags=re.IGNORECASE)
            # Quitar comillas
            linea = linea.strip('"\'')
            if linea:
                return linea
        return query.strip('"\'')
    
    # ------------------------------------------
    # FLUJO PRINCIPAL Y PLANIFICADOR
    # ------------------------------------------
    def procesar(self, tarea):
        """
        Punto de entrada principal. Delega al planificador.
        """
        console.rule("[bold]Nueva Tarea Compleja")
        console.print(f"[white]📝 {tarea}[/white]\n")
        
        resultado = self._flujo_planificador(tarea)
        return {"exito": True, "resultado": resultado, "tipo": "PLAN_COMPLEJO"}
        
    def _flujo_planificador(self, tarea_principal):
        """Ejecuta el plan paso a paso, inyectando contexto entre pasos."""
        plan = self.planificar_tarea(tarea_principal)
        contexto_global = ""
        resultados_pasos = []
        
        for i, paso in enumerate(plan):
            tipo = paso.get("tipo", "CHAT").upper()
            sub_tarea = paso.get("tarea", "")
            
            console.print(f"\n[bold magenta]▶️ Ejecutando Paso {i+1}/{len(plan)}: {tipo}[/bold magenta]")
            console.print(f"[italic]{sub_tarea}[/italic]")
            
            # Inyectar contexto global a la subtarea
            tarea_con_contexto = sub_tarea
            if contexto_global:
                tarea_con_contexto = f"CONTEXTO DE PASOS ANTERIORES:\n{contexto_global}\n\nNUEVA TAREA:\n{sub_tarea}"
            
            # Ejecutar el flujo correspondiente
            if tipo == "INVESTIGACION":
                resultado_paso = self._flujo_investigacion(tarea_con_contexto)
            elif tipo == "CODIGO":
                resultado_paso = self._flujo_codigo(tarea_con_contexto)
            elif tipo == "AUDITORIA":
                resultado_paso = self._flujo_auditoria(tarea_con_contexto)
            else:
                resultado_paso = self._flujo_chat(tarea_con_contexto)
                
            # Verificar si falló críticamente
            if "No se logró completar la tarea" in resultado_paso or "INCOMPLETO" in resultado_paso:
                console.print(f"[bold red]❌ El Paso {i+1} falló críticamente. Añadiendo resumen de fallo al contexto global.[/bold red]")
                contexto_global += f"\n--- RESULTADO PASO {i+1} (FALLIDO) ---\nEl agente falló en realizar este paso. Información rescatada: {resultado_paso[-500:]}"
                resultados_pasos.append(f"Paso {i+1} Fallido")
            else:
                contexto_global += f"\n--- RESULTADO PASO {i+1} ---\n{resultado_paso}"
                resultados_pasos.append(f"Paso {i+1} Éxito")
                
            # Guardar en memoria general
            guardar_en_memoria(resultado_paso, {"autor": "Planner-Zero", "paso": f"{i+1}/{len(plan)}"})
            
        console.rule("[bold green]Plan Completado")
        return contexto_global
    
    # ------------------------------------------
    # FLUJO: INVESTIGACIÓN
    # ------------------------------------------
    def _flujo_investigacion(self, tarea):
        """
        Flujo de investigación iterativa con Bucle de Persistencia y Verificación Estricta.
        """
        console.rule("[bold cyan]Modo: INVESTIGACIÓN")
        
        hallazgos = []
        fuentes = []
        sintesis = ""
        reporte_final = ""
        
        for iteracion in range(1, self.config["max_iteraciones_investigacion"] + 1):
            console.print(f"\n[bold magenta]🔄 Iteración {iteracion}[/bold magenta]")
            
            # 1. Construir contexto con hallazgos previos
            contexto_previo = ""
            if hallazgos:
                contexto_previo = f"\nHALLAZGOS PREVIOS:\n" + "\n".join(hallazgos[-3:])  # últimos 3
            
            # 2. Buscar en memoria local (ChromaDB)
            contexto_memoria = buscar_memoria(tarea)
            if contexto_memoria:
                console.print("[green]💾 Encontrado conocimiento en memoria local[/green]")
                hallazgos.append(f"[Memoria Local] {contexto_memoria[:500]}")
                fuentes.append({"tipo": "memoria_local", "contenido": contexto_memoria[:200]})
            
            # 3. Generar query de búsqueda web con el investigador
            query_web_raw = self.investigador.pensar(
                f"Genera únicamente los términos de búsqueda (query) que usarías en Google/DuckDuckGo para investigar sobre: {tarea}. No agregues introducciones, explicaciones, ni comillas.",
                contexto=contexto_previo,
                max_tokens=50
            )
            query_web = self.limpiar_query(query_web_raw)
            console.print(f"[bold cyan]🔍 Query de búsqueda limpia: '{query_web}'[/bold cyan]")
            
            # 4. Buscar en web
            resultados_web = buscar_web(query_web, max_resultados=3)
            if resultados_web:
                texto_web = formatear_resultados_web(resultados_web)
                hallazgos.append(f"[Web] {texto_web[:500]}")
                for r in resultados_web:
                    fuentes.append({"tipo": "web", "url": r.get("href", r.get("url", "")), "titulo": r.get("title", "")})
            
            # 5. Sintetizar todo
            todo_el_contexto = "\n---\n".join(hallazgos)
            sintesis = self.sintetizador.pensar(
                f"Sintetiza toda la información recopilada para responder: {tarea}",
                contexto=f"INFORMACIÓN RECOPILADA:\n{todo_el_contexto}"
            )
            
            # 6. Evaluar si necesitamos más investigación (Investigador)
            evaluacion = self.investigador.pensar(
                f"¿La siguiente síntesis responde COMPLETAMENTE a la pregunta '{tarea}'? Responde SOLO 'COMPLETO' o 'INCOMPLETO: [qué falta]'.",
                contexto=f"SÍNTESIS:\n{sintesis}",
                max_tokens=100
            )
            
            if "INCOMPLETO" in evaluacion.upper() or "COMPLETO" not in evaluacion.upper():
                console.print(f"[yellow]🔄 Investigación incompleta: {evaluacion[:100]}[/yellow]")
                hallazgos.append(f"[PENALIZACIÓN] Tu investigación previa fue evaluada como INCOMPLETA. Razón: {evaluacion}. Busca de nuevo enfocándote en lo que falta.")
                continue
                
            # 7. Verificación Estricta (Citation Agent)
            console.print("[bold yellow]⚖️ CitationAgent verificando fuentes...[/bold yellow]")
            
            str_fuentes = ""
            for i, f in enumerate(fuentes, 1):
                str_fuentes += f"[{i}] {f.get('titulo', 'Local')} - {f.get('url', 'Memoria')}\n"
                
            verificacion = self.citation.pensar(
                f"Verifica la siguiente síntesis e insértale citaciones numéricas [N] respaldadas por las fuentes. Si hay datos inventados o sin fuente, pon [FALTA_FUENTE]. Al final evalúa tu propio trabajo con [VERIFICACION_EXITOSA] o [VERIFICACION_FALLIDA].\n\nSÍNTESIS:\n{sintesis}",
                contexto=f"FUENTES DISPONIBLES:\n{str_fuentes}\n\nTEXTO RECOPILADO:\n{todo_el_contexto}",
                max_tokens=1500
            )
            
            if "[VERIFICACION_FALLIDA]" in verificacion.upper() or "[FALTA_FUENTE]" in verificacion.upper():
                console.print("[bold red]❌ Alucinación o falta de fuentes detectada por CitationAgent.[/bold red]")
                hallazgos.append(f"[PENALIZACIÓN] El CitationAgent detectó afirmaciones sin fuente verificable. Busca pruebas sólidas para las afirmaciones faltantes.")
                continue
                
            # Éxito
            console.print("[bold green]🏆 [RECOMPENSA] Investigación completa y verificada exitosamente.[/bold green]")
            reporte_final = verificacion
            break
        
        if not reporte_final:
            console.print("[bold red]⚠️ Se alcanzó el límite de iteraciones sin éxito total. Devolviendo mejor esfuerzo.[/bold red]")
            reporte_final = sintesis
            
        # Guardar en memoria para el futuro
        guardar_en_memoria(reporte_final, {"autor": "Investigador-Alpha", "tarea": tarea[:100]})
        
        console.print(Panel(reporte_final, title="📋 Reporte de Investigación Verificado", border_style="green"))
        return reporte_final
    
    # ------------------------------------------
    # FLUJO: CÓDIGO (hereda lógica del motor_neuronal original)
    # ------------------------------------------
    def _flujo_codigo(self, tarea):
        """
        Flujo de generación y ejecución de código.
        Coder genera → Docker ejecuta → Tester evalúa → repite si falla.
        Si falla varias veces, descompone el problema automáticamente.
        """
        console.rule("[bold green]Modo: CÓDIGO")
        
        from docker_sandbox import DockerSandbox
        sandbox = DockerSandbox()
        archivos = listar_workspace()
        feedback = ""
        fallos_consecutivos = 0
        
        for intento in range(1, self.config["max_intentos_correccion"] + 1):
            console.print(f"\n[bold]Ciclo {intento}/{self.config['max_intentos_correccion']}[/bold]")
            
            # Contexto
            contexto = buscar_memoria(tarea)
            if feedback:
                contexto += f"\nFEEDBACK ANTERIOR: {feedback}\n"
                
            # Descomposición Automática si hay muchos fallos
            if fallos_consecutivos >= 2:
                console.print("[bold yellow]⚠️ Múltiples fallos detectados. Descomponiendo el problema automáticamente...[/bold yellow]")
                descomposicion = self.investigador.pensar(f"El código para '{tarea}' ha fallado {fallos_consecutivos} veces. Descompón este problema en 3 pasos lógicos y extremadamente simples para el programador. No escribas código, solo la estrategia paso a paso.")
                contexto += f"\n[NUEVA ESTRATEGIA (DESCOMPOSICIÓN)]:\n{descomposicion}\nSigue esta estrategia paso a paso."
                fallos_consecutivos = 0 # Reiniciar contador
                
            contexto += f"\nArchivos disponibles en workspace: {archivos}"
            
            # Coder genera código
            codigo = self.coder.pensar(tarea, contexto=contexto, max_tokens=self.config["max_tokens_codigo"])
            
            # Ejecutar en sandbox
            exito, salida = sandbox.ejecutar_codigo(codigo)
            console.print(f"[cyan]📄 Salida Docker:[/cyan]\n{salida[:500]}")
            
            # Tester evalúa
            eval_qa = self.tester.pensar(
                f"Tarea original: {tarea}\nSalida del programa:\n{salida}\nError: {'Ninguno' if exito else salida}\nRecuerda: Si es correcto, di EXITO_TOTAL. Si falla, di FALLO: [razon]."
            )
            
            if "EXITO" in eval_qa.upper() and exito:
                console.print("[bold green]🏆 [RECOMPENSA] CÓDIGO COMPLETADO CON ÉXITO Y SIN ERRORES.[/bold green]")
                sandbox.apagar()
                return f"Código ejecutado exitosamente.\nSalida:\n{salida}"
            
            console.print(f"[bold red]❌ [PENALIZACIÓN] El código no cumplió los requisitos. Evaluador dice: {eval_qa[:100]}...[/bold red]")
            feedback = f"[PENALIZACIÓN] Tu código anterior falló. El tester reporta: {eval_qa}. Analiza tu error y arréglalo."
            fallos_consecutivos += 1
            time.sleep(1)
        
        sandbox.apagar()
        return f"No se logró completar la tarea después de {self.config['max_intentos_correccion']} intentos.\nÚltimo feedback: {feedback}"
    
    # ------------------------------------------
    # FLUJO: CHAT (RAG simple)
    # ------------------------------------------
    def _flujo_chat(self, tarea):
        """Chat simple con RAG: busca en memoria y responde."""
        console.rule("[bold blue]Modo: CHAT")
        
        contexto = buscar_memoria(tarea)
        respuesta = self.sintetizador.pensar(tarea, contexto=f"CONOCIMIENTO DISPONIBLE:\n{contexto}")
        
        console.print(Panel(respuesta, title="💬 Respuesta", border_style="blue"))
        return respuesta
    
    # ------------------------------------------
    # FLUJO: AUDITORÍA
    # ------------------------------------------
    def _flujo_auditoria(self, tarea):
        """Audita un archivo del workspace."""
        console.rule("[bold red]Modo: AUDITORÍA")
        
        # Intentar extraer nombre de archivo de la tarea
        archivos = listar_workspace()
        archivo_encontrado = None
        for archivo in archivos:
            if archivo.lower() in tarea.lower():
                archivo_encontrado = archivo
                break
        
        if archivo_encontrado:
            contenido = leer_archivo(archivo_encontrado)
            respuesta = self.investigador.pensar(
                f"Audita este código/archivo y reporta problemas, vulnerabilidades y mejoras:\n{contenido[:2000]}",
                contexto=f"Tarea del usuario: {tarea}"
            )
        else:
            respuesta = self.investigador.pensar(
                f"El usuario pide una auditoría pero no se encontró un archivo específico. Archivos disponibles: {archivos}\nPregunta: {tarea}"
            )
        
        console.print(Panel(respuesta, title="🔍 Resultado de Auditoría", border_style="red"))
        return respuesta


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    import argparse
    import multiprocessing as mp
    mp.set_start_method("spawn", force=True)

    parser = argparse.ArgumentParser(description="Jarvis Harness v0.3")
    parser.add_argument("tarea", type=str, nargs='?', default=None, 
                        help="Tarea a procesar")
    parser.add_argument("--interactivo", "-i", action="store_true",
                        help="Modo interactivo (bucle de conversación)")
    args = parser.parse_args()
    
    harness = JarvisHarness()
    
    if args.interactivo or not args.tarea:
        # Modo interactivo
        console.print("[bold]Modo interactivo activado. Escribe 'salir' para terminar.[/bold]\n")
        while True:
            tarea = input("\n👤 Tú: ").strip()
            if tarea.lower() in ["salir", "exit", "quit", "q"]:
                console.print("[magenta]Cerrando Harness...[/magenta]")
                break
            if tarea:
                harness.procesar(tarea)
    else:
        harness.procesar(args.tarea)
