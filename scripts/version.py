#!/usr/bin/env python3
"""
Version Management Script for Insurance AI PoC
Handles automatic semantic versioning based on commit messages and manual overrides.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class VersionManager:
    """Manages semantic versioning for the Insurance AI PoC project."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.pyproject_path = self.project_root / "pyproject.toml"
        
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        try:
            with open(self.pyproject_path, 'r') as f:
                content = f.read()
                match = re.search(r'version = "([^"]+)"', content)
                if match:
                    return match.group(1)
                else:
                    raise ValueError("Version not found in pyproject.toml")
        except FileNotFoundError:
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
    
    def update_version_in_file(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        with open(self.pyproject_path, 'r') as f:
            content = f.read()
        
        updated_content = re.sub(
            r'version = "[^"]+"',
            f'version = "{new_version}"',
            content
        )
        
        with open(self.pyproject_path, 'w') as f:
            f.write(updated_content)
    
    def get_git_commits_since_tag(self, since_tag: str = None) -> List[str]:
        """Get git commits since the last tag or specified tag."""
        try:
            if since_tag is None:
                # Get last tag
                result = subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    capture_output=True, text=True, check=True
                )
                since_tag = result.stdout.strip()
            
            # Get commits since tag
            result = subprocess.run(
                ["git", "log", f"{since_tag}..HEAD", "--oneline"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            # No tags found, get all commits from last 24 hours
            result = subprocess.run(
                ["git", "log", "--oneline", "--since=1 day ago"],
                capture_output=True, text=True, check=False
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    def determine_version_bump(self, commits: List[str]) -> str:
        """Determine version bump type based on commit messages."""
        commit_text = ' '.join(commits).lower()
        
        # Check for breaking changes
        if any(keyword in commit_text for keyword in ['break', 'breaking', 'major']):
            return 'major'
        
        # Check for new features
        if any(keyword in commit_text for keyword in ['feat', 'feature', 'minor']):
            return 'minor'
        
        # Default to patch
        return 'patch'
    
    def bump_version(self, current_version: str, bump_type: str) -> str:
        """Bump version according to semantic versioning."""
        # Remove any pre-release suffix
        version_core = current_version.split('-')[0]
        major, minor, patch = map(int, version_core.split('.'))
        
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'patch':
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
        
        return f"{major}.{minor}.{patch}"
    
    def create_prerelease_version(self, base_version: str, branch: str) -> str:
        """Create a pre-release version for non-main branches."""
        # Sanitize branch name
        clean_branch = re.sub(r'[^a-zA-Z0-9]', '-', branch)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{base_version}-{clean_branch}.{timestamp}"
    
    def get_changelog(self, since_tag: str = None) -> str:
        """Generate changelog from git commits."""
        commits = self.get_git_commits_since_tag(since_tag)
        if not commits or commits == ['']:
            return "- Initial release"
        
        changelog_lines = []
        for commit in commits[:10]:  # Limit to 10 recent commits
            if commit:
                changelog_lines.append(f"- {commit}")
        
        return '\n'.join(changelog_lines)
    
    def create_version_info(self, version: str, branch: str = "main") -> Dict:
        """Create comprehensive version information."""
        try:
            git_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
        except subprocess.CalledProcessError:
            git_commit = "unknown"
        
        return {
            "version": version,
            "git_commit": git_commit,
            "branch": branch,
            "build_date": datetime.utcnow().isoformat() + "Z",
            "is_release": branch == "main" and not "-" in version,
            "components": ["main", "adk"],
            "features": ["google-adk", "litellm", "openrouter", "monitoring"]
        }


def main():
    """Main CLI interface for version management."""
    parser = argparse.ArgumentParser(description="Insurance AI PoC Version Manager")
    parser.add_argument(
        "--bump", 
        choices=['major', 'minor', 'patch', 'auto'],
        default='auto',
        help="Version bump type (default: auto-detect from commits)"
    )
    parser.add_argument(
        "--branch",
        default="main", 
        help="Current branch name (for pre-release versions)"
    )
    parser.add_argument(
        "--prerelease",
        action="store_true",
        help="Create pre-release version regardless of branch"
    )
    parser.add_argument(
        "--update-file",
        action="store_true",
        help="Update version in pyproject.toml"
    )
    parser.add_argument(
        "--output-format",
        choices=['text', 'json'],
        default='text',
        help="Output format"
    )
    parser.add_argument(
        "--changelog",
        action="store_true",
        help="Generate changelog"
    )
    
    args = parser.parse_args()
    
    try:
        vm = VersionManager()
        current_version = vm.get_current_version()
        
        if args.bump == 'auto':
            commits = vm.get_git_commits_since_tag()
            bump_type = vm.determine_version_bump(commits)
        else:
            bump_type = args.bump
        
        # Calculate new version
        new_version = vm.bump_version(current_version, bump_type)
        
        # Add pre-release suffix if needed
        if args.prerelease or (args.branch != "main" and not args.branch.startswith("v")):
            new_version = vm.create_prerelease_version(new_version, args.branch)
        
        # Update file if requested
        if args.update_file:
            vm.update_version_in_file(new_version)
            print(f"Updated version in pyproject.toml: {current_version} -> {new_version}")
        
        # Generate output
        if args.output_format == 'json':
            version_info = vm.create_version_info(new_version, args.branch)
            if args.changelog:
                version_info['changelog'] = vm.get_changelog()
            print(json.dumps(version_info, indent=2))
        else:
            print(f"Current version: {current_version}")
            print(f"Bump type: {bump_type}")
            print(f"New version: {new_version}")
            print(f"Tag: v{new_version}")
            
            if args.changelog:
                print(f"\nChangelog:")
                print(vm.get_changelog())
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 