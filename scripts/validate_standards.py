#!/usr/bin/env python3
"""
Validation script to check compliance with code standardization patterns.

This script validates that files follow the standardized patterns for:
- Import ordering and grouping
- Error handling patterns
- Sample data usage
- Documentation standards
"""

# Standard library imports
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

def check_import_patterns(file_path: str) -> Dict[str, Any]:
    """Check if a Python file follows standardized import patterns."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find import section
    import_start = None
    import_end = None
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            if import_start is None:
                import_start = i
            import_end = i
    
    if import_start is None:
        return {"status": "no_imports", "issues": []}
    
    import_lines = lines[import_start:import_end + 1]
    issues = []
    
    # Check for shebang and docstring
    has_shebang = lines[0].startswith('#!/usr/bin/env python3')
    has_docstring = '"""' in content[:500]
    
    if not has_shebang:
        issues.append("Missing shebang line")
    if not has_docstring:
        issues.append("Missing module docstring")
    
    # Check for proper grouping (simplified check)
    has_stdlib = any('import ' in line and 'from ' not in line for line in import_lines)
    has_thirdparty = any('httpx' in line or 'streamlit' in line for line in import_lines)
    has_local = any('shared.' in line or 'app.' in line for line in import_lines)
    
    return {
        "status": "checked",
        "has_shebang": has_shebang,
        "has_docstring": has_docstring,
        "has_stdlib": has_stdlib,
        "has_thirdparty": has_thirdparty,
        "has_local": has_local,
        "issues": issues
    }

def check_sample_data_usage(file_path: str) -> Dict[str, Any]:
    """Check if a file uses standardized sample data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for old patterns
    old_patterns = [
        'SAMPLE_TEXTS = {',
        'sample_text = """',
        '"text": "Artificial intelligence is transforming'
    ]
    
    # Check for new patterns
    new_patterns = [
        'from shared.sample_data import',
        'get_sample_text(',
        'STANDARD_SAMPLE_TEXTS'
    ]
    
    has_old_patterns = any(pattern in content for pattern in old_patterns)
    has_new_patterns = any(pattern in content for pattern in new_patterns)
    
    return {
        "has_old_patterns": has_old_patterns,
        "has_new_patterns": has_new_patterns,
        "status": "updated" if has_new_patterns and not has_old_patterns else "needs_update" if has_old_patterns else "no_sample_data"
    }

def check_error_handling(file_path: str) -> Dict[str, Any]:
    """Check if a file uses standardized error handling patterns."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for improved error handling patterns
    good_patterns = [
        'except httpx.TimeoutException:',
        'except httpx.HTTPStatusError',
        'logger.error(',
        'response.raise_for_status()',
        'timeout=30.0'
    ]
    
    # Check for old patterns that should be updated
    old_patterns = [
        'except Exception as e:',
        'print(f"❌'
    ]
    
    has_good_patterns = sum(1 for pattern in good_patterns if pattern in content)
    has_old_patterns = sum(1 for pattern in old_patterns if pattern in content)
    
    return {
        "good_patterns_count": has_good_patterns,
        "old_patterns_count": has_old_patterns,
        "status": "good" if has_good_patterns > 0 else "needs_improvement"
    }

def validate_file(file_path: str) -> Dict[str, Any]:
    """Validate a single Python file against all standards."""
    if not file_path.endswith('.py'):
        return {"status": "skipped", "reason": "not_python"}
    
    if not os.path.exists(file_path):
        return {"status": "error", "reason": "file_not_found"}
    
    try:
        import_check = check_import_patterns(file_path)
        sample_data_check = check_sample_data_usage(file_path)
        error_handling_check = check_error_handling(file_path)
        
        return {
            "status": "validated",
            "imports": import_check,
            "sample_data": sample_data_check,
            "error_handling": error_handling_check
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def main():
    """Main validation function."""
    print("🔍 Code Standards Validation")
    print("=" * 50)
    
    # Files to check
    files_to_check = [
        "examples/basic_usage.py",
        "examples/custom_operation.py",
        "shared/sample_data.py",
        "frontend/app/app.py"
    ]
    
    results = {}
    
    for file_path in files_to_check:
        print(f"\n📁 Checking: {file_path}")
        result = validate_file(file_path)
        results[file_path] = result
        
        if result["status"] == "validated":
            # Import patterns
            imports = result["imports"]
            if imports["status"] == "checked":
                print(f"   ✅ Imports: {len(imports['issues'])} issues")
                for issue in imports["issues"]:
                    print(f"      ⚠️  {issue}")
            
            # Sample data
            sample_data = result["sample_data"]
            if sample_data["status"] == "updated":
                print("   ✅ Sample data: Using standardized patterns")
            elif sample_data["status"] == "needs_update":
                print("   ⚠️  Sample data: Still using old patterns")
            else:
                print("   ℹ️  Sample data: No sample data found")
            
            # Error handling
            error_handling = result["error_handling"]
            if error_handling["status"] == "good":
                print(f"   ✅ Error handling: {error_handling['good_patterns_count']} good patterns found")
            else:
                print("   ⚠️  Error handling: Could be improved")
        
        elif result["status"] == "skipped":
            print(f"   ⏭️  Skipped: {result['reason']}")
        else:
            print(f"   ❌ Error: {result.get('reason', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)
    
    validated_files = [f for f, r in results.items() if r["status"] == "validated"]
    print(f"Files checked: {len(validated_files)}")
    
    # Count files with good patterns
    good_imports = sum(1 for f in validated_files if len(results[f]["imports"]["issues"]) == 0)
    good_sample_data = sum(1 for f in validated_files if results[f]["sample_data"]["status"] == "updated")
    good_error_handling = sum(1 for f in validated_files if results[f]["error_handling"]["status"] == "good")
    
    print(f"✅ Good import patterns: {good_imports}/{len(validated_files)}")
    print(f"✅ Using standardized sample data: {good_sample_data}/{len(validated_files)}")
    print(f"✅ Good error handling: {good_error_handling}/{len(validated_files)}")
    
    if good_imports == len(validated_files) and good_sample_data == len(validated_files):
        print("\n🎉 All files follow standardized patterns!")
    else:
        print("\n💡 Some files need updates to follow all standards.")
        print("   See docs/CODE_STANDARDS.md for guidelines.")

if __name__ == "__main__":
    main() 