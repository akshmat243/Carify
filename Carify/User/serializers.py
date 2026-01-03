from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *
from django.utils.timezone import now, localdate
from datetime import timedelta
from CarPDI.models import Vehicle
from django.contrib.auth import get_user_model


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")
        return data

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_verified_by_admin', 'is_superuser']


class RegistrationSerializer(serializers.ModelSerializer):
    # Passwords sirf aayenge, wapas response mein nahi dikhenge (write_only)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        # Wahi fields jo tere RegistrationForm mein hongi
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, data):
        # Password Match Check
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # Confirm password ko hata do, database mein nahi chahiye
        validated_data.pop('confirm_password')
        
        # 'create_user' use karenge taaki password Hash (encrypt) ho jaye
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user



class UserManagementSerializer(serializers.ModelSerializer):
    # Calculated Fields
    vehicle_count = serializers.IntegerField(read_only=True)
    total_login_duration = serializers.SerializerMethodField()
    today_login_duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'emp_id', 'first_name', 'last_name', 'email', 
            'is_verified_by_admin', 'is_active', 
            'vehicle_count', 'total_login_duration', 'today_login_duration', 'status'
        ]

    # --- Helper: Format Duration (e.g. "02:30:00") ---
    def format_duration(self, duration):
        if not duration:
            return "00:00:00"
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_total_login_duration(self, obj):
        duration = getattr(obj, 'total_login_duration', None)
        return self.format_duration(duration)

    def get_today_login_duration(self, obj):
        # Today's sessions calculation
        today = localdate()
        today_sessions = obj.sessions.filter(login_time__date=today)
        total_seconds = 0
        for session in today_sessions:
            logout_time = session.logout_time or now()
            total_seconds += (logout_time - session.login_time).total_seconds()
        return self.format_duration(timedelta(seconds=total_seconds))

    def get_status(self, obj):
        return obj.status

class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = '__all__'


class LeaveCalendarSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = ['title', 'start', 'end', 'color'] 

    def get_title(self, obj):
        return obj.status.title()

    def get_start(self, obj):
        return obj.start_date.isoformat()

    def get_end(self, obj):
        return (obj.end_date + timedelta(days=1)).isoformat()

    def get_color(self, obj):
        colors = {
            'approved': 'green',
            'pending': 'orange',
            'rejected': 'red'
        }
        return colors.get(obj.status, 'gray') # Default gray


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 
            'date_of_birth', 'gender', 'address', 'profile_picture',
            'govt_id_number', 'govt_id_document',
            'pancard_number', 'pancard_document',
            'bank_account_number', 'ifsc_code', 'bank_name'] 
        
class BankVerificationSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=50, required=True)
    ifsc_code = serializers.CharField(max_length=20, required=True)

    def validate_ifsc_code(self, value):
        # Optional: Basic IFSC regex validation
        if len(value) != 11:
            raise serializers.ValidationError("IFSC code must be 11 characters long.")
        return value.upper()


class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = ['id', 'user', 'start_date', 'end_date', 'reason', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'created_at']


class UserSessionSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = ['id', 'login_time', 'logout_time', 'ip_address', 'device_info', 'duration']

    def get_duration(self, obj):
        """Calculates duration for individual session"""
        if obj.logout_time and obj.login_time:
            delta = obj.logout_time - obj.login_time
            # Format: HH:MM:SS
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        return "Active"
    


class VehicleSerializer(serializers.ModelSerializer):
    inspected_by_name = serializers.CharField(source='inspected_by.email', read_only=True)

    class Meta:
        model = Vehicle
        # --- SABSE ZAROORI LINE ---
        fields = '__all__' 
        # Iska matlab: Model ki saari fields (engine_cc, bhp, mileage etc.) accept karo
        # --------------------------
        
        read_only_fields = ['inspected_by', 'status', 'created_at', 'updated_at', 'inspection_date', 'is_completed']


User = get_user_model()

# 1. Permission Serializer
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissions
        fields = ['name', 'code'] # 'code' ya 'codename' jo tere model me ho

# 2. Role Serializer (With Nested Permissions)
class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True) # Read ke liye details

    class Meta:
        model = Roles
        fields = ['id', 'name', 'description', 'permissions']

# 3. Assign Permission to Role Serializer (Input Validation)
class AssignPermissionSerializer(serializers.Serializer):
    role_id = serializers.UUIDField()
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )

# 4. User Role Serializer (Dashboard List ke liye)
class UserRoleSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_email', 'role', 'role_name']

# 5. Assign Role to User Serializer (Input Validation)
class AssignUserRoleSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role_id = serializers.UUIDField()
