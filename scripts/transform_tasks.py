#!/usr/bin/env python3
"""
Script to transform tasks.json into tasks.md with a specific format.

Format:
### Task {id}
**{description}**

{details}
"""

import json
import os
from pathlib import Path


def transform_tasks_to_markdown(input_file="tasks/tasks.json", output_file="tasks/tasks.md"):
    """
    Transform tasks.json into tasks.md with the specified format.
    
    Args:
        input_file (str): Path to the input tasks.json file
        output_file (str): Path to the output tasks.md file
    """
    # Get the script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Resolve paths relative to project root
    input_path = project_root / input_file
    output_path = project_root / output_file
    
    # Check if input file exists
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.")
        return False
    
    try:
        # Read and parse the JSON file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract tasks from the JSON structure
        tasks = data.get('tasks', [])
        
        if not tasks:
            print("Warning: No tasks found in the JSON file.")
            return False
        
        # Generate markdown content
        markdown_content = []
        
        for task in tasks:
            # Extract required fields
            task_id = task.get('id', 'Unknown')
            description = task.get('description', 'No description available')
            details = task.get('details', 'No details available')
            
            # Format the task block
            task_block = f"### Task {task_id}\n"
            task_block += f"**{description}**\n\n"
            task_block += f"{details}\n"
            
            markdown_content.append(task_block)
        
        # Join all task blocks with double newlines for separation
        full_content = "\n".join(markdown_content)
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"Successfully transformed {len(tasks)} tasks from '{input_path}' to '{output_path}'")
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{input_path}': {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main function to run the transformation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Transform tasks.json to tasks.md")
    parser.add_argument(
        "--input", 
        default=".taskmaster/tasks/tasks.json",
        help="Input JSON file path (default: tasks/tasks.json)"
    )
    parser.add_argument(
        "--output", 
        default=".taskmaster/docs/tasks.md",
        help="Output markdown file path (default: tasks.md)"
    )
    
    args = parser.parse_args()
    
    success = transform_tasks_to_markdown(args.input, args.output)
    exit(0 if success else 1)


if __name__ == "__main__":
    main() 