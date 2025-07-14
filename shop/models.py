from django.db import models

# Create your models here.

class Hat(models.Model):
    hat_name = models.CharField(max_length=200, help_text="The name of the hat")
    hat_category = models.CharField(max_length=50, help_text="Hat category")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in US dollars")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the hat")
    hat_picture = models.ImageField(upload_to='hat_images/', blank=True, null=True, help_text="Upload an image of the hat")
    description_pic1 = models.ImageField(upload_to='hat_images/', blank=True, null=True, help_text="Optional additional description image 1")
    description_pic2 = models.ImageField(upload_to='hat_images/', blank=True, null=True, help_text="Optional additional description image 2")
    description_pic3 = models.ImageField(upload_to='hat_images/', blank=True, null=True, help_text="Optional additional description image 3")
    sold_out = models.BooleanField(default=False, help_text="Whether the hat is sold out")
    
    # Optional: Add timestamps for when the hat was created/updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['hat_category', 'hat_name']
        verbose_name = "Hat"
        verbose_name_plural = "Hats"
    
    def __str__(self):
        return f"{self.hat_name} ({self.hat_category})"
    
    @property
    def is_available(self):
        """Returns True if the hat is not sold out"""
        return not self.sold_out

class Order(models.Model):
    # Customer Information
    email = models.EmailField(help_text="Customer's email address")
    first_name = models.CharField(max_length=100, help_text="Customer's first name")
    last_name = models.CharField(max_length=100, help_text="Customer's last name")
    
    # Billing Address
    address = models.CharField(max_length=200, help_text="Street address")
    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=100, help_text="State/Province")
    zip_code = models.CharField(max_length=20, help_text="ZIP/Postal code")
    country = models.CharField(max_length=100, default="US", help_text="Country")
    
    # Payment Information
    stripe_payment_intent_id = models.CharField(max_length=200, unique=True, help_text="Stripe PaymentIntent ID")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount paid")
    currency = models.CharField(max_length=3, default="USD", help_text="Currency code")
    payment_status = models.CharField(max_length=50, default="pending", help_text="Payment status")
    
    # Order Details
    order_items = models.JSONField(help_text="JSON data of ordered items")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"
    
    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name} (${self.total_amount})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}, {self.country}"
