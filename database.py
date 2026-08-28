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

            # Per-guild, per-source connector configuration. `config` holds
            # whatever fields that source's connector declares (tokens,
            # database/space IDs, etc.) as JSON so new connectors don't need
            # schema changes.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS source_config (
                    guild_id VARCHAR(50) NOT NULL,
                    source_name VARCHAR(50) NOT NULL,
                    config JSONB NOT NULL,
                    last_synced_at TIMESTAMP,
                    enabled BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (guild_id, source_name)
                )
            """)

    def get_source_configs(self, source_name=None):
        """Return enabled source configs as a list of dicts, optionally
        filtered to a single source_name."""
        conn = self._get_conn()
        if not conn:
            return []

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if source_name:
                cur.execute(
                    "SELECT guild_id, source_name, config, last_synced_at "
                    "FROM source_config WHERE enabled = TRUE AND source_name = %s",
                    (source_name,)
                )
            else:
                cur.execute(
                    "SELECT guild_id, source_name, config, last_synced_at "
                    "FROM source_config WHERE enabled = TRUE"
                )
            return cur.fetchall()

    def get_guild_source_configs(self, guild_id):
        """Return all configured sources (enabled or not) for one guild."""
        conn = self._get_conn()
        if not conn:
            return []

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT guild_id, source_name, config, last_synced_at, enabled "
                "FROM source_config WHERE guild_id = %s",
                (guild_id,)
            )
            return cur.fetchall()

    def upsert_source_config(self, guild_id, source_name, config: dict):
        conn = self._get_conn()
        if not conn:
            return

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO source_config (guild_id, source_name, config)
                VALUES (%s, %s, %s)
                ON CONFLICT (guild_id, source_name) DO UPDATE SET
                    config = EXCLUDED.config,
                    enabled = TRUE
                """,
                (guild_id, source_name, json.dumps(config))
            )

    def update_source_last_synced(self, guild_id, source_name, synced_at):
        conn = self._get_conn()
        if not conn:
            return

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE source_config SET last_synced_at = %s WHERE guild_id = %s AND source_name = %s",
                (synced_at, guild_id, source_name)
            )

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
        
        # We define a custom embedding function to avoid importing from 
        # chromadb.utils.embedding_functions, which can cause issues with 
        # missing dependencies or version mismatches.
        class CustomFastEmbedEmbeddingFunction:
            def __init__(self, model_name):
                try:
                    from fastembed import TextEmbedding
                    self.model = TextEmbedding(model_name=model_name)
                except ImportError as e:
                    logger.error(f"FastEmbed not installed: {e}")
                    raise ImportError(f"FastEmbed not installed: {e}")

            def __call__(self, input):
                # input is a list of strings
                return [e.tolist() for e in self.model.embed(input)]

        self.embedding_fn = None
        
        try:
            # Initialize custom embedding function
            logger.info(f"Initializing Custom FastEmbed with model: {model_name}")
            self.embedding_fn = CustomFastEmbedEmbeddingFunction(model_name=model_name)
            logger.info("FastEmbed initialized successfully")
            
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
        self.collection = self.client.get_or_create_collection(
            name="messages",
            embedding_function=self.embedding_fn
        )

    def add_message(self, content, username, guild_id, date, source="discord", doc_id=None):
        if not self.embedding_fn:
            logger.warning("Attempted to add message but embedding function is not initialized.")
            return

        # Generate a unique ID for the message, or use a caller-provided stable id
        # (e.g. a Notion page id) so re-syncing the same document updates it in place.
        import uuid
        msg_id = doc_id or str(uuid.uuid4())

        metadata = {
            "username": username,
            "guild_id": guild_id,
            "date": date,
            "source": source
        }

        try:
            self.collection.upsert(
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
