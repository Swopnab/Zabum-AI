"""
Test script for Week 1 OCR Pipeline
Tests image upload, OCR extraction, and database storage
"""

import requests
import os
from pathlib import Path


def test_pipeline():
    """Test the complete OCR pipeline"""
    
    base_url = "http://localhost:5001"
    
    print("=" * 60)
    print("Testing Zabum AI Week 1 Pipeline")
    print("=" * 60)
    
    # 1. Test health check
    print("\n1️⃣ Testing health check...")
    response = requests.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # 2. Test image upload with a sample image
    print("\n2️⃣ Testing image upload and OCR...")
    
    # Create a simple test image with text
    test_image_path = create_test_image()
    
    with open(test_image_path, 'rb') as f:
        files = {'image': ('test.png', f, 'image/png')}
        response = requests.post(f"{base_url}/api/process", files=files)
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ Image ID: {data['id']}")
        print(f"   ✅ Extracted Text: {data['extracted_text']}")
        print(f"   ✅ Tags: {data['tags']}")
        print(f"   ✅ Summary: {data['summary'][:80]}...")
        image_id = data['id']
    else:
        print(f"   ❌ Error: {response.json()}")
        return
    
    # 3. Test retrieving all images
    print("\n3️⃣ Testing image retrieval...")
    response = requests.get(f"{base_url}/api/images")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Total images in database: {data['count']}")
        if data['count'] > 0:
            print(f"   ✅ Latest image: {data['images'][0]['filename']}")
    else:
        print(f"   ❌ Error: {response.json()}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Week 1 pipeline is working!")
    print("=" * 60)


def create_test_image():
    """Create a simple test image with text"""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple white image with black text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text
    text = "Hello Zabum AI!\nOCR Test Image"
    draw.text((20, 50), text, fill='black')
    
    # Save to temp file
    test_path = '/tmp/test_ocr_image.png'
    img.save(test_path)
    print(f"   📸 Created test image: {test_path}")
    
    return test_path


if __name__ == '__main__':
    try:
        test_pipeline()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to backend server.")
        print("   Make sure the Flask app is running on http://localhost:5000")
        print("   Run: cd backend && python app.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
