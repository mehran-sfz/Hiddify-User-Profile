import random
import uuid

from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser,  # Base user classes
                                        BaseUserManager, PermissionsMixin)
from django.core.validators import \
    RegexValidator  # Import for validating phone numbers
from django.db import models  # Django's ORM for defining model fields

#------------------------------------ Custom User Model ------------------------------------#

# Custom manager for the CustomUser model
class CustomUserManager(BaseUserManager):
    # Method to create a regular user
    def create_user(self, phone_number, password=None, **extra_fields):
        # Raise an error if no phone number is provided
        if not phone_number:
            raise ValueError('The Phone number must be set')

        # Create a user instance with the provided phone number and other fields
        user = self.model(phone_number=phone_number, **extra_fields)
        # Set the user's password (will hash it for security)
        user.set_password(password)
        # Save the user instance to the database
        user.save(using=self._db)
        return user

    # Method to create a superuser (admin)
    def create_superuser(self, phone_number, password=None, **extra_fields):
        # Ensure that superusers have the required permissions
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # Use the create_user method to create a superuser
        return self.create_user(phone_number, password, **extra_fields)

# Custom user model replacing email with phone number for authentication
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Validator for the phone number to ensure it starts with '09' and is followed by 9 digits
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',  # Regular expression to match '09*********' format
        message="Phone number must be in the format: '09*********' (starting with '09' followed by 9 digits)."
    )
    
    # Phone number field, with unique constraint and validation
    phone_number = models.CharField(validators=[phone_regex], max_length=11, unique=True)

    # Additional user information fields (optional)
    first_name = models.CharField(max_length=30, blank=True)  # First name field (optional)
    last_name = models.CharField(max_length=30, blank=True)   # Last name field (optional)

    # Required fields for user status
    is_active = models.BooleanField(default=True)  # Determines if the user account is active
    is_staff = models.BooleanField(default=False)  # Determines if the user can access the admin panel

    # Auto-populated field for tracking the account creation time
    date_joined = models.DateTimeField(auto_now_add=True)  # Timestamp of when the user joined

    # Linking the custom manager to this model
    objects = CustomUserManager()

    # Set the phone number field as the unique identifier (replacing email)
    USERNAME_FIELD = 'phone_number'
    # Fields required when creating a superuser; empty as only phone and password are required
    REQUIRED_FIELDS = []

    # String representation of the user (usually their phone number)
    def __str__(self):
        return self.phone_number

    
# ------------------------------------ Profile Model ------------------------------------#
class Profile(models.Model):
    
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # A unique UUID for each profile
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # random 14 digit number to be used as invite code automatically generated
    invite_code = models.CharField(max_length=14, unique=True, editable=False)
    
    # Reference to the user who invited this user
    invited_by = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='invited_users')
    
    is_active = models.BooleanField(default=False)
    
    avatar = models.ImageField(blank=True, upload_to='profile_avatars/')
        
    wallet = models.PositiveIntegerField(default=0)
    
    config_limitation = models.PositiveBigIntegerField(default=3, help_text='The maximum number of configurations a user can create or have at a time.')

    def __str__(self):
        return f'{self.user} - {self.user.phone_number}'
    
    def save(self, *args, **kwargs):
        
        
        if self.invited_by:
            if self.invited_by.is_active: # Check if the inviter's profile is active
                self.is_active = True # Set the new user's profile as active

        if not self.invite_code: # If the user does not have an invite code
            self.invite_code = self.generate_unique_invite_code()
  
        super(Profile, self).save(*args, **kwargs)

    # Method to generate a unique invite code
    def generate_unique_invite_code(self):
        
        code = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        while Profile.objects.filter(invite_code=code).exists():
            code = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        return code
