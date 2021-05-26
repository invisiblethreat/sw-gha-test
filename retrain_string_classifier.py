"""Retrain GibberishDetector"""

import logging
from api_key_detector.string_classifier import StringBinaryClassifier

logging.getLogger().setLevel(logging.INFO)

def main():
    """Main."""

    save_filename = "api_key_detector/string_classifier.pki"

    good_train_files = [
        'api_key_detector/datasets/keys/gen_amazonaws.txt',
        'api_key_detector/datasets/keys/gen_beepbooptoken.txt',
        'api_key_detector/datasets/keys/gen_bitly.txt',
        'api_key_detector/datasets/keys/gen_facebookappsecret.txt',
        'api_key_detector/datasets/keys/gen_flickr.txt',
        'api_key_detector/datasets/keys/gen_foursquare.txt',
        'api_key_detector/datasets/keys/gen_githubkey.txt',
        'api_key_detector/datasets/keys/gen_githubsecret.txt',
        'api_key_detector/datasets/keys/gen_gitlabtoken.txt',
        'api_key_detector/datasets/keys/gen_googleauthtoken.txt',
        'api_key_detector/datasets/keys/gen_googlemaps.txt',
        'api_key_detector/datasets/keys/gen_guidupper.txt',
        'api_key_detector/datasets/keys/gen_herokuapikey.txt',
        'api_key_detector/datasets/keys/gen_linkedin.txt',
        'api_key_detector/datasets/keys/gen_mailchimp.txt',
        'api_key_detector/datasets/keys/gen_mailgun.txt',
        'api_key_detector/datasets/keys/gen_mashapekey.txt',
        'api_key_detector/datasets/keys/gen_sendgrid.txt',
        'api_key_detector/datasets/keys/gen_slacktoken.txt',
        'api_key_detector/datasets/keys/gen_stripelivekey.txt',
        'api_key_detector/datasets/keys/gen_twitter.txt',
        'api_key_detector/datasets/keys/manually_verified_keys.txt',
    ]

    bad_train_files = [
        'api_key_detector/datasets/text/libnative-lib.txt',
        'api_key_detector/datasets/text/libpcap-parser.txt',
        'api_key_detector/datasets/text/strings.txt',
        'api_key_detector/datasets/text/manually_verified_text.txt',
    ]

    good_test_files = [
        'api_key_detector/datasets/keys/api_test_extended.txt',
        'api_key_detector/datasets/keys/manually_verified_keys_test.txt',
    ]

    bad_test_files = [
        'api_key_detector/datasets/text/non_api_test.txt',
        'api_key_detector/datasets/text/manually_verified_text_test.txt',
    ]

    sc = StringBinaryClassifier.train_from_text_files(good_train_files=good_train_files, bad_train_files=bad_train_files, good_test_files=good_test_files, bad_test_files=bad_test_files)
    sc.save(save_filename)

    print("", end='')

if __name__ == "__main__":
    main()
