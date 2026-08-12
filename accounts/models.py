from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_editor(self) -> bool:
        return self.role == self.Role.EDITOR

    @property
    def is_viewer(self) -> bool:
        return self.role == self.Role.VIEWER
