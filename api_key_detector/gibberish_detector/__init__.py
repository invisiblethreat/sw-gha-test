"""Init"""

from api_key_detector.gibberish_detector.gibberish_detector import GibberishDetector

def __get_module_path() -> str:
    import os
    basepath = os.path.dirname(os.path.realpath(__file__))
    return basepath

__get_full_path = lambda filename: f"{__get_module_path()}/{filename}"

MODEL_FILENAME = "gibberish_detector.pki"
detector = GibberishDetector.load(__get_full_path(MODEL_FILENAME))
