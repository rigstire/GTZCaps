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
