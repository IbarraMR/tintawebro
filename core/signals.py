from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from .models import Empleados

@receiver(post_save, sender=Empleados)
def crear_usuario_empleado(sender, instance, created, **kwargs):
    """
    Crea automáticamente un usuario asociado cuando se registra un nuevo empleado.
    """
    if created and not instance.user:
        nombre_usuario = instance.email or instance.dni
        if not nombre_usuario:
            return  

        password_temporal = "1234"
        user = User.objects.create(
            username=nombre_usuario,
            email=instance.email,
            first_name=instance.nombre,
            last_name=instance.apellido or "",
            password=make_password(password_temporal)
        )

        if instance.rol == "Jefe":
            grupo, _ = Group.objects.get_or_create(name="Jefe")
        else:
            grupo, _ = Group.objects.get_or_create(name="Empleado")
        user.groups.add(grupo)

        instance.user = user
        instance.save()
