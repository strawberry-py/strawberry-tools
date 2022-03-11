import re
from typing import Dict, Optional, List
from pathlib import Path

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
            key_variables = set(re.findall(r"{(.+?)}", key))
            value_variables = set(re.findall(r"{(.+?)}", value))

            if key_variables != value_variables:
                vv = ", ".join(value_variables)
                e = f"Translation for '{key}' contains bad variables: {vv}."
                self.errors.append(e)

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
        with open(self.filename, "w", encoding="utf-8") as pofile:
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

    def is_updated(self) -> bool:
        after: Optional[str] = None
        if self.filename.exists():
            with open(self.filename, "r", encoding="utf-8") as handle:
                after = handle.read()
        return self._before != after
