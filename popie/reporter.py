from typing import List

from popie.object_types import String


class Reporter:
    """Object holding strings found in the source files."""

    __slots__ = ("strings",)

    def __init__(self):
        self.strings: List[str] = []

    def add_strings(self, new_strings: List[String]):
        """Add list of strings to internal pool of strings."""
        self.strings += [s.text for s in new_strings]
