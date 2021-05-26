"""Test entropy"""

# pylint: disable=line-too-long

import pytest
from api_key_detector.entropy import shannon_entropy, normalized_entropy

CHARSETS = {
    'HEX_CHARS': "0123456789ABCDEFabcdef",
    'HEX_CHARS_EXT': "-0123456789ABCDEFabcdef",  # for GUID
    'BASE64_CHARS': "+/0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    'BASE64_CHARS_EXT': "+-/0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",
    'BASE64_CHARS_EXT2': "+,-./0123456789;=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",
    'BASE91_CHARS': "!\"#$%&()*+,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    'BASE91_CHARS_EXT': "!\"#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    'PRINT_CHARS': " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
}

CHARSET_NAMES = [
    'HEX_CHARS',
    'HEX_CHARS_EXT',
    'BASE64_CHARS',
    'BASE64_CHARS_EXT',
    'BASE64_CHARS_EXT2',
    'BASE91_CHARS',
    'BASE91_CHARS_EXT',
    'PRINT_CHARS',
]

shannon_test_values = {
    'justsomething': {
        'HEX_CHARS': 0.28464920908777636,
        'HEX_CHARS_EXT': 0.28464920908777636,
        'BASE64_CHARS': 3.392747410448785,
        'BASE64_CHARS_EXT': 3.392747410448785,
        'BASE64_CHARS_EXT2': 3.392747410448785,
        'BASE91_CHARS': 3.392747410448785,
        'BASE91_CHARS_EXT': 3.392747410448785,
        'PRINT_CHARS': 3.392747410448785,
    },
    'AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE': {
        'HEX_CHARS': 1.7377245712463278,
        'HEX_CHARS_EXT': 1.7377245712463278,
        'BASE64_CHARS': 4.547064341344576,
        'BASE64_CHARS_EXT': 4.682587475161557,
        'BASE64_CHARS_EXT2': 4.682587475161557,
        'BASE91_CHARS': 4.682587475161557,
        'BASE91_CHARS_EXT': 4.682587475161557,
        'PRINT_CHARS': 4.682587475161557,
    }
}

normalized_test_values = {
    'justsomething': {
        'True': {
            'BASE64_CHARS_EXT': 0.003895232388574954,
            'BASE64_CHARS_EXT2': 0.0037282938576360274,
            'BASE64_CHARS': 0.004015085692838799,
            'BASE91_CHARS_EXT': 0.0028062426885432467,
            'BASE91_CHARS': 0.002836745326462195,
            'HEX_CHARS_EXT': 0.0009520040437718273,
            'HEX_CHARS': 0.000995276954852365,
            'PRINT_CHARS': 0.002747163895100231,
        },
        'False': {
            'BASE64_CHARS_EXT': 0.2609805700345219,
            'BASE64_CHARS_EXT2': 0.2609805700345219,
            'BASE64_CHARS': 0.2609805700345219,
            'BASE91_CHARS_EXT': 0.2609805700345219,
            'BASE91_CHARS': 0.2609805700345219,
            'HEX_CHARS_EXT': 0.021896093006752028,
            'HEX_CHARS': 0.021896093006752028,
            'PRINT_CHARS': 0.2609805700345219,
        }
    },
    'AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE': {
        'True': {
            'BASE64_CHARS_EXT': 0.0017920350077158657,
            'BASE64_CHARS_EXT2': 0.0017152335073851858,
            'BASE64_CHARS': 0.0017937137441201485,
            'BASE91_CHARS_EXT': 0.0012910359733006775,
            'BASE91_CHARS': 0.0013050689730104675,
            'HEX_CHARS_EXT': 0.0019372626212333644,
            'HEX_CHARS': 0.002025320013107608,
            'PRINT_CHARS': 0.0012638562685996105,
        },
        'False': {
            'BASE64_CHARS_EXT': 0.120066345516963,
            'BASE64_CHARS_EXT2': 0.120066345516963,
            'BASE64_CHARS': 0.11659139336780965,
            'BASE91_CHARS_EXT': 0.120066345516963,
            'BASE91_CHARS': 0.120066345516963,
            'HEX_CHARS_EXT': 0.04455704028836738,
            'HEX_CHARS': 0.04455704028836738,
            'PRINT_CHARS': 0.120066345516963,
        }
    },
}

shannon_test_ids = []
normalized_test_ids = []

compiled_shannon_test_values = []
for test_text, test_values in shannon_test_values.items():
    for this_charset_name in CHARSET_NAMES:
        shannon_test_ids.append(f"{test_text} {this_charset_name}")
        this_charset_value = CHARSETS[this_charset_name]
        expected_entropy_value = test_values[this_charset_name]
        this_charset_value = CHARSETS[this_charset_name]
        compiled_shannon_test_values.append((test_text, expected_entropy_value, this_charset_name, this_charset_value))

compiled_normalized_test_values = []
for test_text, test_values in normalized_test_values.items():
    for this_charset_name in CHARSET_NAMES:
        for normalization_argument in (True, False):
            normalized_test_ids.append(f"{test_text} {this_charset_name} {normalization_argument}")
            this_charset_value = CHARSETS[this_charset_name]
            expected_entropy_value = test_values[str(normalization_argument)][this_charset_name]
            this_charset_value = CHARSETS[this_charset_name]
            compiled_normalized_test_values.append((test_text, expected_entropy_value, this_charset_name, this_charset_value, normalization_argument))


@pytest.fixture(params=compiled_shannon_test_values)
def words_with_charsets(request):
    """Image filenames"""
    return request.param


@pytest.mark.parametrize("text, expected, charset_name, charset_value", compiled_shannon_test_values, ids=shannon_test_ids)
def test_shannon_entropy(text, expected, charset_name, charset_value):
    """Test shannon entropy"""

    observed = shannon_entropy(text, charset_value)
    assert expected == observed, f"Expected shannon entropy for {text} to be {expected} but observed {observed} using charset {charset_name}"


@pytest.mark.parametrize("text, expected, charset_name, charset_value, charset_normalization", compiled_normalized_test_values, ids=normalized_test_ids)
def test_normalized_entropy(text, expected, charset_name, charset_value, charset_normalization):
    """Test normalized entropy"""

    observed = normalized_entropy(text, charset_value, charset_normalization=charset_normalization)
    assert expected == observed, f"Expected normalized entropy for {text} to be {expected} but observed {observed} using charset {charset_name} and normalization {charset_normalization}"
