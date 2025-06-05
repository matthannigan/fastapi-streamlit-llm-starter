#!/usr/bin/env python3
"""
Script to transform tasks.json into tasks.md with a specific format.

Format:
### Task {id}
**{description}**

{details}

#### Subtasks (if any)
"""

import json
import os
from pathlib import Path


def format_item(item, heading_level="##", item_type="Task"):
    """
    Format a task or subtask into markdown.
    
    Args:
        item (dict): Task or subtask data
        heading_level (str): Markdown heading level ("##" for tasks, "###" for subtasks)
        item_type (str): Type label ("Task" or "Subtask")
        
    Returns:
        str: Formatted item markdown
    """
    item_id = item.get('id', 'Unknown')
    title = item.get('title', 'No title available')
    description = item.get('description', 'No description available')
    details = item.get('details', '')
    
    # Start with the heading
    item_block = f"{heading_level} {item_type} {item_id}: {title}\n\n"
    
    # Handle priority/status/dependencies (main tasks only)
    if item_type == "Task":
        priority = item.get('priority', 'unknown')
        status = item.get('status', 'unknown')
        dependencies = item.get('dependencies', [])
        if priority:
            item_block += f"**Priority:** {priority}     "
        if status:
            item_block += f"**Status:** {status}     "
        if dependencies:
            dep_list = ', '.join(map(str, dependencies))
            item_block += f"**Dependencies:** {dep_list}\n\n"
        else:
            item_block += f"**Dependencies:** none\n\n"

    # Add description
    item_block += f"**Description:** {description}\n\n"
    
    # Add details
    if details:
        item_block += f"**Details:** {details}\n\n"
    
    # Add test strategy (main tasks only)
    test_strategy = item.get('testStrategy')
    if test_strategy:
        item_block += f"**Test Strategy:** {test_strategy}\n\n"
    
    return item_block


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
        markdown_content = ["# Tasks\n"]
        total_subtasks = 0
        
        for task in tasks:
            # Format the main task using the unified function
            task_block = format_item(task, heading_level="##", item_type="Task")
            
            # Add subtasks if they exist
            subtasks = task.get('subtasks', [])
            if subtasks:
                task_block += f"**Subtasks ({len(subtasks)}):**\n\n"
                for subtask in subtasks:
                    task_block += format_item(subtask, heading_level="###", item_type="Subtask")
                    total_subtasks += 1
            
            markdown_content.append(task_block)
        
        # Join all task blocks with double newlines for separation
        full_content = "\n".join(markdown_content)
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"Successfully transformed {len(tasks)} tasks and {total_subtasks} subtasks from '{input_path}' to '{output_path}'")
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