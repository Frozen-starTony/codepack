"""
CLI entry point for CodePack: Command-line interface and terminal output.
"""

import argparse
from pathlib import Path
import subprocess
import sys
from typing import List, Optional

from . import __version__
from .compact import compact_content
from .formatter import format_context, generate_ascii_tree
from .scanner import scan_directory, FileInfo
from .security import redact_secrets
from .tokenizer import format_size, format_token_count, estimate_tokens


def copy_to_clipboard(text: str) -> bool:
    """Copies text to clipboard using pyperclip or OS-native utilities."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    # Windows fallback
    if sys.platform.startswith("win"):
        try:
            process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            process.communicate(text.encode("utf-16"))
            return process.returncode == 0
        except Exception:
            pass

    # macOS fallback
    if sys.platform == "darwin":
        try:
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        except Exception:
            pass

    # Linux / X11 / Wayland fallback
    for cmd in [["xclip", "-selection", "clipboard"], ["wl-copy"]]:
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            process.communicate(text.encode("utf-8"))
            if process.returncode == 0:
                return True
        except Exception:
            continue

    return False


def display_rich_summary(files: List[FileInfo], total_tokens: int, redacted_count: int, is_compact: bool):
    """Renders terminal table using rich library without emojis."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        mode_str = " (Compact Mode)" if is_compact else ""
        table = Table(title=f"CodePack Inventory{mode_str}", show_header=True, header_style="bold cyan")
        table.add_column("File", style="dim")
        table.add_column("Lines", justify="right")
        table.add_column("Size", justify="right")
        table.add_column("Tokens", justify="right", style="green")

        for f in files[:25]:
            table.add_row(
                f.rel_path,
                f"{f.line_count:,}",
                format_size(f.size_bytes),
                f"~{format_token_count(f.token_count)}",
            )

        if len(files) > 25:
            table.add_row(f"... and {len(files) - 25} more files", "", "", "")

        console.print(table)

        summary_text = (
            f"[bold]Total Files:[/bold] {len(files)}  |  "
            f"[bold]Total Tokens:[/bold] [green]~{format_token_count(total_tokens)}[/green]  |  "
            f"[bold]Total Size:[/bold] {format_size(sum(f.size_bytes for f in files))}"
        )
        if redacted_count > 0:
            summary_text += f"\n[bold red][Security Alert][/bold red] {redacted_count} sensitive secret(s) detected and [bold green]redacted[/bold green]."

        console.print(Panel(summary_text, style="blue", expand=False))
    except ImportError:
        display_plain_summary(files, total_tokens, redacted_count, is_compact)


def display_plain_summary(files: List[FileInfo], total_tokens: int, redacted_count: int, is_compact: bool):
    """Renders standard ASCII summary table if rich is not installed."""
    mode_str = " [Compact Mode]" if is_compact else ""
    print("\n" + "=" * 60)
    print(f"CodePack Summary{mode_str}")
    print("=" * 60)
    print(f"{'File':<35} {'Lines':>8} {'Size':>8} {'Tokens':>7}")
    print("-" * 60)

    for f in files[:20]:
        rel = f.rel_path if len(f.rel_path) <= 35 else "..." + f.rel_path[-32:]
        print(f"{rel:<35} {f.line_count:>8} {format_size(f.size_bytes):>8} ~{format_token_count(f.token_count):>6}")

    if len(files) > 20:
        print(f"... and {len(files) - 20} more files")

    print("-" * 60)
    total_size = sum(f.size_bytes for f in files)
    print(f"Total: {len(files)} files | ~{format_token_count(total_tokens)} tokens | {format_size(total_size)}")
    if redacted_count > 0:
        print(f"[Security Alert] {redacted_count} sensitive secret(s) redacted.")
    print("=" * 60 + "\n")


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="codepack",
        description="Fast, intelligent CLI utility to pack your codebase into optimized LLM-ready context.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory path to pack (default: current directory).",
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to write the output context file.",
    )
    parser.add_argument(
        "-c", "--clipboard",
        action="store_true",
        help="Copy the generated context directly to system clipboard.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["markdown", "xml", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Extract code outline (classes, functions, signatures) to minimize tokens.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Exclude test folders and test files.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum directory depth in the ASCII tree.",
    )
    parser.add_argument(
        "--only", "--include",
        dest="include_exts",
        help="Comma-separated list of file extensions to include (e.g. 'py,ts,json').",
    )
    parser.add_argument(
        "--exclude",
        help="Comma-separated list of custom glob patterns to exclude.",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=500,
        help="Maximum individual file size in KB to include (default: 500 KB).",
    )
    parser.add_argument(
        "--tree-only",
        action="store_true",
        help="Output only the ASCII directory tree without file contents.",
    )
    parser.add_argument(
        "--no-security",
        action="store_true",
        help="Disable automatic detection and redaction of API keys and credentials.",
    )
    parser.add_argument(
        "-i", "--instructions",
        help="Custom instructions or task description to prepend to the context.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress terminal summary output.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parsed = parser.parse_args(args)

    target_dir = Path(parsed.path).resolve()
    if not target_dir.is_dir():
        print(f"Error: Directory '{target_dir}' does not exist.", file=sys.stderr)
        return 1

    include_set = None
    if parsed.include_exts:
        include_set = {ext.strip().lstrip(".").lower() for ext in parsed.include_exts.split(",") if ext.strip()}

    exclude_list = None
    if parsed.exclude:
        exclude_list = [p.strip() for p in parsed.exclude.split(",") if p.strip()]

    try:
        files = scan_directory(
            root_path=str(target_dir),
            include_exts=include_set,
            exclude_patterns=exclude_list,
            max_file_size_kb=parsed.max_size,
            skip_tests=parsed.skip_tests,
        )
    except Exception as e:
        print(f"Error scanning directory: {e}", file=sys.stderr)
        return 1

    if not files:
        print("No matching files found in the specified directory.")
        return 0

    # Handle tree-only mode
    if parsed.tree_only:
        tree = generate_ascii_tree([f.rel_path for f in files], root_name=target_dir.name, max_depth=parsed.max_depth)
        if parsed.output:
            Path(parsed.output).write_text(tree, encoding="utf-8")
            print(f"[Saved] Tree saved to {parsed.output}")
        elif parsed.clipboard:
            if copy_to_clipboard(tree):
                print("[Success] Directory tree copied to clipboard.")
            else:
                print("[Error] Failed to access system clipboard.", file=sys.stderr)
        else:
            print(tree)
        return 0

    # Redact secrets unless explicitly disabled
    redacted_count = 0
    if not parsed.no_security:
        for f in files:
            if f.content:
                clean_content, report = redact_secrets(f.content)
                if report.has_secrets:
                    redacted_count += len(report.findings)
                    f.content = clean_content
                    f.token_count = estimate_tokens(clean_content)

    # Apply compact mode if requested
    if parsed.compact:
        for f in files:
            if f.content:
                f.content = compact_content(f.content, f.extension)
                f.line_count = f.content.count("\n") + (1 if f.content else 0)
                f.token_count = estimate_tokens(f.content)

    total_tokens = sum(f.token_count for f in files)

    # Format output
    output_text = format_context(
        files=files,
        format_type=parsed.format,
        root_name=target_dir.name,
        instructions=parsed.instructions,
        max_depth=parsed.max_depth,
    )

    if not parsed.quiet:
        display_rich_summary(files, total_tokens, redacted_count, parsed.compact)

    # Handle destination
    if parsed.clipboard:
        copied = copy_to_clipboard(output_text)
        if copied:
            print("[Success] Context successfully copied to clipboard.")
        else:
            print("[Warning] Could not copy to clipboard automatically.", file=sys.stderr)

    if parsed.output:
        out_path = Path(parsed.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_text, encoding="utf-8")
        print(f"[Saved] Saved context to: {out_path.resolve()}")
    elif not parsed.clipboard and not parsed.quiet:
        default_ext = "xml" if parsed.format == "xml" else ("json" if parsed.format == "json" else "md")
        default_file = target_dir / f"codepack-context.{default_ext}"
        default_file.write_text(output_text, encoding="utf-8")
        print(f"[Saved] Saved context to: {default_file.name} (Use -c to copy directly to clipboard)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
