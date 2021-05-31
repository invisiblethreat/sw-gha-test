"""Test"""

# pylint: disable=missing-docstring

import pytest

@pytest.fixture
def document_empty():
    from ContentAnalyzer.lexers import Document
    doc = Document()
    return doc

@pytest.fixture
def lexertoken_empty():
    from ContentAnalyzer.lexers import LexerToken
    token = LexerToken()
    return token
