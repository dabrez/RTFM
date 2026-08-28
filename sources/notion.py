import logging
from datetime import datetime, timezone
from typing import Optional

from sources.base import SourceConnector, ConfigField

logger = logging.getLogger(__name__)

# Block types whose text we pull into the synced document.
_TEXT_BLOCK_TYPES = (
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item", "to_do",
    "toggle", "quote", "callout"
)


def _rich_text_to_plain(rich_text):
    return "".join(part.get("plain_text", "") for part in rich_text or [])


class NotionConnector(SourceConnector):
    source_name = "notion"
    display_name = "Notion"
    config_fields = [
        ConfigField(name="notion_token", label="Notion Integration Token", secret=True, placeholder="secret_..."),
        ConfigField(name="notion_database_id", label="Notion Database ID", placeholder="e.g. a1b2c3d4..."),
    ]

    def _client(self, token):
        from notion_client import Client
        return Client(auth=token)

    def _extract_page_text(self, client, page):
        page_id = page["id"]
        title = ""
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                title = _rich_text_to_plain(prop.get("title"))
                break

        blocks_text = []
        cursor = None
        while True:
            resp = client.blocks.children.list(block_id=page_id, start_cursor=cursor)
            for block in resp.get("results", []):
                btype = block.get("type")
                if btype in _TEXT_BLOCK_TYPES:
                    text = _rich_text_to_plain(block.get(btype, {}).get("rich_text"))
                    if text:
                        blocks_text.append(text)
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")

        content = title
        if blocks_text:
            content += "\n" + "\n".join(blocks_text)
        return content.strip()

    def sync(self, guild_id: str, config: dict, db, last_synced_at: Optional[datetime]) -> int:
        token = config["notion_token"]
        database_id = config["notion_database_id"]
        client = self._client(token)

        filter_payload = None
        if last_synced_at:
            filter_payload = {
                "timestamp": "last_edited_time",
                "last_edited_time": {"after": last_synced_at.isoformat()}
            }

        cursor = None
        synced_count = 0
        while True:
            query_kwargs = {"database_id": database_id, "start_cursor": cursor}
            if filter_payload:
                query_kwargs["filter"] = filter_payload

            resp = client.databases.query(**query_kwargs)

            for page in resp.get("results", []):
                content = self._extract_page_text(client, page)
                if not content:
                    continue

                created_by = page.get("created_by", {}).get("id", "notion")
                db.add_message(
                    content=content,
                    username=f"notion:{created_by}",
                    guild_id=guild_id,
                    date=page.get("last_edited_time", datetime.now(timezone.utc).isoformat()),
                    source=self.source_name,
                    doc_id=f"notion-{page['id']}"
                )
                synced_count += 1

            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")

        return synced_count
