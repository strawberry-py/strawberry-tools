# Pumpkin Tools

A set of tools for the [strawberry.py](https://github.com/strawberry-py/) Discord bot framework.

## Installation

We are not planning on publishing this package on PyPI. The tools will be mostly used as pre-commit hooks, which are installed directly from the version control system.

If you want to use the tools directly, use the following:

```bash
python3 -m pip install git+https://github.com/strawberry-py/strawberry-tools.git
```

## Tools in this repository

### popie

A tool for generating translation files.

PoPie finds all calls to the translation function

```py
async def hello(self, ctx):
	await ctx.reply(_(ctx, "Hello!"))
```

and places them into separate directory (called `po/`) into files with extension `popie`. That's because the generated files are not GNU-gettext compatible, as we had to make some changes to make the system work in the Discord bot environment.

The generated file will look like this:

```
msgid Hello!
msgstr
```

The .popie file will be commited with the code change and will be waiting for translation. Then the translator will fill in the empty spaces.

By using this tool as pre-commit hook we can ensure that all strings are found, and that the translators have no pending work.

You can enable debugging by setting `POPIE_DEBUG=1`.

## Development

strawberry.py was only intended to be run under Linux. Pumpkin tools try to be more open (you don't need Linux to make the translations), so included packages should work under other operating systems as well. However, they aren't officialy supported and we don't test new features on those systems. Feel free to open compatibility issue, but you may get only limited support, as non-Linux systems are not our priority.

The first thing you have to do is to fork the repository.

```bash
# Download the repository
git clone https://github.com/<your nickname>/strawberry-tools.git
# Move into the repository
cd strawberry-tools
# Install and enable virtual environment
python3 -m venv .venv
source .venv/bin/activate
# Install this package in development mode
python3 -m pip install -e .
# Test the installation by running its CLI tool
popie -h
```
