import random
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser  # کلاس‌های پایه کاربر
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db import models  # ORM جنگو برای تعریف فیلدهای مدل
from django.utils.translation import gettext_lazy as _  # برای ترجمه

#------------------------------------ مدیر مدل کاربر سفارشی ------------------------------------#

# مدیر سفارشی برای مدل CustomUser
class CustomUserManager(BaseUserManager):
    """
    مدیر سفارشی کاربر که در آن ایمیل به جای نام کاربری، شناسه منحصر به فرد است.
    """
    # متد برای ایجاد یک کاربر عادی
    def create_user(self, email, password=None, **extra_fields):
        """
        یک کاربر را با ایمیل و رمز عبور داده شده ایجاد و ذخیره می‌کند.
        """
        # اگر ایمیل ارائه نشده باشد، خطا ایجاد می‌کند
        if not email:
            raise ValueError(_('The Email must be set'))
        
        # ایمیل را نرمال‌سازی می‌کند (مثلاً دامنه را به حروف کوچک تبدیل می‌کند)
        email = self.normalize_email(email)
        # یک نمونه کاربر با ایمیل و فیلدهای اضافی ایجاد می‌کند
        user = self.model(email=email, **extra_fields)
        # رمز عبور کاربر را تنظیم می‌کند (برای امنیت هش می‌شود)
        user.set_password(password)
        # نمونه کاربر را در پایگاه داده ذخیره می‌کند
        user.save(using=self._db)
        return user

    # متد برای ایجاد یک ابرکاربر (ادمین)
    def create_superuser(self, email, password=None, **extra_fields):
        """
        یک ابرکاربر را با ایمیل و رمز عبور داده شده ایجاد و ذخیره می‌کند.
        """
        # اطمینان حاصل می‌کند که ابرکاربران مجوزهای لازم را دارند
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # بررسی می‌کند که مقادیر is_staff و is_superuser درست باشند
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        # از متد create_user برای ایجاد ابرکاربر استفاده می‌کند
        return self.create_user(email, password, **extra_fields)

#------------------------------------ مدل کاربر سفارشی ------------------------------------#

# مدل کاربر سفارشی که ایمیل را جایگزین نام کاربری برای احراز هویت می‌کند
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # فیلد ایمیل، با محدودیت منحصر به فرد بودن
    email = models.EmailField(_('email address'), unique=True)

    # فیلدهای اطلاعات اضافی کاربر (اختیاری)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)

    # فیلدهای مورد نیاز برای وضعیت کاربر
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    # فیلد تاریخ پیوستن کاربر که به صورت خودکار پر می‌شود
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)

    # اتصال مدیر سفارشی به این مدل
    objects = CustomUserManager()

    # تنظیم فیلد ایمیل به عنوان شناسه منحصر به فرد (جایگزین username)
    USERNAME_FIELD = 'email'
    # فیلدهای مورد نیاز هنگام ایجاد کاربر؛ خالی است چون فقط ایمیل و رمز عبور لازم است
    REQUIRED_FIELDS = []

    # نمایش رشته‌ای کاربر (ایمیل کاربر)
    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # ایمیل را به حروف کوچک تبدیل می‌کند
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

# ------------------------------------ مدل پروفایل ------------------------------------#
class Profile(models.Model):
    
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # یک UUID منحصر به فرد برای هر پروفایل
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # کد دعوت ۱۴ رقمی که به صورت خودکار و منحصر به فرد تولید می‌شود
    invite_code = models.CharField(max_length=14, unique=True, editable=False)
    
    # ارجاع به کاربری که این کاربر را دعوت کرده است
    invited_by = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='invited_users')
    
    is_active = models.BooleanField(default=False)
    
    avatar = models.ImageField(blank=True, upload_to='profile_avatars/')
        
    wallet = models.PositiveIntegerField(default=0)
    
    config_limitation = models.PositiveBigIntegerField(default=3, help_text='The maximum number of configurations a user can create or have at a time.')

    def __str__(self):
        # نمایش رشته‌ای پروفایل بر اساس ایمیل کاربر
        return f'Profile for {self.user.email}'
    
    def save(self, *args, **kwargs):
        # اگر کاربر توسط شخص دیگری دعوت شده باشد
        if self.invited_by:
            # بررسی می‌کند که آیا کاربر دعوت‌کننده فعال است یا خیر
            if self.invited_by.is_active:
                self.is_active = True # پروفایل کاربر جدید را فعال می‌کند

        # اگر کاربر کد دعوت نداشته باشد، یک کد جدید برای او تولید می‌شود
        if not self.invite_code:
            self.invite_code = self.generate_unique_invite_code()

        super(Profile, self).save(*args, **kwargs)

    # متد برای تولید کد دعوت منحصر به فرد
    def generate_unique_invite_code(self):
        code = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        # تا زمانی که کد تکراری باشد، کد جدید تولید می‌کند
        while Profile.objects.filter(invite_code=code).exists():
            code = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        return code
