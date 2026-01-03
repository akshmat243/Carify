from rest_framework import permissions
from User.models import UserRole  # User app se UserRole model import karo

class IsStaffOrManager(permissions.BasePermission):
    """
    Custom Permission to allow only Admin, Manager, or Staff to perform actions.
    Regular customers will be blocked.
    """
    def has_permission(self, request, view):
        # 1. Agar user login hi nahi hai, to bhaga do
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Agar user Django ka Superuser ya Staff hai, to allow karo
        if request.user.is_superuser or request.user.is_staff:
            return True

        # 3. Check karo ki user ke paas 'Manager' ya 'Staff' role hai ya nahi
        # Hum check kar rahe hain ki UserRole table mein entry hai ya nahi
        allowed_roles = ['Admin', 'Manager', 'Staff', 'Superuser']
        
        has_role = UserRole.objects.filter(
            user=request.user, 
            role__name__in=allowed_roles
        ).exists()

        return has_role