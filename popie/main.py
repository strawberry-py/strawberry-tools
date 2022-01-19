import ast
import argparse
import sys
import os
from enum import IntEnum
from typing import Callable, Iterable, List, Optional, Set
from pathlib import Path

from popie.analyzer import Analyzer
from popie.reporter import Reporter
from popie.constants import LANGUAGES
from popie.popiefile import PoPieFile

OS_SEP = str(os.sep)

debug: Callable = (
    lambda message: print("\033[37m" + "PoPie: \033[3m" + message + "\033[0m")
    if os.getenv("POPIE_DEBUG")
    else lambda *args, **kwargs: None
)


class ExitCode(IntEnum):
    OK: int = 0  # os.EX_OK
    INPUT: int = 64  # os.EX_USAGE
    POPIE: int = 70  # os.EX_SOFTWARE


def main():
    parser = argparse.ArgumentParser(
        prog="popie",
        description=(
            "A tool for string extraction in the pumpkin.py bot framework. "
            "PoPie extracts strings inside of the '_()' function calls into "
            ".po-like files, which can be translated independently."
        ),
        allow_abbrev=False,
        epilog=(
            "If you are a developer, you may have multiple module "
            "repositories next to the main pumpkin repository. "
            "In that case you can use the --detached option. "
            "PoPie won't look for the pumpkin.py file, but will look for "
            "common directory with '.git/' subdirectory instead. That "
            "directory will be considered local root and in that directory "
            "the 'po/' subdirectory will be created. "
            "You don't need this option if you placed your modules inside of "
            "the pumpkin.py's 'modules/' directory."
        ),
    )
    parser.add_argument(
        "--detached",
        help="Run the PoPie in detached mode.",
        action="store_true",
    )
    parser.add_argument(
        "--strict",
        help="Return non-zero code if any of PoPie files changes.",
        action="store_true",
    )
    parser.add_argument(
        "paths",
        help="Paths to directories and files",
        nargs="+",
    )
    args = parser.parse_args()

    paths: List[Path] = get_paths(args.paths)
    directories: List[Path] = get_directories(paths, detached=args.detached)

    error_count: int = 0
    updated_files: int = 0
    for directory in directories:
        reason, count = run(directory)

        if reason == "found errors":
            error_count += count
        if reason == "updated files":
            updated_files += count

        print()

    if args.strict and updated_files > 0:
        print(f"PoPie: {updated_files} files updated in strict mode. ")
        sys.exit(ExitCode.POPIE)

    if error_count:
        print(f"PoPie: {updated_files} files updated, {error_count} errors found. ")
        sys.exit(ExitCode.POPIE)

    print(f"PoPie: {updated_files} files have been updated.")
    sys.exit(ExitCode.OK)


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
            sys.exit(ExitCode.INPUT)
        result.append(path.resolve())
    return sorted(result)


def get_directories(paths: Iterable[Path], *, detached: bool) -> List[Path]:
    """Get list of directories to be run against.

    This function takes an iterable of paths and checks if they are part of
    known pumpkin.py file structure. If they are, the directory will be flagged
    to be scanned.

    If the file is not part of th i18n pumpkin.py scheme, it won't be used, and
    a warning will be printed.
    """
    root: Optional[Path] = None
    i18n_directories: Set[Path] = set()

    def is_root_directory(path: Path, *, detached: bool) -> bool:
        """Detect if the path is pumpkin.py root directory."""
        if not detached:
            if [f for f in path.glob("pumpkin.py") if f.is_file()]:
                return True
        if path.is_dir() and detached:
            if [d for d in path.glob(".git") if d.is_dir()]:
                return True
        return False

    def get_root_directory(path: Path) -> Optional[Path]:
        """Get root directory.

        Go through the path parents and try to find the root.
        """
        if is_root_directory(path, detached=detached):
            return path

        for parent in path.parents:
            if is_root_directory(parent, detached=detached):
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
            sys.exit(ExitCode.POPIE)

        relpath: str = os.path.relpath(path, start=root)
        # The 'pie/' may be specified on its own.
        if relpath == "pie" or relpath.startswith("pie" + OS_SEP):
            i18n_directories.add(root / ("pie" + OS_SEP))
        elif relpath.startswith("modules" + OS_SEP):
            # get just the first two directories, no matter how deep the file is
            repo_dir: str = OS_SEP.join(relpath.split(OS_SEP, 2)[:2])
            i18n_directories.add(root / repo_dir)
        elif detached:
            # allow detached repositories without pie/ & modules/ dirs
            i18n_directories.add(root)
        else:
            warning: str = (
                f"Warning: Ignoring '{path!s}': directory criteria not matched"
            )
            if not detached:
                warning += " (could not find 'pumpkin.py' script)."
            else:
                warning += " (could not find '.git' directory)."
            print(warning)

    sorted_i18n_directories = sorted(list(i18n_directories))
    return sorted_i18n_directories


def run(directory: Path) -> int:
    """Run the PoPie for all files under given directory.

    :return: Number of errors.

    When errors are found, .popie files won't be updated.
    """
    if not directory.is_dir():
        print(f"Error: Can't run for '{directory!s}' (path does not exist).")
        sys.exit(ExitCode.INPUT)

    error_count: int = 0
    reporter = Reporter()
    py_files: List[Path] = sorted(directory.glob("**/*.py"))
    for py_file in py_files:
        debug(f"Opening {py_file}")
        with open(py_file, "r", encoding="utf-8") as source:
            tree = ast.parse(source.read())

        analyzer = Analyzer(py_file)
        analyzer.visit(tree)
        analyzer.report_errors()
        analyzer.report_warnings()
        error_count += len(analyzer.errors)

        if analyzer.strings:
            reporter.add_strings(analyzer.strings)
            debug(f"{len(analyzer.strings)} strings found.")

    msgid_count: int = len(reporter.strings)
    rel_directory: str = os.path.relpath(directory, start=directory.cwd())

    if error_count:
        print(
            f"Error: Directory '{rel_directory}' contains {error_count} errors, "
            ".popie files will not be updated."
        )
        return ("found errors", error_count)

    print(f"Info: Found {msgid_count} strings in '{rel_directory}'.")

    po_directory: Path = directory / "po"
    po_directory.mkdir(exist_ok=True)

    updated_files: int = 0
    for lang in LANGUAGES:
        po: Path = po_directory / f"{lang}.popie"
        rel_po: str = os.path.relpath(po, start=po.cwd())
        pofile = PoPieFile(po)
        pofile.update(reporter)
        pofile.save()
        if pofile.is_updated():
            updated_files += 1
        msgstr_count = len([s for s in pofile.translations.values() if s is not None])
        print(f"Info: Saving {msgstr_count} translated strings to '{rel_po}'.")

    return ("updated files", updated_files)
