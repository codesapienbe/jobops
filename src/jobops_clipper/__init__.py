import subprocess
import os
import sys
from dotenv import load_dotenv

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
    """
    console = Console()
    project_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(project_dir, 'build.log')
    try:
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True
        )
        with open(log_path, 'w') as log_file:
            log_file.write(result.stdout)
            log_file.write('\n')
            log_file.write(result.stderr)
        console.print(Panel.fit(
            Text("Build succeeded!", style="bold green") +
            Text(f"\nOutput written to [bold cyan]{log_path}[/]", style="white"),
            title="[green]Success"
        ))
    except subprocess.CalledProcessError as e:
        with open(log_path, 'w') as log_file:
            log_file.write(e.stdout or '')
            log_file.write('\n')
            log_file.write(e.stderr or '')
        console.print(Panel.fit(
            Text("Build failed!", style="bold red") +
            Text(f"\nSee [bold cyan]{log_path}[/] for details.", style="white"),
            title="[red]Error"
        ))
        sys.exit(1)

def main():
    build()

if __name__ == "__main__":
    main()