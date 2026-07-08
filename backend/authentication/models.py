from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    ADMIN = 'admin'
    HOST = 'host'
    VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (HOST, 'Host'),
        (VIEWER, 'Viewer'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=VIEWER)

    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.username} ({self.role})"
