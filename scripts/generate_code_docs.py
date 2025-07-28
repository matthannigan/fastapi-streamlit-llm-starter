import ast
import re
import argparse
import shutil
from pathlib import Path

def extract_module_docstring(file_path):
    """
    Extracts the module-level docstring from a Python file.

    Args:
        file_path (str or Path): The path to the Python file.

    Returns:
        str: The module docstring, or an empty string if not found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        return ast.get_docstring(tree) or ""
    except (IOError, SyntaxError) as e:
        print(f"Error reading or parsing {file_path}: {e}")
        return ""
    
def analyze_section_header(line):
    """
    Analyze a section header line for word patterns.
    
    Args:
        line: The line to analyze
        
    Returns:
        dict: Analysis results with word counts
    """
    # Regex patterns
    word_count_pattern = re.compile(r'\b\w+\b')
    capital_word_pattern = re.compile(r'\b[A-Z]\w*\b')
    
    # Remove non-alphabetic characters for word counting
    text_without_colon = re.sub(r'[^A-Za-z]', ' ', line).strip()
    
    # Count words
    total_words = len(word_count_pattern.findall(text_without_colon))
    capital_words = len(capital_word_pattern.findall(text_without_colon))
    
    return {
        'total_words': total_words,
        'capital_words': capital_words,
        'capital_ratio': capital_words / total_words if total_words > 0 else 0
    }


def parse_google_docstring(docstring, file_path):
    """
    Parses a Google-style docstring and converts it to Markdown.

    This is a simplified parser that handles common sections.
    It may need to be extended for more complex docstrings.

    Args:
        docstring (str): The Google-style docstring.

    Returns:
        str: The docstring converted to Markdown format.
    """
    if not docstring:
        return ""

    lines = docstring.strip().split('\n')
    
    # The first line is the title
    title = lines[0].strip()
    markdown_parts = [f"# {title}\n\n  file_path: `{file_path}`\n"]
    
    body_lines = lines[1:]
    
    # Regex to identify section headers with indentation (e.g., "Args:", "Returns:")
    # Captures indentation and section title: (indentation, title)
    section_header_pattern = re.compile(r'^(\s*)([A-Za-z\s&\-\(\)]+):$')

    # Regex to identify REPL-style code example
    code_pattern = r'^(>>> |>>>|\.\.\. )'
    
    in_code_block = False
    code_block_lang = ""
    
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        stripped_line = line.strip()

        # Look for section headers, test for capital words ratio
        header_match = section_header_pattern.match(line)  # Use original line with indentation
        if header_match:
            header_analysis = analyze_section_header(header_match.group(2).strip())
            if header_analysis['capital_ratio'] < 0.5:
                header_match = False

        # Look for REPL-style code examples
        code_match = re.match(code_pattern, stripped_line) 

        # If we're in a code block, and the line is not a code example, close the code block
        if in_code_block and not code_match:
            in_code_block = False
            markdown_parts.append(f"```\n")
            i += 1
            continue
        
        # If we're in a section header, add the heading to the markdown
        if header_match:
            indentation = header_match.group(1)  # Captured indentation
            section_title = header_match.group(2).strip()  # Captured section title
            
            # Calculate heading level: no indent=H2, 4 spaces=H3, 8 spaces=H4, etc.
            heading_level = 2 + (len(indentation) // 4)
            heading_prefix = "#" * heading_level
            
            markdown_parts.append(f"\n{heading_prefix} {section_title}\n\n")
            i += 1
        # If we're in a code block, add the line to the markdown
        elif code_match:
            if in_code_block == False:
                in_code_block = True
                code_block_lang = 'python'
                markdown_parts.append(f"```{code_block_lang}\n")
            line_to_add = re.sub(code_pattern, '', stripped_line)
            markdown_parts.append(line_to_add + '\n')
            i += 1
        # If we're in a list, standardize to use '- ' format
        elif stripped_line.startswith('* ') or stripped_line.startswith('- '):
            # Convert '* ' to '- ' for standardization
            standardized_line = re.sub(r'^\* ', '- ', stripped_line)
            
            # Special handling for API endpoints: wrap HTTP method and path in backticks
            # Pattern: "- GET /path: description" -> "- `GET /path`: description"
            api_endpoint_pattern = r'^- (GET|POST)\s+([^:]+):\s*(.*)$'
            api_match = re.match(api_endpoint_pattern, standardized_line)
            if api_match:
                method = api_match.group(1)
                path = api_match.group(2).strip()
                description = api_match.group(3)
                standardized_line = f"- `{method} {path}`: {description}"
            
            # Special handling for environment variables: wrap variable names in backticks
            # Pattern: "- VARIABLE_NAME: description" -> "- `VARIABLE_NAME`: description"
            env_var_pattern = r'^- ([A-Z][A-Z0-9_]*): (.*)$'
            env_match = re.match(env_var_pattern, standardized_line)
            if env_match:
                var_name = env_match.group(1)
                description = env_match.group(2)
                standardized_line = f"- `{var_name}`: {description}"
            
            markdown_parts.append(standardized_line + '\n')
            i += 1
        # If we're not in a code block or section header, add the line to the markdown
        else:
            markdown_parts.append(stripped_line + '\n')
            i += 1
            
    # Join all parts and clean up triple+ newlines
    result = "".join(markdown_parts)
    
    # Replace any sequence of 3+ newlines with exactly 2 newlines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


def process_files(source_dir, output_dir):
    """
    Walks through the source directory, finds .py files, extracts their
    docstrings, converts them to Markdown, and saves them to the output directory.
    Also copies any README.md files found to preserve documentation structure.

    Args:
        source_dir (str or Path): The directory to search for .py files and README.md files.
        output_dir (str or Path): The directory to save the .md files.
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    if not source_path.is_dir():
        print(f"Error: Source directory '{source_dir}' not found.")
        return

    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Searching for .py files in '{source_path.resolve()}'...")

    for py_file in source_path.rglob('*.py'):
        print(f"Processing '{py_file}'...")
        
        docstring = extract_module_docstring(py_file)
        
        if not docstring:
            print(f"  -> No module docstring found. Skipping.")
            continue
            
        markdown_content = parse_google_docstring(docstring, py_file)
        
        # Create a corresponding path in the output directory
        relative_path = py_file.relative_to(source_path)
        md_file_path = output_path / relative_path.with_suffix('.md')
        
        # Ensure the parent directory for the markdown file exists
        md_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"  -> Successfully created '{md_file_path}'")
        except IOError as e:
            print(f"  -> Error writing to file '{md_file_path}': {e}")
    
    # Process README.md files
    print(f"Searching for README.md files in '{source_path.resolve()}'...")
    
    for readme_file in source_path.rglob('README.md'):
        print(f"Copying '{readme_file}'...")
        
        # Create a corresponding path in the output directory
        relative_path = readme_file.relative_to(source_path)
        output_readme_path = output_path / relative_path
        
        # Ensure the parent directory for the README file exists
        output_readme_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(readme_file, output_readme_path)
            print(f"  -> Successfully copied to '{output_readme_path}'")
        except IOError as e:
            print(f"  -> Error copying file to '{output_readme_path}': {e}")

def main():
    """Main function to run the script from the command line."""
    parser = argparse.ArgumentParser(
        description="Convert Python module docstrings from Google format to Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "source_dir",
        help="The source directory containing Python files."
    )
    parser.add_argument(
        "output_dir",
        help="The output directory where Markdown files will be saved."
    )
    
    args = parser.parse_args()
    
    process_files(args.source_dir, args.output_dir)

if __name__ == '__main__':
    # Example usage:
    # python your_script_name.py ./backend/app ./docs/code_ref
    main()
