import datetime
import os
import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from home_app.models import FAQ
from product_app.forms import AddressForm
from product_app.models import Order, User
from .forms import CustomLoginForm, UserCreationForm, ContactForm, VerifyCodeForm, PhoneNumberForm, PasswordResetForm, \
    VerifyCode_signupForm
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from .forms import ProfileEditForm, PasswordChangeCustomForm
from .models import Address, ContactUs, Otp
from .sms import verification
from .utils import generate_otp_code, generate_unique_token


# Create your views here.

class LoginView(FormView):
    template_name = 'account_app/login.html'
    form_class = CustomLoginForm
    success_url = reverse_lazy('home_app:home')  # تغییر به صفحه‌ای که پس از ورود موفقیت‌آمیز هدایت می‌شود

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'شما قبلاً وارد سیستم شده‌اید.')
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        else:
            form.add_error(None, 'نام کاربری یا رمز عبور نادرست است.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notification_type = self.request.GET.get('notification')
        if notification_type == 'not_login':
            show_notification = True
            notification_message = 'شما هنوز ثبت نام نکرده اید'
            notification_status = 'error'
        else:
            show_notification = False
            notification_message = ''
            notification_status = 'none'

        context.update({
            'show_notification': show_notification,
            'notification_message': notification_message,
            'notification_status': notification_status,
        })
        return context





class SignupView(FormView):
    template_name = "account_app/signup.html"
    form_class = UserCreationForm
    success_url = reverse_lazy('account_app:verify_code_signup')  # صفحه‌ای که کاربر باید کد تایید را وارد کند

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'شما قبلاً وارد سیستم شده‌اید.')
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        phone = form.cleaned_data.get('phone')
        email = form.cleaned_data.get('email')

        if User.objects.filter(phone=phone).exists():
            form.add_error('phone', 'این شماره تلفن قبلاً ثبت شده است.')
            return self.form_invalid(form)

        if email and User.objects.filter(email=email).exists():
            form.add_error('email', 'این ایمیل قبلاً ثبت شده است.')
            return self.form_invalid(form)

        # تولید کد تأیید و توکن
        code = generate_otp_code()
        token = generate_unique_token()  # تولید توکن یکتا
        expiration_date = timezone.now() + datetime.timedelta(minutes=10)  # تنظیم تاریخ انقضا

        # ذخیره اطلاعات OTP
        Otp.objects.update_or_create(
            phone=phone,
            defaults={
                'code': code,
                'expiration_date': expiration_date,
                'token': token
            }
        )

        verification(phone, code)  # تابعی برای ارسال پیامک
        # print(code)

        # ذخیره شماره تلفن و اطلاعات فرم در session برای استفاده در مرحله تایید
        self.request.session['phone'] = phone
        self.request.session['signup_form_data'] = form.cleaned_data  # ذخیره اطلاعات فرم برای استفاده در مرحله تایید
        return redirect(self.success_url)

class VerifyCodeSignupView(FormView):
    template_name = "account_app/verify_code_signup.html"
    form_class = VerifyCode_signupForm
    success_url = reverse_lazy('home_app:home')  # یا هر URL دیگری که بعد از تایید می‌خواهید

    def form_valid(self, form):
        phone = self.request.session.get('phone')
        code = form.cleaned_data.get('code')


        # چاپ برای بررسی داده‌ها
        print(f"Phone: {phone}, Code: {code}")

        try:
            otp = Otp.objects.get(phone=phone, code=code)
            if otp.expiration_date < timezone.now():
                form.add_error(None, 'کد تایید منقضی شده است.')
                return self.form_invalid(form)

            # دریافت اطلاعات فرم ثبت نام از session
            form_data = self.request.session.get('signup_form_data')
            if form_data:
                # ایجاد کاربر جدید
                user = User(
                    phone=form_data.get('phone'),
                    fullname=form_data.get('fullname'),
                    email=form_data.get('email')
                )
                user.set_password(form_data.get('password1'))
                user.is_active = True
                user.save()
                login(self.request, user)

            # پاک‌سازی اطلاعات OTP
            otp.delete()
            self.request.session.pop('phone', None)
            self.request.session.pop('signup_form_data', None)

            messages.success(self.request, 'ثبت نام با موفقیت انجام شد!')
            return super().form_valid(form)
        except Otp.DoesNotExist:
            form.add_error(None, 'کد تایید نامعتبر است.')
            return self.form_invalid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            print("Form errors:", form.errors)  # برای دیباگ کردن خطاهای فرم
            return self.form_invalid(form)


class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('home_app:home')


class ProfileView(LoginRequiredMixin,TemplateView):
    template_name = "account_app/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        order = Order.objects.filter(user=user).order_by('-id')
        notification_type = self.request.GET.get('notification')
        if notification_type == 'confirmOrder':
            show_notification = True
            notification_message = 'پرداخت با موفقیت انجام شد!'
        else:
            show_notification = False
            notification_message = ''
        context.update({
            'user': user,
            'orders': order,
            'show_notification': show_notification,
            'notification_message': notification_message
        })

        return context

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # اگر کاربر وارد نشده است، او را به صفحه ثبت‌نام هدایت کن
            return redirect('account_app:login')  # فرض کنید نام URL صفحه ثبت‌نام 'signup' است
        return super().get(request, *args, **kwargs)

# /////////////////////////////////////////////

class ProfileEditView(UpdateView):
    model = User
    form_class = ProfileEditForm
    template_name = 'account_app/edit_profile.html'
    success_url = reverse_lazy('account_app:profile_edit')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'پروفایل با موفقیت به‌روز شد.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'برخی از فیلدها اشتباه است.')
        return self.render_to_response(self.get_context_data(form=form))

class PasswordChangeViewCustom(PasswordChangeView):
    form_class = PasswordChangeCustomForm
    template_name = 'account_app/edit_profile.html'
    success_url = reverse_lazy('account_app:profile_edit')

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'رمز عبور با موفقیت تغییر کرد.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'خطایی در تغییر رمز عبور وجود دارد.')
        return self.render_to_response(self.get_context_data(form=form))

class EditProfileView(TemplateView):
    template_name = 'account_app/edit_profile.html'
    success_url = reverse_lazy('account_app:edit_profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_form'] = ProfileEditForm(instance=self.request.user)
        context['password_form'] = PasswordChangeCustomForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        profile_form = ProfileEditForm(request.POST, instance=request.user)
        password_form = PasswordChangeCustomForm(user=request.user, data=request.POST)
        print('change')
        if profile_form.is_valid() and password_form.is_valid():
            print('pass user')
            profile_form.save()
            user = password_form.save()
            update_session_auth_hash(request, user)  # مهم برای عدم خروج کاربر پس از تغییر رمز
            return redirect('account_app:profile')

        elif profile_form.is_valid():
            print('user')
            profile_form.save()
            return redirect('account_app:profile')
        elif password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # مهم برای عدم خروج کاربر پس از تغییر رمز
            return redirect('account_app:profile')

        return self.render_to_response(self.get_context_data(profile_form=profile_form, password_form=password_form))

# ///////////////////////////////////////////

@method_decorator(login_required, name='dispatch')
class AddAddressView(CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'account_app/add_address.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):

        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        print(next_url)
        if next_url:
            return next_url
        return reverse_lazy('account_app:profile')


class EditAddressView(UpdateView):
    model = Address
    form_class = AddressForm
    template_name = 'account_app/edit_address.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('account_app:profile')


class DeleteAddressView(LoginRequiredMixin, DeleteView):
    model = Address
    template_name = 'account_app/delete_address.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('account_app:profile')

    def get_object(self, queryset=None):
        # فیلتر کردن بر اساس کاربر جاری
        obj = get_object_or_404(Address, pk=self.kwargs['pk'], user=self.request.user)
        return obj
@login_required
def upload_profile_picture(request):
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']

            # حذف تصویر قبلی اگر وجود دارد
            if request.user.profile_picture:
                delete_profile_picture(request)

            # ذخیره تصویر جدید
            request.user.profile_picture = profile_picture
            request.user.save()

            return redirect('account_app:profile')
    return redirect('account_app:profile')


@login_required
def delete_profile_picture(request):
    if request.method == 'POST':
        user = request.user
        if user.profile_picture:
            filepath = user.profile_picture.path
            if os.path.exists(filepath):
                os.remove(filepath)
            user.profile_picture = None
            user.save()

        return redirect('account_app:profile')


# /////////////////////////////////////////////////////////////





class ContactUsView(LoginRequiredMixin, CreateView):
    model = ContactUs
    form_class = ContactForm
    template_name = 'account_app/contact_form.html'
    success_url = reverse_lazy('home_app:home')  # مسیر هدایت پس از ارسال موفق

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        faqs = FAQ.objects.all()
        context.update({
            "faqs": faqs,
        })

        return context

# ////////////////////////////////////////////////////
class SendCodeView(View):
    def get(self, request):
        form = PhoneNumberForm()
        return render(request, 'account_app/send_code.html', {'form': form})

    def post(self, request):
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            try:
                user = User.objects.get(phone=phone)  # به جای profile__phone از phone استفاده کنید
                code = random.randint(100000, 999999)
                expiration_date = timezone.now() + datetime.timedelta(minutes=10)
                Otp.objects.update_or_create(phone=phone, defaults={'code': code, 'expiration_date': expiration_date})
                verification(phone, code)  # ارسال پیامک کد تایید به کاربر
                messages.success(request, 'کد تایید برای شما ارسال شد.')
                return redirect('account_app:verify_code', phone=phone)
            except User.DoesNotExist:
                messages.error(request, 'کاربری با این شماره تلفن وجود ندارد.')
        return render(request, 'account_app/send_code.html', {'form': form})


class VerifyCodeView(View):
    def get(self, request, phone):
        form = VerifyCodeForm()
        return render(request, 'account_app/verify_code.html', {'form': form, 'phone': phone})

    def post(self, request, phone):
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                otp = Otp.objects.get(phone=phone, code=code)
                if otp.is_valid():  # فرض می‌کنیم که شما متدی برای بررسی اعتبار کد دارید
                    request.session['verified_phone'] = phone
                    return redirect('account_app:reset_password', phone=phone)
                else:
                    messages.error(request, 'کد تایید منقضی شده است.')
            except Otp.DoesNotExist:
                messages.error(request, 'کد تایید نادرست است.')
        return render(request, 'account_app/verify_code.html', {'form': form, 'phone': phone})


class ResetPasswordView(View):
    def get(self, request, phone):
        if 'verified_phone' not in request.session or request.session['verified_phone'] != phone:
            messages.error(request, 'ابتدا باید کد تایید را وارد کنید.')
            return redirect('account_app:verify_code', phone=phone)

        form = PasswordResetForm()
        return render(request, 'account_app/reset_password.html', {'form': form, 'phone': phone})

    def post(self, request, phone):
        if 'verified_phone' not in request.session or request.session['verified_phone'] != phone:
            messages.error(request, 'ابتدا باید کد تایید را وارد کنید.')
            return redirect('account_app:verify_code', phone=phone)

        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(phone=phone)
                user.set_password(password)
                user.save()
                messages.success(request, 'رمز عبور شما با موفقیت تغییر یافت.')
                del request.session['verified_phone']
                return redirect('account_app:login')
            except User.DoesNotExist:
                messages.error(request, 'کاربری با این شماره تلفن وجود ندارد.')
        return render(request, 'account_app/reset_password.html', {'form': form, 'phone': phone})


def verify_code(request):
    if request.method == 'POST':
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            phone = request.session.get('phone')

            try:
                otp = Otp.objects.get(phone=phone)
                if otp.code == code and otp.expiration_date > datetime.datetime.now():
                    # ثبت‌نام کاربر
                    user_data = request.session.get('user_data')
                    user = User.objects.create(
                        fullname=user_data['fullname'],
                        phone=user_data['phone'],
                        email=user_data['email'],
                    )
                    user.set_password(user_data['password1'])
                    user.save()

                    # ورود کاربر به سیستم
                    login(request, user)

                    # حذف داده‌های موقت از جلسه
                    request.session.pop('user_data', None)
                    request.session.pop('phone', None)
                    otp.delete()

                    messages.success(request, 'ثبت نام با موفقیت انجام شد!')
                    return redirect('home_app:home')
                else:
                    messages.error(request, 'کد تأیید نادرست یا منقضی شده است.')
            except Otp.DoesNotExist:
                messages.error(request, 'کد تأیید نادرست یا منقضی شده است.')

    else:
        form = VerifyCodeForm()

    return render(request, 'account_app/verify_code_signup.html', {'form': form})