from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Roles, Permissions, UserRole, Leave
from django.contrib.auth.forms import PasswordResetForm

# Reset Password
class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your registered email',
            'autocomplete': 'email'
        })

# CustomUser forms
class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "password1", "password2" )

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email",)

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class RoleForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = ['name', 'permissions', 'status']
        widgets = {
            'permissions': forms.CheckboxSelectMultiple
        }

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permissions
        fields = ['name']



class UserRoleAssignForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Roles.objects.all(), label="Select Role")

class RolePermissionForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Roles.objects.all(), label="Select Role")
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permissions.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Assign Permissions"
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender', 'address',
            'profile_picture',
            'govt_id_number', 'govt_id_document',
            'pancard_number', 'pancard_document',
            'bank_account_number', 'ifsc_code', 'bank_name',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }