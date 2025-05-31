import pytest
from app.utils.sanitization import sanitize_input, sanitize_options

def test_sanitize_input_removes_disallowed_chars():
    raw_input = "<script>alert('hello')</script>{};|`'""
    expected_output = "scriptalerthelloscript" # All disallowed chars removed
    assert sanitize_input(raw_input) == expected_output

def test_sanitize_input_empty_string():
    assert sanitize_input("") == ""

def test_sanitize_input_already_clean():
    clean_input = "This is a clean sentence."
    assert sanitize_input(clean_input) == clean_input

def test_sanitize_input_max_length():
    long_input = "a" * 2000
    expected_output = "a" * 1024
    assert sanitize_input(long_input) == expected_output

def test_sanitize_input_non_string():
    assert sanitize_input(123) == ""
    assert sanitize_input(None) == ""
    assert sanitize_input([]) == ""

def test_sanitize_options_valid():
    raw_options = {
        "max_length": 100,
        "detail_level": "<high>",
        "user_comment": "Please summarize this for me; it's important."
    }
    expected_options = {
        "max_length": 100,
        "detail_level": "high",
        "user_comment": "Please summarize this for me its important."
    }
    assert sanitize_options(raw_options) == expected_options

def test_sanitize_options_empty():
    assert sanitize_options({}) == {}

def test_sanitize_options_non_dict():
    assert sanitize_options("not a dict") == {}
    assert sanitize_options(None) == {}

def test_sanitize_options_mixed_types():
    raw_options = {
        "count": 5,
        "enabled": True,
        "filter_text": "{danger}"
    }
    expected_options = {
        "count": 5,
        "enabled": True,
        "filter_text": "danger"
    }
    assert sanitize_options(raw_options) == expected_options
