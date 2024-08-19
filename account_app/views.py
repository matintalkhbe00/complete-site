import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from home_app.models import FAQ
from product_app.forms import AddressForm
from product_app.models import Order, User
from .forms import CustomLoginForm, UserCreationForm, ContactForm
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from .forms import ProfileEditForm, PasswordChangeCustomForm
from .models import Address, ContactUs


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
    success_url = reverse_lazy('home_app:home')  # صفحه‌ای که پس از ثبت‌نام موفقیت‌آمیز هدایت می‌شود

    def dispatch(self, request, *args, **kwargs):
        # اگر کاربر قبلاً وارد سیستم شده باشد، او را به صفحه اصلی هدایت کن
        if request.user.is_authenticated:
            messages.info(request, 'شما قبلاً وارد سیستم شده‌اید.')
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # مقایسه پسوردها
        password1 = form.cleaned_data.get('password1')
        password2 = form.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            form.add_error('password2', 'رمزهای عبور مطابقت ندارند')
            return self.form_invalid(form)

        # بررسی تکراری بودن شماره تلفن
        phone = form.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            form.add_error('phone', 'این شماره تلفن قبلاً ثبت شده است.')
            return self.form_invalid(form)

        # ذخیره کاربر
        user = form.save()
        # ورود کاربر به سیستم به صورت خودکار پس از ثبت‌نام
        login(self.request, user)
        messages.success(self.request, 'ثبت نام با موفقیت انجام شد!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'لطفاً فرم را بررسی کنید.')
        return super().form_invalid(form)

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

