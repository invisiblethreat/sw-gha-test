"""Example 6"""

def main():
    """Main."""
    from ContentAnalyzer.analyzers import GitLogAnalyzer

    blah = GitLogAnalyzer()
    blah.filename = "tests/data/git/HEAD"
    blah.analyze()

    print("breakpoint")

if __name__ == "__main__":
    main()
