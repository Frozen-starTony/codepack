"""
Formatter module for CodePack: Generates ASCII directory trees and formats prompts (Markdown, XML, JSON).
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .scanner import FileInfo
from .tokenizer import format_size, format_token_count


LANGUAGE_MAP: Dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "jsx": "jsx",
    "ts": "typescript",
    "tsx": "tsx",
    "html": "html",
    "htm": "html",
    "css": "css",
    "scss": "scss",
    "sass": "sass",
    "less": "less",
    "json": "json",
    "xml": "xml",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "toml",
    "ini": "ini",
    "md": "markdown",
    "rst": "rst",
    "sh": "bash",
    "bash": "bash",
    "zsh": "bash",
    "ps1": "powershell",
    "bat": "batch",
    "cmd": "batch",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "hpp": "cpp",
    "cc": "cpp",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "kt": "kotlin",
    "kts": "kotlin",
    "cs": "csharp",
    "php": "php",
    "rb": "ruby",
    "swift": "swift",
    "sql": "sql",
    "dockerfile": "dockerfile",
}


def get_syntax_lang(ext: str, filename: str) -> str:
    """Returns markdown fence language identifier."""
    lower_fn = filename.lower()
    if lower_fn == "dockerfile" or lower_fn.startswith("dockerfile."):
        return "dockerfile"
    return LANGUAGE_MAP.get(ext.lower(), "")


def generate_ascii_tree(
    file_paths: List[str],
    root_name: str = "project",
    max_depth: Optional[int] = None,
) -> str:
    """
    Constructs an ASCII tree structure from a list of relative file paths.
    Supports limiting tree depth via max_depth.
    """
    tree: Dict = {}
    for path in sorted(file_paths):
        parts = path.replace("\\", "/").split("/")
        curr = tree
        for part in parts:
            curr = curr.setdefault(part, {})

    lines: List[str] = [f"{root_name}/"]

    def _render(node: Dict, prefix: str = "", current_depth: int = 1):
        keys = sorted(node.keys())
        for i, key in enumerate(keys):
            is_last = i == len(keys) - 1
            branch = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            is_dir = bool(node[key])
            display_name = f"{key}/" if is_dir else key
            lines.append(f"{prefix}{branch}{display_name}")
            if is_dir:
                if max_depth is not None and current_depth >= max_depth:
                    lines.append(f"{prefix}{extension}└── ...")
                else:
                    _render(node[key], prefix + extension, current_depth + 1)

    _render(tree)
    return "\n".join(lines)


def format_markdown(
    files: List[FileInfo],
    root_name: str = "project",
    instructions: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Generates clean Markdown representation of the codebase."""
    total_tokens = sum(f.token_count for f in files)
    total_lines = sum(f.line_count for f in files)
    total_size = sum(f.size_bytes for f in files)

    tree_str = generate_ascii_tree([f.rel_path for f in files], root_name=root_name, max_depth=max_depth)

    parts: List[str] = []
    parts.append(f"# Codebase Context: {root_name}\n")
    parts.append(
        f"> **Files**: {len(files)} | **Lines**: {total_lines:,} | "
        f"**Estimated Tokens**: ~{format_token_count(total_tokens)} | **Size**: {format_size(total_size)}\n"
    )

    if instructions:
        parts.append(f"## Task / Instructions\n{instructions.strip()}\n")

    parts.append(f"## Project Structure\n```text\n{tree_str}\n```\n")
    parts.append("## Files Content\n")

    for f in files:
        lang = get_syntax_lang(f.extension, Path(f.rel_path).name)
        parts.append(f"### `{f.rel_path}`")
        parts.append(f"*Tokens: ~{format_token_count(f.token_count)} | Lines: {f.line_count}*\n")
        parts.append(f"```{lang}\n{f.content or ''}\n```\n")

    return "\n".join(parts)


def format_xml(
    files: List[FileInfo],
    root_name: str = "project",
    instructions: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Generates Claude-optimized XML prompt context."""
    parts: List[str] = []
    parts.append("<context>")
    if instructions:
        parts.append(f"  <instructions>\n    {instructions.strip()}\n  </instructions>")

    parts.append("  <structure>")
    tree_str = generate_ascii_tree([f.rel_path for f in files], root_name=root_name, max_depth=max_depth)
    parts.append(f"<![CDATA[\n{tree_str}\n]]>")
    parts.append("  </structure>")

    parts.append("  <documents>")
    for idx, f in enumerate(files, start=1):
        parts.append(f'    <document index="{idx}">')
        parts.append(f"      <source>{f.rel_path}</source>")
        parts.append(f"      <document_content><![CDATA[\n{f.content or ''}\n]]></document_content>")
        parts.append("    </document>")
    parts.append("  </documents>")
    parts.append("</context>")

    return "\n".join(parts)


def format_json(
    files: List[FileInfo],
    root_name: str = "project",
    instructions: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Generates structured JSON representation for programmatic use."""
    total_tokens = sum(f.token_count for f in files)
    total_lines = sum(f.line_count for f in files)
    total_size = sum(f.size_bytes for f in files)

    data = {
        "project": root_name,
        "instructions": instructions,
        "summary": {
            "total_files": len(files),
            "total_lines": total_lines,
            "total_tokens": total_tokens,
            "total_size_bytes": total_size,
        },
        "tree": generate_ascii_tree([f.rel_path for f in files], root_name=root_name, max_depth=max_depth),
        "files": [
            {
                "path": f.rel_path,
                "lines": f.line_count,
                "tokens": f.token_count,
                "size_bytes": f.size_bytes,
                "content": f.content,
            }
            for f in files
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_context(
    files: List[FileInfo],
    format_type: str = "markdown",
    root_name: str = "project",
    instructions: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Formats files into the requested format (markdown, xml, json)."""
    fmt = format_type.lower()
    if fmt == "xml":
        return format_xml(files, root_name=root_name, instructions=instructions, max_depth=max_depth)
    elif fmt == "json":
        return format_json(files, root_name=root_name, instructions=instructions, max_depth=max_depth)
    return format_markdown(files, root_name=root_name, instructions=instructions, max_depth=max_depth)
