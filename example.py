"""blah"""

import time
from api_key_detector import detector

def main():
    """Main."""

    # test = ["justsomething", "reallynothingimportant", "AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE", "eqwioqweioqiwoe"]
    # res1 = detector.detect_api_keys(test)
    # res2 = detector.filter_api_keys(test)
    # print(res1)
    # print(res2)

    from api_key_detector.entropy import shannon_entropy, normalized_entropy
    from api_key_detector.gibberish_detector import detector as gibberish_detector
    API_BASE91_CHARS = "!\"#$%&()*+,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

    # value = "AizaSyDtEV5rwG_F1jvyj6WVlOOzD2vZa8DEpLE"
    value = "I see London, I see France"

    HEX_CHARS = "1234567890abcdefABCDEF"
    BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=-_!@#$&%^()*?"
    
    CHARSET = API_BASE91_CHARS
    start_time = time.time()
    # ent = shannon_entropy(value, CHARSET)
    ent = normalized_entropy(value, CHARSET)
    print(f"{value} => {ent} => {gibberish_detector.evaluate(value)} in {time.time() - start_time}")

    print("", end='')

if __name__ == "__main__":
    main()
