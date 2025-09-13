---
sidebar_label: transform_tasks
---

# Script to transform tasks.json into tasks.md with a specific format.

  file_path: `scripts/transform_tasks.py`

Format:
### Task {id}
**{description}**

{details}

#### Subtasks (if any)

## format_item()

```python
def format_item(item, heading_level = '##', item_type = 'Task'):
```

Format a task or subtask into markdown.

Args:
    item (dict): Task or subtask data
    heading_level (str): Markdown heading level ("##" for tasks, "###" for subtasks)
    item_type (str): Type label ("Task" or "Subtask")
    
Returns:
    str: Formatted item markdown

## transform_tasks_to_markdown()

```python
def transform_tasks_to_markdown(input_file = 'tasks/tasks.json', output_file = 'tasks/tasks.md'):
```

Transform tasks.json into tasks.md with the specified format.

Args:
    input_file (str): Path to the input tasks.json file
    output_file (str): Path to the output tasks.md file

## main()

```python
def main():
```

Main function to run the transformation.
