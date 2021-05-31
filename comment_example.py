"""Comment tester"""

from ContentAnalyzer.analyzers import comments

def main():
    """Main."""

    import time

    filename = "tests/data/php/sample8.php"

    with open(filename, 'r', encoding='utf-8') as f:
        bt = time.time()
        cs = comments.extract_c_like_comments(f.read())
        rt = round(time.time() - bt, 2)

    print(f"Found {len(cs)} comments in {rt} seconds")
    print("", end='')


if __name__ == "__main__":
    main()
