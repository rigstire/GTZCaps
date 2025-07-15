from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Home page showing all categories and hats
    path('', views.shop_home, name='home'),
    
    # Category view showing hats in a specific category
    path('category/<str:category>/', views.category_view, name='category'),
    
    # Individual hat detail view
    path('hat/<int:hat_id>/', views.hat_detail, name='hat_detail'),
    
    # Cart functionality
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:hat_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:hat_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:hat_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    
    # Payment functionality
    path('checkout/', views.checkout, name='checkout'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Debug functionality
    path('debug-static/', views.debug_static_files, name='debug_static'),
    path('test-social/', views.test_social_media_tags, name='test_social'),
    
    # Admin setup (USE ONLY ONCE after deployment)
    path('setup-admin/', views.create_admin_user, name='create_admin'),
] 