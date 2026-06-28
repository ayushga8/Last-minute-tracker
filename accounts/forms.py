from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):
    """Registration form — email-based with password."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
        }),
        min_length=8,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        }),
        label='Confirm Password',
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'you@example.com',
                'autocomplete': 'email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Last name',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        pw2 = cleaned_data.get('password_confirm')
        if pw and pw2 and pw != pw2:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email.split('@')[0]
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class OTPRequestForm(forms.Form):
    """Form to request an OTP for login."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        })
    )


class OTPVerifyForm(forms.Form):
    """Form to verify 6-digit OTP."""
    digit_1 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-digit', 'maxlength': '1', 'autofocus': True,
    }))
    digit_2 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-digit', 'maxlength': '1',
    }))
    digit_3 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-digit', 'maxlength': '1',
    }))
    digit_4 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-digit', 'maxlength': '1',
    }))
    digit_5 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-digit', 'maxlength': '1',
    }))
    digit_6 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={
        'class': 'otp-digit', 'maxlength': '1',
    }))

    def get_otp(self):
        """Concatenate all digit fields into a single OTP string."""
        return ''.join([
            self.cleaned_data.get(f'digit_{i}', '') for i in range(1, 7)
        ])
