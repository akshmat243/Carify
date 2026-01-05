from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Roles, Permissions, UserRole, UserSession, Leave

from .forms import UserCreationForm, CustomUserChangeForm

# Inline for assigning roles to a user
class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1

class LeaveInline(admin.TabularInline):
    model = Leave
    extra = 1


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    inlines = [UserRoleInline, LeaveInline]

    list_display = ("emp_id","email", "first_name", "last_name", "is_verified_by_admin", "is_active")
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "first_name", "last_name", "password")}),
        ("Personal Info", {
            "fields": (
                "phone", "date_of_birth", "gender", "address", "profile_picture"
            )
        }),
        ("Verification", {
            "fields": (
                "govt_id_number", "govt_id_document",
                "pancard_number", "pancard_document"
            )
        }),
        ("Bank Details", {
            "fields": (
                "bank_account_number", "ifsc_code", "bank_name"
            )
        }),
        ("Permissions", {
            "fields": (
                "is_staff", "is_verified_by_admin", "is_active", "is_superuser",
                "groups", "user_permissions"
            )
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_active")}
        ),
    )


@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ("name", "status")
    search_fields = ("name",)
    list_filter = ("status",)
    filter_horizontal = ("permissions",)  # for better M2M UI

@admin.register(Permissions)
class PermissionsAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("name",)
    ordering = ("code",)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("user", "role")
    search_fields = ("user__email", "role__name")

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "logout_time", "session_duration")
    list_filter = ("user",)
    search_fields = ("user__email",)

    def session_duration(self, obj):
        return obj.session_duration
    session_duration.short_description = "Session Duration"


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ("user", "start_date", "end_date", "status")
    list_filter = ("status", "start_date")
    actions = ["approve_leaves", "reject_leaves"]

    def approve_leaves(self, request, queryset):
        queryset.update(status='approved')
    approve_leaves.short_description = "Mark selected leaves as approved"

    def reject_leaves(self, request, queryset):
        queryset.update(status='rejected')
    reject_leaves.short_description = "Mark selected leaves as rejected"


# @admin.register(Vehicle)
# class VehicleAdmin(admin.ModelAdmin):
#     list_display = ('model', 'inspected_by', 'inspection_date', 'status')
#     list_filter = ('status', 'inspection_date')
#     search_fields = ('model', 'inspected_by__email')