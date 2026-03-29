from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import redis
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
import time

logger = logging.getLogger(__name__)

class PostgresDatabase:
    """Postgres database for structured data (query history)"""
    
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "db")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.dbname = os.getenv("POSTGRES_DB", "rtfm_db")
        self.user = os.getenv("POSTGRES_USER", "rtfm_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "rtfm_password")
        self.conn = None
        self._setup_db()

    def _get_conn(self):
        if self.conn is None or self.conn.closed != 0:
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password
                )
                self.conn.autocommit = True
            except Exception as e:
                logger.error(f"Failed to connect to Postgres: {e}")
                return None
        return self.conn

    def _setup_db(self):
        conn = self._get_conn()
        if not conn:
            return
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id SERIAL PRIMARY KEY,
                    query_id VARCHAR(50) UNIQUE,
                    question TEXT,
                    response TEXT,
                    username VARCHAR(100),
                    user_id VARCHAR(50),
                    channel_id VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def log_query(self, query_id, question, response, username, user_id, channel_id):
        conn = self._get_conn()
        if not conn:
            return
        
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO query_history (query_id, question, response, username, user_id, channel_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (query_id) DO NOTHING
                    """,
                    (query_id, question, response, username, user_id, channel_id)
                )
            except Exception as e:
                logger.error(f"Error logging query to Postgres: {e}")

class CacheManager:
    """Redis cache manager for AI responses"""
    
    def __init__(self, host="redis", port=6379, db=0):
        try:
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis = None

    def get_response(self, question: str) -> str:
        if not self.redis:
            return None
        return self.redis.get(f"q:{question}")

    def set_response(self, question: str, response: str, ttl: int = 3600):
        if not self.redis:
            return
        self.redis.set(f"q:{question}", response, ex=ttl)

class Database:
    def __init__(self, persist_directory="./discord_db", model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        # Initialize Chroma vector database
        self.vector_db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)


    def add_message(self, content, username, date):
        metadata = {
            "username": username,
            "date": date
        }
        self.vector_db.add_texts([content], metadatas=[metadata])


    def query(self, question, k=50, min_confidence=0.7, max_results=None):
        """
        Perform a semantic search with normalized confidence.


        Args:
            question (str): Query text.
            k (int): Number of top results to retrieve initially.
            min_confidence (float): Minimum confidence (0-1) to keep a message.
            max_results (int | None): Maximum number of messages to return.


        Returns:
            List of tuples: (content, metadata, confidence)
        """
        # Get top-k results with raw scores
        results_with_scores = self.vector_db.similarity_search_with_score(question, k=k)


        if not results_with_scores:
            return []


        # Extract raw distances/scores
        scores = [score for _, score in results_with_scores]
        min_score, max_score = min(scores), max(scores)


        # Normalize to confidence 0-1 (higher = more similar)
        normalized_results = []
        for doc, score in results_with_scores:
            if max_score - min_score == 0:
                confidence = 1.0  # avoid divide by zero
            else:
                confidence = 1 - (score - min_score) / (max_score - min_score)
            if confidence >= min_confidence:
                normalized_results.append((doc.page_content, doc.metadata, confidence))




        # Optionally limit max results
        if max_results:
            normalized_results = normalized_results[:max_results]


        return normalized_results


# Example usage
if __name__ == "__main__":
    db = Database()
'''    db.add_message("Alex said to meet at 3 PM", "Alex", "2025-10-04")
    db.add_message("Don't forget the meeting tomorrow", "Jamie", "2025-10-03")
    db.add_message("Fuck off", "Jamie", "2025-10-03")


    query_results = db.query("When did Alex say to meet?", k=10, min_confidence=0.5)


    for content, metadata, confidence in query_results:
        print(f"Content: {content}, Metadata: {metadata}, Confidence: {confidence:.7f}")'''
