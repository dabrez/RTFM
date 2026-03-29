import os
import unittest
import logging
import sys

# Add current directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDatabase(unittest.TestCase):
    def test_database_initialization(self):
        """
        Test that the Database initializes correctly and the embedding model is loaded.
        """
        # Set a temporary directory for ChromaDB
        test_db_dir = "./test_discord_db"
        if os.path.exists(test_db_dir):
            import shutil
            shutil.rmtree(test_db_dir)
        os.makedirs(test_db_dir, exist_ok=True)
        
        try:
            # This should either succeed or raise a RuntimeError
            try:
                db = Database(persist_directory=test_db_dir)
                logger.info("Database initialized successfully in test.")
            except RuntimeError as e:
                self.fail(f"Database failed to initialize with RuntimeError: {e}")
            except Exception as e:
                self.fail(f"Database failed to initialize with unexpected exception: {e}")
            
            # Check if embedding_fn is not None
            self.assertIsNotNone(
                db.embedding_fn, 
                "Embedding function (FastEmbed) was not initialized properly (is None)."
            )
            
            # Try to add a message to verify it works
            db.add_message(
                content="This is a test message.",
                username="test_user",
                guild_id="test_guild",
                date="2024-01-01T00:00:00"
            )
            
            # Try to query the message
            results = db.query(
                question="This is a test message.",
                guild_id="test_guild",
                k=1,
                min_confidence=0.0
            )
            
            self.assertTrue(len(results) > 0, "Query returned no results after adding a message.")
            self.assertEqual(results[0][0], "This is a test message.")
            logger.info("Query test passed.")
            
        finally:
            # Cleanup
            import shutil
            if os.path.exists(test_db_dir):
                shutil.rmtree(test_db_dir)

if __name__ == '__main__':
    unittest.main()
