"""package-lock.json analyzer."""

from ContentAnalyzer.analyzers.json import JsonAnalyzer

class PackageLockJsonAnalyzer(JsonAnalyzer):
    """Analyzer for package-lock.json"""

    @property
    def resolved(self):
        """repository."""

        values = [n.value for n in self._only_kvs if n.key == "resolved"]
        return values

    @property
    def targets(self):
        """Get targets."""

        all_resolved = self.resolved

        values = {
            'resolved': all_resolved
        }
        return values

    @property
    def urls(self):
        """Returns just the url fields."""

        return self.resolved

def main():
    """Main."""

    doc = PackageLockJsonAnalyzer()
    doc.filename = "tests/data/misc/package-lock.json"
    doc.analyze()

    print(doc.targets)

    print("breakpoint")

if __name__ == "__main__":
    main()
