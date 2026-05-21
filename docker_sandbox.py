import docker
import os
import re
from rich.console import Console

console = Console()

class DockerSandbox:
    def __init__(self, image="python:3.11-slim", container_name="jarvis_sandbox", deps_extra=None):
        self.client = docker.from_env()
        self.image = image
        self.container_name = container_name
        self.workspace_dir = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
        os.makedirs(self.workspace_dir, exist_ok=True)
        self.container = None
        self.deps_extra = deps_extra
        self._iniciar_contenedor()

    def _iniciar_contenedor(self):
        console.print(f"[bold cyan]🐳 Iniciando Sandbox Docker ({self.image})...[/bold cyan]")
        try:
            viejo = self.client.containers.get(self.container_name)
            viejo.stop()
            viejo.remove()
        except: pass

        self.container = self.client.containers.run(
            self.image,
            command="tail -f /dev/null",
            name=self.container_name,
            detach=True,
            volumes={self.workspace_dir: {'bind': '/workspace', 'mode': 'rw'}},
            mem_limit="2g",
            working_dir="/workspace"
        )
        
        def run_check(cmd, msg):
            console.print(f"[yellow]📦 {msg}...[/yellow]")
            res = self.container.exec_run(cmd)
            if res.exit_code != 0:
                console.print(f"[bold red]❌ Falló: {cmd}[/bold red]\n{res.output.decode()}")
                return False
            return True

        run_check("apt-get update", "Actualizando apt")
        run_check("apt-get install -y ffmpeg build-essential libsndfile1 git", "Instalando herramientas de sistema")
        run_check("pip install --upgrade pip", "Actualizando pip")
        
        # Librerías mínimas requeridas por defecto
        run_check("pip install numpy scipy beautifulsoup4 mutagen", "Instalando librerías base")
        
        # Instalación opcional/configurable de dependencias pesadas
        if self.deps_extra:
            for dep in self.deps_extra:
                if dep == "whisper":
                    run_check("pip install openai-whisper", "Instalando Whisper")
                elif dep == "nltk":
                    run_check("pip install nltk", "Instalando NLTK")
                    run_check("python -m nltk.downloader punkt averaged_perceptron_tagger stopwords vader_lexicon", "Descargando datos NLTK")
                elif dep == "librosa":
                    run_check("pip install librosa matplotlib", "Instalando Librosa y Matplotlib")
                else:
                    run_check(f"pip install {dep}", f"Instalando {dep}")
        else:
            # Fallback por compatibilidad: instalar todo si no se especifica
            run_check("pip install librosa nltk beautifulsoup4 pypdf ebooklib numpy scipy matplotlib mutagen", "Instalando todas las librerías")
            run_check("pip install openai-whisper", "Instalando Whisper")
            run_check("python -m nltk.downloader punkt averaged_perceptron_tagger stopwords vader_lexicon", "Descargando datos NLTK")
        
        console.print("[bold green]🚀 Sandbox Preparado y listo.[/bold green]")

    def ejecutar_codigo(self, script_content, filename=None):
        if not self.container: return False, "Contenedor inactivo."
        codigo = script_content.strip()
        if "```" in codigo:
            parts = codigo.split("```")
            for p in parts:
                if p.strip().startswith("python") or p.strip().startswith("import"):
                    codigo = p.strip()
                    if codigo.startswith("python"): codigo = codigo[6:].strip()
                    break
        codigo = re.sub(r'^(python|markdown|code|script)\s+', '', codigo, flags=re.IGNORECASE)
        filename = filename or "script.py"
        filepath = os.path.join(self.workspace_dir, filename)
        with open(filepath, "w") as f:
            f.write(codigo)
        try:
            res = self.container.exec_run(f"python {filename}")
            output = res.output.decode("utf-8").strip()
            return res.exit_code == 0, output
        except Exception as e:
            return False, str(e)

    def apagar(self):
        if self.container:
            try:
                self.container.remove(force=True)
            except Exception:
                pass
            self.container = None
