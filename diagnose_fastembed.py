import os
import sys
import socket
import psutil
import traceback
import logging

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Diagnostics")

def check_network(host="huggingface.co", port=443):
    """Check if the environment can reach Hugging Face."""
    try:
        socket.setdefaulttimeout(5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logger.info(f"✅ Network: Connected to {host}:{port}")
        return True
    except Exception as e:
        logger.error(f"❌ Network: Failed to connect to {host}:{port}. Error: {e}")
        return False

def check_resources():
    """Check available RAM and Disk space."""
    mem = psutil.virtual_memory()
    logger.info(f"📊 Memory: Total={mem.total/1024/1024:.1f}MB, Available={mem.available/1024/1024:.1f}MB")
    
    path = os.getenv("FASTEMBED_CACHE_PATH", "./model_cache")
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"✅ Disk: Created cache directory at {path}")
        except Exception as e:
            logger.error(f"❌ Disk: Failed to create cache directory {path}. Error: {e}")
            return
    
    usage = psutil.disk_usage(path)
    logger.info(f"📊 Disk: Path={path}, Free={usage.free/1024/1024:.1f}MB")
    
    if not os.access(path, os.W_OK):
        logger.error(f"❌ Disk: No write permission for {path}")
    else:
        logger.info(f"✅ Disk: Write permission confirmed for {path}")

def check_fastembed():
    """Attempt to initialize the embedding function and catch detailed errors."""
    try:
        import fastembed
        logger.info(f"✅ Library: FastEmbed version {fastembed.__version__} found")
    except ImportError:
        logger.error("❌ Library: FastEmbed NOT installed")
        return

    try:
        from chromadb.utils.embedding_functions import FastEmbedEmbeddingFunction
        model_name = "BAAI/bge-small-en-v1.5"
        logger.info(f"🔄 Attempting to initialize FastEmbed model '{model_name}'...")
        
        # This is where it usually fails
        ef = FastEmbedEmbeddingFunction(model_name=model_name)
        
        # Test a simple encoding
        test_text = ["Hello world"]
        embeddings = ef(test_text)
        logger.info(f"✅ Success: Model loaded and test encoding successful (dim: {len(embeddings[0])})")
        
    except Exception:
        logger.error("❌ Model Initialization Failed!")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("=== Starting FastEmbed Diagnostics ===")
    check_network()
    check_resources()
    check_fastembed()
    logger.info("=== Diagnostics Complete ===")
