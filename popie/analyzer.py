import ast
from pathlib import Path
from typing import List, Iterable

from popie.object_types import String, Error


class Analyzer(ast.NodeVisitor):
    def __init__(self, filename: Path):
        self.filename = filename
        self.errors: List[Error] = []
        self.strings: List[String] = []

    def report_errors(self):
        """Print errors to the stdout."""
        for error in self.errors:
            print(f"Analyzer error: {error}")

    def _iterate(self, iterable: Iterable):
        """Call itself over all found iterables to find all 'Call's."""
        for item in iterable:
            if item.__class__ is ast.Call:
                self.visit_Call(item)
            if item.__class__ in (ast.List, ast.Tuple):
                self._iterate(item.elts)
            if item.__class__ is ast.Dict:
                self._iterate(item.keys)
                self._iterate(item.values)
            if item.__class__ is ast.BinOp:
                self._iterate([item.left, item.right])

    def visit_Call(self, node: ast.Call):
        """Visit every function call.

        This function will ignore all function calls that are not called
        with as a function called '_' (an underscore).

        Those functions have to have two arguments:
        - one named 'ctx' or 'tc',
        - one string.

        These strings are saved to internal string pool and used to update
        the PO files.
        """
        # Inspect formatted translations (the .format() is parent in AST form)
        if getattr(node.func, "value", None).__class__ is ast.Call:
            self.visit_Call(node.func.value)
        # Inspect unnamed arguments for function calls
        self._iterate(node.args)
        # Inspect named arguments for function calls
        self._iterate([kw.value for kw in node.keywords])

        # Ignore calls to functions with we don't care about
        if node.func.__class__ != ast.Name or node.func.id != "_":
            return

        if len(node.args) != 2:
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                f"Bad argument count (expected 2, got {len(node.args)}).",
            )
            self.errors.append(e)
            return

        node_ctx, node_str = node.args

        if node_ctx.id not in ("ctx", "tc"):
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                "Translation context variable has to have name 'ctx' or 'tc', "
                f"got '{node_ctx.id}'.",
            )
            self.errors.append(e)
            return

        if node_str.__class__ is ast.Constant:
            # plain string
            if node_str.value.__class__ is not str:
                e = Error(
                    self.filename,
                    node.func.lineno,
                    node.func.col_offset,
                    "Translation string has to be of type 'str', "
                    f"not '{node_str.value.__class__.__name__}'.",
                )
                self.errors.append(e)
                return

            s = String(
                self.filename, node_str.lineno, node_str.col_offset, node_str.value
            )
            self.strings.append(s)

        if node_str.__class__ is ast.Call:
            # formatted string
            if node_str.func.value.value.__class__ is not str:
                e = Error(
                    self.filename,
                    node_str.func.lineno,
                    node_str.func.col_offset,
                    "Translation string has to be of type 'str', "
                    f"not '{node_str.func.value.value.__class__.__name__}'.",
                )
                self.errors.append(e)
                return

            s = String(
                self.filename,
                node_str.func.lineno,
                node_str.func.col_offset,
                node_str.func.value.value,
            )
            self.strings.append(s)

        self.generic_visit(node)
