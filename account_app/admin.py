# در فایل admin.py مربوط به account_app

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.utils.html import format_html  # برای ایجاد لینک HTML

from account_app.models import User, Otp, Address
from product_app.models import Order, OrderItem  # مدل‌های سفارش و آیتم سفارش

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    password1 = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تایید رمز عبور", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["phone"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field."""

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"

class OrderInline(admin.TabularInline):
    model = Order
    fields = ['id', 'total_price', 'status', 'created_at', 'view_order_link']
    readonly_fields = ['total_price', 'status', 'created_at', 'view_order_link']
    ordering = ['-created_at']
    extra = 0

    def view_order_link(self, obj):
        return format_html('<a href="/admin/product_app/order/{}/change/">View Order</a>', obj.id)
    view_order_link.short_description = 'مشاهده سفارش'

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["phone", "email", "is_admin", "profile_picture"]
    list_filter = ["is_admin"]
    fieldsets = [
        (None, {"fields": ["phone", "password"]}),
        ("اطلاعات شخصی", {"fields": ["fullname", "profile_picture"]}),
        ("ایمیل", {"fields": ["email"]}),
        ("دسترسی", {"fields": ["is_admin"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["phone", "fullname", "email", "profile_picture", "password1", "password2"],
            },
        ),
    ]
    search_fields = ["phone"]
    ordering = ["phone"]
    filter_horizontal = []
    inlines = [OrderInline]  # اضافه کردن لیست داخلی سفارش‌ها

admin.site.register(Address)
admin.site.register(User, UserAdmin)
admin.site.register(Otp)

