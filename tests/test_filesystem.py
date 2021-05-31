"""Test basic filesystem operations"""

# pylint: disable=line-too-long,missing-docstring,consider-using-with

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
        file = open(filesystem_filename, "rb")
    except FileNotFoundError:
        # If file isn't found maybe we're running in vscode so prepend "tests/" to path
        file =  open(f"tests/{filesystem_filename}", "rb")

    extfs = Filesystem(fileobj=file)
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

        readf = extfs.open(read_filename)
        observed = readf.read()
        readf.close()

        assert expected == observed, f"File {read_filename} did not contain expected content!"
