from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
import uuid 
from django.utils import timezone
from django.conf import settings

class Permissions(models.Model):
    code = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not Permissions.objects.exists():
            self.code = 100
        else:
            self.code = Permissions.objects.last().code + 1
        super(Permissions, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

class Roles(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permissions, related_name="roles")
    status=models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class CustomUser(AbstractUser):
    username=None
    emp_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    email=models.EmailField(_("email address"), unique=True)
    is_verified_by_admin = models.BooleanField(default=False)
    
     # ✅ Personal Info
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(blank=True)

    # ✅ Profile Photo
    profile_picture = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    # ✅ Govt ID
    govt_id_number = models.CharField(max_length=20, blank=True)
    govt_id_document = models.FileField(upload_to='documents/govt_id/', blank=True, null=True)
    is_govt_id_verified = models.BooleanField(default=False)

    # ✅ PAN Card
    pancard_number = models.CharField(max_length=10, blank=True)
    pancard_document = models.FileField(upload_to='documents/pancard/', blank=True, null=True)
    is_pancard_verified = models.BooleanField(default=False)

    # ✅ Bank Info
    bank_account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    is_bank_verified = models.BooleanField(default=False)

    USERNAME_FIELD ="email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email   
   
    def save(self, *args, **kwargs):
        if not self.pk and not self.emp_id:
            # Only generate emp_id for new user creation
            last_user = CustomUser.objects.exclude(emp_id__isnull=True).order_by('-id').first()
            if last_user and last_user.emp_id:
                try:
                    last_id_num = int(last_user.emp_id.replace("#CRFY", ""))
                except ValueError:
                    last_id_num = 0
                next_id = last_id_num + 1
            else:
                next_id = 1
            self.emp_id = f"#CRFY{str(next_id).zfill(6)}"
        
        super().save(*args, **kwargs)


    
    @property
    def status(self):
        today = timezone.now().date()

        latest_session = self.sessions.order_by('-login_time').first()

        # No session ever → non-active
        if not latest_session:
            return 'non-active'

        # If session not from today → non-active
        if latest_session.login_time.date() != today:
            return 'non-active'

        # If session ended quickly → non-active
        if latest_session.logout_time:
            duration = latest_session.logout_time - latest_session.login_time
            if duration.total_seconds() < 60:
                return 'non-active'

        # Check if user is currently filling a vehicle form and hasn't logged out
        latest_vehicle = self.inspected_vehicles.filter(
            is_completed=False, inspection_date=today
        ).order_by('-inspection_date').first()

        if latest_vehicle and latest_session.logout_time is None:
            return 'engaged'

        return 'active'


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)

    @property
    def session_duration(self):
        if self.logout_time:
            return self.logout_time - self.login_time
        return timezone.now() - self.login_time
    
    def __str__(self):
        return f"{self.user.email} | Login: {self.login_time} | Logout: {self.logout_time or 'Active'}"

class Leave(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)  # ✅ Correct usage

    def __str__(self):
        return f"{self.user.email} | {self.start_date} to {self.end_date} | {self.status}"
      
class UserRole(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    # description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.id}"
    

# class Vehicle(models.Model):
#     STATUS_CHOICES = (
#         ('pending', 'Pending'),
#         ('passed', 'Passed'),
#         ('failed', 'Failed'),
#     )

#     # Fields based on your usage
#     model = models.CharField(max_length=100, help_text="Vehicle Model Name (e.g., Toyota Fortuner)")
#     inspection_date = models.DateField()
#     inspected_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='inspected_vehicles')
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
#     # Auto timestamp (Industry standard for tracking)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.model} - {self.status}"