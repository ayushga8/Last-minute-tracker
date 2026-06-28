import random
import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods

from .forms import RegisterForm, OTPRequestForm, OTPVerifyForm

User = get_user_model()
logger = logging.getLogger(__name__)

OTP_EXPIRY_SECONDS = 300  # 5 minutes


def _generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def _send_otp_email(email, otp):
    """Send OTP via SMTP email."""
    try:
        send_mail(
            subject='🔐 Your Life Saver Login Code',
            message=f'Your verification code is: {otp}\n\nThis code expires in 5 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=(
                f'<div style="font-family:sans-serif;max-width:400px;margin:0 auto;padding:20px;">'
                f'<h2 style="color:#7c3aed;">Last-Minute Life Saver</h2>'
                f'<p>Your verification code is:</p>'
                f'<h1 style="letter-spacing:8px;color:#7c3aed;font-size:36px;">{otp}</h1>'
                f'<p style="color:#888;">This code expires in 5 minutes.</p>'
                f'</div>'
            ),
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f'Failed to send OTP email to {email}: {e}')
        return False


@require_http_methods(["GET", "POST"])
def register_view(request):
    """Register a new user and send OTP for verification."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generate and store OTP
            otp = _generate_otp()
            cache.set(f'otp:{user.email}', otp, timeout=OTP_EXPIRY_SECONDS)
            # Send OTP email
            if _send_otp_email(user.email, otp):
                request.session['otp_email'] = user.email
                messages.success(request, 'Account created! Check your email for the verification code.')
                return redirect('otp_verify')
            else:
                messages.warning(request, f'Account created but email failed. Your OTP is: {otp}')
                request.session['otp_email'] = user.email
                return redirect('otp_verify')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login page — choose OTP or Google OAuth."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = OTPRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email. Please register first.')
                return render(request, 'accounts/login.html', {'form': form})

            # Generate and send OTP
            otp = _generate_otp()
            cache.set(f'otp:{email}', otp, timeout=OTP_EXPIRY_SECONDS)
            if _send_otp_email(email, otp):
                request.session['otp_email'] = email
                messages.success(request, 'Verification code sent to your email!')
                return redirect('otp_verify')
            else:
                messages.warning(request, f'Email failed. Your OTP is: {otp}')
                request.session['otp_email'] = email
                return redirect('otp_verify')
    else:
        form = OTPRequestForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def otp_verify_view(request):
    """Verify the 6-digit OTP and create session."""
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, 'Please request an OTP first.')
        return redirect('login')

    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            entered_otp = form.get_otp()
            stored_otp = cache.get(f'otp:{email}')

            if stored_otp is None:
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('login')

            if entered_otp == stored_otp:
                # OTP valid — log the user in
                try:
                    user = User.objects.get(email=email)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    cache.delete(f'otp:{email}')
                    del request.session['otp_email']
                    messages.success(request, f'Welcome back, {user.first_name or user.email}!')
                    return redirect('dashboard')
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')
                    return redirect('login')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerifyForm()

    return render(request, 'accounts/otp_verify.html', {
        'form': form,
        'email': email,
    })


def logout_view(request):
    """Log the user out."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def settings_view(request):
    """User settings page."""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.notification_email = request.POST.get('notification_email') == 'on'
        user.notification_in_app = request.POST.get('notification_in_app') == 'on'
        user.dark_mode = request.POST.get('dark_mode') == 'on'
        user.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('settings')

    return render(request, 'settings.html')
