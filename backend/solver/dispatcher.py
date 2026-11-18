import os
import threading
import time
import psutil
from django.db import transaction
from django.utils import timezone
from .models import ComputeTask, ServerNode
from .jacobi import run_jacobi_task

SERVER_ID = os.environ.get("SERVER_ID", "app1")
MAX_SLOTS = int(os.environ.get("MAX_SLOTS", "2"))

_lock =threading.Lock()
_active_count = 0
_started = False

def _execute_in_thread(task_id: int):
    global _active_count
    try:
        run_jacobi_task(task_id)
    finally:
        with _lock:
            _active_count = max(0, _active_count - 1)


def _worker_loop():
    global _active_count
    while True:
        try:
            with _lock:
                current_active = _active_count

            ServerNode.objects.update_or_create(
                server_id=SERVER_ID,
                defaults={
                    "active_tasks": current_active,
                    "max_slots": MAX_SLOTS,
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_percent": psutil.virtual_memory().percent,
                    "is_online": True,
                },
            )

            if current_active < MAX_SLOTS:
                picked_task_id = None
                with transaction.atomic():
                    task = (
                        ComputeTask.objects.select_for_update(skip_locked=True)
                        .filter(status="queued")
                        .order_by("created_at")
                        .first()
                    )
                    if task:
                        task.status = "running"
                        task.server_id = SERVER_ID
                        task.started_at = timezone.now()
                        task.save(update_fields=["status", "server_id", "started_at"])
                        picked_task_id = task.id


                if picked_task_id is not None:
                    with _lock:
                        _active_count += 1
                    t = threading.Thread(target=_execute_in_thread, args=(picked_task_id,), daemon=True)
                    t.start()
                    continue

        except Exception as exc:
            print(f"[{SERVER_ID}] Dispatcher error: {exc}")

        time.sleep(1.5)

def start_dispatcher():

    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_worker_loop, daemon=True)
    t.start()