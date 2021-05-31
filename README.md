# ExtFs

[![Build Status](https://ci.binaryedge.ninja/api/badges/crucible-risk/ld-extfs/status.svg)](https://ci.binaryedge.ninja/crucible-risk/ld-extfs)

## Usage

See `examples/` for some sample examples on useage.

Generally usage will be something like the following:

```python
# Open the ext filesystem file
f = open("filesystem.fs", "rb")

# Read the filesystem
ext3fs = Filesystem(f=f)
ext3fs.run()

# Open the desired file on the filesystem as a file-like object
ef = ext3fs.open("file.txt")

# Print contents of file
contents = ef.read().decode('utf-8')
print(f"Contents of file:\n{contents}")

f.close()
```

## Testing

Stuff for testing

### Creating test files

To create test filesystems on linux:

```shell
dd if=/dev/zero of=filesystem.fs bs=1M count=10
mkfs.ext2 filesystem.fs
```

Substitute `mkfs.ext2` for `mkfs.ext3` or `mkfs.ext4` depending on the desired flavor.

### Mounting test files

To mount test filesystems on linux:

```shell
mkdir -p local_data/fs
sudo mount filesystem.fs local_data/fs
```

Now you can write files to the filesystem (as `root`):

```shell
sudo dd if=/dev/random of=local_data/fs/file.bin bs=512 count=4
```

Don't forget to unmount when you are finished:

```shell
sudo umount local_data/fs
```
