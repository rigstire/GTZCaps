from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
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
    """Display all hats in a specific category"""
    hats = Hat.objects.filter(hat_category=category).order_by('hat_name')
    
    if not hats.exists():
        messages.error(request, f"No hats found in category '{category}'")
        return redirect('shop:home')
    
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
            cart[hat_id_str] = {
                'hat_name': hat.hat_name,
                'hat_category': hat.hat_category,
                'price': float(hat.price),
                'quantity': 1,
                'image_url': hat.hat_picture.url if hat.hat_picture else None
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
            hat_name = cart[hat_id_str]['hat_name']
            del cart[hat_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, f"{hat_name} removed from cart!")
        
        return redirect('shop:cart')
    
    return redirect('shop:cart')

def update_cart_quantity(request, hat_id):
    """Update quantity of a hat in the cart"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        hat_id_str = str(hat_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if hat_id_str in cart and quantity > 0:
            cart[hat_id_str]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, "Cart updated!")
        elif quantity <= 0:
            return remove_from_cart(request, hat_id)
        
        return redirect('shop:cart')
    
    return redirect('shop:cart')

# Set up Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout(request):
    """Display checkout page with Stripe payment"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, "Your cart is empty!")
        return redirect('shop:cart')
    
    # Calculate totals
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
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'total_cents': int(total_price * 100)  # Stripe uses cents
    }
    return render(request, 'shop/checkout.html', context)

@csrf_exempt
@require_POST
def create_payment_intent(request):
    """Create a Stripe PaymentIntent and save customer information"""
    try:
        data = json.loads(request.body)
        cart = request.session.get('cart', {})
        
        if not cart:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Calculate total
        total_price = sum(item['price'] * item['quantity'] for item in cart.values())
        
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(total_price * 100),  # Amount in cents
            currency='usd',
            metadata={
                'cart_items': json.dumps(cart),
                'customer_email': data.get('email', ''),
                'customer_name': data.get('firstName', '') + ' ' + data.get('lastName', ''),
                'customer_address': data.get('address', ''),
                'customer_city': data.get('city', ''),
                'customer_state': data.get('state', ''),
                'customer_zip': data.get('zip', ''),
            }
        )
        
        # Save customer information to database
        order = Order.objects.create(
            email=data.get('email', ''),
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            zip_code=data.get('zip', ''),
            country='US',
            stripe_payment_intent_id=intent.id,
            total_amount=total_price,
            currency='USD',
            payment_status='pending',
            order_items=cart
        )
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'order_id': order.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def payment_success(request):
    """Handle successful payment"""
    # Get payment intent ID from query parameters
    payment_intent_id = request.GET.get('payment_intent')
    
    if payment_intent_id:
        try:
            # Update order status to completed
            order = Order.objects.get(stripe_payment_intent_id=payment_intent_id)
            order.payment_status = 'completed'
            order.save()
            
            # Store order ID in session for display
            request.session['last_order_id'] = order.id
            
        except Order.DoesNotExist:
            pass  # Handle gracefully if order not found
    
    # Clear the cart
    request.session['cart'] = {}
    request.session.modified = True
    
    messages.success(request, "Payment successful! Thank you for your purchase!")
    
    context = {
        'success': True
    }
    return render(request, 'shop/payment_success.html', context)

def payment_cancel(request):
    """Handle cancelled payment"""
    messages.error(request, "Payment was cancelled. Your cart is still available.")
    return redirect('shop:cart')
