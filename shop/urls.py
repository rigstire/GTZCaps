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
] 