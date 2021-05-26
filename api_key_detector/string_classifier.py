"""String classifier"""

import logging
import pickle
from functools import lru_cache
from typing import List, Tuple

import numpy as np
from sklearn.neural_network import MLPClassifier

from api_key_detector import charset
from api_key_detector.entropy import normalized_entropy
from api_key_detector.gibberish_detector import detector
from api_key_detector.sequentiality import string_sequentiality


class StringBinaryClassifier:
    """
    Wrapper object for a Neural Network.
    Used to classify strings based on entropy, sequentiality and gibberish
    """

    # pylint: disable=line-too-long
    def __init__(self, max_iter: int = 100):
        """
        :param max_iter: max iterations for wrapped Neural Network
        """
        self.__neural_network = MLPClassifier(hidden_layer_sizes=(100, 100), solver='lbfgs', max_iter=max_iter, verbose=True)
        self.input_mean = None
        self.input_stdev = None
        self.logger = logging.getLogger(self.__class__.__name__)
    # pylint: enable=line-too-long


    def calculate_normalization_parameters(self, matrix) -> None:
        """
        Calculates train set mean and standard deviation to normalize input
        :param matrix: input train set
        """
        self.input_mean = matrix.mean(axis=0)
        self.input_stdev = matrix.std(axis=0)


    def train(self, matrix_learn_set, good_test, bad_test) -> None:
        """
        Trains the wrapped neural network

        :param matrix_learn_set: input train set, where each row contains the
        already-computed input features
        :param good_test:  set of file paths where each line is a class 1 string, used for testing
        :param bad_test: set of file paths where each line is a class 0 string, used for testing
        """

        # always better to shuffle data before feeding to a NN
        np.random.shuffle(matrix_learn_set)

        # separate expected outputs and inputs features
        train_outputs = np.array(matrix_learn_set[:, -1])
        train_inputs = matrix_learn_set[:, 0:-1]
        self.calculate_normalization_parameters(train_inputs)
        if self.input_mean is not None and self.input_stdev is not None:
            train_inputs -= self.input_mean
            train_inputs /= self.input_stdev

        # train the NN
        self.logger.info("Started training NN...")
        self.__neural_network.fit(train_inputs, train_outputs)
        self.logger.info("Training finished.")

        tot_count = 0
        err_count = 0

        for good_test_file in good_test:
            for line in open(good_test_file):
                tot_count += 1
                line = line.replace('\n', '').replace('\r', '')
                prediction = self.predict_strings([line])
                if prediction[0] != 1:
                    self.logger.warning("String %s was not detected as an API key", line)
                    err_count += 1

        for bad_test_file in bad_test:
            for line in open(bad_test_file):
                tot_count += 1
                line = line.replace('\n', '').replace('\r', '')
                prediction = self.predict_strings([line])
                if prediction[0] != 0:
                    self.logger.warning("String %s was wrongly detected as an API key", line)
                    err_count += 1

        score = (tot_count - err_count) / tot_count
        self.logger.info("Test finished. Classifier score: %s", score)


    def predict(self, inputs: List[List[float]]) -> List[float]:
        """
        Predicts the class for the inserted inputs

        :param inputs: matrix where each row contains input features
        :return: a list of class predictions, one element for each input
        :rtype: list
        """

        # normalization
        if self.input_mean is not None and self.input_stdev is not None:
            inputs = inputs - self.input_mean
            inputs = inputs / self.input_stdev
        return self.__neural_network.predict(inputs)

    def predict_proba(self, inputs: List[np.ndarray]) -> np.ndarray:
        """Predicts the probablity for each class.

        Args:

            inputs (List[np.ndarray]): Matrix where each row contains input features.

        Returns:

            np.ndarray: Matrix where element [0][1] is True probablity
                and [0][0] is False probability.
        """

        # normalization
        if self.input_mean is not None and self.input_stdev is not None:
            inputs = inputs - self.input_mean
            inputs = inputs / self.input_stdev
        return self.__neural_network.predict_proba(inputs)

    def predict_strings(self, strings: List[str]) -> List:
        """
        Predicts the class for the inserted inputs

        :param strings: a list of string whose class should be predicted
        :return: a list of class predictions, one element for each input
        :rtype: list
        """

        inputs = []
        for string in strings:
            inputs.append(calculate_all_features(string))
        return self.predict(np.array(inputs))

    def predict_string(self, string: str):
        """Predict a single string.

        Args:

            string (str): String to predict.

        Returns:

            no idea
        """

        inputs = [calculate_all_features(string)]
        result = self.predict(np.array(inputs))
        return result

    # pylint: disable=line-too-long
    def predict_string_with_inputs(self, string: str) -> Tuple[bool, Tuple[float, float, float, float]]:
        """Predict a single string and include inputs in return results.

        Args:

            string (str): String to predict.

        Returns:

            Tuple[bool, Tuple[float, float, float, float]]: Tuple containing prediction probability
                and Tuple of feature calculation.
        """
        inputs = [calculate_all_features(string)]
        input_ndarray = np.array(inputs)
        result = self.predict(input_ndarray)
        return result, input_ndarray
    # pylint: enable=line-too-long

    def predict_string_proba(self, string: str):
        """Predict a single string.

        Args:

            string (str): String to predict.

        Returns:

            no idea
        """
        inputs = [calculate_all_features(string)]
        result = self.predict_proba(np.array(inputs))
        return result

    # pylint: disable=line-too-long
    def predict_string_proba_with_inputs(self, string: str) -> Tuple[np.ndarray, Tuple[float, float, float, float]]:
        """Predict probability a single string and include inputs in return results.

        Args:

            string (str): String to predict.

        Returns:

            Tuple[np.ndarray, Tuple[float, float, float, float]]: Tuple containing prediction probability
                and Tuple of feature calculation.
        """
        inputs = [calculate_all_features(string)]
        input_ndarray = np.array(inputs)
        result = self.predict_proba(input_ndarray)
        return result, inputs
    # pylint: enable=line-too-long

    def save(self, filename: str) -> None:
        """Save model to file.

        Args:

            filename (str): Filename to save to.

        Returns:

            None.
        """

        self.logger.info("Saving model to file '%s'", filename)

        with open(filename, 'wb') as f:
            pickle.dump(self, f)
            self.logger.info("Finished saving model to file")

    @classmethod
    def load(cls, filename: str) -> 'GibberishDetector':
        """Load model from file.

        Args:

            filename (str): Filename to load from.
        """

        instance = load(filename)
        return instance

    # pylint: disable=line-too-long
    @classmethod
    def train_from_text_files(cls, good_train_files: List[str], bad_train_files: List[str], good_test_files: List[str], bad_test_files: List[str]) -> 'StringBinaryClassifier':
        """Trains the model from the contents of text files.

        Args:

            good_train_files (List[str]): List of files where each line of file is a class 1 string. (training)
            bad_train_files (List[str]): List of files where each line of file is a class 0 string. (training)
            good_test_files (List[str]): List of files where each line of file is a class 1 string. (testing)
            bad_test_files (List[str]): List of files where each line of file is a class 0 string. (testing)

        Returns:

            StringBinaryClassifier: Trained StringBinaryClassifier instance.
        """

        instance = cls(max_iter=100)
        matrix = generate_training_set(good_train_files, bad_train_files)
        instance.train(matrix, good_test_files, bad_test_files)

        return instance
    # pylint: enable=line-too-long

def generate_all_features(list_of_strings: List[str]):
    """
    Python Generator version of calculate_all_features

    :param list_of_strings: a list of strings
    :return: a tuple containing charset-normalized entropy,
    sequentiality and gibberish for the string
    """
    for string in list_of_strings:
        yield calculate_all_features(string)

@lru_cache(maxsize=16384)
def calculate_all_features(string: str) -> Tuple[float, float, float, float]:
    """
    Computes all the string features, like the normalized entropy,
    sequentiality and gibberish, for a given string

    :param string: string to be analyzed
    :return: a tuple containing charset-normalized entropy,
    sequentiality and gibberish for the string
    :rtype: (float, float, float, float)
    """

    if not string:
        return None

    relative_charset, relative_charset_length = charset.get_narrower_charset(string)
    if not relative_charset:
        return None

    string_length = len(string)
    entropy = normalized_entropy(string, relative_charset, False, item_length=string_length)
    sequentiality = string_sequentiality(string, relative_charset, string_length=string_length,
                                         charset_length=relative_charset_length)
    gibberish_probability = detector.evaluate(string, True)

    return entropy, sequentiality, gibberish_probability, relative_charset_length

def generate_training_set(class_one_files, class_zero_files, return_strings=False):
    """
    Generates a matrix containing rows of string features

    :param class_one_files: path of files where each line is a class 1 string, used for training
    :param class_zero_files: path of files where each line is a class 0 string, used for training
    :param return_strings: if True, returns a list with the original strings too
    :return: a matrix containg the training set and (if return_strings is True) the list of strings
             that corresponds to each row of the matrix (order compatible, i.e. the i-th string was
             used to generate the values in the i-th row of the matrix
    :rtype: Union[np.array, (np.array, list)]
    """

    rows = []
    strings = []
    for file_path in class_one_files:
        for line in open(file_path):
            line = line.replace('\n', '').replace('\r', '')
            features = calculate_all_features(line)
            if features is not None:
                array = list(features)
                array.append(1.0)
                if return_strings:
                    strings.append(line)
                rows.append(array)
            else:
                print(f"Invalid line: {line}")

    for file_path in class_zero_files:
        for line in open(file_path):
            line = line.replace('\n', '').replace('\r', '')
            features = calculate_all_features(line)
            if features is not None:
                array = list(features)
                array.append(0.0)
                if return_strings:
                    strings.append(line)
                rows.append(array)
            else:
                print(f"Invalid line: {line}")

    matrix = np.array(rows)
    if return_strings:
        if len(matrix) != len(strings):
            logging.error("Something went wrong")
        return matrix, strings
    return matrix

def load(filename: str) -> StringBinaryClassifier:
    """Load StringBinaryClassifier from a pickle file.

    Args:

        filename (str): Pickle filename.

    Returns:

        StringBinaryClassifier: Unpickled StringBinaryClassifier instance.
    """

    logging.info("Loading from pickled file '%s'", filename)

    with open(filename, 'rb') as f:
        instance = pickle.load(f)
        logging.info("Finished loading from pickled file")

    return instance
