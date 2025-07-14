from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Hat

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
