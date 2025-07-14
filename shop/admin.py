from django.contrib import admin
from .models import Hat

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
