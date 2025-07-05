import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models import Profile
from client_actions.models import Config, Order, Payment
from plans.models import Plan
from task_manager.models import HiddifyUser

User = get_user_model()

# --------------------- Accouts Serializer ----------------

class RegisterSerializer(serializers.ModelSerializer):
    # Validate the phone number to ensure uniqueness
    phone_number = serializers.CharField(
        required=True, 
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    invite_code = serializers.CharField(required=False, allow_blank=True)

    password_1 = serializers.CharField(required=True, write_only=True)
    password_2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ('phone_number', 'invite_code', 'password_1', 'password_2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'invite_code': {'required': False},
        }
        
    # Method to validate the phone number format
    def validate(self, attrs):
        
        # Check if the two passwords match
        if attrs['password_1'] != attrs['password_2']:
            raise serializers.ValidationError("Passwords do not match")
        
        password = attrs['password_1']
        
        # Check if the password is at least 8 characters long
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        # Validate the password using Django's built-in validators (includes common password checks)
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        # Validate the phone number format
        if not re.match(r'^09\d{9}$', attrs['phone_number']):
            raise serializers.ValidationError(
                "Phone number must be in the format: '09*********' (starting with '09' followed by 9 digits)."
            )
            
        
        # Check the invite code if provided
        invite_code = attrs.get('invite_code', None)
        if invite_code:
            # Check if the invite code exists in another user's profile
            try:
                invited_by_user = Profile.objects.get(invite_code=invite_code).user
                attrs['invited_by_user'] = invited_by_user  # Add invited_by_user to the validated data
                
            except Profile.DoesNotExist:
                raise serializers.ValidationError("Invalid invite code.")
        
        return super(RegisterSerializer, self).validate(attrs)
    
    
    # Method to create a new user

    def create(self, validated_data):
        # Remove the password_2 field since it's just for confirmation
        validated_data.pop('password_2')

        # Create the user with the phone number and password
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            password=validated_data['password_1'],  # Use password_1 as the password
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        
        # Create a Profile for the newly created user
        profile = Profile.objects.create(user=user)

        # Set the invited_by field if it exists
        invited_by_user = validated_data.get('invited_by_user', None)
        if invited_by_user:
            profile.invited_by = invited_by_user

        # Save the profile
        profile.save()

        # Return the user instead of the profile
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Profile
        fields = ('user', 'invite_code', 'avatar',  'wallet')
        read_only_fields = ('user', 'invite_code', 'avatar', 'wallet')
        
        
# --------------------- Plan Serializer ----------------

class PlanSerializer(serializers.ModelSerializer):
        
        class Meta:
            model = Plan
            fields = ('pk', 'price', 'duration', 'traffic')
            
            extra_kwargs = {
                'pk': {'read_only': True},
                'price': {'read_only': True},
                'duration': {'read_only': True},
                'traffic': {'read_only': True},
            }
        
        
# --------------------- Client VPN API Serializer ----------------        

class ConfigSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()
    
    uuid = serializers.CharField(required=True,
                                 validators=[UniqueValidator(queryset=Config.objects.all())])
    class Meta:
        model = Config
        fields = ('pk', 'user', 'uuid')
        
        extra_kwargs = {
            'pk': {'read_only': True},
            'user': {'read_only': True},             
        }
        
        
    # the uuid sould have exist in the HiddenUser model
    def validate_uuid(self, value):
        if HiddifyUser.objects.filter(uuid=value).exists():
            return value
        else:
            raise serializers.ValidationError("This uuid is not valid")

class OrderSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()
    config = serializers.StringRelatedField()
    plan = serializers.StringRelatedField()
    
    config = serializers.CharField(required=True)
    plan = serializers.CharField(required=True)
        
    class Meta:
        model = Order
        fields = ( 'pk', 'status', 'user', 'config', 'plan')
        
        
        extra_kwargs = {
            'pk': {'read_only': True},
            'status': {'read_only': True},
            'user': {'read_only': True},
        }

class PaymentSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField()
    order = serializers.StringRelatedField()
    
    order = serializers.CharField(required=True)
    
    screenshot = serializers.ImageField(required=True)
        
    class Meta:
        model = Payment
        fields = ('pk', 'user', 'order', 'screenshot', 'validated')
        
        extra_kwargs = {
            'pk': {'read_only': True},
            'user': {'read_only': True},
            'validated': {'read_only': True},
        }
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        