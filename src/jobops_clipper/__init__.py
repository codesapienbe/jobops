import subprocess
import os
import sys
from dotenv import load_dotenv
import json
import datetime
import shutil

load_dotenv(
    # Load .env file from the parent directory (../../.env)
    dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
)

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

try:
    JOBOPS_API_PORT = os.getenv("JOBOPS_API_PORT")
    if not JOBOPS_API_PORT:
        raise Exception("JOBOPS_API_PORT is not set")
except Exception as e:
    print(f"Error loading environment variables: {e}")
    sys.exit(1)

def build():
    """
    Runs 'npm run build' in the jobops_clipper directory using a subprocess.
    Logs output and ensures graceful failure handling.
    Cross-platform: works on Windows, macOS, and Linux.
    """
    console = Console()
    project_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(project_dir, 'build.log')
    log_json_path = os.path.join(project_dir, 'application.log')

    # Find npm executable in a cross-platform way
    npm_candidates = ['npm']
    if os.name == 'nt':
        npm_candidates = ['npm.cmd', 'npm.exe', 'npm']
    npm_path = None
    for candidate in npm_candidates:
        candidate_path = shutil.which(candidate)
        if candidate_path:
            npm_path = candidate_path
            break
    if not npm_path:
        # Log error in application.log
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "component": "jobops_clipper.build",
            "message": "npm executable not found in PATH",
            "correlation_id": None,
            "user_id": None,
            "request_id": None
        }
        with open(log_json_path, 'a') as app_log:
            app_log.write(json.dumps(log_entry) + "\n")
        console.print(Panel.fit(
            Text("Build failed!", style="bold red") +
            Text("\n'npm' not found in PATH. Please install Node.js and ensure npm is available.", style="white"),
            title="[red]Error"
        ))
        sys.exit(1)

    try:
        result = subprocess.run(
            [npm_path, 'run', 'build'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            shell=False  # Always use shell=False for security and cross-platform
        )
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(result.stdout)
            log_file.write('\n')
            log_file.write(result.stderr)
        # Structured logging
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "component": "jobops_clipper.build",
            "message": "Build succeeded",
            "correlation_id": None,
            "user_id": None,
            "request_id": None,
            "output_path": log_path
        }
        with open(log_json_path, 'a', encoding='utf-8') as app_log:
            app_log.write(json.dumps(log_entry) + "\n")
        success_panel = Panel(
            Text.assemble(
                ("Build succeeded!\n", "bold green"),
                ("Output written to ", "white"),
                (log_path, "bold cyan")
            ),
            title="[green]Success[/green]",
            border_style="green"
        )
        console.print(success_panel)
    except FileNotFoundError as fnf:
        # Structured logging for missing npm
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "component": "jobops_clipper.build",
            "message": f"npm not found: {fnf}",
            "correlation_id": None,
            "user_id": None,
            "request_id": None
        }
        with open(log_json_path, 'a', encoding='utf-8') as app_log:
            app_log.write(json.dumps(log_entry) + "\n")
        console.print(Panel.fit(
            Text("Build failed!", style="bold red") +
            Text("\n'npm' not found in PATH. Please install Node.js and ensure npm is available.", style="white"),
            title="[red]Error"
        ))
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(e.stdout or '')
            log_file.write('\n')
            log_file.write(e.stderr or '')
        # Structured logging
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "component": "jobops_clipper.build",
            "message": "Build failed",
            "correlation_id": None,
            "user_id": None,
            "request_id": None,
            "error": e.stderr
        }
        with open(log_json_path, 'a', encoding='utf-8') as app_log:
            app_log.write(json.dumps(log_entry) + "\n")
        error_panel = Panel(
            Text.assemble(
                ("Build failed!\n", "bold red"),
                ("See ", "white"),
                (log_path, "bold cyan"),
                (" for details.", "white")
            ),
            title="[red]Error[/red]",
            border_style="red"
        )
        console.print(error_panel)
        sys.exit(1)

def main():
    build()

if __name__ == "__main__":
    main()