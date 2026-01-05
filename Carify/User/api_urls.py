from django.urls import path
from . import api_views 
from .api_views import VerifyBankDetailsAPI
from .api_views import *


urlpatterns = [
    path('login/', api_views.LoginAPIView.as_view(), name='api_login'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='api_logout'), 
    path('register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('dashboard/', api_views.AdminDashboardAPIView.as_view(), name='api_admin_dashboard'),

    # User Management Dashboard
    path('user-management/', api_views.UserManagementDashboardAPIView.as_view(), name='api_user_management'),
    
    # Actions (Verify/Unverify) - Example: /api/user/action/verify/5/
    path('action/<str:action>/<int:user_id>/', api_views.UserActionAPIView.as_view(), name='api_user_action'),
    
    # Delete User - Example: /api/user/delete/5/
    path('delete/<int:user_id>/', api_views.UserActionAPIView.as_view(), name='api_user_delete'),

    path('engineers/', api_views.EngineerListAPIView.as_view(), name='api_engineer_list'),

    path('staff/<int:user_id>/calendar/', api_views.StaffLeaveCalendarAPIView.as_view(), name='api_staff_leave_calendar'),

    path('leave-events/<int:user_id>/', api_views.LeaveEventsAPIView.as_view(), name='api_leave_events'),

    path('profile/', api_views.UserProfileAPIView.as_view(), name='api_user_profile'),

    # to see specific user profile 
    path('profile/<int:id>/', api_views.UserProfileDetailAPIView.as_view(), name='api_user_profile_detail'),

    path('verify-bank/', VerifyBankDetailsAPI.as_view(), name='verify-bank'),

    # Employee (Apply and to see the list)
    path('leave/apply/', ApplyLeaveAPI.as_view(), name='api-apply-leave'),

    # Manager/Admin  (Approve aur Reject)
    path('leave/approve/<int:leave_id>/', ApproveLeaveAPI.as_view(), name='api-approve-leave'),
    path('leave/reject/<int:leave_id>/', RejectLeaveAPI.as_view(), name='api-reject-leave'),

    path('admin/leaves/', ManageLeavesAPI.as_view(), name='api-manage-leaves'),

    path('admin/report/user/<int:user_id>/', UserLoginReportAPI.as_view(), name='api-user-report'),

    # Specific User ki History
    path('vehicles/user/<int:user_id>/', UserInspectedVehiclesAPI.as_view(), name='api-user-vehicles'),
    
    # Sabhi Vehicles ki History
    path('vehicles/all/', AllInspectedVehiclesAPI.as_view(), name='api-all-vehicles'),

    # Print Report API (GET)
    path('vehicle/report/<int:vehicle_id>/', VehicleReportAPI.as_view(), name='api-vehicle-report'),
    
    # Delete API (DELETE)
    path('vehicle/delete/<int:pk>/', DeleteVehicleAPI.as_view(), name='api-vehicle-delete'),

    # Create Vehicle (POST)
    path('vehicle/create/', CreateVehicleAPI.as_view(), name='api-vehicle-create'),

    # Manage Roles (Get List / Create New)
    path('admin/roles/', RoleManagementAPI.as_view(), name='api-manage-roles'),

    # Manage Permissions (Get List / Create New)
    path('admin/permissions/', PermissionManagementAPI.as_view(), name='api-manage-permissions'),

    # Assign Permissions to Role
    path('admin/roles/assign-permissions/', AssignRolePermissionsAPI.as_view(), name='api-assign-role-permissions'),

    # User Roles (List All / Assign Role to User)
    path('admin/user-roles/', UserRoleManagementAPI.as_view(), name='api-user-roles'),











]