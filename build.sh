#!/bin/bash

echo "Starting build process..."

# Set Vercel environment variable
export VERCEL=1

echo "Setting up static files for Vercel..."
mkdir -p public/static

# Copy from local staticfiles directory (if it exists)
if [ -d "staticfiles" ]; then
    echo "Copying static files from local staticfiles directory"
    cp -r staticfiles/* public/static/ 2>/dev/null
    echo "Files copied from staticfiles: $(ls staticfiles | wc -l) items"
fi

# Ensure source images exist and copy them explicitly
echo "Checking source hat_images..."
if [ -d "shop/static/shop/hat_images" ]; then
    echo "Found shop/static/shop/hat_images with $(ls shop/static/shop/hat_images | wc -l) files"
    mkdir -p public/static/shop/hat_images
    cp shop/static/shop/hat_images/* public/static/shop/hat_images/ 2>/dev/null
    echo "Copied hat_images to public/static/shop/hat_images"
else
    echo "ERROR: shop/static/shop/hat_images directory not found!"
fi

# Also copy logo and background images with multiple strategies
echo "Checking source logo images..."
if [ -d "shop/static/shop/images" ]; then
    echo "Found shop/static/shop/images with $(ls shop/static/shop/images | wc -l) files"
    
    # Copy to both locations to ensure they're accessible
    mkdir -p public/static/shop/images
    cp shop/static/shop/images/* public/static/shop/images/ 2>/dev/null
    echo "Copied logo images to public/static/shop/images"
    
    # Also copy to the root public directory with static path
    mkdir -p public/shop/images
    cp shop/static/shop/images/* public/shop/images/ 2>/dev/null
    echo "Also copied logo images to public/shop/images (alternative path)"
    
    # List what was actually copied
    echo "Files copied to public/static/shop/images:"
    ls -la public/static/shop/images/
else
    echo "ERROR: shop/static/shop/images directory not found!"
fi

# Debug: Show final structure
echo "Final public/static structure:"
find public/static -type f -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" | head -15

# Verify hat images specifically
echo "Hat images in public directory:"
ls -la public/static/shop/hat_images/ 2>/dev/null || echo "No hat_images directory found in public/static"

# Verify logo images specifically
echo "Logo images in public directory:"
ls -la public/static/shop/images/ 2>/dev/null || echo "No images directory found in public/static"

echo "Build process completed!"
echo "Static files copied successfully!" 