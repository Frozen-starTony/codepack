"""
Compact module for CodePack: Extracts structural skeletons, classes, and function signatures to save tokens.
"""

import ast
import copy
import re
from typing import Optional


def compact_python_code(source_code: str) -> str:
    """
    Parses Python code using AST and generates a minimal skeleton
    containing imports, classes, functions, signatures, docstrings, and type hints.
    Replaces function and method bodies with '...'.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return source_code

    lines = []

    # Module docstring
    docstring = ast.get_docstring(tree)
    if docstring:
        clean_doc = docstring.strip().split("\n")[0]
        lines.append(f'"""{clean_doc}"""')

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            lines.append(ast.unparse(node))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    lines.append(f"{target.id} = ...")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.append(_compact_function_node(node))
        elif isinstance(node, ast.ClassDef):
            lines.append(_compact_class_node(node))

    result = "\n\n".join(lines)
    return result if result.strip() else source_code


def _compact_function_node(node: ast.AST) -> str:
    """Compacts a function by replacing its body with docstring and ellipsis."""
    fn_copy = copy.deepcopy(node)
    doc = ast.get_docstring(node)
    new_body = []
    if doc:
        clean_doc = doc.strip().split("\n")[0]
        new_body.append(ast.Expr(value=ast.Constant(value=clean_doc)))
    new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))

    fn_copy.body = new_body
    ast.fix_missing_locations(fn_copy)
    return ast.unparse(fn_copy)


def _compact_class_node(node: ast.ClassDef) -> str:
    """Compacts a class by keeping docstring, annotations, and compacted methods."""
    class_copy = copy.deepcopy(node)
    new_body = []

    doc = ast.get_docstring(node)
    if doc:
        clean_doc = doc.strip().split("\n")[0]
        new_body.append(ast.Expr(value=ast.Constant(value=clean_doc)))

    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_copy = copy.deepcopy(item)
            m_doc = ast.get_docstring(item)
            m_body = []
            if m_doc:
                clean_m_doc = m_doc.strip().split("\n")[0]
                m_body.append(ast.Expr(value=ast.Constant(value=clean_m_doc)))
            m_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
            method_copy.body = m_body
            ast.fix_missing_locations(method_copy)
            new_body.append(method_copy)
        elif isinstance(item, ast.AnnAssign):
            new_body.append(item)

    if not new_body:
        new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))

    class_copy.body = new_body
    ast.fix_missing_locations(class_copy)
    return ast.unparse(class_copy)


def compact_generic_code(source_code: str) -> str:
    """
    Extracts class, interface, and function signatures from JS/TS and other C-like languages.
    """
    patterns = [
        r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+[a-zA-Z0-9_]+\s*\([^)]*\)",
        r"^(?:export\s+)?(?:abstract\s+)?class\s+[a-zA-Z0-9_]+(?:\s+extends\s+[a-zA-Z0-9_]+)?(?:\s+implements\s+[a-zA-Z0-9_,\s]+)?",
        r"^(?:export\s+)?interface\s+[a-zA-Z0-9_]+",
        r"^(?:export\s+)?type\s+[a-zA-Z0-9_]+\s*=",
        r"^(?:export\s+)?const\s+[a-zA-Z0-9_]+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
    ]
    regex = re.compile("|".join(patterns), re.MULTILINE)

    matches = []
    for match in regex.finditer(source_code):
        matches.append(match.group(0) + " { ... }")

    if matches:
        return "\n\n".join(matches)
    return source_code


def compact_content(content: str, extension: str) -> str:
    """Dispatches content compaction based on file extension."""
    ext = extension.lower().lstrip(".")
    if ext == "py":
        return compact_python_code(content)
    elif ext in {"js", "ts", "jsx", "tsx", "mjs"}:
        return compact_generic_code(content)
    return content
