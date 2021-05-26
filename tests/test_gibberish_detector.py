"""Test GibberishDetector"""

# pylint: disable=line-too-long

import pytest


evaluate_results = [
    ('wxll@191256', 0.01744939078028285),
    ('wxllR191256', 0.014156171922924971),
    ('wxllr191256', 0.014156171922924971),
    ('ghettobooty', 0.044730975902739854),
    ('computer', 0.09760059976081899),
    ('automobile', 0.07412281003715614),
    ('hiusodfouisadhfiljalsdljkhfj', 0.023204403613495232),
]


@pytest.fixture
def gibberish_detector_model():
    """Instantiate GibberishDetector model"""

    from api_key_detector.gibberish_detector.gibberish_detector import GibberishDetector

    model_filename = "api_key_detector/gibberish_detector/gibberish_detector.pki"
    detector = GibberishDetector.load(model_filename)

    return detector


@pytest.mark.parametrize("text, expected", evaluate_results)
def test_gibberish_detector_evaluate(gibberish_detector_model, text, expected):
    """Test gibberish detector evaluate results"""

    model = gibberish_detector_model

    observed = model.evaluate(text)
    assert expected == observed, f"Expected to see gibberish probablity of {expected} but observed {observed} for text '{text}'"


def test_gibberish_detector_threshold(gibberish_detector_model):
    """Test gibberish detector evaluate results"""

    model = gibberish_detector_model

    expected = 0.014854112009282536
    observed = model.threshold
    assert expected == observed, f"Expected to see gibberish model threshold value of {expected} but observed {observed}"
