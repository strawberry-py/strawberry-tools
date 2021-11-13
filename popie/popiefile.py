from typing import Dict, Optional
from pathlib import Path

from popie.reporter import Reporter


class PoPieFile:
    """Object representing a PO file."""

    __slots__ = ("filename", "translations", "_before")

    def __init__(self, filename: Path):
        self.filename = filename
        self.translations: Dict[str, str] = {}

        self.load_strings()

        self._before: Optional[str] = None
        if self.filename.exists():
            with open(self.filename, "r") as handle:
                self._before = handle.read()

    def load_strings(self) -> None:
        """Load translations from the file.

        If the file does not exist it is equivalent to empty file containing
        no translations.
        """
        if not self.filename.exists():
            return

        with open(self.filename, "r") as pofile:
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
        with open(self.filename, "w") as pofile:
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
            with open(self.filename, "r") as handle:
                after = handle.read()
        return self._before != after
