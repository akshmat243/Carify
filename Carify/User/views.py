

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.utils import timezone 
from django.utils.timezone import now
from django.db import models
from django.db.models import Avg, Count, Sum, ExpressionWrapper, DurationField, F, Q
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.conf import settings
from reportlab.pdfgen import canvas
from datetime import date , datetime , timedelta 




# Custom app models and forms
from CarPDI.models import Vehicle, Customer
from .models import CustomUser, Roles, Permissions, UserRole, Leave
from .forms import *
from CarPDI.models import *
# Role management utilities
from .permission import assign_role_to_user, assign_permission_to_role, user_has_permission
from django.contrib import messages

User = get_user_model()

# ========== Access Control Decorators ==========

def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url='login'
    )(view_func), login_url='login')
    return decorated_view_func

def staff_required(view_func):
    decorated_view_func = login_required(user_passes_test(
        lambda user: user.is_authenticated and (user.is_verified_by_admin or user.is_superuser),
        login_url='login'
    )(view_func), login_url='login')
    return decorated_view_func

def superadmin_required(view_func):
    decorated_view_func = login_required(user_passes_test(
        lambda user: user.is_authenticated and user.is_superuser and user.is_staff,
        login_url='login'
    )(view_func), login_url='login')
    return decorated_view_func

# ========== Authentication Views ==========

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Share credentials to the user after verifying.')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'user/register.html', {'form': form})



def login_view(request):
    if request.user.is_authenticated:
        # Already logged in, redirect based on role
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_dashboard')
        elif request.user.is_verified_by_admin:
            return redirect('admin_dashboard')
        else:
            return redirect('profile')  # Unverified users go to profile

    # If not authenticated, proceed with login
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            user = authenticate(request, email=email, password=password)

            if user:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(6000)

                if user.is_superuser or user.is_staff or user.is_verified_by_admin:
                    messages.success(request, f'Welcome {user.get_full_name() or user.email}!')
                    return redirect('admin_dashboard')
                else:
                    messages.info(request, "Please complete your profile. Waiting for admin verification.")
                    return redirect('profile')
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, 'user/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# ========== Dashboard View ==========

@login_required
def admin_dashboard(request):
    total_vehicles = Vehicle.objects.count()
    total_customers = Customer.objects.count()
    avg_health_score = Vehicle.objects.aggregate(avg=Avg('health_score'))['avg'] or 0
    recent_inspections = Vehicle.objects.filter(inspection_date__gte=datetime.today() - timedelta(days=7)).count()

    vehicles = Vehicle.objects.select_related('customer').all()
    users = CustomUser.objects.all()
    
    total_users = users.count()
    active_user_ids = get_active_user_ids()
    active_users = users.filter(id__in=active_user_ids).count()
    inactive_users = total_users - active_users
    verified_users = users.filter(is_verified_by_admin=True).count()

    dashboard_cards = [
        {
            'label': 'Total Users',
            'icon': 'fa-users',
            'value': total_users,
            'width': total_users * 1,
        },
        {
            'label': 'Active Users',
            'icon': 'fa-user-check',
            'value': active_users,
            'width': active_users * 1,
        },
        {
            'label': 'Inactive Users',
            'icon': 'fa-user-slash',
            'value': inactive_users,
            'width': inactive_users * 1,
        },
        {
            'label': 'Verified by Admin',
            'icon': 'fa-user-shield',
            'value': verified_users,
            'width': verified_users * 1,
        },

        {
            'label': 'Total Customers',
            'icon': 'fa-users',
            'value': total_customers,
            'width': total_customers * 1,
        },
        {
            'label': 'Total Vehicles',
            'icon': 'fa-car',
            'value': total_vehicles,
            'width': total_vehicles * 1,
        },
        {
            'label': 'Avg. Health Score',
            'icon': 'fa-heart-pulse',
            'value': f'{avg_health_score:.1f}/5.0',
            'width': avg_health_score * 20,
        },
        {
            'label': 'Recent Inspections',
            'icon': 'fa-clipboard-check',
            'value': recent_inspections,
            'width': recent_inspections * 1,
        },
    ]

    context = {
        'dashboard_cards': dashboard_cards,
        'vehicles': vehicles,
        'page_title': 'Dashboard'
    }
    return render(request, 'user/admin_dashboard1.html', context)


# ========== Vehicle Views ==========

def print_view(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    context = {
        'vehicle': vehicle,
        'customer': vehicle.customer,
        'obd': OBDReading.objects.filter(vehicle=vehicle).first(),
        'system_checks': SystemCheck.objects.filter(vehicle=vehicle),
        'network_systems': NetworkSystem.objects.filter(vehicle=vehicle),
        'fluid_levels': FluidLevel.objects.filter(vehicle=vehicle),
        'live_parameters': LiveParameters.objects.filter(vehicle=vehicle),
        'performance_checks': PerformanceCheck.objects.filter(vehicle=vehicle),
        'paint_finishes': PaintFinish.objects.filter(vehicle=vehicle),
        'tyre_conditions': TyreCondition.objects.filter(vehicle=vehicle),
        'flush_gaps': FlushGap.objects.filter(vehicle=vehicle),
        'rubber_components': RubberComponent.objects.filter(vehicle=vehicle),
        'glass_components': GlassComponent.objects.filter(vehicle=vehicle),
        'interior_components': InteriorComponent.objects.filter(vehicle=vehicle),
        'documentations': Documentation.objects.filter(vehicle=vehicle),
    }

    return render(request, 'car/print.html', context)


def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    vehicle.delete()
    return redirect('admin_dashboard')


@login_required(login_url = 'login')
def vehicles_inspected_by_single_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    model_query = request.GET.get('model', '')
    date_query = request.GET.get('date', '')

    vehicles = Vehicle.objects.filter(inspected_by=user)

    if model_query:
        vehicles = vehicles.filter(model__icontains=model_query)

    if date_query:
        vehicles = vehicles.filter(inspection_date=date_query)

    vehicles = vehicles.order_by('-inspection_date')

    return render(request, 'car/inspected_by_user.html', {
        'inspector': user,
        'vehicles': vehicles,
        'model_query': model_query,
        'date_query': date_query,
        'page_title': 'My Vehicles',
    })

@login_required(login_url = 'login')
def vehicles_inspected(request):
    model_name_query = request.GET.get('model', '')
    inspection_date_query = request.GET.get('date', '')

    vehicles = Vehicle.objects.all()

    if model_name_query:
        vehicles = vehicles.filter(model__icontains=model_name_query)

    if inspection_date_query:
        vehicles = vehicles.filter(inspection_date=inspection_date_query)

    vehicles = vehicles.order_by('-inspection_date')

    return render(request, 'car/inspected_cars.html', {
        'vehicles': vehicles,
        'page_title': 'All Vehicles',
        'model_name_query': model_name_query,
        'inspection_date_query': inspection_date_query,
    })



# ========== User Management ==========

from django.db.models import Sum, ExpressionWrapper, DurationField, F
from django.utils.timezone import localdate

def format_duration(duration):
    if not duration:
        return "00:00:00"
    total_seconds = int(duration.total_seconds())  # truncate microseconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@login_required
def user_dashboard(request):
    today = localdate()
    search_query = request.GET.get('search', '')

    users_qs = CustomUser.objects.all()

    if search_query:
        users_qs = users_qs.filter(email__icontains=search_query)

    users = users_qs.annotate(
        vehicle_count=Count('inspected_vehicles', distinct=True),
        total_login_duration=Sum(
            ExpressionWrapper(
                F('sessions__logout_time') - F('sessions__login_time'),
                output_field=DurationField()
            ),
            distinct=True
        )
    )

    for user in users:
        # Format total login duration
        user.total_login_duration_str = format_duration(user.total_login_duration)

        # Get today's sessions
        today_sessions = user.sessions.filter(login_time__date=today)

        total_seconds_today = 0
        active_session_start = None

        for session in today_sessions:
            login_time = session.login_time
            logout_time = session.logout_time or now()

            if session.logout_time is None:
                active_session_start = login_time

            total_seconds_today += (logout_time - login_time).total_seconds()

        user.today_login_duration_str = format_duration(timedelta(seconds=int(total_seconds_today)))
        user.live_session_start = active_session_start

        # Count of vehicles inspected today
        today_vehicles_qs = user.inspected_vehicles.filter(inspection_date=today).distinct()
        user.today_vehicles = today_vehicles_qs
        user.today_vehicle_count = today_vehicles_qs.count()

    return render(request, 'user/user_dashboard.html', {
        'users': users,
        'users1': users_qs,
        'page_title': 'User Management',
        'search_query': search_query,
    })

def get_active_user_ids():
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = []
    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            user_ids.append(user_id)
    return user_ids


@login_required
def verify_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified_by_admin = True
    user.save()
    messages.success(request, f"User {user.username} has been verified.")
    return redirect('user_dashboard')


@login_required
def unverify_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified_by_admin = False
    user.save()
    messages.success(request, f"User {user.username} has been unverified.")
    return redirect('user_dashboard')


@login_required

def delete_user_view(request, user_id):
    user_obj = get_object_or_404(CustomUser, id=user_id)
    user_obj.delete()
    messages.success(request, 'User deleted successfully.')
    return redirect('user_dashboard')

def leave_calendar_view(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    leaves = user.leaves.all()
    return render(request, 'user/leave_calender.html', {'user': user, 'leaves': leaves, 'page_title': 'Leave Calendar'})

@login_required(login_url = 'login')
def leave_events_json(request, user_id):
    leaves = Leave.objects.filter(user__id=user_id)
    events = []

    for leave in leaves:
        if leave.status == 'approved':
            color = 'green'
        elif leave.status == 'pending':
            color = 'orange'
        else:
            color = 'red'

        events.append({
            'title': leave.status.title(),
            'start': leave.start_date.isoformat(),
            'end': (leave.end_date + timedelta(days=1)).isoformat(),  # FullCalendar is exclusive on end
            'color': color,
        })

    return JsonResponse(events, safe=False)

@login_required(login_url='login')
def view_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'user/view_profile.html', {
        'user_obj': user,
        'page_title': f"{user.get_full_name() or user.email}'s Profile"
    })

@login_required(login_url = 'login')
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'user/profile.html', {'form': form, 'user': user, 'page_title' : 'Profile'})  

def verify_bank_details(request):
    if request.method == 'POST':
        account_number = request.POST.get('account_number')
        ifsc_code = request.POST.get('ifsc_code')

        api_url = "https://api.example.com/bank/verify"
        headers = {
            'Authorization': f'Bearer {settings.BANK_VERIFICATION_API_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'account_number': account_number,
            'ifsc': ifsc_code,
        }

        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get('verified'):
                return JsonResponse({'success': True, 'message': 'Bank account verified successfully!'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid account details.'})
        else:
            return JsonResponse({'success': False, 'message': 'API error occurred.'})
        
@login_required(login_url = 'login')
def apply_leave_view(request):
    leaves = Leave.objects.filter(user=request.user).order_by('-created_at')
    today = date.today().isoformat()

    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()
            return redirect('apply_leave')  
    else:
        form = LeaveForm()

    return render(request, 'user/apply_leave.html', {'form': form, 'leaves':leaves, 'today':today, 'page_title':'Apply For a Leave'})

def approve_leave(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    leave.status = 'approved'
    leave.save()
    messages.success(request, f"Leave for {leave.user.email} approved.")
    return redirect('manage_leaves')

def reject_leave(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    leave.status = 'rejected'
    leave.save()
    messages.warning(request, f"Leave for {leave.user.email} rejected.")
    return redirect('manage_leaves')

def manage_leaves_view(request):
    leaves = Leave.objects.all().order_by('-created_at')
    return render(request, 'user/manage_leaves.html', {'leaves': leaves, 'page_title':'Manage Leaves'})


@login_required(login_url='login')
@user_passes_test(lambda u: u.is_superuser)
def login_logout_report(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    sessions = user.sessions.all().order_by('-login_time')
    
    total_duration = sessions.aggregate(
        total=Sum(ExpressionWrapper(
            F('logout_time') - F('login_time'),
            output_field=DurationField()
        ))
    )['total']

    user.total_duration = format_duration(total_duration)
    user.leave_count = user.leaves.count()

    return render(request, 'user/login_logout_report.html', {
        'user': user,
        'session_data': sessions,
        'page_title': f'{user.email} - Login/Logout Report',
    })


# ========== Engineer Management Views ==========

def engineer_view(request):
    search_query = request.GET.get('search', '')

    # Start with verified engineers only
    engineers = CustomUser.objects.filter(is_verified_by_admin=True)

    # Filter by email if search query is provided
    if search_query:
        engineers = engineers.filter(email__icontains=search_query)

    # Annotate with vehicle count
    engineers = engineers.annotate(vehicle_count=Count('inspected_vehicles'))

    return render(request, 'user/staff.html', {
        'engineers': engineers,
        'search_query': search_query,
        'page_title' : 'Engineer Management',
    })

from django.utils.timezone import localdate


# ========== Role & Permission Views ==========

@login_required
def roles_dashboard(request):
    role_form = RoleForm(request.POST or None)
    permission_form = RolePermissionForm(request.POST or None)

    if request.method == 'POST':
        if 'create_role' in request.POST and role_form.is_valid():
            role_form.save()
            return redirect('roles_dashboard')

        if 'assign_permissions' in request.POST and permission_form.is_valid():
            role = permission_form.cleaned_data['role']
            permissions = permission_form.cleaned_data['permissions']
            role.permissions.set(permissions)  # <-- Correct way now
            return redirect('roles_dashboard')

    roles = Roles.objects.all().prefetch_related('permissions')
    grouped_permissions = {
        role.id: [perm.name for perm in role.permissions.all()]
        for role in roles
    }
    user_roles = UserRole.objects.select_related('user', 'role')

    return render(request, 'roles/dashboard.html', {
        'role_form': role_form,
        'permission_form': permission_form,
        'roles': roles,
        'grouped_permissions': grouped_permissions,
        'user_roles': user_roles,
        'page_title': 'Roles Dashboard'

    })


@login_required
def manage_roles_permissions(request):
    roles = Roles.objects.all()
    permissions = Permissions.objects.all()
    role_form = RoleForm(request.POST or None)
    permission_form = PermissionForm(request.POST or None)

    if request.method == 'POST':
        if 'create_role' in request.POST and role_form.is_valid():
            role = role_form.save()
            messages.success(request, f"Role '{role.name}' created successfully.")
            return redirect('manage_roles_permissions')

        elif 'create_permission' in request.POST and permission_form.is_valid():
            permission = permission_form.save()
            messages.success(request, f"Permission '{permission.name}' created successfully.")
            return redirect('manage_roles_permissions')

        elif 'assign_permission_to_role' in request.POST:
            role_id = request.POST.get('role_id')
            permission_id = request.POST.get('permission_id')
            try:
                role = Roles.objects.get(id=role_id)
                permission = Permissions.objects.get(code=permission_id)
                assign_permission_to_role(role.name, permission.name)
                messages.success(request, f"Permission '{permission.name}' assigned to role '{role.name}'.")
            except ObjectDoesNotExist as e:
                messages.error(request, str(e))
            return redirect('manage_roles_permissions')

    return render(request, 'roles/roles_permission.html', {
        'roles': roles,
        'permissions': permissions,
        'role_form': role_form,
        'permission_form': permission_form,
    })


@login_required
def assign_permissions_to_role(request):
    form = RolePermissionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        role = form.cleaned_data['role']
        permissions = form.cleaned_data['permissions']
        role.permissions.set(permissions)
        return redirect('assign_permissions_to_role')

    roles = Roles.objects.all().prefetch_related('permissions')
    grouped_permissions = {
        role.id: [perm.name for perm in role.permissions.all()]
        for role in roles
    }

    return render(request, 'roles/assign_permissions.html', {
        'form': form,
        'grouped_permissions': grouped_permissions
    })


@login_required
def assign_roles_to_users(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    form = UserRoleAssignForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        role = form.cleaned_data['role']
        UserRole.objects.update_or_create(user=user, defaults={'role': role})
        return redirect('assign_roles_to_users', user_id=user.id)

    assignments = UserRole.objects.select_related('user', 'role')
    return render(request, 'roles/assign_roles.html', {
        'form': form,
        'assignments': assignments,
        'selected_user': user
    })

