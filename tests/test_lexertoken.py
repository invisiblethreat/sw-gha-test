"""Lexer tests"""

# pylint: disable=missing-docstring

import pytest

def test_document_instantiate():
    from ContentAnalyzer.lexers import Document
    doc = Document()
    assert True

# def test_get_file_contents_binary_false(document_arista_app_js_lexer_unset):
#     from ContentAnalyzer.lexers import _read_file_contents
#     doc = document_arista_app_js_lexer_unset
#     filename = "tests/data/arista/app.js"
#     data = _read_file_contents(filename)

#     expected_length = 4255
#     expected_line_count = 145
#     expected_type = str

#     observed_length = len(data)
#     observed_line_count = len(data.split('\n'))

#     assert expected_length == observed_length
#     assert expected_line_count == observed_line_count
#     assert isinstance(data, expected_type)

# def test_get_file_contents_binary_true(document_arista_app_js_lexer_unset):
#     from ContentAnalyzer.lexers import _read_file_contents
#     doc = document_arista_app_js_lexer_unset
#     filename = "tests/data/arista/app.js"
#     data = _read_file_contents(filename)

#     expected_type = bytes

#     assert isinstance(data, expected_type)

def test_lexertoken_value_get_value_stripped(lexertoken_empty):
    from ContentAnalyzer.lexers import FORMAT_STRIPPED

    token = lexertoken_empty

    token.value = " The quick brown fox jumped over the lazy dog\n"

    expected = "The quick brown fox jumped over the lazy dog"

    observed = token.get_value(format_type="stripped")

    assert expected == observed

    observed = token.get_value(format_type=FORMAT_STRIPPED)

    assert expected == observed

def test_lexertoken_value_get_value_string(lexertoken_empty):
    from ContentAnalyzer.lexers import FORMAT_STRING

    token = lexertoken_empty

    token.value = 42

    expected = "42"

    observed = token.get_value(format_type="string")

    assert expected == observed

    observed = token.get_value(format_type=FORMAT_STRING)

    assert expected == observed

def test_lexertoken_value_get_value_quote_removal(lexertoken_empty):
    from ContentAnalyzer.lexers import FORMAT_QUOTE_REMOVAL

    token = lexertoken_empty

    token.value = "'test-domain.domain.com'"

    expected = "test-domain.domain.com"

    observed = token.get_value(format_type="quote_removal")

    assert expected == observed

    observed = token.get_value(format_type=FORMAT_QUOTE_REMOVAL)

    assert expected == observed

def test_lexertoken_value_get_value_quote_removal_strip(lexertoken_empty):
    from ContentAnalyzer.lexers import FORMAT_QUOTE_REMOVAL_STRIP

    token = lexertoken_empty

    token.value = "'    test-domain.domain.com'"

    expected = "test-domain.domain.com"

    observed = token.get_value(format_type="quote_removal_strip")

    assert expected == observed

    observed = token.get_value(format_type=FORMAT_QUOTE_REMOVAL_STRIP)

    assert expected == observed

def test_lexertoken_value_get_value_invalid_format(lexertoken_empty):

    token = lexertoken_empty

    token.value = "'    test-domain.domain.com'"

    try:
        _ = token.get_value(format_type="iNvAliD_fOrM4t")
        pytest.fail("Did not raise ValueError")
    except ValueError:
        assert True
