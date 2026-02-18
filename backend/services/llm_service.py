"""
LLM Service - Smart tagging and categorization using Ollama
Week 2 implementation
"""

import requests
import json


class LLMService:
    """Service for generating metadata from text using local Ollama LLM"""
    
    def __init__(self, model_name="llama3.2", base_url="http://localhost:11434"):
        """
        Initialize LLM service with Ollama
        
        Args:
            model_name: Ollama model name (e.g., 'llama3.2', 'llama3.2:1b')
            base_url: Ollama API base URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        print(f"🤖 Initializing LLM service with model: {model_name}")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test if Ollama is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Connected to Ollama at {self.base_url}")
            else:
                print(f"⚠️  Ollama responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            print("💡 Make sure Ollama is running: 'ollama serve'")
    
    def generate_metadata(self, text):
        """
        Generate tags, summary, and category from extracted text
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            dict: {
                'tags': list of str,
                'summary': str,
                'category': str
            }
        """
        if not text or len(text.strip()) < 3:
            # Return defaults for empty/minimal text
            return {
                'tags': ['no-text'],
                'summary': 'Image with no readable text',
                'category': 'image'
            }
        
        try:
            # Craft prompt for structured output
            prompt = self._create_prompt(text)
            
            # Call Ollama API
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent output
                    }
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            # Extract generated text
            result = response.json()
            generated_text = result.get('response', '').strip()
            
            # Parse JSON from response
            metadata = self._parse_response(generated_text)
            
            print(f"🏷️  Generated tags: {metadata['tags']}")
            print(f"📝 Category: {metadata['category']}")
            
            return metadata
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Return fallback metadata
            return {
                'tags': ['llm-error', 'auto-tagged'],
                'summary': f"Text excerpt: {text[:100]}...",
                'category': 'unknown'
            }
    
    def _create_prompt(self, text):
        """Create a structured prompt for the LLM"""
        return f"""Analyze this text extracted from a screenshot and generate metadata.

Text: {text}

Generate a JSON response with:
1. "tags": 3-5 relevant keywords (lowercase, hyphen-separated)
2. "summary": One sentence summarizing the content
3. "category": One of [document, code, conversation, receipt, note, diagram, social-media, other]

Respond ONLY with valid JSON, no additional text.

Example format:
{{"tags": ["python", "tutorial", "beginner"], "summary": "A beginner's guide to Python programming", "category": "document"}}

JSON:"""
    
    def _parse_response(self, generated_text):
        """Parse LLM response and extract metadata"""
        try:
            # Try to find JSON in response
            # Sometimes LLM adds extra text, so we extract the JSON block
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = generated_text[start_idx:end_idx]
                metadata = json.loads(json_str)
                
                # Validate and sanitize
                tags = metadata.get('tags', [])
                if isinstance(tags, list) and len(tags) > 0:
                    # Ensure tags are strings and lowercase
                    tags = [str(tag).lower().strip() for tag in tags[:5]]
                else:
                    tags = ['auto-tagged']
                
                summary = str(metadata.get('summary', 'No summary available')).strip()
                category = str(metadata.get('category', 'other')).lower().strip()
                
                return {
                    'tags': tags,
                    'summary': summary,
                    'category': category
                }
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️  Failed to parse LLM response: {e}")
            print(f"Raw response: {generated_text[:200]}")
            
            # Fallback: extract keywords from response
            return {
                'tags': ['parsing-error'],
                'summary': generated_text[:100] if generated_text else 'No summary available',
                'category': 'other'
            }


# Global instance (lazy loading)
_llm_service = None


def get_llm_service():
    """Get or create LLM service instance (singleton)"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
