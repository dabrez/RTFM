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
        # Support both custom and Railway-standard env vars
        self.host = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "db"))
        self.port = os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))
        self.dbname = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "rtfm_db"))
        self.user = os.getenv("POSTGRES_USER", os.getenv("PGUSER", "rtfm_user"))
        self.password = os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "rtfm_password"))
        self.conn = None
        self._setup_db()

    def _get_conn(self):
        if self.conn is None or self.conn.closed != 0:
            try:
                # If DATABASE_URL is provided, use it directly (Railway often provides this)
                db_url = os.getenv("DATABASE_URL")
                if db_url:
                    self.conn = psycopg2.connect(db_url)
                else:
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
            # Create table with guild_id
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id SERIAL PRIMARY KEY,
                    query_id VARCHAR(50) UNIQUE,
                    question TEXT,
                    response TEXT,
                    username VARCHAR(100),
                    user_id VARCHAR(50),
                    guild_id VARCHAR(50),
                    channel_id VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Ensure guild_id column exists if table was already created without it
            try:
                cur.execute("ALTER TABLE query_history ADD COLUMN IF NOT EXISTS guild_id VARCHAR(50)")
            except Exception:
                pass

    def log_query(self, query_id, question, response, username, user_id, guild_id, channel_id):
        conn = self._get_conn()
        if not conn:
            return
        
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO query_history (query_id, question, response, username, user_id, guild_id, channel_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (query_id) DO NOTHING
                    """,
                    (query_id, question, response, username, user_id, guild_id, channel_id)
                )
            except Exception as e:
                logger.error(f"Error logging query to Postgres: {e}")

class CacheManager:
    """Redis cache manager for AI responses"""
    
    def __init__(self, host=None, port=None, db=0):
        # Support Railway's REDIS_URL or REDISHOST
        redis_url = os.getenv("REDIS_URL")
        host = host or os.getenv("REDISHOST", os.getenv("REDIS_HOST", "redis"))
        port_env = os.getenv("REDISPORT", os.getenv("REDIS_PORT", "6379"))
        port = port or int(port_env)
        
        try:
            if redis_url:
                self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
            else:
                self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
            logger.info(f"Connected to Redis")
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
    def __init__(self, persist_directory=None, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # Default persist directory
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./discord_db")
        
        # Ensure directory exists
        if not os.path.exists(persist_directory):
            try:
                os.makedirs(persist_directory, exist_ok=True)
                logger.info(f"Created directory for ChromaDB: {persist_directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {persist_directory}: {e}")

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        # Initialize Chroma vector database
        self.vector_db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)


    def add_message(self, content, username, guild_id, date):
        metadata = {
            "username": username,
            "guild_id": guild_id,
            "date": date
        }
        self.vector_db.add_texts([content], metadatas=[metadata])


    def query(self, question, guild_id, k=50, min_confidence=0.7, max_results=None):
        """
        Perform a semantic search with normalized confidence and guild filtering.


        Args:
            question (str): Query text.
            guild_id (str): Discord guild ID to filter by.
            k (int): Number of top results to retrieve initially.
            min_confidence (float): Minimum confidence (0-1) to keep a message.
            max_results (int | None): Maximum number of messages to return.


        Returns:
            List of tuples: (content, metadata, confidence)
        """
        # Get top-k results with raw scores, filtered by guild_id
        results_with_scores = self.vector_db.similarity_search_with_score(
            question, 
            k=k,
            filter={"guild_id": guild_id}
        )


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
