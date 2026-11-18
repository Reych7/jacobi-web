from django.contrib.auth.models import User
from django.db import models

class ServerNode(models.Model):
    server_id = models.CharField(max_length=50, unique=True)
    active_tasks = models.IntegerField(default=0)
    max_slots = models.IntegerField(default=2)
    cpu_percent = models.FloatField(default=0.0)
    ram_percent = models.FloatField(default=0.0)
    last_heartbeat = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.server_id} ({self.active_tasks}/{self.max_slots})"

class ComputeTask(models.Model):

    STATUS_CHOICES = [
        ('queued', 'У черзі'),
        ('running', 'Виконується'),
        ('completed', 'Завершено'),
        ('cancelled', 'Скасовано'),
        ('failed', 'Помилка'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    max_size = models.IntegerField()
    max_iteration = models.IntegerField(default=1000)
    tolerance = models.FloatField(default=1e-6)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress = models.IntegerField(default=0)
    current_iteration = models.IntegerField(default=0)
    server_id = models.CharField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(auto_now_add=True)
    result_preview = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Task #{self.id} (N={self.matrix_size}, {self.status})"



