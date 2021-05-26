"""Gibberish detector"""

import logging
import math
import pickle
from typing import Iterable, List, Set

Matrix = List[List[float]]

# ACCEPTED_CHARSET = 'abcdefghijklmnopqrstuvwxyz '
# ACCEPTED_CHARSET = " +-/0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
# ACCEPTED_CHARSET = " !#+,-./0123456789:;=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
ACCEPTED_CHARSET = "0123456789abcdefghijklmnopqrstuvwxyz"

character_position = {charset: i for i, charset in enumerate(ACCEPTED_CHARSET)}


def init_log_probability_matrix(smoothing_factor: int = 10, charset: str = None) -> Matrix:
    """Initialize log probability matrix using a smoothing factor and charset."""

    k = len(charset)

    # Assume we have seen 10 (smoothing_factor) of each character pair.  This acts
    # as a kind of prior or smoothing factor.  This way, if we see a character transition
    # live that we've never observed in the past, we won't assume the entire
    # string has 0 probability.
    log_prob_matrix = [[smoothing_factor for i in range(k)] for i in range(k)]

    return log_prob_matrix


# pylint: disable=line-too-long
def update_log_probability_matrix_from_lines(log_prob_matrix: Matrix, lines: List[str], charset: str) -> Matrix:
    """Update log probability matrix with the content from a list of strings."""

    # Count transitions from big text files, taken
    # from http://norvig.com/spell-correct.html
    for line in lines:
        for char_a, char_b in ngram(2, line, charset):
            log_prob_matrix[character_position[char_a]][character_position[char_b]] += 1

    return log_prob_matrix
# pylint: enable=line-too-long


# pylint: disable=line-too-long
def update_log_probability_matrix_from_files(log_prob_matrix: Matrix, files: List[str], charset: str) -> Matrix:
    """Update log probability matrix with the content from a list of files."""

    for filename in files:
        lines = open(filename, 'r', encoding='utf-8')
        log_prob_matrix = update_log_probability_matrix_from_lines(log_prob_matrix, lines, charset)
        lines.close()

    return log_prob_matrix
# pylint: enable=line-too-long


def normalize_log_probability_matrix(log_prob_matrix: Matrix) -> Matrix:
    """Normalize log probability matrix"""

    # Normalize the probability_mat so that they become log probabilities.
    # We use log probabilities rather than straight probabilities to avoid
    # numeric underflow issues with long texts.
    # This contains a justification:
    # http://squarecog.wordpress.com/2009/01/10/dealing-with-underflow-in-joint-probability-calculations/

    # Iterate over each row in the matrix
    for row in log_prob_matrix:
        # Sum matrix row
        s = float(sum(row))

        # Iterate over each value in the row and update its
        # value with its current value divided by 's'.
        for j, value in enumerate(row):
            row[j] = math.log(value / s)

    return log_prob_matrix


# pylint: disable=line-too-long
def evaluate_from_log_probability_matrix(log_prob_matrix: Matrix, line: str, default_to_0: bool = False, charset: str = None) -> float:
    """Return the average transition prob from line through log_prob_matrix.

    A value which indicates how likely is the string to be composed of natural language words.
    Recognized languages depends on the training set. The lower the value, the more
    probable is that the string is gibberish.

    Args:

        line (str): String to evaluate.
        default_to_0 (bool, optional): Whenever the submitted string it's made of just one or zero
                            accepted characters, returns 0. Defaults to False.
        charset (str, optional): Charset to use. Defaults to ACCEPTED_CHARSET.

    Return:

        float: The probability that string is NOT gibberish.
    """

    charset = charset or ACCEPTED_CHARSET

    if default_to_0 and len(normalize(line, charset)) <= 1:
        return 0

    log_prob = 0.0
    transition_count = 0

    for char_a, char_b in ngram(2, line, charset):
        log_prob += log_prob_matrix[character_position[char_a]][character_position[char_b]]
        transition_count += 1

    # The exponentiation translates from log probs to probs.
    return math.exp(log_prob / (transition_count or 1))


class GibberishDetector:
    """GibberishDetector.

    Args:

        charset (str, optional): Charset to use. Defaults to ACCEPTED_CHARSET.
    """

    def __init__(self, charset: str = None):
        self.log_prob_mat: Matrix = None
        self.threshold: float = None
        self.charset = charset or ACCEPTED_CHARSET


    # pylint: disable=line-too-long
    def train(self, learnset: List[str], good_test: Set[str], bad_test: Set[str]) -> None:
        """Trains the Gibberish Detector, i.e. creates the transition probability matrix.

        Args:

            learnset (List[str]): List of file paths containing non-gibberish lines of text. (e.g. books, stories)
            good_test (Set[str]): Set of file paths where each line doesn't contain gibberish, used for testing.
            bad_test (Set[str]): Set of file paths where each line contains gibberish, used for testing.

        Returns:

            None.
        """

        logging.info("Training...")

        self.log_prob_mat = init_log_probability_matrix(smoothing_factor=10, charset=self.charset)

        self.log_prob_mat = update_log_probability_matrix_from_files(self.log_prob_mat, learnset, self.charset)

        self.log_prob_mat = normalize_log_probability_matrix(self.log_prob_mat)

        # Find the probability of generating a few arbitrarily choosen good and
        # bad phrases.
        good_probs = []
        for good_test_file in good_test:
            with open(good_test_file, 'r', encoding='utf-8') as f:
                for line in f:
                    good_probs.append(self.evaluate(line))

        bad_probs = []
        for bad_test_file in bad_test:
            with open(bad_test_file, 'r', encoding='utf-8') as f:
                for line in f:
                    bad_probs.append(self.evaluate(line))

        # Assert that we actually are capable of detecting the junk.
        assert min(good_probs) > max(bad_probs)

        # And pick a threshold halfway between the worst good and best bad inputs.
        self.threshold = (min(good_probs) + max(bad_probs)) / 2

        logging.info("Finished training")
    # pylint: enable=line-too-long


    # pylint: disable=line-too-long
    def evaluate(self, line: str, default_to_0: bool = False) -> float:
        """Return the average transition prob from l through log_prob_mat.

        A value which indicates how likely is the string to be composed of natural language words.
        Recognized languages depends on the training set. The lower the value, the more
        probable is that the string is gibberish.

        Args:

            line (str): String to evaluate.
            default_to_0 (bool, optional): Whenever the submitted string it's made of just one or zero
                             accepted characters, returns 0. Defaults to False.

        Return:

            float: The probability that string is NOT gibberish.
        """

        return evaluate_from_log_probability_matrix(self.log_prob_mat, line, default_to_0=default_to_0, charset=self.charset)
    # pylint: enable=line-too-long


    # pylint: disable=line-too-long
    @classmethod
    def train_from_text_files(cls, training_files: List[str], good_test_files: List[str], bad_test_files: List[str]) -> 'GibberishDetector':
        """Trains the model from the contents of text files.

        Args:

            training_files (List[str]): Paths to files containing non-gibberish lines of text.
            good_test_files (List[str]): Paths of files containing non-gibberish test data.
            bad_test_files (List[str]): Paths of files containing gibberish.

        Returns:

            GibberishDetector: GibberishDetector instance.
        """

        instance = cls()
        instance = GibberishDetector()
        instance.train(training_files, good_test_files, bad_test_files)

        return instance
    # pylint: enable=line-too-long


    def save(self, filename: str) -> None:
        """Save model to file.

        Args:

            filename (str): Filename to save to.

        Returns:

            None.
        """

        logging.info("Saving model to file '%s'", filename)

        with open(filename, 'wb') as f:
            pickle.dump(self, f)
            logging.info("Finished saving model to file")


    @classmethod
    def load(cls, filename: str) -> 'GibberishDetector':
        """Load model from file.

        Args:

            filename (str): Filename to load from.
        """

        instance = load(filename)
        return instance


def normalize(line: str, charset: str) -> List[str]:
    """Return only the subset of chars from accepted_chars.

    This helps keep the my_model relatively small by ignoring punctuation,
    infrequenty symbols, etc.

    Args:

        line (str): Line of text.
        charset (str): Character set.

    Returns:

        List[str]: A subset of chars from charset.
    """
    return [c.lower() for c in line if c.lower() in charset]


def ngram(number: int, line: str, charset: str) -> Iterable[str]:
    """Return all `number` grams from `line` after normalizing with charset.

    Args:

        number (int): Number of grams to provide.
        line (str): Line to evaluate.
        charset (str): Charset to use.

    Yields:

        Generator[str]: A `number` length string of characters from `line`.
    """

    filtered = normalize(line, charset)
    for start in range(0, len(filtered) - number + 1):
        yield ''.join(filtered[start:start + number])


def load(filename: str) -> GibberishDetector:
    """Load GibberishDetector from a pickle file.

    Args:

        filename (str): Pickle filename.

    Returns:

        GibberishDetector: Unpickled GibberishDetector instance.
    """

    logging.info("Loading from pickled file '%s'", filename)

    with open(filename, 'rb') as f:
        instance = pickle.load(f)
        logging.info("Finished loading from pickled file")

    return instance


# def main():
#     """Main."""

#     model_filename = "api_key_detector/gibberish_detector/gibberish_detector.pki"

#     # detector = load(model_filename)
#     detector = GibberishDetector.load(model_filename)
#     print(f"\nDetector threshold: {detector.threshold}\n")

#     test_values = [
#         'wxll@191256',
#         'wxllR191256',
#         'wxllr191256',
#         'ghettobooty',
#         'computer',
#         'automobile',
#         'hiusodfouisadhfiljalsdljkhfj',
#     ]

#     for value in test_values:
#         result = detector.evaluate(value)
#         print(f"'{value}' => {result}")

#     # detector.save(model_filename)

#     print("", end='')

# if __name__ == "__main__":
#     main()
