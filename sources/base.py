from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class ConfigField:
    """Describes one piece of connector config the dashboard should collect
    from the guild admin (e.g. an API token or a database/space ID)."""
    name: str
    label: str
    secret: bool = False
    required: bool = True
    placeholder: str = ""


class SourceConnector(ABC):
    """Base class for a pluggable knowledge-source connector.

    A connector knows how to authenticate against one external system and
    pull documents from it into the shared vector store. Tenancy stays
    Discord-guild-scoped: each guild configures its own credentials/target
    per source, stored generically in Postgres via `source_config`.
    """

    #: Unique machine name, e.g. "notion", "slack", "confluence", "gdrive".
    source_name: str = ""

    #: Human-readable name shown in the dashboard.
    display_name: str = ""

    #: Fields the dashboard should render a form for, in order.
    config_fields: list[ConfigField] = []

    @abstractmethod
    def sync(self, guild_id: str, config: dict, db, last_synced_at: Optional[datetime]) -> int:
        """Pull new/changed documents for `guild_id` using `config` (the
        connector-specific credentials/target) and upsert them into `db`
        (a database.Database instance) via db.add_message(..., source=self.source_name).

        Should use `last_synced_at` to do an incremental pull where the
        upstream API supports it. Returns the number of documents synced.
        """
        raise NotImplementedError
