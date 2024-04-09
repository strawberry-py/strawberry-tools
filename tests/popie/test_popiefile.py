import tempfile
from pathlib import Path
from typing import Dict, Generator

import pytest

from popie.popiefile import PoPieFile

# Prepare


SIMPLE_PAIRS = {
    "Hello!": "Ahoj!",
    "I don't know that command.": "Takový příkaz neznám.",
}

VARIABLE_PAIRS = {
    "Channel {channel} already exists.": "Kanál {channel} už existuje.",
    "Role **{role}** is mapped to **{group}**.": "Role **{role}** je mapována na **{group}**.",
}


@pytest.fixture
def empty_file() -> Generator[Path, None, None]:
    tf = tempfile.NamedTemporaryFile(mode="r", suffix=".popie")
    yield Path(tf.name)
    tf.close()


def fill_file(path: Path, dictionary: Dict[str, str]) -> None:
    with path.open("w") as handle:
        for msgid, msgstr in dictionary.items():
            handle.write(f"msgid {msgid}\n")
            handle.write("msgstr")
            if msgstr:
                handle.write(f" {msgstr}")
            handle.write("\n\n")


# Test


def test__attributes():
    ppf = PoPieFile(Path("invalid/path.popie"))

    assert ppf.translations == {}
    assert ppf.errors == []
    assert ppf._before is None


def test__load_strings__no_exist():
    ppf = PoPieFile(Path("invalid/path.popie"))
    ppf.load_strings()

    assert ppf.translations == {}
    assert ppf.errors == []


def test__load_strings__empty(empty_file: Path):
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {}
    assert ppf.errors == []
    assert ppf._before == ""


def test__load_strings__simple(empty_file: Path):
    fill_file(empty_file, SIMPLE_PAIRS)
    ppf = PoPieFile(empty_file)

    assert ppf.translations == SIMPLE_PAIRS
    assert ppf.errors == []


def test__load_strings__variable(empty_file: Path):
    fill_file(empty_file, VARIABLE_PAIRS)
    ppf = PoPieFile(empty_file)

    assert ppf.translations == VARIABLE_PAIRS
    assert ppf.errors == []


def test__load_strings__mixed(empty_file: Path):
    fill_file(empty_file, {**SIMPLE_PAIRS, **VARIABLE_PAIRS})
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {**SIMPLE_PAIRS, **VARIABLE_PAIRS}
    assert ppf.errors == []


def test__load_strings__incomplete(empty_file: Path):
    fill_file(empty_file, {"Before": ""})
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {"Before": None}
    assert ppf.errors == []


def test__check_strings__incomplete(empty_file):
    fill_file(empty_file, {"Loaded **{count}** new items.": ""})
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {"Loaded **{count}** new items.": None}
    assert ppf.errors == []


def test__check_strings__typo(empty_file):
    fill_file(empty_file, {"**{count}** items.": "**{cout}** hodnot."})
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {"**{count}** items.": "**{cout}** hodnot."}
    assert ppf.errors == [
        "Translation for '**{count}** items.' contains bad variables: cout.",
    ]


def test__check_strings__typo__mixed(empty_file):
    fill_file(
        empty_file,
        {
            "**{count}** items.": "**{cout}** hodnot.",
            "**{count}** new items.": "**{count}** nových hodnot.",
        },
    )
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {
        "**{count}** items.": "**{cout}** hodnot.",
        "**{count}** new items.": "**{count}** nových hodnot.",
    }
    assert ppf.errors == [
        "Translation for '**{count}** items.' contains bad variables: cout.",
    ]


def test__check_strings__typo__multiple(empty_file):
    fill_file(empty_file, {"{first} v. {second}": "{first} v. {second}"})
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {"{first} v. {second}": "{first} v. {second}"}
    assert ppf.errors == []


def test__check_strings__typo__multiple_mixed(empty_file):
    fill_file(empty_file, {"{first} v. {second}": "{first} v. {secod}"})
    ppf = PoPieFile(empty_file)

    assert ppf.translations == {"{first} v. {second}": "{first} v. {secod}"}
    assert ppf.errors == [
        "Translation for '{first} v. {second}' contains bad variables: first, secod."
    ]
