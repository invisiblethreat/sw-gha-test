"""package.json analyzer."""

from ContentAnalyzer.analyzers.json import JsonAnalyzer

class PackageJsonAnalyzer(JsonAnalyzer):
    """PackageJsonAnalyzer."""

    @property
    def repository(self):
        """repository."""

        return self.get_path('repository')

    @property
    def repository_url(self):
        """repository url."""

        return self.get_path('repository.url')

    @property
    def scripts(self):
        """scripts."""

        return self.get_path('scripts')

    @property
    def resolved(self):
        """resolved."""

        return self.get_path('_resolved')

    @property
    def where(self):
        """where."""

        return self.get_path('_where')

    @property
    def npm_operational_internal(self):
        """_npmOperationalInternal."""

        return self.get_path('_npmOperationalInternal')

    @property
    def dist(self):
        """dist."""

        return self.get_path('dist')

    @property
    def dist_tarball(self):
        """dist_tarball."""

        return self.get_path('dist.tarball')

    @property
    def git_head(self):
        """gitHead."""

        return self.get_path('gitHead')

    @property
    def bugs(self):
        """bugs."""

        return self.get_path('bugs')

    @property
    def bugs_url(self):
        """bugs_url."""

        return self.get_path('bugs.url')

    @property
    def homepage(self):
        """homepage."""

        return self.get_path('homepage')

    @property
    def targets(self):
        """Get targets."""

        props = [
            'repository',
            'repository_url',
            'scripts',
            'resolved',
            'where',
            'npm_operational_internal',
            'dist',
            'dist_tarball',
            'git_head',
            'bugs',
            'bugs_url',
            'homepage',
        ]

        values = {n: getattr(self, n) for n in props}
        return values

    @property
    def urls(self):
        """Returns just the url fields."""

        data = self.targets

        urls = []

        if data['repository_url'] is None:
            if data['repository'] is not None:
                # This may be a url
                urls.append(data['repository'])

        for n in ('repository_url', 'bugs_url', 'homepage', 'dist_tarball', 'resolved'):
            if data[n] is not None:
                urls.append(data[n])
        
        return urls

def main():
    """Main."""

    pass
    # doc = PackageJsonAnalyzer()
    # doc.filename = "/home/terryrodery/arista/alab/bundle/package.json"
    # doc.analyze()

    # for n in ('repository', 'scripts', 'resolved', 'where', 'npm_operational_internal',
    #           'dist', 'dist_tarball', 'git_head', 'bugs', 'bugs_url', 'homepage'):
    #     print(n, "=>", getattr(doc, n))

    # print(doc.targets)
    # print(doc.urls)

    # print(doc._kvs.repr)
    # print("breakpoint")

if __name__ == "__main__":
    main()
