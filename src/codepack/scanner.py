"""
Scanner module for CodePack: Recursively discovers, filters, and reads codebase files.
"""

from dataclasses import dataclass
import fnmatch
import os
from pathlib import Path
from typing import Callable, Generator, List, Optional, Set

from .tokenizer import estimate_tokens


@dataclass
class FileInfo:
    rel_path: str
    abs_path: Path
    size_bytes: int
    line_count: int
    token_count: int
    extension: str
    is_binary: bool
    content: Optional[str] = None


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "target",
    ".next",
    ".nuxt",
    ".cache",
    "coverage",
    "htmlcov",
    ".idea",
    ".vscode",
    ".gradle",
    "bin",
    "obj",
}

DEFAULT_IGNORE_FILES = {
    ".DS_Store",
    "Thumbs.db",
    ".env",
    ".env.local",
    ".env.production",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Cargo.lock",
    "composer.lock",
    "Gemfile.lock",
    "codepack-context.md",
    "codepack-context.xml",
    "codepack-context.json",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp", ".tiff",
    ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".flac",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a",
    ".pyc", ".pyo", ".pyd", ".class", ".jar", ".war",
    ".wasm", ".pdf", ".epub",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".db", ".sqlite", ".sqlite3",
}


def is_binary_file(filepath: Path) -> bool:
    """Checks extension and probes first 1024 bytes for null characters."""
    if filepath.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
            # Attempt decode
            chunk.decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return True
    return False


def load_ignore_patterns(root_dir: Path) -> List[str]:
    """Loads patterns from .gitignore and .codepackignore if present."""
    patterns: List[str] = []
    for filename in [".gitignore", ".codepackignore"]:
        ignore_file = root_dir / filename
        if ignore_file.is_file():
            try:
                with open(ignore_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except OSError:
                pass
    return patterns


def compile_path_matcher(patterns: List[str]) -> Callable[[str, bool], bool]:
    """
    Returns a matcher function(rel_path_posix, is_dir) -> bool.
    Uses pathspec if installed, otherwise falls back to fnmatch.
    """
    try:
        import pathspec
        spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return lambda path_str, is_dir: spec.match_file(path_str + ("/" if is_dir else ""))
    except ImportError:
        pass

    # Simple fallback using fnmatch
    clean_patterns = []
    for p in patterns:
        clean = p.rstrip("/")
        clean_patterns.append(clean)

    def simple_matcher(path_str: str, is_dir: bool) -> bool:
        normalized = path_str.replace("\\", "/")
        parts = normalized.split("/")
        for pat in clean_patterns:
            # Match anywhere in path or exact filename
            if fnmatch.fnmatch(normalized, pat) or fnmatch.fnmatch(normalized, f"*/{pat}"):
                return True
            for part in parts:
                if fnmatch.fnmatch(part, pat):
                    return True
        return False

    return simple_matcher


def scan_directory(
    root_path: str,
    include_exts: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_file_size_kb: int = 500,
    respect_gitignore: bool = True,
    skip_tests: bool = False,
) -> List[FileInfo]:
    """
    Scans root_path recursively and returns a list of FileInfo objects for matched files.
    """
    root = Path(root_path).resolve()
    if not root.is_dir():
        raise ValueError(f"Path '{root}' is not a valid directory.")

    ignore_patterns = []
    if respect_gitignore:
        ignore_patterns.extend(load_ignore_patterns(root))
    if exclude_patterns:
        ignore_patterns.extend(exclude_patterns)

    matcher = compile_path_matcher(ignore_patterns) if ignore_patterns else (lambda p, d: False)
    max_size_bytes = max_file_size_kb * 1024

    test_dir_names = {"tests", "test", "__tests__", "spec", "specs"}

    files: List[FileInfo] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        rel_dir = current_dir.relative_to(root)
        rel_dir_posix = rel_dir.as_posix() if rel_dir.parts else ""

        # Filter out directories
        filtered_dirs = []
        for d in dirnames:
            if d in DEFAULT_IGNORE_DIRS or d.startswith("."):
                continue
            if skip_tests and d.lower() in test_dir_names:
                continue
            child_rel = f"{rel_dir_posix}/{d}" if rel_dir_posix else d
            if matcher(child_rel, True):
                continue
            filtered_dirs.append(d)
        dirnames[:] = filtered_dirs

        # Process files
        for f in filenames:
            if f in DEFAULT_IGNORE_FILES or f.startswith("."):
                continue

            if skip_tests:
                lower_f = f.lower()
                if (
                    lower_f.startswith("test_")
                    or lower_f.endswith("_test.py")
                    or ".test." in lower_f
                    or ".spec." in lower_f
                ):
                    continue

            file_path = current_dir / f
            rel_file = file_path.relative_to(root).as_posix()

            if matcher(rel_file, False):
                continue

            ext = file_path.suffix.lstrip(".").lower()
            if include_exts and ext not in include_exts:
                continue

            try:
                stat = file_path.stat()
                size = stat.st_size
            except OSError:
                continue

            # Skip files larger than max_file_size_kb
            if size > max_size_bytes:
                continue

            binary = is_binary_file(file_path)
            if binary:
                continue

            content = None
            lines = 0
            tokens = 0

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as file_handle:
                    content = file_handle.read()
                    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
                    tokens = estimate_tokens(content)
            except OSError:
                continue

            files.append(
                FileInfo(
                    rel_path=rel_file,
                    abs_path=file_path,
                    size_bytes=size,
                    line_count=lines,
                    token_count=tokens,
                    extension=ext,
                    is_binary=binary,
                    content=content,
                )
            )

    # Sort files alphabetically
    files.sort(key=lambda x: x.rel_path)
    return files
