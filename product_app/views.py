from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView, FormView
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.db import transaction

from account_app.models import Address, User
from home_app.models import FAQ
from .forms import ProductReviewForm, ReplyForm, OrderItemUpdateForm, OrderItemDeleteForm, AddressForm
from .models import Product, ProductReview, Order, OrderItem, DiscountCode

from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from .models import Product, Order, OrderItem, DiscountCode


def add_reply(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(ProductReview, id=review_id)
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.product = review.product
            reply.user = request.user  # استفاده از کاربر فعلی به عنوان نویسنده
            reply.parent = review
            reply.save()
            return HttpResponseRedirect(
                reverse('product_app:product_detail', args=[review.product.id]) + '?active_tab=reviews')
        return HttpResponseRedirect(reverse('product_app:product_detail', args=[review.product.id]))


class ProductDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect(f'/account/login/?next={request.get_full_path()}&notification=not_login')
        product = get_object_or_404(Product, pk=pk)
        product_images = product.images.all()
        product_features = product.features.all()
        product_reviews = product.reviews.filter(parent__isnull=True).prefetch_related('replies')
        user_reviews = product.reviews.filter(user=request.user)
        faqs = FAQ.objects.all()
        form = ProductReviewForm()

        # Fetch user profile pictures safely
        # user_profiles = {}
        # review_users = set(review.user for review in product_reviews)
        # for user in review_users:
        #     if user.profile_picture:
        #         user_profiles[user.id] = user.profile_picture.url
        #

        # بررسی وجود محصول در سبد خرید
        product_in_cart = False
        product_quantity = 0

        # جستجو در سفارش‌های در حال پردازش یا تایید نشده برای کاربر
        order_items = OrderItem.objects.filter(
            order__user=request.user,
            order__status__in=['notRegistered'],
            product=product
        )

        if order_items.exists():
            product_in_cart = True
            product_quantity = order_items.first().quantity

        context = {
            'product': product,
            'product_images': product_images,
            'product_features': product_features,
            'product_reviews': product_reviews,
            'form': form,
            'user_reviews': user_reviews,
            'faqs': faqs,
            'product_in_cart': product_in_cart,
            'product_quantity': product_quantity,

        }

        return render(request, 'product_app/product_details.html', context)

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect(f'/account/login/?next={request.get_full_path()}&notification=not_login')
        product = get_object_or_404(Product, pk=pk)
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                review.parent = ProductReview.objects.get(id=parent_id)
            review.save()
        return redirect('product_app:product_detail', pk=product.id)



class ProductListView(ListView):
    model = Product
    template_name = 'product_app/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products_with_ratings = {product.pk: product.calculate_average_rating() for product in Product.objects.all()}
        context['products_with_ratings'] = products_with_ratings
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        # دریافت پارامتر جستجو از URL
        search = self.request.GET.get('search', '')

        # فیلتر بر اساس نام محصول و توضیحات
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        # فیلتر بر اساس قیمت
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


# ////////////////////////////////////////////////////////////////


class ProductAddOrderView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        product = get_object_or_404(Product, pk=pk)
        quantity = int(request.POST.get('quantity', 1))
        order = Order.objects.filter(status="notRegistered", user=user)

        if order:
            order = Order.objects.get(status="notRegistered", user=user)
            flag = False
            for item in order.items.all():
                if item.product == product:
                    flag = True
                    OrderItem.objects.get(id=item.id, order=order).delete()
                    OrderItem.objects.create(order=order, product=product, quantity=quantity + item.quantity,
                                             price=product.get_final_price())
            if not flag:
                OrderItem.objects.create(order=order, product=product, quantity=quantity,
                                         price=product.get_final_price())
            pass
        else:
            order = Order.objects.create(user=user)
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)

        # order_item.save()

        # به‌روزرسانی قیمت کل سفارش
        order.update_total_price()

        return redirect(reverse("product_app:order_detail") + "?notification=product_added")


class OrderNotRegisteredView(LoginRequiredMixin, TemplateView):
    template_name = 'product_app/order_notRegistered.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        addresses = Address.objects.filter(user=user)
        selected_address_id = self.request.session.get('selected_address_id')
        order = Order.objects.filter(user=user, status="notRegistered")
        faqs = FAQ.objects.all()
        notification_type = self.request.GET.get('notification')

        if notification_type == 'product_added':
            show_notification = True
            notification_message = 'محصول با موفقیت به سبد خرید اضافه شد!'
            notification_status = 'success'
        elif notification_type == 'discount_applied':
            show_notification = True
            notification_message = 'تخفیف به سفارش شما اعمال شد!'
            notification_status = 'success'
        elif notification_type == 'discount_removed':
            show_notification = True
            notification_message = 'کد تخفیف با موفقیت حذف شد!'
            notification_status = 'success'
        elif notification_type == 'order_item_updated':
            show_notification = True
            notification_message = 'آیتم سفارش با موفقیت به‌روزرسانی شد!'
            notification_status = 'success'
        elif notification_type == 'order_item_deleted':
            show_notification = True
            notification_message = 'آیتم سفارش با موفقیت حذف شد!'
            notification_status = 'success'
        elif notification_type == 'address_selected':
            show_notification = True
            notification_message = 'آدرس با موفقیت انتخاب شد!'
            notification_status = 'success'
        elif notification_type == 'discount_code_missing':
            show_notification = True
            notification_message = 'لطفاً کد تخفیف را وارد کنید.'
            notification_status = 'warning'
        elif notification_type == 'no_order_found':
            show_notification = True
            notification_message = 'سفارشی برای شما پیدا نشد.'
            notification_status = 'warning'
        elif notification_type == 'invalid_discount_code':
            show_notification = True
            notification_message = 'کد تخفیف معتبر نیست.'
            notification_status = 'error'
        elif notification_type == 'update_failed':
            show_notification = True
            notification_message = 'به‌روزرسانی ناموفق بود.'
            notification_status = 'error'
        elif notification_type == 'delete_failed':
            show_notification = True
            notification_message = 'حذف ناموفق بود.'
            notification_status = 'error'
        elif notification_type == 'order_address':
            show_notification = True
            notification_message = 'لطفا آدرسی انتخاب یا اضافه کنید'
            notification_status = 'warning'
        else:
            show_notification = False
            notification_message = ''
            notification_status = 'none'

        context.update({
            'user': user,
            'addresses': addresses,
            'selected_address_id': selected_address_id,
            'form': AddressForm(),
            'orders': order,
            'show_notification': show_notification,
            'notification_message': notification_message,
            'notification_status': notification_status,
            'faqs': faqs,
        })

        return context


class ConfirmOrderView(LoginRequiredMixin, View):
    def get(self, request):
        order = Order.objects.get(user=request.user, status="notRegistered")
        if not order.address:
            return redirect(reverse('product_app:order_detail') + "?notification=order_address")

        order.status = "pending"
        order.save()
        return redirect(reverse("account_app:profile") + '?notification=confirmOrder')


class OrderDetailsView(LoginRequiredMixin, TemplateView):
    template_name = 'product_app/order_details.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        pk = self.kwargs.get('pk')

        order = get_object_or_404(Order, user=user, id=pk)
        discount_price = order.original_price - order.total_price

        context.update({
            'user': user,
            'order': order,
            'address': order.address,
            'total_price': order.total_price,
            'original_price': order.original_price,
            'discount_price': order.original_price - order.total_price,
            'created_at': order.created_at,
            'status': order.status,

        })

        return context


# ////////////////////////////////////////// Order development
class ApplyDiscountView(View):
    def post(self, request):
        discount_code = request.POST.get('discount_code')

        if not discount_code:
            messages.error(request, 'لطفاً کد تخفیف را وارد کنید.')
            return redirect(reverse('product_app:order_detail') + "?notification=discount_code_missing")

        order = Order.objects.filter(user=request.user, status='notRegistered').first()
        if not order:
            messages.error(request, 'سفارشی برای شما پیدا نشد.')
            return redirect(reverse('product_app:order_detail') + "?notification=no_order_found")

        try:
            discount = DiscountCode.objects.get(name=discount_code)
        except DiscountCode.DoesNotExist:
            messages.error(request, 'کد تخفیف معتبر نیست.')
            return redirect(reverse('product_app:order_detail') + "?notification=invalid_discount_code")

        if not discount.is_valid():
            messages.error(request, 'کد تخفیف معتبر نیست.')
            return redirect(reverse('product_app:order_detail') + "?notification=invalid_discount_code")

        discount_amount = (order.original_price * discount.discount) / 100
        order.total_price = order.original_price - discount_amount
        order.discount_code = discount
        order.save()

        discount.quantity -= 1
        discount.save()

        messages.success(request, f'تخفیف {discount.discount}% به سفارش شما اعمال شد.')
        return redirect(reverse('product_app:order_detail') + "?notification=discount_applied")


class RemoveDiscountView(View):
    def post(self, request):
        order = Order.objects.filter(status='notRegistered', user=request.user).first()

        if not order:
            messages.error(request, "سفارشی برای حذف تخفیف یافت نشد.")
            return redirect(reverse('product_app:order_detail') + "?notification=no_order_found")

        if order.discount_code:
            discount = order.discount_code
            order.discount_code = None
            order.total_price = order.original_price
            order.save()

            discount.quantity += 1
            discount.save()

            messages.success(request, "کد تخفیف با موفقیت حذف شد.")
            return redirect(reverse('product_app:order_detail') + "?notification=discount_removed")
        else:
            messages.error(request, "هیچ کد تخفیفی برای حذف وجود ندارد.")
            return redirect(reverse('product_app:order_detail') + "?notification=no_discount_to_remove")


class UpdateOrderItemView(View):
    def post(self, request, *args, **kwargs):
        form = OrderItemUpdateForm(request.POST)
        if form.is_valid():
            item_id = request.POST.get('item_id')
            order_item = get_object_or_404(OrderItem, id=item_id)
            quantity = form.cleaned_data['quantity']
            order_item.quantity = quantity
            order_item.save()
            return redirect(reverse('product_app:order_detail') + "?notification=order_item_updated")
        else:
            return redirect(reverse('product_app:order_detail') + "?notification=update_failed")


class DeleteOrderItemView(View):
    def post(self, request, *args, **kwargs):
        order_item_id = request.POST.get('order_item_id')

        if order_item_id:
            order_item = get_object_or_404(OrderItem, id=order_item_id)
            order = order_item.order

            order_item.delete()
            order.update_total_price()

            return redirect(reverse('product_app:order_detail') + "?notification=order_item_deleted")
        else:
            return redirect(reverse('product_app:order_detail') + "?notification=delete_failed")


def select_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    order = Order.objects.filter(user=request.user, status='notRegistered').first()

    if order:
        order.address = address
        order.save()

    request.session['selected_address_id'] = address.id

    return redirect(reverse('product_app:order_detail') + "?notification=address_selected")
