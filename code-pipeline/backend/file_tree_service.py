"""
File Tree Service - Build and serve project file tree with git integration

Features:
- Hierarchical file tree generation
- Git status integration (modified, staged, untracked, etc.)
- Efficient caching and incremental updates
- Ignore patterns (.gitignore, .dockerignore, etc.)
- File metadata (size, permissions, timestamps)
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileTreeService:
    """Generates and maintains file tree for a workspace"""

    # Default ignore patterns
    DEFAULT_IGNORE_PATTERNS = {
        # Version control
        ".git",
        ".svn",
        ".hg",
        # Dependencies
        "node_modules",
        "vendor",
        "bower_components",
        # Build outputs
        "dist",
        "build",
        "out",
        "target",
        "bin",
        "obj",
        # Python
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        "env",
        ".env",
        # IDE
        ".vscode",
        ".idea",
        "*.swp",
        "*.swo",
        ".DS_Store",
        # Logs
        "*.log",
        "logs",
        # Misc
        ".cache",
        "tmp",
        "temp",
    }

    def __init__(self, workspace_path: str, max_depth: int = 10):
        """
        Initialize file tree service

        Args:
            workspace_path: Root directory path
            max_depth: Maximum directory traversal depth
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.max_depth = max_depth
        self.git_repo = self._init_git_repo()
        self.ignore_patterns = self._load_ignore_patterns()

    def _init_git_repo(self) -> Optional[Path]:
        """
        Initialize git repository path if workspace is a git repo

        Returns:
            Path to .git directory or None
        """
        current = self.workspace_path
        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                logger.info(f"Found git repository at {current}")
                return current
            current = current.parent
        logger.info("No git repository found")
        return None

    def _load_ignore_patterns(self) -> Set[str]:
        """
        Load ignore patterns from .gitignore and other sources

        Returns:
            Set of ignore patterns
        """
        patterns = self.DEFAULT_IGNORE_PATTERNS.copy()

        # Load from .gitignore if it exists
        gitignore_path = self.workspace_path / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.add(line)
            except Exception as e:
                logger.warning(f"Failed to read .gitignore: {e}")

        return patterns

    def _should_ignore(self, name: str, path: Path) -> bool:
        """
        Check if file/directory should be ignored

        Args:
            name: File/directory name
            path: Full path

        Returns:
            True if should be ignored
        """
        # Check exact matches
        if name in self.ignore_patterns:
            return True

        # Check wildcard patterns (simplified)
        for pattern in self.ignore_patterns:
            if "*" in pattern:
                # Simple wildcard matching
                if pattern.startswith("*") and name.endswith(pattern[1:]):
                    return True
                if pattern.endswith("*") and name.startswith(pattern[:-1]):
                    return True

        return False

    async def get_tree(self, relative_path: str = "") -> Dict[str, Any]:
        """
        Build file tree starting from relative path

        Args:
            relative_path: Relative path within workspace

        Returns:
            File tree structure
        """
        start_path = self.workspace_path / relative_path
        if not start_path.exists():
            raise ValueError(f"Path does not exist: {start_path}")

        tree = await self._build_tree(start_path, depth=0)
        git_status = await self._get_git_status()

        # Merge git status into tree
        tree_with_git = self._merge_git_status(tree, git_status)

        return {
            "path": str(start_path),
            "tree": tree_with_git,
            "gitEnabled": self.git_repo is not None,
        }

    async def _build_tree(self, path: Path, depth: int = 0) -> List[Dict[str, Any]]:
        """
        Recursively build file tree

        Args:
            path: Current directory path
            depth: Current recursion depth

        Returns:
            List of file/directory nodes
        """
        if depth > self.max_depth:
            return []

        nodes = []

        try:
            entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
            return []

        for entry in entries:
            # Skip ignored files/directories
            if self._should_ignore(entry.name, entry):
                continue

            node = {
                "name": entry.name,
                "path": str(entry.relative_to(self.workspace_path)),
                "type": "directory" if entry.is_dir() else "file",
                "depth": depth,
            }

            if entry.is_dir():
                # Recursively build children
                node["children"] = await self._build_tree(entry, depth + 1)
            else:
                # Add file metadata
                try:
                    stat = entry.stat()
                    node["size"] = stat.st_size
                    node["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except Exception as e:
                    logger.warning(f"Failed to stat {entry}: {e}")

            nodes.append(node)

        return nodes

    async def _get_git_status(self) -> Dict[str, str]:
        """
        Get git status for all files in workspace

        Returns:
            Dictionary mapping file paths to status
            (modified, staged, untracked, deleted, added)
        """
        if not self.git_repo:
            return {}

        status_map = {}

        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--name-status", "--cached"],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        status_code, file_path = parts
                        if status_code == "M":
                            status_map[file_path] = "staged"
                        elif status_code == "A":
                            status_map[file_path] = "added"
                        elif status_code == "D":
                            status_map[file_path] = "deleted"

            # Get modified files (not staged)
            result = subprocess.run(
                ["git", "diff", "--name-status"],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        status_code, file_path = parts
                        # Only mark as modified if not already staged
                        if file_path not in status_map:
                            if status_code == "M":
                                status_map[file_path] = "modified"
                            elif status_code == "D":
                                status_map[file_path] = "deleted"

            # Get untracked files
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=self.git_repo,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                for file_path in result.stdout.strip().split("\n"):
                    if file_path:
                        status_map[file_path] = "untracked"

        except subprocess.TimeoutExpired:
            logger.warning("Git command timed out")
        except Exception as e:
            logger.warning(f"Failed to get git status: {e}")

        return status_map

    def _merge_git_status(
        self, nodes: List[Dict[str, Any]], git_status: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Merge git status into file tree nodes

        Args:
            nodes: File tree nodes
            git_status: Git status map

        Returns:
            Nodes with git status added
        """
        for node in nodes:
            file_path = node["path"]

            if file_path in git_status:
                node["gitStatus"] = git_status[file_path]

            # Recursively merge children
            if "children" in node:
                node["children"] = self._merge_git_status(node["children"], git_status)

        return nodes

    async def get_file_content(self, relative_path: str) -> Dict[str, Any]:
        """
        Get file content and metadata

        Args:
            relative_path: Relative path to file

        Returns:
            File content and metadata
        """
        file_path = self.workspace_path / relative_path

        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            stat = file_path.stat()

            # Read content (with size limit)
            max_size = 1024 * 1024  # 1MB
            if stat.st_size > max_size:
                content = f"[File too large to display: {stat.st_size} bytes]"
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            return {
                "path": relative_path,
                "content": content,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "language": self._detect_language(file_path),
            }
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension

        Args:
            file_path: Path to file

        Returns:
            Language identifier
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".xml": "xml",
            ".md": "markdown",
            ".sh": "bash",
            ".sql": "sql",
        }

        ext = file_path.suffix.lower()
        return extension_map.get(ext, "text")


# Singleton registry for file tree services
_file_tree_services: Dict[str, FileTreeService] = {}


def get_file_tree_service(workspace_path: str) -> FileTreeService:
    """
    Get or create file tree service for a workspace

    Args:
        workspace_path: Workspace directory path

    Returns:
        FileTreeService instance
    """
    if workspace_path not in _file_tree_services:
        _file_tree_services[workspace_path] = FileTreeService(workspace_path)
    return _file_tree_services[workspace_path]
