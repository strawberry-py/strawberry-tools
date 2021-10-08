import ast
import argparse
import sys
import os
from typing import List
from pathlib import Path

from popie.analyzer import Analyzer
from popie.reporter import Reporter
from popie.languages import LANGUAGES
from popie.popiefile import PoPieFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        help="Path to scanned directory",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Path {directory!s} does not exist.")
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
    print(f"Found {msgid_count} strings.")

    po_directory: Path = directory / "po"
    po_directory.mkdir(exist_ok=True)

    for lang in LANGUAGES:
        po: Path = po_directory / f"{lang}.popie"
        pofile = PoPieFile(po)
        pofile.update(reporter)
        pofile.save()
        msgstr_count = len([s for s in pofile.translations.values() if s is not None])
        print(f"Saving {msgstr_count} translated strings to {po!s}.")
