import logging
from datetime import datetime, timezone

from database import Database, PostgresDatabase
from sources.registry import CONNECTORS

logger = logging.getLogger(__name__)


class SourceSyncManager:
    """Periodically pulls every guild's configured external sources
    (Notion, and whatever else gets registered in sources/registry.py)
    into the shared vector store."""

    def __init__(self, db: Database, postgres: PostgresDatabase):
        self.db = db
        self.postgres = postgres

    def sync_all(self):
        """Run one sync pass across every configured guild/source pair.
        Failures in one pair are logged and skipped so they don't block
        the rest."""
        configs = self.postgres.get_source_configs()
        if not configs:
            logger.debug("No source configs found; skipping sync pass.")
            return

        for row in configs:
            guild_id = row["guild_id"]
            source_name = row["source_name"]
            connector = CONNECTORS.get(source_name)

            if not connector:
                logger.warning(f"No connector registered for source '{source_name}' (guild {guild_id}); skipping.")
                continue

            try:
                synced_count = connector.sync(
                    guild_id=guild_id,
                    config=row["config"],
                    db=self.db,
                    last_synced_at=row["last_synced_at"]
                )
                logger.info(f"{source_name} sync for guild {guild_id}: upserted {synced_count} document(s)")
                self.postgres.update_source_last_synced(guild_id, source_name, datetime.now(timezone.utc))
            except Exception as e:
                logger.error(f"{source_name} sync failed for guild {guild_id}: {e}", exc_info=True)
