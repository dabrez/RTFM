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
    def __init__(self, persist_directory=None, model_name="BAAI/bge-small-en-v1.5"):
        import chromadb
        self.embedding_fn = None
        
        try:
            # Check if fastembed is installed first
            import fastembed
            from chromadb.utils.embedding_functions import FastEmbedEmbeddingFunction
            
            # Initialize embedding function
            # This may trigger a download on first run
            logger.info(f"Initializing FastEmbed with model: {model_name}")
            self.embedding_fn = FastEmbedEmbeddingFunction(model_name=model_name)
            logger.info("FastEmbed initialized successfully")
            
        except ImportError as e:
            logger.error(f"FastEmbed not installed: {e}")
            raise RuntimeError(f"FastEmbed not installed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize FastEmbed model '{model_name}': {e}")
            raise RuntimeError(f"Failed to initialize FastEmbed model '{model_name}': {e}")

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

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        # Note: If embedding_fn is None, Chroma will use its default (which also requires sentence-transformers)
        # We explicitly pass it to avoid surprises
        self.collection = self.client.get_or_create_collection(
            name="messages",
            embedding_function=self.embedding_fn
        )

    def add_message(self, content, username, guild_id, date):
        if not self.embedding_fn:
            logger.warning("Attempted to add message but embedding function is not initialized.")
            return

        # Generate a unique ID for the message
        import uuid
        msg_id = str(uuid.uuid4())
        
        metadata = {
            "username": username,
            "guild_id": guild_id,
            "date": date
        }
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[msg_id]
            )
        except Exception as e:
            logger.error(f"Error adding message to ChromaDB: {e}")

    def query(self, question, guild_id, k=50, min_confidence=0.7, max_results=None):
        """
        Perform a semantic search with normalized confidence and guild filtering.
        """
        if not self.embedding_fn:
            logger.warning("Attempted to query but embedding function is not initialized.")
            return []

        try:
            # Query ChromaDB directly
            results = self.collection.query(
                query_texts=[question],
                n_results=k,
                where={"guild_id": guild_id}
            )
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

        if not results or not results['documents'][0]:
            return []

        # Extract results
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        # Distances: lower is better (more similar)
        distances = results['distances'][0] if 'distances' in results else [0.0] * len(documents)

        if not distances:
            return []

        # Normalize to confidence 0-1 (higher = more similar)
        # ChromaDB distances for l2 (default) are squared L2. 
        # For simplicity, we'll use a relative normalization within the results
        min_dist, max_dist = min(distances), max(distances)
        
        normalized_results = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            if max_dist - min_dist == 0:
                confidence = 1.0
            else:
                confidence = 1 - (dist - min_dist) / (max_dist - min_dist)
            
            if confidence >= min_confidence:
                normalized_results.append((doc, meta, confidence))

        # Sort by confidence descending
        normalized_results.sort(key=lambda x: x[2], reverse=True)

        if max_results:
            normalized_results = normalized_results[:max_results]

        return normalized_results
