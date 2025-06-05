# Export tasks with subtasks
_Exported on 6/5/2025 at 11:55:09 EDT from Cursor (1.0.0)_

---

**User**

If a task has subtasks, I want to also export those

---

**Cursor**

I'll help you modify the `transform_tasks.py` script to include subtasks in the output. Looking at the current implementation, I can see it processes the main tasks but skips the subtasks array.

Now I'll modify the script to include subtasks. I need to add logic to process the subtasks array and format them as subsections under their parent tasks.

```python
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


def format_subtask(subtask):
    """
    Format a single subtask into markdown.
    
    Args:
        subtask (dict): Subtask data
        
    Returns:
        str: Formatted subtask markdown
    """
    subtask_id = subtask.get('id', 'Unknown')
    title = subtask.get('title', 'No title available')
    description = subtask.get('description', 'No description available')
    status = subtask.get('status', 'No status available')
    details = subtask.get('details', '')
    dependencies = subtask.get('dependencies', [])
    
    # Format the subtask block
    subtask_block = f"### Subtask {subtask_id}: {title}\n\n"
    subtask_block += f"**Status:** {status}\n\n"
    subtask_block += f"**Description:** {description}\n\n"
    
    if details:
        subtask_block += f"**Details:** {details}\n\n"
    
    if dependencies:
        dep_list = ', '.join(map(str, dependencies))
        subtask_block += f"**Dependencies:** {dep_list}\n\n"
    
    return subtask_block


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
        total_subtasks = 0
        
        for task in tasks:
            # Extract required fields
            task_id = task.get('id', 'Unknown')
            title = task.get('title', 'No title available')
            description = task.get('description', 'No description available')
            details = task.get('details', 'No details available')
            testStrategy = task.get('testStrategy', 'No test strategy available')
            priority = task.get('priority', 'No priority available')
            status = task.get('status', 'No status available')
            subtasks = task.get('subtasks', [])
            
            # Format the task block
            task_block = f"## Task {task_id}: {title}\n\n"
            task_block += f"**Priority/Status:** {priority} priority - {status}\n\n"
            task_block += f"**Description:** {description}\n\n"
            task_block += f"**Details:** {details}\n\n"
            task_block += f"**Test Strategy:** {testStrategy}\n\n"
            
            # Add subtasks if they exist
            if subtasks:
                task_block += f"**Subtasks ({len(subtasks)}):**\n\n"
                for subtask in subtasks:
                    task_block += format_subtask(subtask) + "\n"
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
```

Now let's test the updated script to make sure it works correctly with the current tasks.json file:

Perfect! Let's check a portion of the generated markdown file to see how the subtasks are formatted:

Excellent! The updated script is working perfectly. Let's also check another section with subtasks to see the consistent formatting:

Perfect! The updated script is working exactly as intended. Here's a summary of what I've improved:

## Summary of Changes

I've successfully modified the `scripts/transform_tasks.py` script to include subtasks in the output. The key changes include:

### 1. **Added Subtask Formatting Function**
- Created a `format_subtask()` function that handles individual subtask formatting
- Formats subtasks with their ID, title, description, status, details (if present), and dependencies (if present)

### 2. **Enhanced Main Task Processing**
- Modified the main loop to check for subtasks in each task
- Added a counter to track total subtasks processed
- When subtasks exist, they're added under a "**Subtasks (X):**" section

### 3. **Improved Output Structure**
The generated markdown now includes:
- **Main tasks** formatted as `## Task {id}: {title}` 
- **Subtasks** formatted as `### Subtask {id}: {title}` with proper nesting
- **Subtask details** including status, description, details, and dependencies
- **Summary information** showing both task and subtask counts

### 4. **Key Features**
- **Hierarchical structure**: Subtasks are properly nested under their parent tasks
- **Complete information**: All subtask fields are included when present
- **Consistent formatting**: Maintains the same style as main tasks
- **Conditional content**: Only shows details and dependencies if they exist
- **Count tracking**: Reports total number of tasks and subtasks processed

The script now successfully transforms 20 tasks and 23 subtasks from your `tasks.json` file, providing a comprehensive markdown representation that includes all the subtask information you requested.

---

**User**

Can we update the format_subtask() function so that it also works for tasks? There seems to be some duplication of similar code. 

---

**Cursor**

You're absolutely right! There's definitely code duplication between the task formatting logic and the `format_subtask()` function. Let me refactor this to use a single, more flexible function that can handle both tasks and subtasks.

```python
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
    status = item.get('status', 'No status available')
    details = item.get('details', '')
    
    # Start with the heading
    item_block = f"{heading_level} {item_type} {item_id}: {title}\n\n"
    
    # Handle priority/status (main tasks) vs status only (subtasks)
    priority = item.get('priority')
    if priority:
        item_block += f"**Priority/Status:** {priority} priority - {status}\n\n"
    else:
        item_block += f"**Status:** {status}\n\n"
    
    # Add description
    item_block += f"**Description:** {description}\n\n"
    
    # Add details
    if details:
        item_block += f"**Details:** {details}\n\n"
    
    # Add test strategy (main tasks only)
    test_strategy = item.get('testStrategy')
    if test_strategy:
        item_block += f"**Test Strategy:** {test_strategy}\n\n"
    
    # Add dependencies (subtasks only)
    dependencies = item.get('dependencies', [])
    if dependencies:
        dep_list = ', '.join(map(str, dependencies))
        item_block += f"**Dependencies:** {dep_list}\n\n"
    
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
        markdown_content = []
        total_subtasks = 0
        
        for task in tasks:
            # Format the main task using the unified function
            task_block = format_item(task, heading_level="##", item_type="Task")
            
            # Add subtasks if they exist
            subtasks = task.get('subtasks', [])
            if subtasks:
                task_block += f"**Subtasks ({len(subtasks)}):**\n\n"
                for subtask in subtasks:
                    task_block += format_item(subtask, heading_level="###", item_type="Subtask") + "\n"
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
```

Perfect! Now let's test the refactored script to make sure it still works correctly:

Great! Let's verify that the output is still correctly formatted by checking a section with both tasks and subtasks:

I notice there's an issue! The refactored code is now displaying dependencies for main tasks, which wasn't happening before. Let me fix this by ensuring that dependencies are only shown for subtasks:

I can see the issue now. Main tasks do have dependencies arrays in the JSON, and my refactored function is now displaying all dependencies regardless of whether it's a main task or subtask. The original code handled this differently. Let me look at the original behavior and fix this:

I can see the issue now! The current code is showing dependencies for main tasks (like "**Dependencies:** 1, 2" and "**Dependencies:** 5"), which wasn't in the original format. The original code didn't include dependencies for main tasks in the markdown output.

Let me fix this by modifying the logic to only show dependencies for subtasks, not for main tasks:

```python
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
    status = item.get('status', 'No status available')
    details = item.get('details', '')
    
    # Start with the heading
    item_block = f"{heading_level} {item_type} {item_id}: {title}\n\n"
    
    # Handle priority/status (main tasks) vs status only (subtasks)
    priority = item.get('priority')
    if priority:
        item_block += f"**Priority/Status:** {priority} priority - {status}\n\n"
    else:
        item_block += f"**Status:** {status}\n\n"
    
    # Add description
    item_block += f"**Description:** {description}\n\n"
    
    # Add details
    if details:
        item_block += f"**Details:** {details}\n\n"
    
    # Add test strategy (main tasks only)
    test_strategy = item.get('testStrategy')
    if test_strategy:
        item_block += f"**Test Strategy:** {test_strategy}\n\n"
    
    # Add dependencies (subtasks only)
    dependencies = item.get('dependencies', [])
    if dependencies and item_type == "Subtask":
        dep_list = ', '.join(map(str, dependencies))
        item_block += f"**Dependencies:** {dep_list}\n\n"
    
    return item_block
```

Now let's test the script again to ensure it produces the correct output:

Let's verify that the fix worked by checking the output:

Perfect! Let me also check a subtask that has dependencies to make sure those are still showing correctly:

Excellent! The refactoring is working perfectly now. Let me summarize what has been successfully accomplished:

## ✅ Refactoring Complete - Summary

I have successfully refactored the `transform_tasks.py` script to eliminate code duplication while maintaining the correct behavior. Here's what was accomplished:

### 🔧 **Key Changes Made**

1. **Unified Function**: Replaced the separate `format_subtask()` function with a single, flexible `format_item()` function that handles both tasks and subtasks.

2. **Parameterized Formatting**: The new function accepts parameters for:
   - `heading_level` ("##" for tasks, "###" for subtasks)
   - `item_type` ("Task" or "Subtask")

3. **Smart Field Handling**: The function intelligently handles different fields based on context:
   - **Priority**: Only shown for main tasks (e.g., "high priority - done")
   - **Status**: Shown for subtasks (e.g., "done")
   - **Test Strategy**: Only included for main tasks
   - **Dependencies**: Only shown for subtasks (fixed to match original behavior)

### 🎯 **Benefits Achieved**

- ✅ **Eliminated Code Duplication**: Single function handles both tasks and subtasks
- ✅ **Maintained Original Behavior**: Dependencies only show for subtasks, not main tasks
- ✅ **Improved Maintainability**: Changes need to be made in only one place
- ✅ **Cleaner Code Structure**: More logical and easier to understand
- ✅ **Same Output Quality**: 20 tasks and 23 subtasks processed correctly

### 📋 **Verification Results**

The script now produces the exact same output as before but with much cleaner, more maintainable code:
- **Main tasks**: Show priority/status, description, details, test strategy (no dependencies)
- **Subtasks**: Show status, description, details, dependencies (no test strategy)
- **Hierarchical structure**: Properly nested with correct markdown heading levels
- **Complete information**: All relevant fields included when present

The refactoring successfully addresses your request to eliminate duplication while preserving all functionality!

