from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.templatetags.static import static
import stripe
import json
import os
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

def debug_static_files(request):
    """Debug view to check static file paths and existence"""
    if not settings.DEBUG and not os.getenv('VERCEL'):
        return HttpResponse("Debug view not available", status=404)
    
    debug_info = {
        'STATIC_URL': settings.STATIC_URL,
        'STATIC_ROOT': settings.STATIC_ROOT,
        'STATICFILES_DIRS': settings.STATICFILES_DIRS,
        'DEBUG': settings.DEBUG,
        'VERCEL': os.getenv('VERCEL', 'Not set'),
    }
    
    # Test static file URLs and existence
    test_files = [
        'shop/images/logo.jpeg',
        'shop/images/gtzbackground.png',
        'shop/images/bigbosslogo.png',
    ]
    
    file_info = {}
    for file_path in test_files:
        static_url = static(file_path)
        
        # Check different possible locations
        locations = []
        
        # Check in STATIC_ROOT
        if settings.STATIC_ROOT:
            static_root_path = os.path.join(settings.STATIC_ROOT, file_path)
            locations.append(f"STATIC_ROOT: {static_root_path} - Exists: {os.path.exists(static_root_path)}")
        
        # Check in public directory
        public_path = os.path.join('public', 'static', file_path)
        locations.append(f"public/static: {public_path} - Exists: {os.path.exists(public_path)}")
        
        # Check in alternative public path
        alt_public_path = os.path.join('public', file_path)
        locations.append(f"public: {alt_public_path} - Exists: {os.path.exists(alt_public_path)}")
        
        file_info[file_path] = {
            'static_url': static_url,
            'locations': locations
        }
    
    # Create HTML response
    html = f"""
    <html>
    <head><title>Static Files Debug</title></head>
    <body>
        <h1>Static Files Debug Information</h1>
        <h2>Django Settings</h2>
        <pre>{json.dumps(debug_info, indent=2)}</pre>
        
        <h2>File Information</h2>
        <pre>{json.dumps(file_info, indent=2)}</pre>
    </body>
    </html>
    """
    
    return HttpResponse(html)

def test_social_media_tags(request):
    """Test view to show how the site will appear when shared on social media"""
    
    # Get the logo URL
    logo_url = request.build_absolute_uri(static('shop/images/logo.jpeg'))
    
    # Sample hat for testing
    sample_hat = None
    try:
        sample_hat = Hat.objects.first()
        if sample_hat and sample_hat.get_main_image_filename():
            sample_hat_image = request.build_absolute_uri(static(f'shop/hat_images/{sample_hat.get_main_image_filename()}'))
        else:
            sample_hat_image = logo_url
    except:
        sample_hat_image = logo_url
    
    social_info = {
        'site_name': 'GTZ CAPS',
        'title': 'GTZ CAPS - Unleash Your Style',
        'description': 'Premium Quality Caps. Discover our exclusive collection of stylish hats from top brands including Big Boss, Dandy Hats, and El Barbas Hats.',
        'logo_url': logo_url,
        'sample_hat_image': sample_hat_image,
        'sample_hat': sample_hat.hat_name if sample_hat else 'No hats found',
        'current_url': request.build_absolute_uri(),
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Social Media Preview Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .preview {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }}
            .preview img {{ max-width: 300px; height: auto; border-radius: 4px; }}
            .meta-info {{ background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 10px 0; }}
            pre {{ background: #f8f8f8; padding: 10px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h1>Social Media Sharing Preview</h1>
        
        <div class="preview">
            <h2>🏠 Homepage Preview</h2>
            <img src="{logo_url}" alt="GTZ CAPS Logo">
            <h3>{social_info['title']}</h3>
            <p>{social_info['description']}</p>
            <small>gtzcaps.com</small>
        </div>
        
        <div class="preview">
            <h2>🧢 Hat Detail Preview</h2>
            <img src="{sample_hat_image}" alt="Sample Hat">
            <h3>{social_info['sample_hat']} | GTZ CAPS</h3>
            <p>Premium quality hat from GTZ CAPS.</p>
            <small>gtzcaps.com/hat/1</small>
        </div>
        
        <div class="meta-info">
            <h3>Meta Tag Information</h3>
            <pre>{json.dumps(social_info, indent=2)}</pre>
        </div>
        
        <div class="meta-info">
            <h3>How to Test:</h3>
            <ol>
                <li><strong>Facebook/Meta:</strong> Use <a href="https://developers.facebook.com/tools/debug/" target="_blank">Facebook Sharing Debugger</a></li>
                <li><strong>Twitter/X:</strong> Use <a href="https://cards-dev.twitter.com/validator" target="_blank">Twitter Card Validator</a></li>
                <li><strong>LinkedIn:</strong> Use <a href="https://www.linkedin.com/post-inspector/" target="_blank">LinkedIn Post Inspector</a></li>
                <li><strong>General:</strong> Use <a href="https://www.opengraph.xyz/" target="_blank">Open Graph Checker</a></li>
            </ol>
            <p><strong>Note:</strong> After deployment, test with your actual domain URL to see the preview.</p>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html)

def create_admin_user(request):
    """Create a superuser for admin access - USE ONLY ONCE after deployment"""
    from django.middleware.csrf import get_token
    
    if request.method == 'POST' and request.POST.get('confirm') == 'yes':
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            existing_superuser = User.objects.filter(is_superuser=True).first()
            message = f"❌ Superuser already exists: {existing_superuser.username}"
            status = "error"
        else:
            # Create superuser
            username = request.POST.get('username', 'admin')
            email = request.POST.get('email', 'admin@gtzcaps.com')
            password = request.POST.get('password', 'gtzcaps_admin_2024')
            
            try:
                superuser = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                message = f"✅ Superuser created! Username: {username}, Password: {password}"
                status = "success"
            except Exception as e:
                message = f"❌ Error creating superuser: {e}"
                status = "error"
    else:
        message = ""
        status = ""
    
    # Get CSRF token
    csrf_token = get_token(request)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Admin User - GTZ CAPS</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .form {{ background: #f9f9f9; padding: 20px; border-radius: 8px; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }}
            .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px; margin: 20px 0; }}
            .error {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin: 20px 0; }}
            input, button {{ padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; }}
            button {{ background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <h1>🔧 Create Admin User</h1>
        
        <div class="warning">
            <strong>⚠️ Security Warning:</strong><br>
            • Use this ONLY ONCE after initial deployment<br>
            • Change the default password immediately<br>
            • Delete this endpoint URL after use for security
        </div>
        
        {f'<div class="{status}">{message}</div>' if message else ''}
        
        <div class="form">
            <form method="post">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <h3>Create Superuser</h3>
                <input type="text" name="username" placeholder="Username (default: admin)" value="admin">
                <input type="email" name="email" placeholder="Email" value="admin@gtzcaps.com">
                <input type="password" name="password" placeholder="Password (CHANGE THIS!)" value="gtzcaps_admin_2024">
                <label>
                    <input type="checkbox" name="confirm" value="yes" required> 
                    I confirm I want to create an admin user
                </label>
                <button type="submit">Create Admin User</button>
            </form>
        </div>
        
        <div class="warning">
            <h3>After Creating Admin User:</h3>
            <ol>
                <li>Visit <a href="/admin/">/admin/</a> to login</li>
                <li>Change the password immediately</li>
                <li>Remove this URL for security</li>
            </ol>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html)
