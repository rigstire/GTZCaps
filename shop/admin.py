from django.contrib import admin
from .models import Hat, Order

# Register your models here.

@admin.register(Hat)
class HatAdmin(admin.ModelAdmin):
    list_display = ['hat_name', 'hat_category', 'price', 'sold_out', 'hat_picture_preview', 'created_at']
    list_filter = ['hat_category', 'sold_out', 'created_at']
    search_fields = ['hat_name', 'hat_category', 'description']
    list_editable = ['sold_out']
    readonly_fields = ['created_at', 'updated_at', 'hat_picture_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hat_name', 'hat_category', 'price')
        }),
        ('Main Image', {
            'fields': ('hat_picture', 'hat_picture_preview')
        }),
        ('Additional Description Images', {
            'fields': ('description_pic1', 'description_pic2', 'description_pic3'),
            'description': 'Upload additional images to create an image carousel on the hat detail page'
        }),
        ('Additional Details', {
            'fields': ('description', 'sold_out')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def hat_picture_preview(self, obj):
        """Display a small preview of the hat image in the admin"""
        if obj.hat_picture:
            return f'<img src="{obj.hat_picture.url}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />'
        return "No image"
    
    hat_picture_preview.short_description = "Image Preview"
    hat_picture_preview.allow_tags = True

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'total_amount', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'created_at', 'state', 'country']
    search_fields = ['email', 'first_name', 'last_name', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'created_at', 'updated_at', 'order_items_display']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'stripe_payment_intent_id', 'payment_status', 'total_amount', 'currency')
        }),
        ('Customer Information', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Billing Address', {
            'fields': ('address', 'city', 'state', 'zip_code', 'country')
        }),
        ('Order Items', {
            'fields': ('order_items_display',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_items_display(self, obj):
        """Display order items in a readable format"""
        items_html = "<ul>"
        for item_id, item in obj.order_items.items():
            items_html += f"<li><strong>{item['hat_name']}</strong> ({item['hat_category']}) - ${item['price']} x {item['quantity']} = ${item['price'] * item['quantity']}</li>"
        items_html += "</ul>"
        return items_html
    
    order_items_display.short_description = "Order Items"
    order_items_display.allow_tags = True
