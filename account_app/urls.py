from django.urls import path

from . import views

app_name = 'account_app'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    # path('products' , views.ProductListView.as_view(), name='products'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('addaddress/', views.AddAddressView.as_view(), name='addAddress'),
    path('editaddress/<int:pk>/', views.EditAddressView.as_view(), name='editAddress'),
    path('deleteaddress/<int:pk>/', views.DeleteAddressView.as_view(), name='deleteAddress'),

    # ////////////////////////////////////////////////////

    path('upload_profile_picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('delete_profile_picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('password_change/', views.PasswordChangeViewCustom.as_view(), name='password_change'),
    # //////////////////////////////////////////////////////
    path('contact/', views.ContactUsView.as_view(), name='contact_form_submit'),
]
