#!/usr/bin/env python3
"""
Poetry Dependency Maintenance and Security Scanning Script

This script provides automated Poetry maintenance operations including:
- Security scanning with pip-audit
- Dependency updates and conflict resolution
- Poetry lock file maintenance
- Cross-component dependency validation
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import json


class PoetryMaintenance:
    """Poetry maintenance and security operations."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.components = ["backend", "frontend", "shared"]

    def run_command(self, cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        working_dir = cwd or self.project_root
        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            print(f"❌ Command failed: {' '.join(cmd)}")
            print(f"Error: {e}")
            sys.exit(1)

    def check_poetry_installations(self) -> bool:
        """Verify Poetry is properly configured in all components."""
        print("🔍 Checking Poetry installations...")

        for component in self.components:
            component_path = self.project_root / component
            if not component_path.exists():
                print(f"❌ Component directory not found: {component}")
                return False

            pyproject_path = component_path / "pyproject.toml"
            if not pyproject_path.exists():
                print(f"❌ pyproject.toml not found in {component}")
                return False

            # Check Poetry lock file
            lock_path = component_path / "poetry.lock"
            if not lock_path.exists():
                print(f"⚠️  poetry.lock not found in {component}, running poetry install...")
                result = self.run_command(["poetry", "install"], cwd=component_path)
                if result.returncode != 0:
                    print(f"❌ Poetry install failed in {component}")
                    return False

            print(f"✅ {component}: Poetry configured correctly")

        return True

    def security_scan(self) -> Dict[str, Any]:
        """Run security scanning on all components."""
        print("\n🔒 Running security scans...")
        results = {}

        for component in self.components:
            print(f"Scanning {component}...")
            component_path = self.project_root / component

            # Export requirements for scanning
            export_cmd = ["poetry", "export", "--format=requirements.txt", "--output=/tmp/scan-requirements.txt"]
            result = self.run_command(export_cmd, cwd=component_path)

            if result.returncode != 0:
                print(f"❌ Failed to export requirements for {component}")
                results[component] = {"status": "export_failed", "error": result.stderr}
                continue

            # Run pip-audit using Poetry environment (skip editable packages)
            component_path = self.project_root / component
            audit_cmd = [
                "poetry", "run", "pip-audit",
                "-r", "/tmp/scan-requirements.txt",
                "--skip-editable"
            ]

            audit_result = self.run_command(audit_cmd, cwd=component_path)

            if audit_result.returncode == 0:
                results[component] = {"status": "clean", "vulnerabilities": 0}
                print(f"✅ {component}: No vulnerabilities found")
            else:
                # Parse vulnerabilities from output
                vuln_count = audit_result.stdout.count("VULNERABILITY")
                results[component] = {
                    "status": "vulnerabilities_found",
                    "vulnerabilities": vuln_count,
                    "details": audit_result.stdout
                }
                print(f"⚠️  {component}: {vuln_count} vulnerabilities found")

        return results

    def update_dependencies(self) -> bool:
        """Update dependencies in all components."""
        print("\n📦 Updating dependencies...")

        for component in self.components:
            print(f"Updating {component}...")
            component_path = self.project_root / component

            # Run poetry update
            result = self.run_command(["poetry", "update"], cwd=component_path)

            if result.returncode != 0:
                print(f"❌ Failed to update dependencies in {component}")
                print(f"Error: {result.stderr}")
                return False

            print(f"✅ {component}: Dependencies updated successfully")

        return True

    def validate_cross_component_compatibility(self) -> bool:
        """Validate that components can work together."""
        print("\n🔗 Validating cross-component compatibility...")

        # Check shared library version consistency
        backend_path = self.project_root / "backend"
        frontend_path = self.project_root / "frontend"

        # Check that backend and frontend both reference the same shared library
        for component_name, component_path in [("backend", backend_path), ("frontend", frontend_path)]:
            result = self.run_command(["poetry", "show", "my-project-shared-lib"], cwd=component_path)

            if result.returncode != 0:
                print(f"❌ {component_name}: Shared library not found in dependencies")
                return False

            print(f"✅ {component_name}: Shared library dependency validated")

        return True

    def maintenance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive maintenance report."""
        print("\n📊 Generating maintenance report...")

        report = {
            "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            "poetry_installations": self.check_poetry_installations(),
            "security_scan": self.security_scan(),
            "cross_component_compatibility": self.validate_cross_component_compatibility()
        }

        return report


def main():
    """Main maintenance script execution."""
    project_root = Path(__file__).parent.parent
    maintenance = PoetryMaintenance(project_root)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "security-scan":
            results = maintenance.security_scan()
            print(f"\n📋 Security scan results: {json.dumps(results, indent=2)}")

        elif command == "update":
            if maintenance.update_dependencies():
                print("\n✅ All dependencies updated successfully")
            else:
                print("\n❌ Dependency update failed")
                sys.exit(1)

        elif command == "validate":
            if maintenance.validate_cross_component_compatibility():
                print("\n✅ Cross-component compatibility validated")
            else:
                print("\n❌ Cross-component compatibility issues found")
                sys.exit(1)

        elif command == "report":
            report = maintenance.maintenance_report()
            print(f"\n📋 Maintenance report: {json.dumps(report, indent=2)}")

        else:
            print(f"Unknown command: {command}")
            print("Available commands: security-scan, update, validate, report")
            sys.exit(1)
    else:
        # Run full maintenance check
        report = maintenance.maintenance_report()

        # Determine overall status
        if (report["poetry_installations"] and
            report["cross_component_compatibility"] and
            all(comp["status"] == "clean" for comp in report["security_scan"].values())):
            print("\n🎉 All maintenance checks passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some maintenance issues found. Check the report above.")
            sys.exit(1)


if __name__ == "__main__":
    main()