import os
import sys
import time
import logging
import subprocess
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ─── Configuration ───────────────────────────────────────────────────────────
WATCH_DIR = "data"
TARGET_SCRIPT = "app.py"
DEBOUNCE_SECONDS = 2.0      # Wait before triggering to catch duplicate events
FILE_SETTLE_SECONDS = 1.5   # Wait for file copy/write to finish completely
MAX_CONCURRENT = 1           # Prevent overlapping app.py runs

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class SafeQuizFileHandler(FileSystemEventHandler):
    """Watches for new CSV files and triggers processing only when the file
    is fully written and no duplicate events have occurred recently."""

    def __init__(self):
        super().__init__()
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self._active_runs = 0

    def on_created(self, event):
        if event.is_directory:
            return

        if not event.src_path.lower().endswith(".csv"):
            return

        file_path = event.src_path

        # ── Debounce: cancel previous timer for this path if it exists ──
        if file_path in self._timers:
            self._timers[file_path].cancel()
            log.debug(f"Debounced duplicate event for: {file_path}")

        # ── Schedule processing after debounce period ──
        self._timers[file_path] = threading.Timer(
            DEBOUNCE_SECONDS,
            self._safe_process,
            args=[file_path],
        )
        self._timers[file_path].start()

    def _safe_process(self, file_path: str):
        """Wait for file to settle, then run app.py."""
        # Remove from timer dict
        self._timers.pop(file_path, None)

        # ── Wait for file copy/write to finish completely ──
        log.info(f"Detected: {file_path} — waiting for file to settle...")
        if not self._wait_for_file_settle(file_path):
            log.error(f"File disappeared before processing: {file_path}")
            return

        file_size = os.path.getsize(file_path)
        log.info(f"File ready ({file_size:,} bytes): {file_path}")

        # ── Prevent concurrent runs ──
        with self._lock:
            if self._active_runs >= MAX_CONCURRENT:
                log.warning(
                    f"Skipping {file_path} — {TARGET_SCRIPT} is already running. "
                    f"Wait for it to finish before adding new files."
                )
                return
            self._active_runs += 1

        try:
            self._run_script(file_path)
        finally:
            with self._lock:
                self._active_runs -= 1

    def _wait_for_file_settle(self, file_path: str, timeout: float = 15.0) -> bool:
        """Block until the file size stops changing (meaning the write is done)."""
        last_size = -1
        stable_ticks = 0
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not os.path.exists(file_path):
                return False  # File was deleted

            try:
                current_size = os.path.getsize(file_path)
            except OSError:
                return False

            if current_size == last_size:
                stable_ticks += 1
                # File size hasn't changed for 2 consecutive checks (~0.5s)
                if stable_ticks >= 2:
                    return True
            else:
                stable_ticks = 0
                last_size = current_size

            time.sleep(0.25)

        # Timeout reached but file exists — process it anyway
        log.warning(f"Settle timeout reached for {file_path}, processing anyway.")
        return True

    def _run_script(self, file_path: str):
        """Execute app.py, passing the CSV path as an argument."""
        if not os.path.exists(TARGET_SCRIPT):
            log.error(f"Cannot find {TARGET_SCRIPT} in the current directory!")
            return

        # Pass the specific file path so app.py knows exactly what to process
        # app.py can read this via: sys.argv[1]
        command = [sys.executable, TARGET_SCRIPT, file_path]

        log.info(f"Executing: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,  # Don't raise, we want to log output manually
            )

            # Log stdout if app.py produced any
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n")[-10:]:
                    log.info(f"[app.py] {line}")

            # Log stderr if app.py crashed
            if result.returncode != 0:
                log.error(f"{TARGET_SCRIPT} exited with code {result.returncode}")
                if result.stderr.strip():
                    for line in result.stderr.strip().split("\n")[-10:]:
                        log.error(f"[app.py] {line}")
            else:
                log.info(f"✅ Successfully processed: {file_path}")

        except FileNotFoundError:
            log.error(f"Python interpreter not found: {sys.executable}")
        except Exception as e:
            log.exception(f"Unexpected error running {TARGET_SCRIPT}: {e}")


def main():
    watch_path = Path(WATCH_DIR)

    # ── Ensure the watch directory exists ──
    if not watch_path.exists():
        log.error(f"Watch directory '{watch_path}' does not exist. Creating it...")
        try:
            watch_path.mkdir(parents=True, exist_ok=True)
            log.info(f"Created directory: {watch_path}")
        except OSError as e:
            log.critical(f"Failed to create directory '{watch_path}': {e}")
            sys.exit(1)

    # ── Start the watcher ──
    event_handler = SafeQuizFileHandler()
    observer = Observer()

    observer.schedule(
        event_handler,
        str(watch_path),
        recursive=False,
    )
    observer.start()

    log.info(f"👁️  Watching '{watch_path.resolve()}/' for new .csv files...")
    log.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down observer...")
        observer.stop()

    observer.join()
    log.info("Observer stopped.")


if __name__ == "__main__":
    main()