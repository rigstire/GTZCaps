from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.shop_home, name='home'),
    path('hat/<int:hat_id>/', views.hat_detail, name='hat_detail'),
    path('category/<str:category>/', views.category_view, name='category'),
    path('add-to-cart/<int:hat_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('remove-from-cart/<int:hat_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:hat_id>/', views.update_cart_quantity, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    # Static file serving for Vercel
    path('static/<path:path>', views.serve_static, name='serve_static'),
] 