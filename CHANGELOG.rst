Changelog
=========

1.7.3
-----
- Get path separator from OS instead of hardcoding

1.7.2
-----
- Force UTF-8 for Windows compatibility

1.7.1
-----
- Alter return codes for Windows compatibility
- Force UTF-8 for Windows compatibility

1.7.0
-----
- Add debugging support with ``POPIE_DEBUG=1``
- Add support for ``self.ctx`` format

1.6.1
-----
- Correct PoPie's package version

1.6.0
-----
- Look for 'pie/' directory instead for 'core/'
- Describe why a directory is ignored

1.5.0
-----
- Inspect all function values
- Catch bad placements of .format() in _() calls.

1.4.1
-----
- Keep the list of files stable

1.4.0
-----
- Add ``--strict`` argument

1.3.1
-----
- Fix 'tc' deprecation hint

1.3.0
-----
- Set valid context names to 'ctx', 'utx' and 'gtx'

1.2.1
-----
- Fix package version

1.2.0
-----
- Don't allow spaces and tabs at beggining or the end of strings
- Don't allow newlines inside of the strings

1.1.0
-----
- Add detached mode

1.0.2
-----
- Correctly inspect ``_(ctx, "foo").format()``

1.0.1
-----
- Visit left and right ``BinOp`` branches

1.0.0
-----
- Initial release
