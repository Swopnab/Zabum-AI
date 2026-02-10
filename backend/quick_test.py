"""
Simple test to verify upload and database without waiting for OCR model download
"""

import requests
from PIL import Image

# Create a simple test image
img = Image.new('RGB', (100, 100), color='white')
img.save('/tmp/quick_test.png')

# Test upload
with open('/tmp/quick_test.png', 'rb') as f:
    files = {'image': ('test.png', f, 'image/png')}
    response = requests.post('http://localhost:5001/api/process', files=files, timeout=120)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Check database
response = requests.get('http://localhost:5001/api/images')
print(f"\nDatabase has {response.json()['count']} images")
