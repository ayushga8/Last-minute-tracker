from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Auto-create/connect accounts for Google OAuth without showing signup form."""

    def populate_user(self, request, sociallogin, data):
        """Auto-populate user fields from Google profile data."""
        user = super().populate_user(request, sociallogin, data)
        # Generate username from email (part before @)
        if not user.username:
            email = data.get('email', '')
            base_username = email.split('@')[0] if email else 'user'
            # Ensure uniqueness
            from accounts.models import User
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1
            user.username = username
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """Always allow auto signup for social accounts."""
        return True

    def pre_social_login(self, request, sociallogin):
        """
        If a user with this email already exists (registered via OTP),
        auto-connect the Google account to that existing user.
        """
        if sociallogin.is_existing:
            return

        email = None
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email

        if not email:
            return

        from accounts.models import User
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            raise ImmediateHttpResponse(redirect('/dashboard/'))
        except User.DoesNotExist:
            pass
