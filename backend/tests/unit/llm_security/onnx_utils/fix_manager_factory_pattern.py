#!/usr/bin/env python3
"""
Fix MockONNXModelManager factory fixture usage in test_onnx_model_manager.py.

The fixture returns a factory function that creates instances, so the correct pattern is:
    def test_something(self, mock_onnx_model_manager):
        manager = mock_onnx_model_manager()  # Direct call to factory

NOT:
    manager_factory = mock_onnx_model_manager()
    manager = manager_factory()
"""

import re

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Fix functions that have NO fixture parameter but use mock_onnx_model_manager
    # Find all functions that use mock_onnx_model_manager but don't have it as parameter
    
    # Split into functions
    function_pattern = r'(    def (test_\w+)\(self(?:, [^)]+)?\):[^}]+?(?=\n    def |\nclass |\Z))'
    
    functions = list(re.finditer(function_pattern, content, re.DOTALL))
    
    fixes_made = []
    
    for match in functions:
        func_content = match.group(1)
        func_name = match.group(2)
        func_start = match.start(1)
        
        # Check if function uses mock_onnx_model_manager
        if 'mock_onnx_model_manager' in func_content:
            # Check if it's already in the parameters
            signature_match = re.search(r'def ' + re.escape(func_name) + r'\(([^)]+)\):', func_content)
            if signature_match:
                params = signature_match.group(1)
                
                # If mock_onnx_model_manager is NOT in parameters, add it
                if 'mock_onnx_model_manager' not in params:
                    # Add the fixture parameter
                    if params == 'self':
                        new_params = 'self, mock_onnx_model_manager'
                    else:
                        new_params = params + ', mock_onnx_model_manager'
                    
                    old_signature = f'def {func_name}({params}):'
                    new_signature = f'def {func_name}({new_params}):'
                    
                    content = content.replace(old_signature, new_signature, 1)
                    fixes_made.append(f"Added mock_onnx_model_manager parameter to {func_name}")
    
    # Pattern 2: Fix the double-call pattern
    # Replace: manager_factory = mock_onnx_model_manager()
    #          manager = manager_factory(...)
    # With:    manager = mock_onnx_model_manager(...)
    
    # Find all occurrences of the pattern
    double_call_pattern = r'(\s+)manager_factory = mock_onnx_model_manager\(\)\s+manager = manager_factory\(([^)]*)\)'
    
    def replace_double_call(match):
        indent = match.group(1)
        args = match.group(2)
        fixes_made.append(f"Fixed double-call pattern with args: {args}")
        return f'{indent}manager = mock_onnx_model_manager({args})'
    
    content = re.sub(double_call_pattern, replace_double_call, content)
    
    # Pattern 3: Fix standalone manager_factory = ... lines that weren't caught
    # This handles cases where the manager_factory assignment is on its own line
    standalone_factory_pattern = r'(\s+)manager_factory = mock_onnx_model_manager\(\)'
    
    def replace_standalone(match):
        # Only replace if not already handled by double-call pattern
        indent = match.group(1)
        fixes_made.append("Fixed standalone manager_factory assignment")
        return f'{indent}manager_factory = mock_onnx_model_manager'
    
    content = re.sub(standalone_factory_pattern, replace_standalone, content)
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed {len(fixes_made)} issues in {file_path}")
        for fix in fixes_made[:10]:  # Show first 10 fixes
            print(f"   - {fix}")
        if len(fixes_made) > 10:
            print(f"   ... and {len(fixes_made) - 10} more")
        return True
    else:
        print(f"ℹ️  No changes needed in {file_path}")
        return False

if __name__ == '__main__':
    file_path = 'test_onnx_model_manager.py'
    fix_file(file_path)
