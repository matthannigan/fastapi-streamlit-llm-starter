---
sidebar_label: generate_doc_views
---

# Documentation View Generator

  file_path: `scripts/generate_doc_views.py`

Generates alternative views of documentation based on metadata from docs/docs_metadata.json.
Creates DOCS_BY_TOPIC.md and DOCS_BY_AUDIENCE.md files organized by topic_category and audience_level respectively.

## load_metadata()

```python
def load_metadata(metadata_path: Path) -> Dict[str, Any]:
```

Load and parse the documentation metadata JSON file.

## validate_metadata()

```python
def validate_metadata(metadata: Dict[str, Any]) -> None:
```

Validate that all required metadata keys are present.

## generate_by_topic()

```python
def generate_by_topic(metadata: Dict[str, Any], output_path: Path) -> None:
```

Generate documentation organized by topic category.

## generate_by_audience()

```python
def generate_by_audience(metadata: Dict[str, Any], output_path: Path) -> None:
```

Generate documentation organized by audience level.

## write_markdown_file()

```python
def write_markdown_file(output_path: Path, content: List[str]) -> None:
```

Write content to a Markdown file.

## main()

```python
def main():
```

Main function to orchestrate the documentation view generation.
