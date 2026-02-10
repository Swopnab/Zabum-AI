"""
Zabum AI - Main Flask Application
Local-first screenshot knowledge management system
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import uuid
from services.ocr_service import get_ocr_service
from models.database import get_database

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
UPLOAD_FOLDER = '../storage/uploads'
THUMBNAIL_FOLDER = '../storage/thumbnails'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

# Initialize services (lazy loading)
ocr_service = None
database = None


def init_services():
    """Initialize OCR and database services"""
    global ocr_service, database
    if ocr_service is None:
        ocr_service = get_ocr_service()
    if database is None:
        database = get_database()
    return ocr_service, database


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Zabum AI Backend is running!',
        'version': '0.1.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/process', methods=['POST'])
def process_image():
    """
    Main endpoint: Upload image → OCR → LLM tagging → Save to DB
    
    Expected: multipart/form-data with 'image' file
    Returns: JSON with extracted text, tags, summary, etc.
    """
    # Check if file is in request
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {ALLOWED_EXTENSIONS}'}), 400
    
    try:
        # Generate unique ID and filename
        image_id = str(uuid.uuid4())
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{image_id}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save uploaded file
        file.save(filepath)
        
        # Initialize services
        ocr, db = init_services()
        
        # Week 1: Extract text using OCR
        print(f"🔍 Extracting text from {filename}...")
        extracted_text = ocr.extract_text(filepath)
        print(f"✅ Extracted: {extracted_text[:100]}..." if len(extracted_text) > 100 else f"✅ Extracted: {extracted_text}")
        
        # TODO: Week 2 - Implement LLM tagging
        # metadata = llm_service.generate_metadata(extracted_text)
        tags = ["ocr-processed"]
        summary = f"Image contains: {extracted_text[:100]}..." if len(extracted_text) > 100 else f"Image contains: {extracted_text}"
        category = "document" if extracted_text else "image"
        
        # Week 1: Save to database
        db.save_image(image_id, filename, extracted_text, tags, summary, category)
        print(f"💾 Saved to database: {image_id}")
        
        # Return response
        return jsonify({
            'success': True,
            'id': image_id,
            'filename': filename,
            'extracted_text': extracted_text,
            'tags': tags,
            'summary': summary,
            'category': category,
            'created_at': datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images', methods=['GET'])
def get_images():
    """
    Get all processed images
    Returns: JSON array of image metadata
    """
    # Week 1: Fetch from database
    _, db = init_services()
    images = db.get_all_images()
    
    return jsonify({
        'images': images,
        'count': len(images)
    })


@app.route('/api/search', methods=['GET'])
def search_images():
    """
    Search images by query
    Query params: ?q=search_term
    """
    query = request.args.get('q', '')
    
    # TODO: Week 3 - Implement search logic
    return jsonify({
        'query': query,
        'results': [],
        'message': 'Search will be implemented in Week 3'
    })


@app.route('/api/export', methods=['POST'])
def export_markdown():
    """
    Export selected images to Markdown
    Request body: { "image_ids": [...] }
    """
    # TODO: Week 4 - Implement export
    return jsonify({
        'message': 'Export feature coming in Week 4'
    })


if __name__ == '__main__':
    print("🚀 Starting Zabum AI Backend...")
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"🖼️  Thumbnail folder: {os.path.abspath(THUMBNAIL_FOLDER)}")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5001)
