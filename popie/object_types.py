from pathlib import Path
from typing import Optional


class AbstractGettextObject:
    def __init__(self, filename: Path, line: int, column: int, text: str):
        self.filename = filename
        self.line = line
        self.column = column
        self.text = text

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} filename='{self.filename!s}' "
            f"line={self.line} column={self.column} "
            f"text='{self.text}'>"
        )


class Error(AbstractGettextObject):
    """Information about invalid call to the translation function."""

    __slots__ = ("filename", "line", "column", "text")

    def __str__(self) -> str:
        return f"{self.filename!s}:{self.line}:{self.column} {self.text} "


class String(AbstractGettextObject):
    """String reference."""

    __slots__ = ("filename", "line", "column", "text", "translation")

    def __init__(self, filename: Path, line: int, column: int, text: str):
        super().__init__(filename, line, column, text)
        self.translation: Optional[str] = None
