from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.templatetags.static import static
import stripe
import json
from .models import Hat, Order

# Create your views here.

def shop_home(request):
    """Display all hat categories and their hats"""
    # Get all unique categories
    categories = Hat.objects.values_list('hat_category', flat=True).distinct().order_by('hat_category')
    
    # Get all hats grouped by category
    hats_by_category = {}
    for category in categories:
        hats_by_category[category] = Hat.objects.filter(hat_category=category).order_by('hat_name')
    
    context = {
        'categories': categories,
        'hats_by_category': hats_by_category,
    }
    return render(request, 'shop/home.html', context)

def category_view(request, category):
    """Display hats in a specific category"""
    hats = Hat.objects.filter(hat_category=category).order_by('hat_name')
    context = {
        'category': category,
        'hats': hats,
    }
    return render(request, 'shop/category.html', context)


def hat_detail(request, hat_id):
    """Display individual hat details"""
    hat = get_object_or_404(Hat, id=hat_id)
    
    # Get related hats in the same category (excluding current hat)
    related_hats = Hat.objects.filter(
        hat_category=hat.hat_category
    ).exclude(id=hat_id)[:4]
    
    context = {
        'hat': hat,
        'related_hats': related_hats,
    }
    return render(request, 'shop/hat_detail.html', context)

def add_to_cart(request, hat_id):
    """Add a hat to the cart (using session-based cart)"""
    if request.method == 'POST':
        hat = get_object_or_404(Hat, id=hat_id)
        
        # Check if hat is sold out
        if hat.sold_out:
            messages.error(request, f"Sorry, {hat.hat_name} is sold out!")
            return redirect('shop:hat_detail', hat_id=hat_id)
        
        # Get or create cart in session
        cart = request.session.get('cart', {})
        
        # Add hat to cart or increment quantity
        hat_id_str = str(hat_id)
        if hat_id_str in cart:
            cart[hat_id_str]['quantity'] += 1
        else:
            # Use static URL for image instead of media URL
            image_url = None
            if hat.get_main_image_filename():
                image_url = static(f'shop/hat_images/{hat.get_main_image_filename()}')
            
            cart[hat_id_str] = {
                'hat_name': hat.hat_name,
                'hat_category': hat.hat_category,
                'price': float(hat.price),
                'quantity': 1,
                'image_url': image_url
            }
        
        # Save cart back to session
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f"{hat.hat_name} added to cart!")
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"{hat.hat_name} added to cart!",
                'cart_count': sum(item['quantity'] for item in cart.values())
            })
        
        return redirect('shop:hat_detail', hat_id=hat_id)
    
    return redirect('shop:home')

def cart_view(request):
    """Display cart contents"""
    cart = request.session.get('cart', {})
    
    cart_items = []
    total_price = 0
    
    for hat_id, item in cart.items():
        item_total = item['price'] * item['quantity']
        cart_items.append({
            'hat_id': hat_id,
            'hat_name': item['hat_name'],
            'hat_category': item['hat_category'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total': item_total,
            'image_url': item.get('image_url')
        })
        total_price += item_total
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': len(cart_items)
    }
    return render(request, 'shop/cart.html', context)

def remove_from_cart(request, hat_id):
    """Remove a hat from the cart"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        hat_id_str = str(hat_id)
        
        if hat_id_str in cart:
            del cart[hat_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, "Item removed from cart!")
        
        return redirect('shop:cart')
    
    return redirect('shop:cart')

def update_cart_quantity(request, hat_id):
    """Update the quantity of a hat in the cart"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        hat_id_str = str(hat_id)
        
        if hat_id_str in cart:
            try:
                new_quantity = int(request.POST.get('quantity', 1))
                if new_quantity > 0:
                    cart[hat_id_str]['quantity'] = new_quantity
                    request.session['cart'] = cart
                    request.session.modified = True
                    messages.success(request, "Cart updated!")
                else:
                    del cart[hat_id_str]
                    request.session['cart'] = cart
                    request.session.modified = True
                    messages.success(request, "Item removed from cart!")
            except ValueError:
                messages.error(request, "Invalid quantity!")
        
        return redirect('shop:cart')
    
    return redirect('shop:cart')

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout(request):
    """Display checkout page with cart items"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect('shop:cart')
    
    cart_items = []
    total_price = 0
    
    for hat_id, item in cart.items():
        item_total = item['price'] * item['quantity']
        cart_items.append({
            'hat_id': hat_id,
            'hat_name': item['hat_name'],
            'hat_category': item['hat_category'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total': item_total,
        })
        total_price += item_total
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'shop/checkout.html', context)

@csrf_exempt
@require_POST
def create_payment_intent(request):
    """Create a Stripe PaymentIntent for the cart total"""
    try:
        data = json.loads(request.body)
        cart = request.session.get('cart', {})
        
        if not cart:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Calculate total amount
        total_amount = 0
        for item in cart.values():
            total_amount += item['price'] * item['quantity']
        
        # Convert to cents for Stripe
        amount_cents = int(total_amount * 100)
        
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            metadata={
                'cart_data': json.dumps(cart),
                'customer_email': data.get('email', ''),
            }
        )
        
        return JsonResponse({
            'client_secret': intent.client_secret
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def payment_success(request):
    """Handle successful payment"""
    payment_intent_id = request.GET.get('payment_intent')
    
    if payment_intent_id:
        try:
            # Retrieve the PaymentIntent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                # Clear the cart
                if 'cart' in request.session:
                    del request.session['cart']
                    request.session.modified = True
                
                # You could create an Order record here if needed
                # For now, just show success message
                messages.success(request, "Payment successful! Thank you for your order!")
                
                context = {
                    'payment_intent_id': payment_intent_id,
                    'amount': intent.amount / 100,  # Convert back from cents
                }
                return render(request, 'shop/payment_success.html', context)
            
        except stripe.error.StripeError as e:
            messages.error(request, f"Payment verification failed: {e}")
    
    messages.error(request, "Payment verification failed!")
    return redirect('shop:cart')

def payment_cancel(request):
    """Handle cancelled payment"""
    messages.warning(request, "Payment was cancelled.")
    return redirect('shop:cart')


