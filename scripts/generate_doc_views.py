#!/usr/bin/env python3
"""
Documentation View Generator

Generates alternative views of documentation based on metadata from docs/docs_metadata.json.
Creates DOCS_BY_TOPIC.md and DOCS_BY_AUDIENCE.md files organized by topic_category and audience_level respectively.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load and parse the documentation metadata JSON file."""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file not found at {metadata_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in metadata file: {e}")
        sys.exit(1)


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """Validate that all required metadata keys are present."""
    required_keys = {'title', 'topic_category', 'audience_level', 'description'}
    
    for file_path, data in metadata.items():
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            print(f"Warning: Missing keys in {file_path}: {missing_keys}")


def generate_by_topic(metadata: Dict[str, Any], output_path: Path) -> None:
    """Generate documentation organized by topic category."""
    
    # Group documents by topic category
    by_topic = {}
    for file_path, data in metadata.items():
        topic = data.get('topic_category', 'Unknown').title()
        if topic not in by_topic:
            by_topic[topic] = []
        
        by_topic[topic].append({
            'title': data.get('title', 'Untitled'),
            'path': file_path,
            'description': data.get('description', 'No description available')
        })
    
    # Sort categories and documents within categories
    sorted_topics = sorted(by_topic.keys())
    for topic in sorted_topics:
        by_topic[topic].sort(key=lambda x: x['title'])
    
    # Generate Markdown content
    timestamp = datetime.now().strftime('%Y-%m-%d')
    content = [
        "# Documentation by Topic",
        "",
        "This view organizes all documentation by topic category, providing an alternative navigation structure to help you find content related to specific domains.",
        "",
        f"*Last updated on {timestamp}*",
        ""
    ]
    
    for topic in sorted_topics:
        content.append(f"## {topic}")
        content.append("")
        
        for doc in by_topic[topic]:
            content.append(f"- **[{doc['title']}]({doc['path']})**: {doc['description']}\n")
        
        content.append("")
    
    # Write the file
    write_markdown_file(output_path, content)
    #print(f"Generated {output_path}")


def generate_by_audience(metadata: Dict[str, Any], output_path: Path) -> None:
    """Generate documentation organized by audience level."""
    
    # Group documents by audience level
    by_audience = {}
    audience_order = ['Introductory', 'Intermediate', 'Advanced']
    
    for file_path, data in metadata.items():
        audience = data.get('audience_level', 'Unknown').title()
        if audience not in by_audience:
            by_audience[audience] = []
        
        by_audience[audience].append({
            'title': data.get('title', 'Untitled'),
            'path': file_path,
            'description': data.get('description', 'No description available')
        })
    
    # Sort documents within each audience level
    for audience in by_audience:
        by_audience[audience].sort(key=lambda x: x['title'])
    
    # Generate Markdown content
    timestamp = datetime.now().strftime('%Y-%m-%d')
    content = [
        "# Documentation by Audience Level",
        "",
        "This view organizes all documentation by target audience level, helping you find content appropriate for your experience level.",
        "",
        f"*Last updated on {timestamp}*",
        ""
    ]
    
    # Use predefined order for audience levels, then any additional ones alphabetically
    all_audiences = [a for a in audience_order if a in by_audience]
    additional_audiences = sorted([a for a in by_audience.keys() if a not in audience_order])
    all_audiences.extend(additional_audiences)
    
    for audience in all_audiences:
        content.append(f"## {audience}")
        content.append("")
        
        # Add description for each audience level
        if audience == 'Introductory':
            content.append("*Perfect for getting started with the template and understanding basic concepts.*")
        elif audience == 'Intermediate':
            content.append("*For developers comfortable with the basics who want to dive deeper into specific features.*")
        elif audience == 'Advanced':
            content.append("*For experienced developers implementing production deployments and complex customizations.*")
        content.append("")
        
        for doc in by_audience[audience]:
            content.append(f"- **[{doc['title']}]({doc['path']})**: {doc['description']}\n")
        
        content.append("")
    
    # Write the file
    write_markdown_file(output_path, content)
    #print(f"Generated {output_path}")


def write_markdown_file(output_path: Path, content: List[str]) -> None:
    """Write content to a Markdown file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    except IOError as e:
        print(f"Error writing to {output_path}: {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate the documentation view generation."""
    
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    metadata_path = project_root / 'docs' / 'docs_metadata.json'
    docs_dir = project_root / 'docs'
    
    # Ensure docs directory exists
    docs_dir.mkdir(exist_ok=True)
    
    # Load and validate metadata
    #print("Loading documentation metadata...")
    metadata = load_metadata(metadata_path)
    validate_metadata(metadata)
    
    #print(f"Found {len(metadata)} documents in metadata")
    
    # Generate views
    #print("Generating documentation views...")
    
    # Generate DOCS_BY_TOPIC.md
    topic_output = docs_dir / 'DOCS_BY_TOPIC.md'
    generate_by_topic(metadata, topic_output)
    
    # Generate DOCS_BY_AUDIENCE.md
    audience_output = docs_dir / 'DOCS_BY_AUDIENCE.md'
    generate_by_audience(metadata, audience_output)
    
    #print(f"\nSuccessfully generated documentation views:")
    #print(f"  - {topic_output}")
    #print(f"  - {audience_output}")
    #print(f"\nThese files provide alternative navigation structures for the documentation.")


if __name__ == "__main__":
    main()