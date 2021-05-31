"""Test basic filesystem operations"""

# pylint: disable=line-too-long,missing-docstring

import pytest
from ExtFs import Filesystem

filesystems_files = [
    "data/ext2_default.fs",
    "data/ext3_default.fs",
    "data/ext4_default.fs",
]


@pytest.mark.parametrize("filesystem_filename", filesystems_files)
def test_file_contents(filesystem_filename):
    """Test file contents of various sizes match expected."""

    try:
        f = open(filesystem_filename, "rb")
    except FileNotFoundError:
        # If file isn't found maybe we're running in vscode so prepend "tests/" to path
        f = open(f"tests/{filesystem_filename}", "rb")

    extfs = Filesystem(fileobj=f)
    extfs.run()

    read_sizes = [
        512,
        1024,
        2048,
        4096,
        8192,
    ]

    for read_size in read_sizes:
        expected = b"C" * read_size
        read_filename = f"/{read_size}byte.txt"

        rf = extfs.open(read_filename)
        observed = rf.read()
        rf.close()

        assert expected == observed, f"File {read_filename} did not contain expected content!"
