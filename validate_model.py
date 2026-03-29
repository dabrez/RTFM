import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validate_model")

def validate():
    print("Validating embedding model...")
    try:
        # Import after setting up environment if needed
        from database import Database
        
        # Initialize Database (this will raise an exception if it fails now)
        # Use a temporary directory
        db = Database(persist_directory="/tmp/test_chroma")
        
        if db.embedding_fn is None:
            print("ERROR: Embedding function is None")
            sys.exit(1)
            
        print("SUCCESS: Embedding model loaded successfully")
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: Failed to validate embedding model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    validate()
