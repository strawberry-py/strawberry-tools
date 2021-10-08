import ast
import argparse
import sys
import os
from typing import Iterable, List, Optional, Set
from pathlib import Path

from popie.analyzer import Analyzer
from popie.reporter import Reporter
from popie.languages import LANGUAGES
from popie.popiefile import PoPieFile


def main():
    parser = argparse.ArgumentParser(
        prog="popie",
        description=(
            "A tool for string extraction in the pumpkin.py bot framework. "
            "PoPie extracts strings inside of the '_()' function calls into "
            ".po-like files, which can be translated independently."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "paths",
        help="Paths to directories and files",
        nargs="+",
    )
    args = parser.parse_args()

    paths: List[Path] = get_paths(args.paths)
    directories: Set[Path] = get_directories(paths)

    for directory in directories:
        run(directory)


def get_paths(paths: Iterable[str]) -> List[Path]:
    """Get list of valid paths.

    For a path to be valid, it has to exist. If it does not exist, an error
    is printed and the program aborts.
    """
    result: List[Path] = []
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Error: Specified path '{path!s}' does not exist.")
            sys.exit(os.EX_USAGE)
        result.append(path.resolve())
    return result


def get_directories(paths: Iterable[Path]) -> Set[Path]:
    """Get list of directories to be run against.

    This function takes an iterable of paths and checks if they are part of
    known pumpkin.py file structure. If they are, the directory will be flagged
    to be scanned.

    If the file is not part of th i18n pumpkin.py scheme, it won't be used, and
    a warning will be printed.
    """
    root: Optional[Path] = None
    i18n_directories: Set[Path] = set()

    def is_root_directory(path: Path) -> bool:
        """Detect if the path is pumpkin.py root directory."""
        for file in path.glob("*.py"):
            if file.name == "pumpkin.py":
                return True
        return False

    def get_root_directory(path: Path) -> Optional[Path]:
        """Get root directory.

        Go through the path parents and try to find the root.
        """
        if is_root_directory(path):
            return path

        for parent in path.parents:
            if is_root_directory(parent):
                return parent

        return None

    # The easiest way to find the directories is to hardcode some paths.
    # First, the root directory is found by inspecting the parents; if the n-th
    # parent contains file 'pumpkin.py', it is the root.
    # This check is done for every path, which not be effective. However, this
    # way we can detect if there are multiple 'pumpkin.py' files, and if there
    # are, we cause an abort.

    for path in paths:
        path_root = get_root_directory(path)
        if root is None:
            root = path_root
        if path_root != root:
            print("Error: Multiple project roots detected:")
            rel_root: str = os.path.relpath(root, start=Path.cwd())
            print(f"- {rel_root}")
            rel_path_root: str = os.path.relpath(path_root, start=Path.cwd())
            print(f"- {rel_path_root}")
            sys.exit(os.EX_PROGRAM)

        relpath: str = os.path.relpath(path, start=root)
        # The 'core/' may be specified on its own, probably.
        if relpath == "core" or relpath.startswith("core/"):
            i18n_directories.add(root / "core/")
        elif relpath.startswith("modules/"):
            # get just the first two directories, no matter how deep the
            # file is
            repo_dir: str = "/".join(relpath.split("/", 2)[:2])
            i18n_directories.add(root / repo_dir)
        else:
            print(f"Warning: Ignoring '{path!s}' (directory criteria not matched).")

    return i18n_directories


def run(directory: Path):
    """Run the PoPie for all files under given directory."""
    if not directory.is_dir():
        print(f"Error: Can't run for '{directory!s}' (path does not exist).")
        sys.exit(os.EX_USAGE)

    reporter = Reporter()
    py_files: List[Path] = directory.glob("**/*.py")
    for py_file in py_files:
        with open(py_file, "r") as source:
            tree = ast.parse(source.read())

        analyzer = Analyzer(py_file)
        analyzer.visit(tree)
        analyzer.report_errors()

        reporter.add_strings(analyzer.strings)

    msgid_count: int = len(reporter.strings)
    rel_directory: str = os.path.relpath(directory, start=directory.cwd())
    print(f"Info: Found {msgid_count} strings in '{rel_directory}'.")

    po_directory: Path = directory / "po"
    po_directory.mkdir(exist_ok=True)

    for lang in LANGUAGES:
        po: Path = po_directory / f"{lang}.popie"
        rel_po: str = os.path.relpath(po, start=po.cwd())
        pofile = PoPieFile(po)
        pofile.update(reporter)
        pofile.save()
        msgstr_count = len([s for s in pofile.translations.values() if s is not None])
        print(f"Info: Saving {msgstr_count} translated strings to '{rel_po}'.")
