from pathlib import Path

from mercatura.discovery.model import SourceRegistry


def load_source_registry(path: Path) -> SourceRegistry:

    content: str = path.read_text(encoding="utf-8")

    return SourceRegistry.model_validate_json(json_data=content)
