from .models import CustomUser, Roles, Permissions, UserRole
from django.core.exceptions import ObjectDoesNotExist


def assign_role_to_user(user: CustomUser, role_name: str):
    try:
        role = Roles.objects.get(name=role_name)
    except Roles.DoesNotExist:
        raise ObjectDoesNotExist(f"Role '{role_name}' does not exist.")

    UserRole.objects.get_or_create(user=user, role=role)


def remove_role_from_user(user: CustomUser, role_name: str):
    try:
        role = Roles.objects.get(name=role_name)
    except Roles.DoesNotExist:
        raise ObjectDoesNotExist(f"Role '{role_name}' does not exist.")

    UserRole.objects.filter(user=user, role=role).delete()


def assign_permission_to_role(role_name: str, permission_name: str):
    try:
        role = Roles.objects.get(name=role_name)
        permission = Permissions.objects.get(name=permission_name)
    except (Roles.DoesNotExist, Permissions.DoesNotExist) as e:
        raise ObjectDoesNotExist(str(e))

    role.permissions.add(permission)


def remove_permission_from_role(role_name: str, permission_name: str):
    try:
        role = Roles.objects.get(name=role_name)
        permission = Permissions.objects.get(name=permission_name)
    except (Roles.DoesNotExist, Permissions.DoesNotExist) as e:
        raise ObjectDoesNotExist(str(e))

    role.permissions.remove(permission)


def get_user_permissions(user: CustomUser):
    user_roles = UserRole.objects.select_related('role').filter(user=user)
    permissions = set()
    for user_role in user_roles:
        permissions.update(user_role.role.permissions.values_list('name', flat=True))
    return permissions


def user_has_permission(user: CustomUser, permission_name: str):
    return permission_name in get_user_permissions(user)
