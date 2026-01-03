from . import views
from . import api_views
from django.urls import path

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('admin-dashboard', views.admin_dashboard, name="admin_dashboard"),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('verify-user/<int:user_id>/', views.verify_user_view, name='verify_user'),
    path('unverify-user/<int:user_id>/', views.unverify_user_view, name='unverify_user'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('engineers/', views.engineer_view, name = 'engineer'),
    path('staff/<int:user_id>/calendar/', views.leave_calendar_view, name='leave_calendar'),
    path('staff/<int:user_id>/calendar/events/', views.leave_events_json, name='leave_events_json'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('verify-bank/', views.verify_bank_details, name='verify_bank'),
    path('apply-leave/', views.apply_leave_view, name='apply_leave'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    path('admin/leaves/', views.manage_leaves_view, name='manage_leaves'),
    path('login-log/<int:user_id>', views.login_logout_report, name='login_logout_report'),


    path('vehicles/inspected/user/<int:user_id>/', views.vehicles_inspected_by_single_user, name='vehicles_inspected_by_user'),
    path('vehicles/inspected/', views.vehicles_inspected, name='vehicles_inspected'),

    path('vehicle/<int:vehicle_id>/print/', views.print_view, name='print_vehicle_report'),
    path('vehicle/delete/<int:pk>/', views.delete_vehicle, name='delete_vehicle'),

    path('roles-dashboard/', views.roles_dashboard, name='roles_dashboard'),
    path('role-manage/', views.manage_roles_permissions, name='manage_roles_permissions'),
    path('assign-role-permission/', views.assign_permissions_to_role, name='assign_permissions_to_role'),
    path('assign-user-role/<int:user_id>', views.assign_roles_to_users, name='assign_roles_to_users'),



    #NEW-WORK
    # path('api/login/', api_views.LoginAPIView.as_view(), name='api_login'),
    # path('api/profile/', api_views.UserProfileAPIView.as_view(), name='api_profile'),
    # path('api/register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    # path('api/profile/update/', api_views.UserProfileDetailAPIView.as_view(), name='api_profile_update'),
    # path('api/bank/verify/', api_views.VerifyBankAPIView.as_view(), name='api_bank_verify'),


]
