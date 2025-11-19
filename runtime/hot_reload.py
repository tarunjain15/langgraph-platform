"""
Hot Reload - File watching with automatic workflow restart

Watches workflow files and triggers reload on changes (<2s latency).
"""

import time
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class WorkflowWatcher(FileSystemEventHandler):
    """Watches workflow file for modifications"""

    def __init__(self, workflow_path: str, executor, callback):
        self.workflow_path = Path(workflow_path).resolve()
        self.executor = executor
        self.callback = callback
        self.last_modified = 0
        self.debounce_seconds = 0.5  # Debounce to avoid multiple triggers

    def on_modified(self, event):
        """Handle file modification event"""
        if isinstance(event, FileModifiedEvent):
            event_path = Path(event.src_path).resolve()

            # Check if it's our workflow file
            if event_path == self.workflow_path:
                current_time = time.time()

                # Debounce: Ignore if modified within last 0.5s
                if current_time - self.last_modified < self.debounce_seconds:
                    return

                self.last_modified = current_time

                print(f"[lgp] File changed detected ({time.time():.1f})")
                print(f"[lgp] Reloading workflow...")

                # Trigger callback
                self.callback()


def watch_and_execute(workflow_path: str, executor):
    """Watch workflow file and execute on changes

    This is the main entry point for hot reload mode.
    """
    workflow_path = Path(workflow_path).resolve()
    watch_dir = workflow_path.parent

    print(f"[lgp] Watching: {workflow_path}")
    print()

    # Track reload timing
    reload_start = None

    def execute_workflow():
        """Execute workflow and track timing"""
        nonlocal reload_start

        if reload_start is not None:
            # This is a reload
            reload_time = time.time() - reload_start
            print(f"[lgp] Reload complete ({reload_time:.1f}s)")
            print()

        reload_start = time.time()

        try:
            # Execute workflow
            executor.execute(str(workflow_path))

            # Reset timer (execution complete)
            reload_start = None

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[lgp] Execution failed: {e}")
            print()
            # Don't exit, keep watching
            reload_start = None

    # Initial execution
    execute_workflow()

    # Setup file watcher
    event_handler = WorkflowWatcher(
        workflow_path=str(workflow_path),
        executor=executor,
        callback=execute_workflow
    )

    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()

    try:
        # Keep watching until Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("[lgp] Stopping hot reload...")
        observer.stop()
        observer.join()
        print("[lgp] Stopped")
