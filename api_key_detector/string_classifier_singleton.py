"""
Singleton implementation for classifier object
"""

from api_key_detector.string_classifier import StringBinaryClassifier

def __get_module_path() -> str:
    import os
    basepath = os.path.dirname(os.path.realpath(__file__))
    return basepath

__get_full_path = lambda filename: f"{__get_module_path()}/{filename}"

MODEL_FILENAME = "string_classifier.pki"

classifier = StringBinaryClassifier.load(__get_full_path(MODEL_FILENAME))
