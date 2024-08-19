from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from .models import User, ContactUs
from django.contrib.auth.forms import PasswordChangeForm


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'ایمیل یا شماره تلفن خود را وارد کنید',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'رمز عبور خود را وارد کنید',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )


class UserCreationForm(forms.ModelForm):
    fullname = forms.CharField(
        max_length=100,
        help_text='نام کامل خود را وارد کنید.',
        widget=forms.TextInput(attrs={
            'placeholder': 'نام کامل',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )
    phone = forms.CharField(
        max_length=15,
        help_text='شماره تلفن خود را وارد کنید.',
        widget=forms.TextInput(attrs={
            'placeholder': 'شماره تلفن',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )
    email = forms.EmailField(
        required=False,
        help_text='ایمیل خود را وارد کنید (اختیاری).',
        widget=forms.EmailInput(attrs={
            'placeholder': 'ایمیل (اختیاری)',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )
    password1 = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'رمز عبور خود را وارد کنید',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )
    password2 = forms.CharField(
        label="تایید رمز عبور",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'تایید رمز عبور خود را وارد کنید',
            'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
        })
    )

    class Meta:
        model = User
        fields = ["fullname", "phone", "email", "profile_picture"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("رمزهای عبور مطابقت ندارند")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={
                'placeholder': 'موضوع پیام را وارد کنید',
                'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'متن پیام را وارد کنید',
                'class': 'block w-full p-2 border border-blue-500 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white placeholder-gray-400',
                'rows': 5,
            }),
        }


class PasswordChangeCustomForm(PasswordChangeForm):
    old_password = forms.CharField(label='رمز عبور قبلی', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label='رمز عبور جدید', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label='تکرار رمز عبور جدید', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(
        validators=[EmailValidator()],
        error_messages={
            'invalid': 'ایمیل وارد شده معتبر نمی‌باشد.',
            'unique': 'این ایمیل قبلاً ثبت شده است.'
        }
    )

    class Meta:
        model = User
        fields = ['fullname', 'phone', 'email']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.exclude(pk=self.instance.pk).filter(phone=phone).exists():
            raise ValidationError('این شماره تلفن قبلاً ثبت شده است.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email