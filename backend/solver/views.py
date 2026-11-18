from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import ComputeTask, ServerNode


MIN_MATRIX_SIZE = 10
MAX_MATRIX_SIZE = 1500
MAX_ITERATIONS_LIMIT = 5000
MAX_ACTIVE_TASKS_PER_USER = 3



@api_view(['POST'])
def register_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or len(password) < 6:
        return Response(
            {'error': 'Вкажіть логін і пароль (мінімум 6 символів).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Користувач із таким логіном уже існує.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(username=username, password=password)
    login(request, user)
    return Response(
        {'username': user.username, 'is_staff': user.is_staff},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'error': 'Невірний логін або пароль.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    login(request, user)
    return Response({'username': user.username, 'is_staff': user.is_staff})


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'detail': 'Вихід виконано.'})


@api_view(['GET'])
@ensure_csrf_cookie
def me_view(request):
    """Повертає поточного юзера і видає cookie csrftoken для Vue."""
    if request.user.is_authenticated:
        return Response({'username': request.user.username, 'is_staff': request.user.is_staff})
    return Response({'detail': 'Не авторизовано.'}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tasks_view(request):
    if request.method == 'GET':
        # Рахуємо середній час виконання по останніх 10 завершених задачах для прогнозу черги
        recent_done = ComputeTask.objects.filter(status='completed').order_by('-finished_at')[:10]
        durations = [
            t.result_preview.get('execution_time_sec', 8.0)
            for t in recent_done
            if t.result_preview and 'execution_time_sec' in t.result_preview
        ]
        avg_duration = (sum(durations) / len(durations)) if durations else 8.0

        cutoff = timezone.now() - timedelta(seconds=10)
        online_nodes = ServerNode.objects.filter(last_heartbeat__gte=cutoff)
        total_slots = sum(node.max_slots for node in online_nodes) or 4

        user_tasks = ComputeTask.objects.filter(user=request.user).order_by('-created_at')
        queued_ids = list(
            ComputeTask.objects.filter(status='queued')
            .order_by('created_at')
            .values_list('id', flat=True)
        )

        data = []
        for task in user_tasks:
            queue_pos = None
            estimated_wait = None
            if task.status == 'queued' and task.id in queued_ids:
                queue_pos = queued_ids.index(task.id) + 1
                estimated_wait = round((queue_pos * avg_duration) / total_slots, 1)

            data.append({
                'id': task.id,
                'matrix_size': task.matrix_size,
                'max_iterations': task.max_iterations,
                'tolerance': task.tolerance,
                'status': task.status,
                'progress': task.progress,
                'current_iteration': task.current_iteration,
                'server_id': task.server_id,
                'queue_position': queue_pos,
                'estimated_wait_sec': estimated_wait,
                'result_preview': task.result_preview,
                'error_message': task.error_message,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'finished_at': task.finished_at,
            })

        return Response(data)

    try:
        matrix_size = int(request.data.get('matrix_size', 0))
        max_iterations = int(request.data.get('max_iterations', 1000))
        tolerance = float(request.data.get('tolerance', 1e-6))
    except (TypeError, ValueError):
        return Response({'error': 'Некоректні числові параметри.'}, status=status.HTTP_400_BAD_REQUEST)

    if not (MIN_MATRIX_SIZE <= matrix_size <= MAX_MATRIX_SIZE):
        return Response(
            {'error': f'Розмірність матриці N має бути від {MIN_MATRIX_SIZE} до {MAX_MATRIX_SIZE}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not (10 <= max_iterations <= MAX_ITERATIONS_LIMIT):
        return Response(
            {'error': f'Кількість ітерацій має бути від 10 до {MAX_ITERATIONS_LIMIT}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    active_count = ComputeTask.objects.filter(
        user=request.user,
        status__in=['queued', 'running'],
    ).count()
    if active_count >= MAX_ACTIVE_TASKS_PER_USER:
        return Response(
            {'error': f'Досягнуто ліміт активних задач ({MAX_ACTIVE_TASKS_PER_USER}). Дочекайтеся завершення або скасуйте поточну.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    task = ComputeTask.objects.create(
        user=request.user,
        matrix_size=matrix_size,
        max_iterations=max_iterations,
        tolerance=tolerance,
        status='queued',
    )
    return Response({'id': task.id, 'status': task.status}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_task_view(request, pk):
    task = get_object_or_404(ComputeTask, pk=pk, user=request.user)
    if task.status not in ('queued', 'running'):
        return Response(
            {'error': 'Можна скасувати лише задачу, яка в черзі або виконується.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    task.status = 'cancelled'
    task.finished_at = timezone.now()
    task.save(update_fields=['status', 'finished_at'])
    return Response({'id': task.id, 'status': task.status})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def monitor_view(request):
    cutoff = timezone.now() - timedelta(seconds=10)
    nodes = ServerNode.objects.all().order_by('server_id')

    servers_data = []
    for node in nodes:
        online = node.last_heartbeat >= cutoff
        servers_data.append({
            'server_id': node.server_id,
            'active_tasks': node.active_tasks if online else 0,
            'max_slots': node.max_slots,
            'cpu_percent': round(node.cpu_percent, 1),
            'ram_percent': round(node.ram_percent, 1),
            'is_online': online,
            'last_heartbeat': node.last_heartbeat,
        })

    active_tasks = (
        ComputeTask.objects.select_related('user')
        .filter(status__in=['queued', 'running'])
        .order_by('created_at')
    )
    tasks_data = [
        {
            'id': t.id,
            'username': t.user.username,
            'matrix_size': t.matrix_size,
            'status': t.status,
            'progress': t.progress,
            'server_id': t.server_id or '—',
            'created_at': t.created_at,
        }
        for t in active_tasks
    ]

    return Response({
        'servers': servers_data,
        'active_tasks': tasks_data,
    })