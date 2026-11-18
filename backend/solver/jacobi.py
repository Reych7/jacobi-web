import time
import numpy as np
from django.utils import timezone
from .models import ComputeTask


def run_jacobi_task(task_id: int):
    task = ComputeTask.objects.get(pk=task_id)
    n = task.matrix_size
    max_iter = task.max_iterations
    tol = task.tolerance

    start_time = time.perf_counter()

    try:

        rng = np.random.default_rng(seed=task_id)
        A = rng.uniform(-1.0, 1.0, size=(n, n))
        np.fill_diagonal(A, 0.0)
        row_sums = np.sum(np.abs(A), axis=1)
        D = row_sums + rng.uniform(1.0, 5.0, size=n)
        np.fill_diagonal(A, D)

        b = rng.uniform(-10.0, 10.0, size=n)
        x = np.zeros(n, dtype=np.float64)


        step_check = max(1, max_iter // 20)
        final_error = 0.0
        completed_iter = 0

        for k in range(1, max_iter + 1):
            x_new = (b - (A @ x - D * x)) / D
            final_error = float(np.max(np.abs(x_new - x)))
            x = x_new
            completed_iter = k


            time.sleep(0.005)


            if k % step_check == 0 or k == max_iter:
                current_status = (
                    ComputeTask.objects.filter(pk=task_id)
                    .values_list('status', flat=True)
                    .first()
                )
                if current_status == 'cancelled':
                    ComputeTask.objects.filter(pk=task_id).update(
                        current_iteration=k,
                        finished_at=timezone.now(),
                    )
                    return

                progress = min(99, int((k / max_iter) * 100))
                ComputeTask.objects.filter(pk=task_id).update(
                    progress=progress,
                    current_iteration=k,
                )


            if final_error < tol:
                break

        elapsed = round(time.perf_counter() - start_time, 3)


        ComputeTask.objects.filter(pk=task_id).update(
            status='completed',
            progress=100,
            current_iteration=completed_iter,
            finished_at=timezone.now(),
            result_preview={
                'execution_time_sec': elapsed,
                'iterations_used': completed_iter,
                'final_error': final_error,
                'x_sample': [round(float(val), 6) for val in x[:10]],
            },
        )

    except Exception as exc:
        ComputeTask.objects.filter(pk=task_id).update(
            status='failed',
            error_message=str(exc),
            finished_at=timezone.now(),
        )