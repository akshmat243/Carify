from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils.timezone import now
from .models import UserSession

@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    UserSession.objects.create(user=user, login_time=now())

@receiver(user_logged_out)
def handle_user_logged_out(sender, request, user, **kwargs):
    try:
        last_session = UserSession.objects.filter(user=user, logout_time__isnull=True).latest('login_time')
        last_session.logout_time = now()
        last_session.save()
    except UserSession.DoesNotExist:
        pass  # No open session found
