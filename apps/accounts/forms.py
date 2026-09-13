import os
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm as BasePasswordChangeForm,
    PasswordResetForm as BasePasswordResetForm,
    SetPasswordForm as BaseSetPasswordForm,
)
from .models import Profile

User = get_user_model()



class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'placeholder': 'First Name',
        'class': 'form-input',
    }))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'placeholder': 'Last Name',
        'class': 'form-input',
    }))
    email = forms.EmailField(max_length=254, required=True, widget=forms.EmailInput(attrs={
        'placeholder': 'name@example.com',
        'class': 'form-input',
    }))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-input'})
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'placeholder': 'Enter a password (min. 8 characters)',
                'class': 'form-input',
                'autocomplete': 'new-password',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'placeholder': 'Confirm your password',
                'class': 'form-input',
                'autocomplete': 'new-password',
            })
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-input')


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={
        'placeholder': 'name@example.com',
        'class': 'form-input',
        'autofocus': True,
        'autocomplete': 'email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter your password',
        'class': 'form-input',
        'autocomplete': 'current-password',
    }))


class PasswordChangeForm(BasePasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'old_password' in self.fields:
            self.fields['old_password'].widget.attrs.update({
                'placeholder': 'Enter your current password',
                'class': 'form-input',
            })
        if 'new_password1' in self.fields:
            self.fields['new_password1'].widget.attrs.update({
                'placeholder': 'Enter new password (min. 8 characters)',
                'class': 'form-input',
            })
        if 'new_password2' in self.fields:
            self.fields['new_password2'].widget.attrs.update({
                'placeholder': 'Confirm your new password',
                'class': 'form-input',
            })


class PasswordResetForm(BasePasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': 'name@example.com',
                'autocomplete': 'email',
                'autofocus': True,
            })


class SetPasswordForm(BaseSetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'new_password1' in self.fields:
            self.fields['new_password1'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': 'Enter new password (min. 8 characters)',
                'autocomplete': 'new-password',
            })
        if 'new_password2' in self.fields:
            self.fields['new_password2'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': 'Confirm your new password',
                'autocomplete': 'new-password',
            })




class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'website', 'github', 'linkedin', 'twitter')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Tell readers about yourself...'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://yourwebsite.com'}),
            'github': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://github.com/username'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://linkedin.com/in/username'}),
            'twitter': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://x.com/username'}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'size'):
            # 1. Size limit: 3MB
            if avatar.size > 3 * 1024 * 1024:
                raise forms.ValidationError("Avatar image size cannot exceed 3MB.")
            
            # 2. Extension whitelist (prevent SVG XSS, executable uploads)
            valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError("Only JPG, JPEG, PNG, or WebP images are allowed.")
            
            # 3. Content verification via PIL
            try:
                from PIL import Image
                img = Image.open(avatar)
                img.verify()
                # Reset file pointer after verify()
                if hasattr(avatar, 'seek'):
                    avatar.seek(0)
            except Exception:
                raise forms.ValidationError("Uploaded file is corrupt or not a valid image.")

        return avatar


class EmailChangeRequestForm(forms.Form):
    """Form to initiate email change with password verification and new email uniqueness check."""

    new_email = forms.EmailField(
        label='New Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'new.email@example.com',
            'class': 'form-input',
            'autocomplete': 'email',
        })
    )
    current_password = forms.CharField(
        label='Current Account Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your current password to confirm',
            'class': 'form-input',
            'autocomplete': 'current-password',
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if not self.user.check_password(password):
            raise forms.ValidationError("Your current password was entered incorrectly.")
        return password

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email', '').strip().lower()
        if new_email == self.user.email.lower():
            raise forms.ValidationError("The new email must be different from your current email address.")
        if User.objects.filter(email__iexact=new_email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return new_email


class EmailChangeVerifyForm(forms.Form):
    """Form to verify the 6-digit OTP sent to the new email address."""

    otp_code = forms.CharField(
        label='Verification Code',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '••••••',
            'class': 'form-input text-center',
            'maxlength': '6',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code',
            'style': 'letter-spacing: 0.45em; font-family: monospace; font-size: 1.5rem; text-align: center; font-weight: 700;',
        })
    )

    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit numeric code.")
        return code

