import time
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from account_app.models import Address
from django.db.models.signals import post_save
from django.dispatch import receiver
User = get_user_model()

class Product(models.Model):
    PRODUCT_STATUS_CHOICES = [
        ('in_stock', 'موجود'),
        ('out_of_stock', 'ناموجود'),
    ]

    name = models.CharField(max_length=255, verbose_name='نام محصول')
    description = models.TextField(verbose_name='توضیحات محصول')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت')
    discount_percentage = models.DecimalField(max_digits=2, decimal_places=0, blank=True, null=True,
                                              verbose_name='درصد تخفیف')
    status = models.CharField(max_length=20, choices=PRODUCT_STATUS_CHOICES, default='in_stock', verbose_name='وضعیت')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')
    def get_final_price(self):
        if self.discount_percentage and self.discount_percentage > 0:
            discount_amount = (self.price * self.discount_percentage) / 100
            return self.price - discount_amount
        return self.price

    def calculate_average_rating(self):
        reviews = self.reviews.all()
        sum_rating = 0.0
        count = 0

        for review in reviews:
            if review.rating is not None:
                sum_rating += review.rating
                count += 1

        if count > 0:
            return sum_rating / count
        else:
            return 0.0

    def update_stock_status(self, status):
        self.status = status
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductFeature(models.Model):
    product = models.ForeignKey(Product, related_name='features', on_delete=models.CASCADE, verbose_name='محصول')
    name = models.CharField(max_length=255, verbose_name='ویژگی')
    value = models.CharField(max_length=255, verbose_name='مقدار ویژگی')

    def __str__(self):
        return f"{self.name}: {self.value}"

    class Meta:
        verbose_name = 'ویژگی محصول'
        verbose_name_plural = 'ویژگی‌های محصول'


class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE, verbose_name='محصول')
    author = models.CharField(max_length=255, verbose_name='نویسنده')
    rating = models.FloatField(verbose_name='امتیاز', null=True, blank=True)
    comment = models.TextField(verbose_name='نظر')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE,
                               verbose_name='پاسخ به')

    def __str__(self):
        return f"نظر {self.author} بر روی {self.product.name}"

    class Meta:
        verbose_name = 'نظر محصول'
        verbose_name_plural = 'نظرات محصول'
        ordering = ['-created_at']


class DiscountCode(models.Model):
    name = models.CharField(max_length=50, unique=True)
    discount = models.SmallIntegerField(default=0)
    quantity = models.SmallIntegerField(default=1)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        now = timezone.now()
        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date and self.quantity > 0
        elif self.start_date:
            return self.start_date <= now and self.quantity > 0
        elif self.end_date:
            return now <= self.end_date and self.quantity > 0
        else:
            return self.quantity > 0

    def __str__(self):
        return self.name



# /////////////////////////////////////////////////////////////////////////////
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('notRegistered','تایید نشده'),
        ('pending', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل شده'),
        ('cancelled', 'لغو شده'),
    ]


    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True, blank=True, verbose_name='آدرس')
    total_price = models.IntegerField(default=0)
    original_price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='notRegistered', verbose_name='وضعیت')
    discount_code = models.ForeignKey(DiscountCode, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')

    def __str__(self):
        return f'Order {self.id} by {self.user.fullname}'

    def save(self, *args, **kwargs):
        if self.pk:
            # فقط هنگام به‌روزرسانی قیمت‌ها به‌روز می‌شود
            self.original_price = sum(item.get_total_price() for item in self.items.all())
            self.total_price = self.get_discounted_total_price()
        super().save(*args, **kwargs)

    def update_total_price(self):
        self.original_price = sum(item.get_total_price() for item in self.items.all())
        self.total_price = self.get_discounted_total_price()
        self.save()

    def get_discounted_total_price(self):
        if self.discount_code and self.discount_code.is_valid():
            discount_percentage = self.discount_code.discount
            discount_amount = (self.original_price * discount_percentage) / 100
            return self.original_price - discount_amount
        return self.original_price

    def get_discount_price(self):
        if self.discount_code and self.discount_code.is_valid():
            discount_percentage = self.discount_code.discount
            discount_amount = (self.original_price * discount_percentage) / 100
            return discount_amount


    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name='سفارش')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='قیمت')

    def get_total_price(self):
        total_price = self.product.get_final_price() * self.quantity
        return total_price

    def get_discounted_price(self):
        if self.product.discount_percentage:
            return self.product.price * self.product.discount_percentage /100



    class Meta:
        verbose_name = 'ایتم سفرش'
        verbose_name_plural = 'ایتم های سفارش'

    def __str__(self):
        return f'{self.quantity} x {self.product.name} in {self.order.id}'

@receiver(post_save, sender=OrderItem)
def update_order_total_price(sender, instance, **kwargs):
    order = instance.order
    order.update_total_price()



class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='نام دسته‌بندی')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE, verbose_name='دسته‌بندی اصلی')
    products = models.ManyToManyField(Product, related_name='subcategories', blank=True, verbose_name='محصولات')

    def __str__(self):
        return self.category.name

    class Meta:
        verbose_name = 'زیر دسته‌بندی'
        verbose_name_plural = 'زیر دسته‌بندی‌ها'

class SubShop(models.Model):
    categories = models.ManyToManyField(Category, related_name='subshops', verbose_name='دسته‌بندی‌های فروشگاه')

    def __str__(self):
        # نمایش نام‌های دسته‌بندی‌ها به صورت لیست در متد __str__
        return f"فروشگاه با دسته‌بندی‌ها: {', '.join(str(cat) for cat in self.categories.all())}"

    class Meta:
        verbose_name = 'فروشگاه فرعی'
        verbose_name_plural = 'فروشگاه‌های فرعی'


