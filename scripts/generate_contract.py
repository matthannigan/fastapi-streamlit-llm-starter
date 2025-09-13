"""
Public Contract Generator
=========================

Generates a "public contract" type-stub from Python source, suitable for tests,
type checking, and documentation. The output is designed to be stable and
readable, preserving public API shape (signatures, docstrings, inheritance) while
omitting implementation details.

Features
--------
- **Robust signature builder**: Handles positional-only, keyword-only, varargs,
  kwargs, defaults, annotations, and async functions.
- **Class method emission**: Emits methods nested within classes; nested classes
  are supported.
- **Empty class handling**: Emits a configurable placeholder when a class body
  would otherwise be empty.
- **Docstrings**: Preserves and indents module, class, and function docstrings
  as multi-line blocks.
- **Imports**: Collects and emits only top-level imports (deduplicated, order
  preserved) near the module top.
- **Stable ordering**: Module docstring → imports → classes → functions.
- **Filtering**: Control inclusion of private names and dunder methods.
- **Directory mode**: Recursively process a directory tree, mirroring structure
  into an output directory and generating ``.pyi`` files.

Usage
-----
Single file:
```bash
python generate_contract.py backend/app/main.py -o backend/contracts/main.pyi
```

Directory (smart detection or explicit flags):
```bash
python generate_contract.py backend/app -o backend/contracts
# or
python generate_contract.py --input-dir backend/app --output-dir backend/contracts
```

CLI Options
-----------
- ``input_path``: Positional path to a source ``.py`` file or a directory
  (smart-detected). If ``--input-dir`` is supplied, it takes precedence.
- ``-o, --output_file``: Output file (single-file mode) or output directory
  (directory mode). In single-file mode, if this points to a directory, the
  output name is derived from the input and written as ``.pyi``.
- ``--input-dir``: Explicit directory mode input. Preferred for CI/scripts.
- ``--output-dir``: Explicit output directory for directory mode.
- ``--include-private``: Include names starting with a single underscore.
- ``--exclude-dunder``: Exclude ``__dunder__`` names (keeps ``__init__`` for methods).
- ``--body-placeholder {ellipsis,pass}``: Placeholder for generated bodies.
  Defaults to ``ellipsis`` (``...``), recommended for ``.pyi`` stubs.
- ``--encoding``: File encoding for reading source (default: ``utf-8``).

Behavior
--------
- Generates type stubs (``.pyi``) and uses ``...`` by default.
- Creates intermediate directories as needed.
- Skips hidden directories and ``__pycache__`` when processing trees.
- Prints a summary in directory mode (``Processed X/Y files``).

Exit Codes
----------
- ``1``: Failed to read input file
- ``2``: Syntax error while parsing
- ``3``: Unexpected generation error
- ``4``: Directory mode without a valid output directory

Notes
-----
- For contract snapshots used in tests and static analysis, prefer ``.pyi`` with
  ``...`` bodies. Use ``pass`` only if you truly need executable skeletons.
- The generator targets Python 3.9+ (uses ``ast.unparse``).
"""

import ast
import argparse
import sys
import os
from pathlib import Path
from typing import List, Union, Set, Optional

class PublicContractGenerator(ast.NodeVisitor):
    """
    Traverses a Python AST and generates a public contract file.
    """
    def __init__(self, *, include_private: bool = False, exclude_dunder: bool = False, body_placeholder: str = "...", public_object_types: Optional[List[str]] = None):
        self.lines = []
        self._current_indent = 0
        # Tracks whether we've emitted any members for the current class scope.
        # Each class entry pushes a boolean flag; methods/nested classes flip it to True.
        self._class_member_emitted_stack: List[bool] = []
        # Collects top-level imports to render once near the top
        self._top_level_import_lines: List[str] = []
        self._seen_import_lines = set()
        # Public/private filtering configuration
        self._include_private = include_private
        self._exclude_dunder = exclude_dunder
        # Placeholder used in bodies: "..." or "pass"
        self._body_placeholder = "..." if body_placeholder == "ellipsis" else "pass"
        # Recognized call callee names for public objects to capture (e.g., APIRouter)
        default_types = {"APIRouter", "Blueprint", "SQLAlchemy"}
        self._public_object_types: Set[str] = set(t.strip() for t in (public_object_types or [])) or default_types
        # Tracks whether current module is an __init__.py
        self._is_init_file: bool = False

    def _add_line(self, line: str):
        """Adds a line with the current indentation level."""
        self.lines.append(" " * self._current_indent + line)

    def _trim_trailing_blank_lines(self, max_keep: int = 0):
        """Trim trailing blank lines to at most max_keep."""
        count = 0
        while self.lines and self.lines[-1] == "":
            self.lines.pop()
            count += 1
        # Re-add up to max_keep blank lines
        for _ in range(min(count, max_keep)):
            self.lines.append("")

    def _ensure_top_level_separator(self):
        """Ensure exactly two blank lines separate top-level constructs."""
        if not self.lines:
            return
        self._trim_trailing_blank_lines(max_keep=0)
        self.lines.extend(["", ""])

    def _add_docstring(self, docstring: str):
        """Emit a properly indented multi-line docstring block."""
        self._add_line('"""')
        for line in (docstring.splitlines() or [""]):
            self._add_line(line)
        self._add_line('"""')

    def _call_callee_name(self, call: ast.Call) -> Optional[str]:
        """Extract the final attribute/name used as callee, e.g., fastapi.APIRouter -> APIRouter."""
        func = call.func
        # Name
        if isinstance(func, ast.Name):
            return func.id
        # Attribute chain: value.attr(.attr ...). We want the last attribute.
        if isinstance(func, ast.Attribute):
            current = func
            while isinstance(current, ast.Attribute):
                last_attr = current.attr
                current = current.value
            return last_attr
        return None

    def _is_private(self, name: str) -> bool:
        return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))

    def _is_dunder(self, name: str) -> bool:
        return name.startswith("__") and name.endswith("__")

    def _should_emit_name(self, name: str, is_method: bool = False) -> bool:
        # If excluding dunders, still allow __init__ for methods
        if self._exclude_dunder and self._is_dunder(name):
            if is_method and name == "__init__":
                return True
            return False
        if not self._include_private and self._is_private(name):
            return False
        return True

    def _get_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Reconstructs a function/method signature from an AST node using its arg structure."""
        def unparse(expr: Union[ast.AST, None]) -> str:
            return ast.unparse(expr) if expr is not None else ""

        def format_param(arg: ast.arg, default_expr: Union[ast.expr, None]) -> str:
            name = arg.arg
            annotation = f": {unparse(arg.annotation)}" if arg.annotation is not None else ""
            default = f" = {unparse(default_expr)}" if default_expr is not None else ""
            return f"{name}{annotation}{default}"

        params: List[str] = []

        posonly = list(getattr(node.args, "posonlyargs", []) or [])
        normal = list(node.args.args or [])
        vararg = node.args.vararg
        kwonly = list(node.args.kwonlyargs or [])
        kw_defaults = list(node.args.kw_defaults or [])
        kwarg = node.args.kwarg
        pos_defaults = list(node.args.defaults or [])

        total_pos = len(posonly) + len(normal)
        num_pos_defaults = len(pos_defaults)
        default_start = total_pos - num_pos_defaults if num_pos_defaults <= total_pos else 0

        # Positional-only parameters
        for i, a in enumerate(posonly):
            default_expr = pos_defaults[i - default_start] if i >= default_start else None
            params.append(format_param(a, default_expr))
        if posonly:
            params.append("/")

        # Regular positional-or-keyword parameters
        for j, a in enumerate(normal):
            idx = len(posonly) + j
            default_expr = pos_defaults[idx - default_start] if idx >= default_start else None
            params.append(format_param(a, default_expr))

        # *args or bare * (for keyword-only section)
        if vararg is not None:
            var_ann = f": {unparse(vararg.annotation)}" if vararg.annotation is not None else ""
            params.append(f"*{vararg.arg}{var_ann}")
        elif kwonly:
            # Need a bare * to introduce keyword-only params
            params.append("*")

        # Keyword-only parameters
        for k, a in enumerate(kwonly):
            default_expr = kw_defaults[k] if k < len(kw_defaults) else None
            params.append(format_param(a, default_expr))

        # **kwargs
        if kwarg is not None:
            kw_ann = f": {unparse(kwarg.annotation)}" if kwarg.annotation is not None else ""
            params.append(f"**{kwarg.arg}{kw_ann}")

        params_str = ", ".join(params)
        is_async = isinstance(node, ast.AsyncFunctionDef)
        prefix = "async " if is_async else ""
        ret = f" -> {unparse(node.returns)}" if node.returns is not None else ""
        return f"{prefix}def {node.name}({params_str}){ret}:"

    def _process_function_node(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Processes a function or method node."""
        # Respect public filtering
        in_class = bool(self._class_member_emitted_stack)
        if not self._should_emit_name(node.name, is_method=in_class):
            return

        for decorator in node.decorator_list:
            self._add_line(f"@{ast.unparse(decorator)}")

        self._add_line(self._get_signature(node))

        docstring = ast.get_docstring(node)
        if docstring:
            self._current_indent += 4
            self._add_docstring(docstring)
            self._current_indent -= 4

        self._current_indent += 4
        self._add_line(self._body_placeholder)
        self._current_indent -= 4
        self.lines.append("") # Add a blank line for spacing

    def visit_Assign(self, node: ast.Assign):
        """
        Captures public module-level constants AND common public objects
        like FastAPI Routers, Blueprints, etc.
        """
        if self._current_indent == 0:
            # Special-case: emit __all__ verbatim only in __init__.py modules
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and self._is_init_file:
                    self._add_line(ast.unparse(node))
                    if self.lines and self.lines[-1]:
                        self.lines.append("")
                    return
            # Heuristic 1: Is it an ALL_CAPS constant?
            is_constant = False
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper() and self._should_emit_name(target.id, is_method=False):
                    is_constant = True
                    break

            # Heuristic 2: Is it an instantiation of a known public object type?
            is_public_object = False
            if isinstance(node.value, ast.Call):
                callee = self._call_callee_name(node.value)
                if callee and callee in self._public_object_types:
                    is_public_object = True

            if is_constant or is_public_object:
                self._add_line(ast.unparse(node))
                if self.lines and self.lines[-1]:
                    self.lines.append("")

    def visit_Import(self, node: ast.Import):
        # Do not emit imports inline; handled in generate_contract at module top.
        return

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # Do not emit imports inline; handled in generate_contract at module top.
        return

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Capture top-level annotated assignments if they look public/constant objects and pass filters."""
        if self._current_indent != 0:
            return
        # Only handle simple names (x: T = value)
        target = node.target
        if not isinstance(target, ast.Name):
            return
        # Respect name filtering
        if not self._should_emit_name(target.id, is_method=False):
            return
        is_constant = target.id.isupper()
        is_public_object = False
        if isinstance(node.value, ast.Call):
            callee = self._call_callee_name(node.value)
            if callee and callee in self._public_object_types:
                is_public_object = True
        if is_constant or is_public_object:
            self._add_line(ast.unparse(node))
            if self.lines and self.lines[-1]:
                self.lines.append("")

    def visit_ClassDef(self, node: ast.ClassDef):
        # Respect public filtering for class names
        if not self._should_emit_name(node.name, is_method=False):
            return
        # Spacing before class: two blank lines at top-level, one inside a class
        in_class = bool(self._class_member_emitted_stack)
        if self.lines:
            if in_class:
                self._trim_trailing_blank_lines(max_keep=0)
                self.lines.append("")
            else:
                self._ensure_top_level_separator()

        for decorator in node.decorator_list:
            self._add_line(f"@{ast.unparse(decorator)}")
            
        base_classes = [ast.unparse(b) for b in node.bases]
        class_def_line = f"class {node.name}"
        if base_classes:
            class_def_line += f"({', '.join(base_classes)})"
        class_def_line += ":"
        self._add_line(class_def_line)
        self._current_indent += 4

        # If we're inside another class, mark that parent as having emitted a member
        if self._class_member_emitted_stack:
            self._class_member_emitted_stack[-1] = True

        docstring = ast.get_docstring(node)
        if docstring:
            self._add_docstring(docstring)
            self.lines.append("") # Blank line after class docstring

        # Begin tracking whether this class actually emits members
        self._class_member_emitted_stack.append(False)

        # Visit child nodes (methods, nested classes)
        self.generic_visit(node)
        
        # If nothing was emitted in this class body, add an ellipsis
        emitted = self._class_member_emitted_stack.pop()
        if not emitted:
            self._add_line(self._body_placeholder)

        self._current_indent -= 4

    def visit_FunctionDef(self, node: ast.FunctionDef):
        in_class = bool(self._class_member_emitted_stack)
        if not in_class:
            self._ensure_top_level_separator()
        self._process_function_node(node)
        if in_class:
            # Mark that the current class emitted a member
            self._class_member_emitted_stack[-1] = True

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        in_class = bool(self._class_member_emitted_stack)
        if not in_class:
            self._ensure_top_level_separator()
        self._process_function_node(node)
        if in_class:
            # Mark that the current class emitted a member
            self._class_member_emitted_stack[-1] = True
            
    def generate_contract(self, source_code: str, is_init_file: bool = False) -> str:
        """Parses source code and returns the public contract."""
        tree = ast.parse(source_code)

        # Reset state that may persist across invocations
        self.lines = []
        self._top_level_import_lines = []
        self._seen_import_lines = set()
        self._class_member_emitted_stack = []
        self._is_init_file = bool(is_init_file)

        # Module docstring first
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            self._add_docstring(module_docstring)
            self.lines.append("") # Blank line after module docstring

        # Collect top-level imports (deduped, preserve order)
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                line = ast.unparse(node)
                if line not in self._seen_import_lines:
                    self._seen_import_lines.add(line)
                    self._top_level_import_lines.append(line)

        if self._top_level_import_lines:
            for imp in self._top_level_import_lines:
                self._add_line(imp)
            self.lines.append("")

        # Emit selected top-level assignments (constants / known public objects)
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                self.visit(node)

        # Emit classes first (source order), then functions (source order)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.visit(node)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.visit(node)

        # Final polish: trim trailing blanks and ensure single trailing newline
        self._trim_trailing_blank_lines(max_keep=0)
        output = "\n".join(self.lines)
        if not output.endswith("\n"):
            output += "\n"
        return output

def main():
    parser = argparse.ArgumentParser(
        description="Generate a 'public contract' Python file from a source file."
    )
    parser.add_argument(
        "input_path", type=Path, help="Path to the input Python source file or directory."
    )
    parser.add_argument(
        "-o", "--output_file", type=Path, help="Path to the output file or directory (prints to stdout if not provided for single-file mode)."
    )
    parser.add_argument(
        "--input-dir", type=Path, help="Process all .py files under this directory recursively (overrides positional input)."
    )
    parser.add_argument(
        "--output-dir", type=Path, help="Directory to write generated contracts when processing a directory."
    )
    parser.add_argument(
        "--include-private", action="store_true", help="Include members starting with a single underscore."
    )
    parser.add_argument(
        "--exclude-dunder", action="store_true", help="Exclude __dunder__ methods and names (except __init__ for methods)."
    )
    parser.add_argument(
        "--body-placeholder", choices=["ellipsis", "pass"], default="ellipsis", help="Body placeholder for generated members (ellipsis or pass)."
    )
    parser.add_argument(
        "--encoding", default="utf-8", help="Encoding used to read the input file."
    )
    parser.add_argument(
        "--public-object-types", default="APIRouter,Blueprint,SQLAlchemy",
        help="Comma-separated callable names considered public objects for top-level assignment capture."
    )
    args = parser.parse_args()

    # Determine mode: directory vs single-file
    source_path: Path = args.input_dir if args.input_dir else args.input_path
    if not source_path.exists():
        print(f"Error: Input path not found at {source_path}")
        return

    def is_dirish(path: Path) -> bool:
        try:
            return path.exists() and path.is_dir()
        except Exception:
            return False

    def generate_single_file(src: Path, dst: Path | None) -> bool:
        try:
            source_code = src.read_text(encoding=args.encoding)
        except Exception as e:
            print(f"Error: Failed to read input file {src}: {e}", file=sys.stderr)
            return False
        try:
            generator = PublicContractGenerator(
                include_private=args.include_private,
                exclude_dunder=args.exclude_dunder,
                body_placeholder=args.body_placeholder,
                public_object_types=[s for s in (args.public_object_types or "").split(',') if s.strip()],
            )
            is_init = src.name == "__init__.py"
            contract_code = generator.generate_contract(source_code, is_init)
        except SyntaxError as e:
            print(f"Error: Failed to parse input file {src}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: Unexpected failure during contract generation for {src}: {e}", file=sys.stderr)
            return False

        if dst is None:
            print(contract_code)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(contract_code)
        return True

    if source_path.is_dir():
        # Directory mode
        out_dir: Path | None = None
        if args.output_dir:
            out_dir = args.output_dir
        elif args.output_file:
            out_dir = args.output_file
        if out_dir is None:
            print("Error: When processing a directory, you must specify --output-dir or -o pointing to a directory.", file=sys.stderr)
            sys.exit(4)
        # Treat provided output path as directory regardless of current existence
        total = 0
        succeeded = 0
        for src in source_path.rglob("*.py"):
            # Skip hidden directories and __pycache__
            parts = set(src.parts)
            if any(p.startswith('.') for p in src.parts) or "__pycache__" in parts:
                continue
            rel = src.relative_to(source_path)
            dst = (out_dir / rel).with_suffix(".pyi")
            total += 1
            if generate_single_file(src, dst):
                succeeded += 1
        print(f"Processed {succeeded}/{total} files into {out_dir}")
    else:
        # Single file mode
        dst: Path | None = None
        if args.output_file:
            out = args.output_file
            # If the path looks like a directory (exists as dir or ends with separator), treat as dir
            if (out.exists() and out.is_dir()) or (str(out).endswith(os.sep)):
                out_dir = out
                dst = (out_dir / source_path.name).with_suffix(".pyi")
            else:
                dst = out
        ok = generate_single_file(source_path, dst)
        if ok and dst is not None:
            print(f"Public contract successfully written to {dst}")

if __name__ == "__main__":
    main()