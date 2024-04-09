import difflib
import functools
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from popie.reporter import Reporter


class PoPieFile:
    """Object representing a PO file."""

    __slots__ = ("filename", "translations", "errors", "_before")

    def __init__(self, filename: Path):
        self.filename = filename
        self.translations: Dict[str, str] = {}
        self.errors: List[str] = []

        self.load_strings()
        self.check_strings()

        self._before: Optional[str] = None
        if self.filename.exists():
            with open(self.filename, "r", encoding="utf-8") as handle:
                self._before = handle.read()

    def report_errors(self):
        """Print errors to the stdout."""
        for error in self.errors:
            print(f"PopieFile error: {error}")

    def load_strings(self) -> None:
        """Load translations from the file.

        If the file does not exist it is equivalent to empty file containing
        no translations.
        """
        if not self.filename.exists():
            return

        with open(self.filename, "r", encoding="utf-8") as pofile:
            msgid: str = ""
            msgstr: Optional[str] = None

            for line in pofile.readlines():
                line = line.strip()

                if not len(line):
                    continue

                if line.startswith("msgid "):
                    msgid: str = line[len("msgid ") :]
                    continue

                if line.startswith("msgstr"):
                    msgstr: str = line[len("msgstr") :].strip()
                    if not len(msgstr):
                        msgstr = None

                    self.translations[msgid] = msgstr
                    continue

    def check_strings(self) -> None:
        for key, value in self.translations.items():
            if value is None:
                continue
            key_variables: List[str] = re.findall(r"{(.+?)}", key)
            value_variables: List[str] = re.findall(r"{(.+?)}", value)

            if set(key_variables) != set(value_variables):
                error: str = (
                    f"Translation for '{key}' contains bad variables: "
                    f"{', '.join(value_variables)}."
                )
                self.errors.append(error)

    def update(self, reporter: Reporter):
        """Update state of translations.

        If the reporter's string is contained in current translations,
        it will be copied, so the translation is not lost.

        If the reporter's string is not contained in current translations,
        it will get set to `None`.

        Strings not found by the reporter, but are present in the file,
        have been removed from the source files and can be removed here, too.
        """
        translations = self.translations
        self.translations = {}

        for string in reporter.strings:
            if string in translations.keys():
                self.translations[string] = translations[string]
            else:
                self.translations[string] = None

    def save(self):
        """Dump the content into the file."""
        with open(self.filename, "w", encoding="utf-8", newline="\n") as pofile:
            string_count: int = len(self.translations)
            for i, (msgid, msgstr) in enumerate(self.translations.items()):
                pofile.write(f"msgid {msgid}\n")

                if msgstr is not None:
                    pofile.write(f"msgstr {msgstr}\n")
                else:
                    pofile.write("msgstr\n")

                # don't write double newline at the end
                if i < string_count - 1:
                    pofile.write("\n")

    @functools.lru_cache(maxsize=None)
    def _get_after(self) -> Optional[str]:
        """Get contents of changed file."""
        after: Optional[str] = None
        if self.filename.exists():
            with open(self.filename, "r", encoding="utf-8") as handle:
                after = handle.read()
        return after

    def is_updated(self) -> bool:
        """Decide if the file was updated or not."""
        return self._before != self._get_after()

    def _color_diff(self, lines: List[str]) -> List[str]:
        """Colorize diff output."""
        # Windows does not support bash escape codes
        if os.name == "nt":
            return lines
        new_lines: List[str] = []
        for line in lines:
            if line.startswith("+"):
                line = f"\033[32m{line}\033[0m"
            elif line.startswith("-"):
                line = f"\033[31m{line}\033[0m"
            elif line.startswith("@"):
                line = f"\033[33m{line}\033[0m"
            new_lines.append(line)
        return new_lines

    def print_diff(self) -> None:
        """Create and print difference between 'before' and 'after'."""
        if not self._before:
            return

        after = self._get_after()
        if not after:
            return

        before_lines = [line.strip() for line in self._before.split("\n")]
        after_lines = [line.strip() for line in after.split("\n")]

        diff_lines = [
            line
            for line in difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile=f"{self.filename.parents[1].name}/; {self.filename.name}",
                tofile="PoPie changes",
                n=0,
                lineterm="",
            )
        ]
        diff_lines = self._color_diff(diff_lines)
        diff = "\n" + "\n".join(diff_lines)
        print(diff)
