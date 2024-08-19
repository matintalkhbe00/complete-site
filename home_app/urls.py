from django.urls import path
from django.views.decorators.cache import cache_page
from . import views

app_name = 'home_app'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('faq/', views.FAQView.as_view(), name='FAQ'),
    path('guarantee/', views.GuaranteeView.as_view(), name='guarantee'),
    path('about/', views.AboutUsView.as_view(), name='about-us'),

]