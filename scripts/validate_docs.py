#!/usr/bin/env python3
"""
Documentation validation script for FastAPI-Streamlit-LLM Starter.

This script validates that documentation matches the actual implementation,
including file references, environment variables, code examples, and Docker commands.
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class DocumentationValidator:
    """Main class for validating documentation against implementation."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the validator with project root directory."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        
        # Define file patterns to search for documentation
        self.doc_files = [
            "README.md",
            "docs/*.md",
            "backend/README.md", 
            "frontend/README.md",
            "examples/README.md"
        ]
        
        # Define configuration files to validate
        self.config_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml", 
            "docker-compose.prod.yml",
            "Makefile",
            ".env.example",
            "backend/env.example",
            "backend/app/config.py",
            "frontend/app/config.py"
        ]

    def validate_documentation(self):
        """Main validation function that runs all validation checks."""
        print("🔍 Starting documentation validation...")
        print(f"📁 Project root: {self.project_root}")
        
        try:
            # 1. File Reference Validation
            print("\n📄 Validating file references...")
            self.validate_file_references()
            
            # 2. Environment Variable Validation
            print("\n🔧 Validating environment variables...")
            self.validate_environment_variables()
            
            # 3. Code Example Validation
            print("\n💻 Validating code examples...")
            self.validate_code_examples()
            
            # 4. Docker Command Validation
            print("\n🐳 Validating Docker commands...")
            self.validate_docker_commands()
            
            # 5. API Documentation Consistency
            print("\n🌐 Validating API documentation...")
            self.validate_api_documentation()
            
            # 6. Integration Testing
            print("\n🔗 Validating integration scenarios...")
            self.validate_integration()
            
            # Report results
            self.report_results()
            
        except Exception as e:
            logger.error(f"Validation failed with error: {str(e)}")
            self.errors.append(f"Critical error: {str(e)}")
            self.report_results()
            return False
        
        return len(self.errors) == 0

    def validate_file_references(self):
        """Check that all referenced files exist."""
        print("  📋 Checking file references in documentation...")
        
        # Get all markdown files
        md_files = self._get_markdown_files()
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Extract file references from markdown
                file_refs = self._extract_file_references(content)
                
                for file_ref in file_refs:
                    # Resolve relative paths
                    if file_ref.startswith('./') or file_ref.startswith('../'):
                        full_path = (md_file.parent / file_ref).resolve()
                    else:
                        full_path = (self.project_root / file_ref).resolve()
                    
                    if not full_path.exists():
                        self.errors.append(f"Referenced file not found: {file_ref} (in {md_file.relative_to(self.project_root)})")
                    else:
                        print(f"    ✅ Found: {file_ref}")
                        
            except Exception as e:
                self.warnings.append(f"Could not read {md_file}: {str(e)}")
        
        # Check project structure
        self._validate_project_structure()

    def validate_environment_variables(self):
        """Verify environment variables match across all configuration files."""
        print("  🔧 Checking environment variable consistency...")
        
        # Extract environment variables from different sources
        doc_env_vars = self._extract_env_vars_from_docs()
        config_env_vars = self._extract_env_vars_from_config()
        docker_env_vars = self._extract_env_vars_from_docker()
        example_env_vars = self._extract_env_vars_from_examples()
        
        # Find all unique environment variables
        all_env_vars = set()
        all_env_vars.update(doc_env_vars)
        all_env_vars.update(config_env_vars)
        all_env_vars.update(docker_env_vars)
        all_env_vars.update(example_env_vars)
        
        print(f"    📊 Found {len(all_env_vars)} unique environment variables")
        
        # Check consistency
        for env_var in all_env_vars:
            sources = []
            if env_var in doc_env_vars:
                sources.append("documentation")
            if env_var in config_env_vars:
                sources.append("config files")
            if env_var in docker_env_vars:
                sources.append("docker files")
            if env_var in example_env_vars:
                sources.append("example files")
            
            if len(sources) == 1:
                self.warnings.append(f"Environment variable '{env_var}' only found in: {sources[0]}")
            else:
                print(f"    ✅ {env_var}: found in {', '.join(sources)}")

    def validate_code_examples(self):
        """Test that all code examples work."""
        print("  💻 Validating code examples...")
        
        md_files = self._get_markdown_files()
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                code_blocks = self._extract_code_blocks(content)
                
                for i, (language, code) in enumerate(code_blocks):
                    if language in ['python', 'py']:
                        self._validate_python_code(code, f"{md_file.name}:block_{i}")
                    elif language in ['bash', 'sh', 'shell']:
                        self._validate_shell_code(code, f"{md_file.name}:block_{i}")
                    elif language in ['yaml', 'yml']:
                        self._validate_yaml_code(code, f"{md_file.name}:block_{i}")
                    elif language == 'json':
                        self._validate_json_code(code, f"{md_file.name}:block_{i}")
                        
            except Exception as e:
                self.warnings.append(f"Could not validate code examples in {md_file}: {str(e)}")

    def validate_docker_commands(self):
        """Validate Docker commands and configurations."""
        print("  🐳 Validating Docker configurations...")
        
        # Validate docker-compose files
        compose_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml", 
            "docker-compose.prod.yml"
        ]
        
        for compose_file in compose_files:
            file_path = self.project_root / compose_file
            if file_path.exists():
                self._validate_docker_compose(file_path)
            else:
                self.warnings.append(f"Docker compose file not found: {compose_file}")
        
        # Validate Dockerfiles
        dockerfile_paths = [
            "backend/Dockerfile",
            "frontend/Dockerfile"
        ]
        
        for dockerfile_path in dockerfile_paths:
            file_path = self.project_root / dockerfile_path
            if file_path.exists():
                self._validate_dockerfile(file_path)
            else:
                self.warnings.append(f"Dockerfile not found: {dockerfile_path}")
        
        # Validate Makefile commands
        makefile_path = self.project_root / "Makefile"
        if makefile_path.exists():
            self._validate_makefile(makefile_path)

    def validate_api_documentation(self):
        """Validate API documentation consistency."""
        print("  🌐 Validating API documentation...")
        
        # Check if backend is available for validation
        backend_path = self.project_root / "backend"
        if not backend_path.exists():
            self.warnings.append("Backend directory not found, skipping API validation")
            return
        
        # Extract API endpoints from documentation
        doc_endpoints = self._extract_api_endpoints_from_docs()
        
        # Extract API endpoints from FastAPI code
        code_endpoints = self._extract_api_endpoints_from_code()
        
        # Compare endpoints
        for endpoint in doc_endpoints:
            if endpoint not in code_endpoints:
                self.errors.append(f"Documented API endpoint not found in code: {endpoint}")
            else:
                print(f"    ✅ API endpoint verified: {endpoint}")
        
        # Check for undocumented endpoints
        for endpoint in code_endpoints:
            if endpoint not in doc_endpoints:
                self.warnings.append(f"API endpoint not documented: {endpoint}")

    def validate_integration(self):
        """Test integration scenarios."""
        print("  🔗 Validating integration scenarios...")
        
        # Test example scripts
        examples_dir = self.project_root / "examples"
        if examples_dir.exists():
            for example_file in examples_dir.glob("*.py"):
                self._validate_example_script(example_file)
        
        # Test basic Docker build (if Docker is available)
        if self._is_docker_available():
            self._test_docker_build()
        else:
            self.warnings.append("Docker not available, skipping Docker build tests")

    def _get_markdown_files(self) -> List[Path]:
        """Get all markdown files in the project."""
        md_files = []
        
        # Add specific files
        for pattern in self.doc_files:
            if '*' in pattern:
                md_files.extend(self.project_root.glob(pattern))
            else:
                file_path = self.project_root / pattern
                if file_path.exists():
                    md_files.append(file_path)
        
        return md_files

    def _extract_file_references(self, content: str) -> Set[str]:
        """Extract file references from markdown content."""
        file_refs = set()
        
        # Pattern for markdown links to files
        link_pattern = r'\[.*?\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)
        
        for match in matches:
            # Skip URLs
            if match.startswith(('http://', 'https://', 'mailto:')):
                continue
            # Skip anchors
            if match.startswith('#'):
                continue
            file_refs.add(match)
        
        # Pattern for code blocks with file references
        code_pattern = r'```[a-zA-Z]*:([^\s]+)'
        matches = re.findall(code_pattern, content)
        file_refs.update(matches)
        
        # Pattern for direct file mentions
        file_pattern = r'`([^`]+\.(py|md|yml|yaml|json|txt|sh|dockerfile))`'
        matches = re.findall(file_pattern, content, re.IGNORECASE)
        file_refs.update([match[0] for match in matches])
        
        return file_refs

    def _validate_project_structure(self):
        """Validate the expected project structure."""
        expected_dirs = [
            "backend",
            "frontend", 
            "shared",
            "docs",
            "examples",
            "scripts"
        ]
        
        expected_files = [
            "README.md",
            "docker-compose.yml",
            "Makefile"
        ]
        
        for dir_name in expected_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.errors.append(f"Expected directory not found: {dir_name}")
            else:
                print(f"    ✅ Directory found: {dir_name}")
        
        for file_name in expected_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.errors.append(f"Expected file not found: {file_name}")
            else:
                print(f"    ✅ File found: {file_name}")

    def _extract_env_vars_from_docs(self) -> Set[str]:
        """Extract environment variables mentioned in documentation."""
        env_vars = set()
        md_files = self._get_markdown_files()
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Pattern for environment variables
                patterns = [
                    r'\$\{([A-Z_][A-Z0-9_]*)\}',  # ${VAR_NAME}
                    r'\$([A-Z_][A-Z0-9_]*)',      # $VAR_NAME
                    r'([A-Z_][A-Z0-9_]*)\s*=',   # VAR_NAME=
                    r'`([A-Z_][A-Z0-9_]*)`'       # `VAR_NAME`
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    env_vars.update(matches)
                    
            except Exception as e:
                logger.warning(f"Could not extract env vars from {md_file}: {str(e)}")
        
        return env_vars

    def _extract_env_vars_from_config(self) -> Set[str]:
        """Extract environment variables from configuration files."""
        env_vars = set()
        
        config_files = [
            "backend/app/config.py",
            "frontend/app/config.py"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Pattern for os.getenv calls
                    pattern = r'os\.getenv\(["\']([A-Z_][A-Z0-9_]*)["\']'
                    matches = re.findall(pattern, content)
                    env_vars.update(matches)
                    
                except Exception as e:
                    logger.warning(f"Could not extract env vars from {config_file}: {str(e)}")
        
        return env_vars

    def _extract_env_vars_from_docker(self) -> Set[str]:
        """Extract environment variables from Docker files."""
        env_vars = set()
        
        docker_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml"
        ]
        
        for docker_file in docker_files:
            file_path = self.project_root / docker_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        docker_config = yaml.safe_load(f)
                    
                    # Extract environment variables from services
                    if 'services' in docker_config:
                        for service_name, service_config in docker_config['services'].items():
                            if 'environment' in service_config:
                                env_list = service_config['environment']
                                if isinstance(env_list, list):
                                    for env_item in env_list:
                                        if '=' in env_item:
                                            var_name = env_item.split('=')[0]
                                            env_vars.add(var_name)
                                        else:
                                            env_vars.add(env_item)
                                elif isinstance(env_list, dict):
                                    env_vars.update(env_list.keys())
                    
                except Exception as e:
                    logger.warning(f"Could not extract env vars from {docker_file}: {str(e)}")
        
        return env_vars

    def _extract_env_vars_from_examples(self) -> Set[str]:
        """Extract environment variables from example files."""
        env_vars = set()
        
        example_files = [
            ".env.example",
            "backend/env.example"
        ]
        
        for example_file in example_files:
            file_path = self.project_root / example_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Pattern for env file format
                    pattern = r'^([A-Z_][A-Z0-9_]*)\s*='
                    matches = re.findall(pattern, content, re.MULTILINE)
                    env_vars.update(matches)
                    
                except Exception as e:
                    logger.warning(f"Could not extract env vars from {example_file}: {str(e)}")
        
        return env_vars

    def _extract_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """Extract code blocks from markdown content."""
        code_blocks = []
        
        # Pattern for fenced code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append((language.lower() if language else '', code.strip()))
        
        return code_blocks

    def _validate_python_code(self, code: str, source: str):
        """Validate Python code syntax."""
        try:
            # Skip code blocks that are just examples or incomplete
            if any(skip in code.lower() for skip in ['# example', '# ...', '...', 'your_api_key_here']):
                print(f"    ⏭️  Skipping example code in {source}")
                return
            
            ast.parse(code)
            print(f"    ✅ Python syntax valid in {source}")
            
        except SyntaxError as e:
            self.errors.append(f"Python syntax error in {source}: {str(e)}")
        except Exception as e:
            self.warnings.append(f"Could not validate Python code in {source}: {str(e)}")

    def _validate_shell_code(self, code: str, source: str):
        """Validate shell code syntax."""
        try:
            # Basic validation - check for common shell syntax errors
            lines = code.strip().split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check for unmatched quotes
                if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                    self.warnings.append(f"Possible unmatched quotes in {source} line {i+1}: {line}")
            
            print(f"    ✅ Shell syntax appears valid in {source}")
            
        except Exception as e:
            self.warnings.append(f"Could not validate shell code in {source}: {str(e)}")

    def _validate_yaml_code(self, code: str, source: str):
        """Validate YAML code syntax."""
        try:
            yaml.safe_load(code)
            print(f"    ✅ YAML syntax valid in {source}")
            
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error in {source}: {str(e)}")
        except Exception as e:
            self.warnings.append(f"Could not validate YAML code in {source}: {str(e)}")

    def _validate_json_code(self, code: str, source: str):
        """Validate JSON code syntax."""
        try:
            json.loads(code)
            print(f"    ✅ JSON syntax valid in {source}")
            
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON syntax error in {source}: {str(e)}")
        except Exception as e:
            self.warnings.append(f"Could not validate JSON code in {source}: {str(e)}")

    def _validate_docker_compose(self, file_path: Path):
        """Validate Docker Compose file."""
        try:
            with open(file_path, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            # Basic validation
            if 'services' not in compose_config:
                self.errors.append(f"No services defined in {file_path.name}")
                return
            
            # Check service references
            services = compose_config['services']
            for service_name, service_config in services.items():
                if 'depends_on' in service_config:
                    depends_on = service_config['depends_on']
                    if isinstance(depends_on, list):
                        for dep in depends_on:
                            if dep not in services:
                                self.errors.append(f"Service '{service_name}' depends on undefined service '{dep}' in {file_path.name}")
                    elif isinstance(depends_on, dict):
                        for dep in depends_on.keys():
                            if dep not in services:
                                self.errors.append(f"Service '{service_name}' depends on undefined service '{dep}' in {file_path.name}")
            
            print(f"    ✅ Docker Compose file valid: {file_path.name}")
            
        except yaml.YAMLError as e:
            self.errors.append(f"YAML error in {file_path.name}: {str(e)}")
        except Exception as e:
            self.warnings.append(f"Could not validate {file_path.name}: {str(e)}")

    def _validate_dockerfile(self, file_path: Path):
        """Validate Dockerfile syntax."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            
            valid_instructions = {
                'FROM', 'RUN', 'CMD', 'LABEL', 'EXPOSE', 'ENV', 'ADD', 'COPY',
                'ENTRYPOINT', 'VOLUME', 'USER', 'WORKDIR', 'ARG', 'ONBUILD',
                'STOPSIGNAL', 'HEALTHCHECK', 'SHELL'
            }
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                instruction = line.split()[0].upper()
                if instruction not in valid_instructions:
                    self.warnings.append(f"Unknown Dockerfile instruction '{instruction}' in {file_path.name} line {i+1}")
            
            print(f"    ✅ Dockerfile appears valid: {file_path.name}")
            
        except Exception as e:
            self.warnings.append(f"Could not validate {file_path.name}: {str(e)}")

    def _validate_makefile(self, file_path: Path):
        """Validate Makefile syntax."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Basic validation - check for target definitions
            target_pattern = r'^([a-zA-Z_-]+):\s*'
            targets = re.findall(target_pattern, content, re.MULTILINE)
            
            if not targets:
                self.warnings.append(f"No targets found in {file_path.name}")
            else:
                print(f"    ✅ Makefile valid with {len(targets)} targets: {file_path.name}")
            
        except Exception as e:
            self.warnings.append(f"Could not validate {file_path.name}: {str(e)}")

    def _extract_api_endpoints_from_docs(self) -> Set[str]:
        """Extract API endpoints from documentation."""
        endpoints = set()
        md_files = self._get_markdown_files()
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Pattern for API endpoints
                patterns = [
                    r'`(GET|POST|PUT|DELETE|PATCH)\s+([^`]+)`',
                    r'http://[^/]+(/[^\s)]+)',
                    r'localhost:\d+(/[^\s)]+)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if isinstance(matches[0], tuple) if matches else False:
                        endpoints.update([match[1] if len(match) > 1 else match[0] for match in matches])
                    else:
                        endpoints.update(matches)
                        
            except Exception as e:
                logger.warning(f"Could not extract API endpoints from {md_file}: {str(e)}")
        
        return endpoints

    def _extract_api_endpoints_from_code(self) -> Set[str]:
        """Extract API endpoints from FastAPI code."""
        endpoints = set()
        
        backend_dir = self.project_root / "backend"
        if not backend_dir.exists():
            return endpoints
        
        # Look for Python files with FastAPI routes
        for py_file in backend_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Pattern for FastAPI route decorators
                patterns = [
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    endpoints.update([match[1] for match in matches])
                    
            except Exception as e:
                logger.warning(f"Could not extract API endpoints from {py_file}: {str(e)}")
        
        return endpoints

    def _validate_example_script(self, script_path: Path):
        """Validate an example script."""
        try:
            # Check if it's a Python script
            if script_path.suffix == '.py':
                content = script_path.read_text(encoding='utf-8')
                
                # Check syntax
                ast.parse(content)
                
                # Check for required imports
                if 'import' not in content:
                    self.warnings.append(f"Example script {script_path.name} has no imports")
                
                print(f"    ✅ Example script valid: {script_path.name}")
            
        except SyntaxError as e:
            self.errors.append(f"Syntax error in example script {script_path.name}: {str(e)}")
        except Exception as e:
            self.warnings.append(f"Could not validate example script {script_path.name}: {str(e)}")

    def _is_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _test_docker_build(self):
        """Test Docker build process."""
        try:
            # Test docker-compose config validation
            result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("    ✅ Docker Compose configuration valid")
            else:
                self.errors.append(f"Docker Compose configuration error: {result.stderr}")
                
        except FileNotFoundError:
            self.warnings.append("docker-compose not available for testing")
        except Exception as e:
            self.warnings.append(f"Could not test Docker build: {str(e)}")

    def report_results(self):
        """Report validation results."""
        print(f"\n{'='*60}")
        print("📊 VALIDATION RESULTS")
        print(f"{'='*60}")
        
        if not self.errors and not self.warnings:
            print("🎉 All validations passed! Documentation is consistent with implementation.")
            return
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
            print(f"\n💡 Please fix the above errors to ensure documentation accuracy.")
        else:
            print(f"\n✅ No critical errors found.")
        
        print(f"\n📈 Summary:")
        print(f"  • Errors: {len(self.errors)}")
        print(f"  • Warnings: {len(self.warnings)}")


def validate_documentation():
    """Main validation function."""
    validator = DocumentationValidator()
    success = validator.validate_documentation()
    
    if not success:
        sys.exit(1)
    
    return success


if __name__ == "__main__":
    validate_documentation()
