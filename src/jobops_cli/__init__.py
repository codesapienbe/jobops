import sys
import os
import subprocess
import socket
import time
import typer
from typing import Optional
import logging
from typing_extensions import Annotated
import psutil
from rich.live import Live
from rich.table import Table
import glob
from rich.progress import Progress
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("jobops-cli")

app = typer.Typer(help="JobOps CLI - Manage JobOps API and Tray applications")

def check_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start=8000, end=9000):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("No available port found in range.")

def start_api_service(port: int = 8000) -> Optional[subprocess.Popen]:
    """Start the JobOps API service and verify it is running."""
    logger.info(f"Starting JobOps API on port {port}...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "jobops_api:app", f"--port={port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait up to 5 seconds for the port to be open
        for _ in range(10):
            time.sleep(0.5)
            if check_port_in_use(port):
                return process
            # Check if process has exited early
            if process.poll() is not None:
                break
        # If we get here, the port is not open or process exited
        stdout, stderr = process.communicate(timeout=2)
        logger.error(f"API service failed to start on port {port}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        typer.echo(f"[ERROR] API service failed to start on port {port}. See logs for details.")
        process.terminate()
        return None
    except Exception as e:
        logger.error(f"Failed to start API service: {e}")
        typer.echo(f"[ERROR] Exception while starting API service: {e}")
        return None

def start_tray_application() -> subprocess.Popen:
    """Start the JobOps Tray application."""
    logger.info("Starting JobOps Tray application...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "jobops_tray"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Give it a moment to start
        time.sleep(2)
        return process
    except Exception as e:
        logger.error(f"Failed to start Tray application: {e}")
        raise

def write_pid_file(pid, name):
    config_dir = os.path.expanduser("~/.jobops")
    os.makedirs(config_dir, exist_ok=True)
    pid_file = os.path.join(config_dir, f"jobops_{name}_pid.txt")
    with open(pid_file, "w") as f:
        f.write(str(pid))

def read_pid_file(name):
    config_dir = os.path.expanduser("~/.jobops")
    pid_file = os.path.join(config_dir, f"jobops_{name}_pid.txt")
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None

def is_pid_alive(pid):
    if pid is None:
        return False
    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except Exception:
        return False

def is_process_running(names, debug_log=None, check_pid_file=None):
    if isinstance(names, str):
        names = [names]
    found = False
    debug_lines = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_name = proc.info.get('name')
            cmdline = proc.info.get('cmdline')
            line = f"PID {proc.info.get('pid')}: {proc_name} | {cmdline}"
            for n in names:
                if proc_name and n in proc_name:
                    found = True
                    debug_lines.append(f"MATCH: {line}")
                elif cmdline and any(n in (cmd or '') for cmd in cmdline):
                    found = True
                    debug_lines.append(f"MATCH: {line}")
                else:
                    debug_lines.append(line)
        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError) as e:
            debug_lines.append(f"ERROR: {e}")
            continue
    if debug_log is not None:
        debug_log.extend(debug_lines)
    # If check_pid_file is set, use PID file for detection
    if check_pid_file:
        pid = read_pid_file(check_pid_file)
        alive = is_pid_alive(pid)
        if debug_log is not None:
            debug_log.append(f"PID file check for {check_pid_file}: {pid} alive={alive}")
        return alive
    return found

def check_clipper_status(debug_log=None):
    base_dir = os.getcwd()
    dist_dir = os.path.join(base_dir, 'dist', 'jobops_clipper')
    manifest_path = os.path.join(dist_dir, 'manifest.json')
    js_files = glob.glob(os.path.join(dist_dir, '*.js'))
    status = 'READY' if os.path.exists(manifest_path) and js_files else 'NOT READY'
    details = []
    if not os.path.exists(manifest_path):
        details.append('Missing manifest.json')
    if not js_files:
        details.append('No JS files found')
    if js_files:
        details.append('JS files: ' + ', '.join([os.path.basename(f) for f in js_files]))
    if debug_log is not None:
        debug_log.append(f"Clipper check: manifest={os.path.exists(manifest_path)}, js_files={len(js_files)} (cwd={base_dir})")
    return status, '; '.join(details) if details else 'All files present'

def truncate_debug(debug_str, max_lines=4):
    lines = debug_str.splitlines()
    if len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + '\n...(truncated)'
    return '\n'.join(lines)

def get_status_table(api_port, debug_log=None):
    table = Table(title="JobOps Real-Time Monitor")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Debug", style="yellow")
    table.add_column("Details", style="green")
    # API
    api_debug = []
    try:
        api_running = is_process_running(["jobops_api"], api_debug, check_pid_file="api")
        if api_running:
            api_status = "RUNNING"
            api_details = f"Port: {api_port}"
        else:
            api_status = "STOPPED"
            api_details = f"Port: {api_port} (not in use)"
            api_debug.append(f"API port {api_port} not in use.")
    except Exception as e:
        api_status = "ERROR"
        api_details = "Status check failed"
        api_debug.append(f"Exception: {e}")
    table.add_row("API", api_status, truncate_debug("\n".join(api_debug)), api_details)
    # Tray
    tray_debug = []
    try:
        tray_running = is_process_running(["jobops_tray", "jobops.views.app"], tray_debug, check_pid_file="tray")
        if tray_running:
            tray_status = "RUNNING"
            tray_details = "Process detected"
        else:
            tray_status = "STOPPED"
            tray_details = "No process detected"
            tray_debug.append("Tray process not running or PID file missing.")
    except Exception as e:
        tray_status = "ERROR"
        tray_details = "Status check failed"
        tray_debug.append(f"Exception: {e}")
    table.add_row("Tray", tray_status, truncate_debug("\n".join(tray_debug)), tray_details)
    # Clipper
    clipper_debug = []
    try:
        clipper_status, clipper_details = check_clipper_status(clipper_debug)
    except Exception as e:
        clipper_status = "ERROR"
        clipper_details = "Status check failed"
        clipper_debug.append(f"Exception: {e}")
    table.add_row("Clipper", clipper_status, truncate_debug('\n'.join(clipper_debug)), clipper_details)
    return table

def monitor_services(api_port, live):
    debug_log = []
    try:
        while True:
            live.update(get_status_table(api_port, debug_log))
            time.sleep(1)
    except KeyboardInterrupt:
        pass

@app.command()
def status(api_port: Annotated[int, typer.Option(help="Port for the API service")] = 8000):
    """Check the status of JobOps services."""
    # Check API status
    api_running = is_process_running(["jobops_api"], check_pid_file="api")
    typer.echo(f"JobOps API: {'RUNNING' if api_running else 'STOPPED'} (Port {api_port})")
    
    # For tray application, we can only check if the process exists
    # This is a simplified check and might not be 100% accurate
    if is_process_running("jobops_tray", check_pid_file="tray"):
        tray_running = True
    else:
        tray_running = False
    
    typer.echo(f"JobOps Tray: {'RUNNING' if tray_running else 'STOPPED'}")
    
    return api_running, tray_running

@app.command()
def start(
    api: Annotated[bool, typer.Option(help="Start the API service")] = True,
    tray: Annotated[bool, typer.Option(help="Start the Tray application")] = True,
    api_port: Annotated[int, typer.Option(help="Port for the API service")] = 8000
):
    """Start JobOps services."""
    processes = []
    actual_api_port = api_port
    progress_state = {"API": "Pending", "Tray": "Pending", "Clipper": "Pending"}
    debug_state = {"API": "", "Tray": "", "Clipper": ""}
    details_state = {"API": "", "Tray": "", "Clipper": ""}
    try:
        with Live(get_status_table_with_progress(api_port, progress_state, debug_state, details_state), refresh_per_second=4) as live:
            # API startup
            if api:
                progress_state["API"] = "Starting..."
                debug_state["API"] = "Launching API process"
                live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                if check_port_in_use(api_port):
                    actual_api_port = find_available_port(api_port + 1, api_port + 100)
                    debug_state["API"] = f"API port {api_port} in use, using {actual_api_port}"
                    live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                config_dir = os.path.expanduser("~/.jobops")
                os.makedirs(config_dir, exist_ok=True)
                port_file = os.path.join(config_dir, "jobops_api_port.txt")
                with open(port_file, "w") as f:
                    f.write(str(actual_api_port))
                process = start_api_service(actual_api_port)
                if process:
                    write_pid_file(process.pid, "api")
                    processes.append((process, "api"))
                    # Wait for port to be open
                    for _ in range(10):
                        if check_port_in_use(actual_api_port):
                            progress_state["API"] = "Started"
                            debug_state["API"] = f"API running on port {actual_api_port}"
                            details_state["API"] = f"Port: {actual_api_port}"
                            break
                        time.sleep(0.5)
                        live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                    else:
                        progress_state["API"] = "Failed"
                        debug_state["API"] = "API did not open port"
                        details_state["API"] = f"Port: {actual_api_port} (not in use)"
                    live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                else:
                    progress_state["API"] = "Failed"
                    debug_state["API"] = "API process failed to start"
                    details_state["API"] = f"Port: {actual_api_port} (not in use)"
                    live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
            else:
                progress_state["API"] = "Skipped"
                debug_state["API"] = "API not started"
                details_state["API"] = ""
                live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
            # Tray startup
            if tray:
                progress_state["Tray"] = "Starting..."
                debug_state["Tray"] = "Launching Tray process"
                live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                if is_process_running(["jobops_tray", "jobops.views.app"], check_pid_file="tray"):
                    progress_state["Tray"] = "Already running"
                    debug_state["Tray"] = "Tray already running"
                    details_state["Tray"] = "Process detected"
                    live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                else:
                    process = start_tray_application()
                    if process:
                        write_pid_file(process.pid, "tray")
                        processes.append((process, "tray"))
                        # Wait for PID file and process
                        if wait_for_pid_file("tray", timeout=10):
                            progress_state["Tray"] = "Started"
                            debug_state["Tray"] = "Tray running"
                            details_state["Tray"] = "Process detected"
                        else:
                            progress_state["Tray"] = "Failed"
                            # Try to print tray process output for diagnosis
                            try:
                                stdout, stderr = process.communicate(timeout=2)
                                debug_state["Tray"] = f"Tray did not start or PID file missing\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                            except Exception as e:
                                debug_state["Tray"] = f"Tray did not start or PID file missing\nError reading output: {e}"
                            details_state["Tray"] = "No process detected"
                        live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
                    else:
                        progress_state["Tray"] = "Failed"
                        debug_state["Tray"] = "Tray process failed to start"
                        details_state["Tray"] = "No process detected"
                        live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
            else:
                progress_state["Tray"] = "Skipped"
                debug_state["Tray"] = "Tray not started"
                details_state["Tray"] = ""
                live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
            # Clipper status
            progress_state["Clipper"] = "Checking..."
            debug_state["Clipper"] = "Checking build status"
            details_state["Clipper"] = ""
            live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
            # After startup, switch to monitoring
            time.sleep(1)
            progress_state["API"] = "Monitoring"
            progress_state["Tray"] = "Monitoring"
            progress_state["Clipper"] = "Monitoring"
            live.update(get_status_table_with_progress(api_port, progress_state, debug_state, details_state))
            # Switch to monitoring mode using the same Live context
            monitor_services(actual_api_port, live)
    finally:
        typer.echo("Stopping services...")
        for process, name in processes:
            try:
                process.terminate()
                process.wait()
                remove_pid_file(name)
                typer.echo(f"Stopped {name} service (PID {process.pid})")
            except Exception as e:
                typer.echo(f"Error stopping {name} service: {e}")
        typer.echo("All services stopped")


def get_status_table_with_progress(api_port, progress_state, debug_state, details_state):
    # Clear the console before rendering the table to avoid header duplication
    os.system('cls' if os.name == 'nt' else 'clear')
    term_width = shutil.get_terminal_size((100, 20)).columns
    # Assign proportional widths (min 10 per col)
    col_widths = [max(10, int(term_width * 0.13)),  # Service
                  max(10, int(term_width * 0.13)),  # Status
                  max(10, int(term_width * 0.44)),  # Debug
                  max(10, int(term_width * 0.3))]   # Details
    table = Table(title="JobOps Real-Time Monitor", width=term_width)
    table.add_column("Service", style="cyan", width=col_widths[0])
    table.add_column("Status", style="magenta", width=col_widths[1])
    table.add_column("Debug", style="yellow", width=col_widths[2])
    table.add_column("Details", style="green", width=col_widths[3])
    # API
    api_debug = [progress_state["API"]]
    if debug_state["API"]:
        api_debug.append(debug_state["API"])
    api_details = details_state["API"]
    table.add_row("API", progress_state["API"], truncate_debug("\n".join(api_debug)), api_details)
    # Tray
    tray_debug = [progress_state["Tray"]]
    if debug_state["Tray"]:
        tray_debug.append(debug_state["Tray"])
    tray_details = details_state["Tray"]
    table.add_row("Tray", progress_state["Tray"], truncate_debug("\n".join(tray_debug)), tray_details)
    # Clipper
    clipper_debug = [progress_state["Clipper"]]
    if debug_state["Clipper"]:
        clipper_debug.append(debug_state["Clipper"])
    clipper_details = details_state["Clipper"]
    table.add_row("Clipper", progress_state["Clipper"], truncate_debug("\n".join(clipper_debug)), clipper_details)
    return table

@app.command()
def stop():
    """Stop all JobOps services."""
    try:
        # Stop API service
        subprocess.run(["pkill", "-f", "uvicorn jobops_api.main:app"], check=False)
        typer.echo("API service stopped")
        
        # Stop Tray application
        subprocess.run(["pkill", "-f", "jobops_tray"], check=False)
        typer.echo("Tray application stopped")
    except Exception as e:
        typer.echo(f"Error stopping services: {e}")

def remove_pid_file(name):
    config_dir = os.path.expanduser("~/.jobops")
    pid_file = os.path.join(config_dir, f"jobops_{name}_pid.txt")
    try:
        os.remove(pid_file)
    except Exception:
        pass

def wait_for_pid_file(name, timeout=10):
    config_dir = os.path.expanduser("~/.jobops")
    pid_file = os.path.join(config_dir, f"jobops_{name}_pid.txt")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(pid_file):
            try:
                pid = int(open(pid_file).read().strip())
                if is_pid_alive(pid):
                    return True
            except Exception:
                pass
        time.sleep(0.5)
    return False

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()
