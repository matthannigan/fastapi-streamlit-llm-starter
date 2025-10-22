#!/usr/bin/env python3
"""
Query tool for integration test seams manifest.

Usage:
    python seams_query.py --status IMPLEMENTED
    python seams_query.py --tag cache --tag security
    python seams_query.py --component AIResponseCache
    python seams_query.py --depends-on resilience-api-circuit-breaker
    python seams_query.py --summary
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any

def load_manifest() -> Dict[str, Any]:
    """Load seams manifest."""
    path = Path(__file__).parent / "seams_manifest.yaml"
    with open(path) as f:
        return yaml.safe_load(f)

def query_by_status(manifest: Dict, status: str) -> List[Dict]:
    """Find all seams with given status."""
    return [s for s in manifest['seams'] if s['status'] == status]

def query_by_tags(manifest: Dict, tags: List[str]) -> List[Dict]:
    """Find seams matching ALL given tags."""
    return [
        s for s in manifest['seams']
        if all(tag in s.get('tags', []) for tag in tags)
    ]

def query_by_component(manifest: Dict, component: str) -> List[Dict]:
    """Find seams involving a component."""
    return [
        s for s in manifest['seams']
        if component in s.get('components', [])
    ]

def query_depends_on(manifest: Dict, seam_id: str) -> List[Dict]:
    """Find seams that depend on given seam."""
    return [
        s for s in manifest['seams']
        if seam_id in s.get('depends_on', [])
    ]

def print_summary(manifest: Dict):
    """Print manifest summary."""
    seams = manifest['seams']
    statuses = {}
    for seam in seams:
        status = seam['status']
        statuses[status] = statuses.get(status, 0) + 1

    print("Integration Test Seams Summary")
    print("=" * 50)
    print(f"Total seams: {len(seams)}")
    print("\nBy Status:")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")

    # Coverage by area
    areas = {}
    for seam in seams:
        area = seam['id'].split('-')[0]
        areas[area] = areas.get(area, 0) + 1

    print("\nBy Area:")
    for area, count in sorted(areas.items()):
        print(f"  {area}: {count}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Query integration test seams')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--tag', action='append', help='Filter by tag')
    parser.add_argument('--component', help='Filter by component')
    parser.add_argument('--depends-on', help='Find dependents of seam')
    parser.add_argument('--summary', action='store_true', help='Print summary')

    args = parser.parse_args()
    manifest = load_manifest()

    if args.summary:
        print_summary(manifest)
    elif args.status:
        results = query_by_status(manifest, args.status)
        for seam in results:
            print(f"{seam['id']}: {seam['description']}")
    elif args.tag:
        results = query_by_tags(manifest, args.tag)
        for seam in results:
            print(f"{seam['id']}: {seam['description']}")
    elif args.component:
        results = query_by_component(manifest, args.component)
        for seam in results:
            print(f"{seam['id']}: {seam['description']}")
    elif args.depends_on:
        results = query_depends_on(manifest, args.depends_on)
        for seam in results:
            print(f"{seam['id']}: {seam['description']}")
