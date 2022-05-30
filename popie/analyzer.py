import ast
from pathlib import Path
from typing import List, Iterable

from popie.object_types import String, Error
from popie.constants import CONTEXTS


class Analyzer(ast.NodeVisitor):
    def __init__(self, filename: Path):
        self.filename = filename
        self.errors: List[Error] = []
        self.warnings: List[Error] = []
        self.strings: List[String] = []

    def report_errors(self):
        """Print errors to the stdout."""
        for error in self.errors:
            print(f"Analyzer error: {error}")

    def report_warnings(self):
        """Print warnings to the stdout."""
        for warning in self.warnings:
            print(f"Analyzer warning: {warning}")

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

    def _check_string(self, string: String) -> bool:
        if string.text[0] in (" ", "\t"):
            e = Error.from_string(
                string,
                "Translation string must not start with whitespace.",
            )
            self.errors.append(e)
            return False
        if string.text[-1] in (" ", "\t"):
            e = Error.from_string(
                string,
                "Translation string must not end with whitespace.",
            )
            self.errors.append(e)
            return False
        if "\n" in string.text:
            e = Error.from_string(
                string,
                "Translation string must not contain newlines.",
            )
            self.errors.append(e)
            return False
        return True

    def visit_Call(self, node: ast.Call):
        """Visit every function call.

        This function will ignore all function calls that are not called
        with as a function called '_' (an underscore).

        Those functions have to have two arguments:
        - one named 'ctx', 'utx' or 'gtx',
        - one string.

        These strings are saved to internal string pool and used to update
        the PO files.
        """
        # Inspect formatted translations (the .format() is parent in AST form)
        if getattr(node.func, "value", None) is not None:
            self._iterate([node.func.value])
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

        if (
            getattr(node.func, "id", "") == "_"
            and getattr(node.args[1], "func", None) is not None
            and getattr(node.args[1].func, "attr", "") == "format"
        ):
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                "Bad '.format()' placement in translation function "
                "(has to be outside of '_()' call.)",
            )
            self.errors.append(e)
            return

        if getattr(node.func, "id", "") == "_" and not isinstance(
            node.args[1], ast.Constant
        ):
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                "Bad string argument (has to be literal, not variable).",
            )
            self.errors.append(e)
            return

        if node_ctx.__class__ is ast.Attribute:
            # we support 'self.ctx'
            if node_ctx.value.id != "self" or node_ctx.attr not in CONTEXTS:
                e = Error(
                    self.filename,
                    node_ctx.lineno,
                    node_ctx.col_offset,
                    "Inherited translation context variable has to be one of "
                    + ", ".join(f"'{c}'" for c in CONTEXTS)
                    + f", got '{node_ctx.attr}'.",
                )
                self.errors.append(e)
                return
        elif node_ctx.id not in CONTEXTS + ("tc",):
            e = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                "Translation context variable has to be one of "
                + ", ".join(f"'{c}'" for c in CONTEXTS)
                + f", got '{node_ctx.id}'.",
            )
            self.errors.append(e)
            return
        elif node_ctx.id == "tc":
            w = Error(
                self.filename,
                node.func.lineno,
                node.func.col_offset,
                "Translation context variable name 'tc' is deprecated, use 'utx' "
                "instead. 'tc' may not be accepted in the future.",
            )
            self.warnings.append(w)

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
            if not self._check_string(s):
                return
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
            if not self._check_string(s):
                return
            self.strings.append(s)

        self.generic_visit(node)
