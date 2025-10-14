#!/usr/bin/env python3
"""
Fix ImportError issues in test_onnx_model_manager.py.

The tests are importing MockInfrastructureError incorrectly.
MockInfrastructureError should be accessed via fixture, not imported.
"""

import re

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern: Find test functions that have the bad import
    # and fix them to use the fixture instead
    
    # Find all test functions with the import issue
    bad_import_pattern = r'(    def (test_\w+)\(self(?:, [^)]+)?\):.*?)(        import asyncio\s+from \.\.conftest import MockInfrastructureError)'
    
    def fix_import(match):
        func_signature = match.group(1)
        func_name = match.group(2)
        
        # Check if mock_infrastructure_error is already in parameters
        if 'mock_infrastructure_error' in func_signature:
            # Already has fixture, just remove the bad import
            return func_signature + '        import asyncio'
        else:
            # Add fixture parameter
            # Find the function signature line
            sig_match = re.search(r'(    def ' + re.escape(func_name) + r'\()([^)]+)(\):)', func_signature)
            if sig_match:
                before = sig_match.group(1)
                params = sig_match.group(2)
                after = sig_match.group(3)
                
                # Add mock_infrastructure_error to parameters
                new_params = params + ', mock_infrastructure_error'
                new_signature = func_signature.replace(
                    f'{before}{params}{after}',
                    f'{before}{new_params}{after}'
                )
                return new_signature + '        import asyncio'
            else:
                # Fallback: just remove the import
                return func_signature + '        import asyncio'
    
    content = re.sub(bad_import_pattern, fix_import, content, flags=re.DOTALL)
    
    # Now replace all uses of MockInfrastructureError with mock_infrastructure_error
    # But only within test functions that now have the fixture
    
    # Simpler approach: just replace the import line with nothing
    content = re.sub(
        r'        from \.\.conftest import MockInfrastructureError\n',
        '',
        content
    )
    
    # Replace pytest.raises(MockInfrastructureError) with pytest.raises(mock_infrastructure_error)
    content = re.sub(
        r'pytest\.raises\(MockInfrastructureError\)',
        'pytest.raises(mock_infrastructure_error)',
        content
    )
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed ImportError issues in {file_path}")
        
        # Count fixes
        import_removals = original_content.count('from ..conftest import MockInfrastructureError')
        pytest_fixes = len(re.findall(r'pytest\.raises\(mock_infrastructure_error\)', content))
        
        print(f"   - Removed {import_removals} bad import statements")
        print(f"   - Fixed {pytest_fixes} pytest.raises() calls")
        return True
    else:
        print(f"ℹ️  No changes needed in {file_path}")
        return False

if __name__ == '__main__':
    file_path = 'test_onnx_model_manager.py'
    fix_file(file_path)
