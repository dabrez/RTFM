from sources.notion import NotionConnector

# Add new connectors here as they're implemented.
CONNECTORS = {
    connector.source_name: connector
    for connector in [NotionConnector()]
}
