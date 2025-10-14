#!/usr/bin/env python3
"""
Add mock_infrastructure_error fixture parameter to functions that use it.
"""

import re

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # List of function names that use mock_infrastructure_error but might not have it as parameter
    functions_needing_fixture = [
        'test_raises_infrastructure_error_when_hash_verification_fails',
        'test_raises_infrastructure_error_when_all_providers_fail',
        'test_raises_infrastructure_error_when_auto_download_disabled_and_model_missing',
        'test_handles_tokenizer_loading_failures_gracefully'
    ]
    
    for func_name in functions_needing_fixture:
        # Find the function signature
        pattern = f'(def {re.escape(func_name)}\\(self, mock_onnx_model_manager)\\):)'
        replacement = f'def {func_name}(self, mock_onnx_model_manager, mock_infrastructure_error):'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"  - Added mock_infrastructure_error parameter to {func_name}")
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed ImportError issues in {file_path}")
        return True
    else:
        print(f"ℹ️  No changes needed in {file_path}")
        return False

if __name__ == '__main__':
    file_path = 'test_onnx_model_manager.py'
    fix_file(file_path)
