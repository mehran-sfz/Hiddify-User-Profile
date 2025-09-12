# your_app/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from accounts.models import Profile, CustomUser


CustomUser = get_user_model()

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل خود را وارد کنید'})
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'})
    )



class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    invite_code = forms.CharField(
        label="Invite Code (Optional)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Invite Code'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        }

    def clean_email(self):
        # No changes here
        email = self.cleaned_data.get('email').lower()
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_confirm_password(self):
        # No changes here
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError("The passwords do not match.")
        return confirm_password

    @transaction.atomic
    def save(self, commit=True):
        # 1. Create the user
        # This line triggers your post_save signal, which creates the empty profile.
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )

        # 2. Process the invite code
        invite_code = self.cleaned_data.get('invite_code')
        if invite_code:
            try:
                inviter_profile = Profile.objects.get(invite_code=invite_code)
                
                # 3. Update the profile that the signal created
                # Since the signal has run, the profile is accessible via user.profile.
                user.profile.invited_by = inviter_profile.user
                user.profile.save() # Save the changes to the profile

            except Profile.DoesNotExist:
                self.add_error('invite_code', 'The provided invite code is not valid.')
                # This error rolls back the entire transaction (including user creation).
                raise ValidationError("Invalid invite code.")

        return user
    
    
    
    
    