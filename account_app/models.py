from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone

#//////////////////////////////////
# UserManager
#//////////////////////////////////
class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        """
        Creates and saves a User with the given phone and password.
        """
        if not phone:
            raise ValueError("The Phone field must be set")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given phone and password.
        """
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(phone, password, **extra_fields)

#//////////////////////////////////
# User Model
#//////////////////////////////////
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="ایمیل",
        max_length=255,
        null=True,
        blank=True
    )
    fullname = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="نام کامل"
    )
    phone = models.CharField(
        max_length=12,
        unique=True,
        verbose_name="شماره تلفن",
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="شماره تلفن معتبر نیست")]
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        verbose_name="عکس پروفایل"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    is_admin = models.BooleanField(
        default=False,
        verbose_name="ادمین"
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="عضو کادر"
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="سوپر کاربر"
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربرها"

    def __str__(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return self.is_admin

    def get_orders(self):
        return self.orders.all()

#//////////////////////////////////
# Address Model
#//////////////////////////////////
class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name="کاربر"
    )
    first_name = models.CharField(
        max_length=50,
        verbose_name="نام"
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name="نام خانوادگی"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="ایمیل"
    )
    phone = models.CharField(
        max_length=12,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="شماره تلفن معتبر نیست")],
        verbose_name="شماره تلفن"
    )
    address = models.TextField(
        verbose_name="آدرس"
    )
    postal_code = models.TextField(
        verbose_name="کد پستی"
    )

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس‌ها"

#//////////////////////////////////
# Otp Model
#//////////////////////////////////
class Otp(models.Model):
    token = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="توکن"
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="شماره تلفن معتبر نیست")],
        verbose_name="شماره تلفن"
    )
    code = models.SmallIntegerField(
        verbose_name="کد"
    )
    expiration_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انقضا"
    )

    def __str__(self):
        return self.phone

    def is_valid(self):
        """
        Check if the OTP code is still valid.
        """
        now = timezone.now()
        return now <= self.expiration_date

    class Meta:
        verbose_name = "کد تایید"
        verbose_name_plural = "کدهای تایید"

#//////////////////////////////////
# ContactUs Model
#//////////////////////////////////
class ContactUs(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contactus',
        verbose_name="کاربر"
    )
    subject = models.CharField(
        max_length=50,
        verbose_name="موضوع"
    )
    message = models.TextField(
        verbose_name="پیام"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name="تاریخ ایجاد"
    )

    def __str__(self):
        return f'Contact from {self.user.fullname} - {self.subject[:20]}'

    class Meta:
        verbose_name = "تماس با ما"
        verbose_name_plural = "تماس‌ با ما"
        ordering = ['-created_at']
