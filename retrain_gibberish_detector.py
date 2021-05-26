"""Retrain GibberishDetector"""

from api_key_detector.gibberish_detector.gibberish_detector import GibberishDetector

def main():
    """Main."""

    save_filename = "api_key_detector/gibberish_detector/gibberish_detector.pki"

    learnset = [
        'datasets/gibberish_detector/pride_and_prejudice.txt',
        'datasets/gibberish_detector/i_promessi_sposi.txt',
        'datasets/gibberish_detector/le_comte_de_monte_cristo.txt',
        'datasets/gibberish_detector/menschliches_allzumenschliches.txt',
    ]

    good_test = [
        'datasets/gibberish_detector/good.txt',
    ]

    bad_test = [
        'datasets/gibberish_detector/bad.txt'
    ]

    gd = GibberishDetector.train_from_text_files(training_files=learnset, good_test_files=good_test, bad_test_files=bad_test)
    gd.save(save_filename)

    print("", end='')

if __name__ == "__main__":
    main()
