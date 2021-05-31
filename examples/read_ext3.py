"""Read ext3 filesystem"""

from ExtFs import Filesystem

def number_of_files(fs: Filesystem) -> None:
    """Number of files on filesystem."""
    print(f"{len(list(fs.files))} files")

def read_file(fs, full_path: str) -> None:
    """Read a file."""
    ef = fs.open(full_path)
    contents = ef.read().decode('utf-8')
    print(f"Contents of file:\n{contents}")

def main():
    """Main."""

    # Filename of an ext filesystem
    source_filename = "ext2_default.fs"

    # Name of file on filesystem that we wish to read
    read_filename = "/1024byte.txt"

    # Open the ext filesystem file
    f = open(source_filename, "rb")

    # Read the filesystem
    ext3fs = Filesystem(f=f)
    ext3fs.run()

    # Print contents of file
    read_file(ext3fs, read_filename)

    # Open the desired file on the filesystem as a file-like object
    ef = ext3fs.open(read_filename)

    # Print contents of file
    contents = ef.read().decode('utf-8')
    print(f"Contents of file:\n{contents}")

    print("", end='')
    f.close()

if __name__ == "__main__":
    main()
