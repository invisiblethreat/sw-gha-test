"""Test key detector"""

# pylint: disable=line-too-long

import pytest
from api_key_detector import detector

# For detecting
api_key_detect_set = [
    (["justsomething", "reallynothingimportant", "AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE", "eqwioqweioqiwoe"], [False, False, True, False]),
]

# For filtering
api_key_filter_set = [
    (["justsomething", "reallynothingimportant", "AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE", "eqwioqweioqiwoe"], ["AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE"]),
]


@pytest.mark.parametrize("keys, expected", api_key_detect_set)
def test_api_key_detector(keys, expected):
    """Test api key detector"""

    observed = detector.detect_api_keys(keys)
    assert expected == observed, f"Expected detection results to be {expected} but observed {observed} for keys {keys}"


@pytest.mark.parametrize("keys, expected", api_key_filter_set)
def test_api_key_filter(keys, expected):
    """Test api key filter"""

    observed = detector.filter_api_keys(keys)
    assert expected == observed, f"Expected filter results to be {expected} but observed {observed} for keys {keys}"
