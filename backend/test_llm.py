"""
Test script to verify LLM service functionality
"""

from services.llm_service import get_llm_service

def test_llm_service():
    """Test LLM service connection and metadata generation"""
    print("=" * 60)
    print("Testing LLM Service")
    print("=" * 60)
    
    # Initialize service
    try:
        llm = get_llm_service()
        print("✅ LLM service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize LLM service: {e}")
        return False
    
    # Test cases
    test_cases = [
        "Python programming tutorial for beginners",
        "Invoice #12345 - Total: $299.99 - Due: 2024-03-15",
        "def hello_world():\n    print('Hello, World!')",
        "",  # Empty text test
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        try:
            metadata = llm.generate_metadata(text)
            print(f"Tags: {metadata['tags']}")
            print(f"Summary: {metadata['summary']}")
            print(f"Category: {metadata['category']}")
            print("✅ Test passed")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✨")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_llm_service()
