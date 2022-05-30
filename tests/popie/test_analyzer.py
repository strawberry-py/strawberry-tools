import ast
from pathlib import Path

from popie.analyzer import Analyzer


def test_basic():
    tree = ast.parse("_(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_assignment():
    tree = ast.parse("s = _(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_formatted():
    tree = ast.parse("_(ctx, 'Text {s}').format(s='s')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text {s}"


def test_formatted_with_assignment():
    tree = ast.parse("s = _(ctx, 'Text {s}').format(s='s')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text {s}"


def test_concatenation():
    tree = ast.parse("_(ctx, 'Text1') + _(ctx, 'Text2')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text1"
    assert analyzer.strings[1].text == "Text2"


def test_concatenation_with_assignment():
    tree = ast.parse("s = _(ctx, 'Text1') + _(ctx, 'Text2')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text1"
    assert analyzer.strings[1].text == "Text2"


def test_in_list():
    tree = ast.parse("[_(ctx, 'Text')]")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_in_list_with_assignment():
    tree = ast.parse("s = [_(ctx, 'Text')]")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_in_tuple():
    tree = ast.parse("(_(ctx, 'Text'), )")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_in_tuple_with_assignment():
    tree = ast.parse("s = (_(ctx, 'Text'), )")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_key_of_dict():
    tree = ast.parse("{_(ctx, 'Text'): 'value'}")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_value_of_dict():
    tree = ast.parse("{'key': _(ctx, 'Text')}")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_in_try_block():
    tree = ast.parse("try:\n\t_(ctx, 'Text')\nexcept:\n\tpass")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_in_except_block():
    tree = ast.parse("try:\n\tpass\nexcept:\n\t_(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_in_finally_block():
    tree = ast.parse("try:\n\tpass\nexcept:\n\tpass\nfinally:\n\t_(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_list_comprehention():
    tree = ast.parse("[_(ctx, 'Text') for _ in range(10)]")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_unnamed_argument():
    tree = ast.parse("function(_(ctx, 'Text'))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_named_argument():
    tree = ast.parse("function(key=_(ctx, 'Text'))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_named_argument_after_unnamed_argument():
    tree = ast.parse("function('key', key=_(ctx, 'Text'))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_named_argument_after_named_argument():
    tree = ast.parse("function(key='key', value=_(ctx, 'Text'))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_unnamed_list_argument():
    tree = ast.parse("function([_(ctx, 'Text')])")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_named_list_argument():
    tree = ast.parse("function(key=[_(ctx, 'Text')])")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_unnamed_tuple_argument():
    tree = ast.parse("function((_(ctx, 'Text'), ))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_named_tuple_argument():
    tree = ast.parse("function((_(ctx, 'Text'), ))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_unnamed_dict_argument_as_key():
    tree = ast.parse("function({_(ctx, 'Text'): 'value'})")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_unnamed_dict_argument_as_value():
    tree = ast.parse("function({'key': _(ctx, 'Text')})")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_named_dict_argument_as_key():
    tree = ast.parse("function(key={_(ctx, 'Text'): 'value'})")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_inside_named_dict_argument_as_value():
    tree = ast.parse("function(key={'key': _(ctx, 'Text')})")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_fn_value():
    # https://github.com/pumpkin-py/pumpkin-tools/issues/4
    text = 'object.function(key=(_(ctx, "Text") + "\\n").format())'
    tree = ast.parse(text)
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert len(analyzer.strings) == 1
    assert analyzer.strings[0].text == "Text"


def test_cls_attribute():
    tree = ast.parse("class C:\n\tattr = _(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_cls_fn_basic():
    tree = ast.parse("class C:\n\tdef f(self):\n\t\t_(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_cls_fn_with_assignment():
    tree = ast.parse("class C:\n\tdef f(self):\n\t\ts = _(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_cls_async_fn_basic():
    tree = ast.parse("class C:\n\tasync def f(self):\n\t\t_(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_cls_async_fn_with_assignment():
    tree = ast.parse("class C:\n\tasync def f(self):\n\t\ts = _(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_disallow_space_before():
    tree = ast.parse("_(ctx, ' Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert (
        analyzer.errors[0].text == "Translation string must not start with whitespace."
    )


def test_disallow_space_after():
    tree = ast.parse("_(ctx, 'Text ')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.errors[0].text == "Translation string must not end with whitespace."


def test_disallow_newline():
    tree = ast.parse(r"_(ctx, 'Te\nxt')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.errors[0].text == "Translation string must not contain newlines."


def test_diallow_bad_format():
    # https://github.com/pumpkin-py/pumpkin-tools/issues/6
    tree = ast.parse("_(ctx, '{text}'.format(text='Text'))")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.errors[0].text == (
        "Bad '.format()' placement in translation function "
        "(has to be outside of '_()' call.)"
    )


def test_diallow_bad_format_FP():
    # Prevent false positives for test_diallow_bad_format()
    tree = ast.parse("'{text}'.format(text='Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert len(analyzer.errors) == 0


def test_context_ctx():
    tree = ast.parse("_(ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_context_utx():
    tree = ast.parse("_(utx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_context_gtx():
    tree = ast.parse("_(gtx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_context_tc():
    tree = ast.parse("_(tc, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"
    assert analyzer.warnings[0].text == (
        "Translation context variable name 'tc' is deprecated, "
        "use 'utx' instead. 'tc' may not be accepted in the future."
    )


def test_context_self_ctx():
    tree = ast.parse("_(self.ctx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_context_self_utx():
    tree = ast.parse("_(self.utx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_context_self_gtx():
    tree = ast.parse("_(self.gtx, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.strings[0].text == "Text"


def test_context_self_foo():
    tree = ast.parse("_(self.foo, 'Text')")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert len(analyzer.strings) == 0
    assert analyzer.errors[0].text == (
        "Inherited translation context variable has to be "
        "one of 'ctx', 'utx', 'gtx', got 'foo'."
    )


def test_disallow_variable_arg():
    tree = ast.parse("_(ctx, text)")
    analyzer = Analyzer(Path("."))
    analyzer.visit(tree)
    assert analyzer.errors[0].text == (
        "Bad string argument (has to be literal, not variable)."
    )
