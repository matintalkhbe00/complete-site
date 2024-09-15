from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from home_app.models import CategoryProduct, FAQ, Footer, PhoneCompany
from product_app.models import Order, OrderItem, SubCategory, Category, Product


# Create your views here.


class HomeView(TemplateView):
    template_name = "home_app/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        new_products_category = get_object_or_404(Category, name="new_products")
        best_selling_category = get_object_or_404(Category, name="best_selling")

        new_subcategories = SubCategory.objects.filter(category=new_products_category)
        best_subcategory = SubCategory.objects.filter(category=best_selling_category)

        new_products = Product.objects.filter(subcategories__in=new_subcategories).distinct()[:8]
        best_products = Product.objects.filter(subcategories__in=best_subcategory).distinct()[:8]

        categories = CategoryProduct.objects.all()

        if self.request.user.is_authenticated:
            user = self.request.user
            order = Order.objects.filter(user=user, status="notRegistered").first()
            count = order.items.count() if order else 0
            context.update({
                'user': user,
                'order': order,
                'count': count,
                'products': new_products,
                'best_selling_products': best_products,
                'categories': categories,

            })

        else:
            context.update({
                'products': new_products,
                'best_selling_products' : best_products,
                'categories': categories,

            })

        return context


class FAQView(TemplateView):
    template_name = 'home_app/FAQhome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        faqs = FAQ.objects.all()
        context.update({
            "faqs": faqs,
        })

        return context


class GuaranteeView(TemplateView):
    template_name = 'home_app/guarantee.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        info = Footer.objects.all().first()
        phone = PhoneCompany.objects.all().first()

        context.update({
            'info': info,
            'phone': phone,
        })

        return context


class AboutUsView(TemplateView):
    template_name = 'home_app/about-us.html'

class RolesView(TemplateView):
    template_name = 'home_app/roles.html'