"""Filesystem API
"""

# pylint: disable=too-many-lines

from typing import Dict, Iterator
import io
import more_itertools
from ExtFs.ext3 import Ext3Filesystem
from ExtFs.filehandle import ExtFsFileHandle


D_FILE_TYPE = {
    'unknown': 0,
    'file': 1,
    'directory': 2,
    'character_device': 3,
    'block_device': 4,
    'fifo': 5,
    'socket': 6,
    'symlink': 7
}


INODE_PROPS = [
    'i_mode',
    'i_uid',
    'i_size_lo',
    'i_atime',
    'i_ctime',
    'i_mtime',
    'i_dtime',
    'i_gid',
    'i_links_count',
    'i_blocks_lo',
    'i_flags',
    'union_osd1',
    'i_generation',
    'i_file_acl_lo',
    'i_size_high',
    'i_dir_acl',
    'union_osd2',
    'i_extra_size',
    # 'S_IXOTH',
    # 'S_IWOTH',
    # 'S_IROTH',
    # 'S_IXGRP',
    # 'S_IWGRP',
    # 'S_IRGRP',
    # 'S_IXUSR',
    # 'S_IWUSR',
    # 'S_IRUSR',
    # 'S_ISVTX',
    # 'S_ISGID',
    # 'S_ISUID',
    # 'S_IFIFO',
    # 'S_IFCHR',
    # 'S_IFDIR',
    # 'S_IFBLK',
    # 'S_IFREG',
    # 'S_IFLNK',
    # 'S_IFSOCK',
    'sparse',
]

class Filesystem:
    """Ext3 Filesystem abstraction class.
    """

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # pylint: disable=line-too-long
    def __init__(self, fileobj: io.BytesIO = None, f: io.BytesIO = None, master_offset: int = 0, filename: str = None):
        # TODO: Make sure everything using this class stops using 'f' and switches to 'fileobj
        self.__f = fileobj or f

        self.filename = filename
        self.master_offset = master_offset
        self.obj_count = 1
        self.dir_entries = dict()
        self.root_dir = None
        self.fs: Ext3Filesystem = None
    # pylint: enable=line-too-long

    def run(self) -> None:
        """Run."""
        self.__run_ext3filesystem()

    def __run_ext3filesystem(self) -> None:
        """Sets up and runs Ext3Filesystem and walks directory tree."""

        if self.fs is None:
            self.fs = Ext3Filesystem()
        self.fs.filename = self.filename
        self.fs.master_offset = self.master_offset
        # Provide our file handle if it isn't None
        if self.f is not None:
            self.fs.f = self.f
        self.fs.run()
        self.fs.walk_root_directory(inode_num=2)
        # Check to see if root inode is zeroed
        if self.fs.is_inode_zeroed(2) is True:
            raise RuntimeError("inode 2 is zeroed!")
        # Process inode 2 as the root directory
        self.root_dir = self.fs.dirs[2]
        # Build directory walking with "" as the parent_path
        self.directory_walking(self.root_dir, "")

    # pylint: disable=line-too-long
    def directory_walking(self, root: 'Ext3Directory', parent_path: str, recurse: bool = True) -> None:
        """Directory walking recursion.

        Args:

            root (Ext3Directory): Root directory instance.
            parent_path (str): The path of directory in which this directory resides.
            recurse (bool): Recurse into subdirectories. Defaults to True.
        """

        if root is None:
            raise ValueError("root is None!")
        if root.entries is None or not root.entries:
            # Guess I've never had an empty directory??? What about lost+and+found?
            # Maybe only due to it being an hashed directory?
            return

        # List of tuples of subdirectories to recurse on
        subdirectories = list()
        # Read every entry in root directory
        for e in root.entries:
            # e.inode = e.inode

            if e.inode == 0:
                # Not processing entries with inode 0 for now. These are deleted stuff
                # most likely.
                # TODO: Add deleted file accounting here
                continue

            # If the directory name is not . and not ..
            if e.name != "." and e.name != ".." and e.file_type_str != "unknown":

                full_path = f"{parent_path}/{e.name}"
                inode = self.fs.get_inode(e.inode)

                props = {
                    'obj_id': self.obj_count,
                    'name': e.name,
                    'parent_path': parent_path,
                    'full_path': full_path,
                    'inode': e.inode,
                    'size': inode.i_size_lo,
                }

                for attribute in INODE_PROPS:
                    props[attribute] = getattr(inode, attribute)

                # TODO: If self.fs.sb.INCOMPAT_FILETYPE is True we should grab the
                # file type information from the directory.
                if self.superblock.INCOMPAT_FILETYPE:
                    props['file_type'] = e.file_type
                    props['file_type_str'] = e.file_type_str
                else:
                    props['file_type'] = D_FILE_TYPE[inode.file_type]
                    props['file_type_str'] = inode.file_type

                self.dir_entries[full_path] = props
                self.obj_count += 1

                # Recurse if we are a directory
                if props['file_type_str'] == "directory":
                    self.fs.walk_root_directory(e.inode)
                    subdir = self.fs.dirs[e.inode]
                    # Add directory to subdirectories list for recursion
                    subdirectories.append((subdir, full_path))

        # Return if we aren't recursing
        if recurse is False:
            return

        # Now recurse into subdirectories
        for entry in subdirectories:
            subdir, my_path = entry
            self.directory_walking(subdir, my_path)
    # pylint: enable=line-too-long

    def calculate_file_parts(self, full_path: str) -> Dict:
        """Calculates the file parts of a file.

        Calculates the file parts of the file. This is going to be the byte
        ranges of the file in various sequences so the file can be read and
        returned as a file-like object.

        """

        e = self.get_file(full_path)
        inode = self.fs.get_inode(e['inode'])

        # Only do the range calculation on regular files
        if e['file_type_str'] == "file" and e['size'] > 0:
            dblocks = inode.dblocks

            consec_blocks = list((i[0], i[-1]) for i in [list(group) for group in more_itertools.consecutive_groups(dblocks)]) # pylint: disable=line-too-long

            parts = dict()

            i = 0
            running_start = 0
            for pair in consec_blocks:
                start_block, end_block = pair
                end_block += 1
                start_byte = (start_block * self.fs.sb.block_size) + self.master_offset
                end_byte = (end_block * self.fs.sb.block_size) + self.master_offset
                length = end_byte - start_byte
                parts[i] = {}
                parts[i]['block_start'] = start_block
                parts[i]['block_end'] = end_block
                parts[i]['byte_start'] = start_byte
                parts[i]['byte_end'] = end_byte
                parts[i]['byte_len'] = length
                parts[i]['running_start'] = running_start
                parts[i]['running_end'] = running_start + length
                parts[i]['sparse'] = False
                running_start += length
                i += 1

            # Remove slack
            last = parts[i-1]
            slack = last['byte_end'] - e['size']
            last['byte_end'] -= slack

            return {'file_parts': parts}

    def __read_to_str(self, full_path: str, number_of_bytes: int = None, include_slack: bool = False, slack_only: bool = False) -> bytes: # pylint: disable=line-too-long
        """Read file.

        Args:

            full_path (str): Full path of file to read.
            number_of_bytes (int, optional): Number of bytes to read. Defaults to None.
            include_slack (bool, optional): Include slack with file contents. Defaults to False.
            slack_only (bool, optional): Include ONLY slack contents of file. Defaults to False.

        Returns:

            bytes: Bytes for full_path.
        """

        file_entry = self.directory_entries[full_path]
        file_size = file_entry['size']

        if file_size == 0:
            # if include_slack or slack_only:
            #     self.__log.warning("file size is 0 and no slack is processed")
            buf = b""
            return buf

        buf = b""
        bytes_read = 0
        if number_of_bytes is None:
            bytes_remaining = file_size
        else:
            if file_size < number_of_bytes:
                bytes_remaining = file_size
            else:
                bytes_remaining = number_of_bytes

        if 'file_parts' not in file_entry:
            # Try and get file_parts
            file_parts = self.calculate_file_parts(full_path)
            if file_parts is not None:
                self.directory_entries[full_path].update(file_parts)
                file_entry.update(file_parts)
            else:
                # For some reason there are no file_parts in this object.
                # TODO: Raise custom exception here
                raise RuntimeError(f"No file_parts in {full_path}")

        # This needs to be sorted since the key is numeric and dictionaries are
        # in random order. This means that are sequence may be processed out of order.
        for seq_no in sorted(file_entry['file_parts']):
            # self.__log.debug("parsing seq_no: %s", seq_no)
            byte_start = file_entry['file_parts'][seq_no]['byte_start']
            byte_len = file_entry['file_parts'][seq_no]['byte_len']
            if bytes_remaining < byte_len:
                byte_len = bytes_remaining
            if slack_only is True:
                # We're only interested in the slack so we don't need to read the
                # contents... just seek...
                seek_to = byte_start + byte_len
                self.f.seek(seek_to)
            else:
                if file_entry['file_parts'][seq_no]['sparse'] is True:
                    # If this sequence is a sparse sequence then zero fill
                    # self.__log.debug("Sequence: %s added byte_len: %s"
                    #            "bytes of zero fill for sparse", seq_no, byte_len)
                    buf += b"\x00" * byte_len
                else:
                    # Seek to the byte start location and read byte_len bytes
                    self.f.seek(byte_start)
                    buf += self.f.read(byte_len)
            bytes_remaining -= byte_len
            bytes_read += byte_len

        if bytes_remaining > 0:
            # We've read all the file parts and we still have bytes remaining
            # so this is probably a sparse file no end blocks.
            buf += b"\x00" * bytes_remaining
            return buf

        if number_of_bytes is None and include_slack is True:
            # If we want to include the slack along with the contents of the file
            # then we need to know the size of the slack and read that amount
            # into buf.
            slack_size = self.slack_space_size(full_path)
            buf += self.f.read(slack_size)
        elif slack_only is True:
            # If we are only interested in the slack then let's do this ghetto
            # hack and overwrite buf after the file has been read. We could
            # speed this up by being less lazy and just moving the file pointer
            # instead of reading the entire file contents.
            # 2018-06-30 - Added a check for slack_size since apparently I had
            # the foresight to add that as a property/attribute to a file entry
            # way far in the past.
            # if 'slack_size' in self.dir_entries[full_path]:
            #     slack_size = self.dir_entries[full_path]['slack_size']
            # else:
            slack_size = self.slack_space_size(full_path)
            buf = self.f.read(slack_size)

        return buf

    def open(self, full_path: str) -> io.BytesIO:
        """Open a file.

        Opens a file for reading and returns a file-like object.

        Args:

            full_path (str): Full path of file to open.

        Returns:

            io.BytesIO: io.BytesIO instance containing contents of file.
        """

        return io.BytesIO(self.__read_to_str(full_path))

    def open_test_handle(self, full_path: str) -> ExtFsFileHandle:
        """Open a file using experimental file handle.

        Args:

            full_path (str): Full path of file to open.

        Returns:

            ExtFsFileHandle: ExtFsFileHandle object.
        """

        file_entry = self.directory_entries[full_path]
        size = file_entry['size']
        name = file_entry['name']
        if 'file_parts' not in file_entry:
            # Try and get file_parts
            file_parts = self.calculate_file_parts(full_path)
            if file_parts is not None:
                self.directory_entries[full_path].update(file_parts)
                file_entry.update(file_parts)
            else:
                # For some reason there are no file_parts in this object.
                raise RuntimeError(f"No file_parts in {full_path}")

        file_parts = file_entry['file_parts']

        return ExtFsFileHandle(self.f, name, size, file_parts)

    def slack_open(self, full_path: str) -> io.BytesIO:
        """Opens a file's slack.

        Args:
            full_path (str): Full path of file to open.

        Returns:
            io.BytesIO: io.BytesIO instance containing slack contents of file.
        """

        return io.BytesIO(self.__read_to_str(full_path, slack_only=True))

    def slack_space_size(self, full_path: str) -> int:
        """Gives the amount of space in bytes of slack.

        Args:

            full_path (str): Full path of file to open.

        Returns:

            int: Slack space of file in bytes.
        """

        if 'd_blocks_count' in self.dir_entries[full_path]:
            size_on_fs = self.superblock.block_size * self.dir_entries[full_path]['d_blocks_count']
            size = self.dir_entries[full_path]['size']
            slack = size_on_fs - size
            if slack < 0:
                # self.__log.critical("NEGATIVE slack size! file: %s size: %s "
                #            "size_on_fs: %s slack: %s", full_path, size, size_on_fs, slack)
                # self.__log.critical("node dump: %s", self.dir_entries[full_path])
                return 0
            elif slack > self.superblock.block_size:
                # self.__log.crtitical("SLACK > BLOCK SIZE file! file: %s size: %s "
                #            "size_on_fs: %s slack: %s", full_path, size, size_on_fs, slack)
                # self.__log.critical("node dump: %s", self.dir_entries[full_path])
                pass
            return 0

        return 0

    def is_file(self, full_path: str) -> bool:
        """Is full path a file?

        Args:

            full_path (str): Full path of file to open.

        Returns:

            bool: Whether or not full_path is a file.
        """
        if full_path not in self.directory_entries:
            raise RuntimeError("Could not find file with path: " + full_path)

        file_attributes = self.get_file(full_path)
        return file_attributes['file_type_str'] == "file"

    def is_directory(self, full_path: str) -> bool:
        """Is full path a directory?

        Args:

            full_path (str): Full path of file to open.

        Returns:
            bool: Whether or not full_path is a file.
        """
        if full_path not in self.directory_entries:
            raise RuntimeError("Could not find file with path: " + full_path)

        file_attributes = self.get_file(full_path)
        return file_attributes['file_type_str'] == "directory"

    def get_inode(self, inode_number: int) -> 'Ext3Inode':
        """Get an inode by its number.

        Args:

            inode_number (int): Inode number.

        Returns:

            Ext3Inode: Ext3Inode instance for inode number.
        """
        return self.fs.get_inode(inode_number)

    def get_directory(self, full_path: str):
        """Gets directory attributes.

        :param full_path: Path of directory to get attributes of.
        :type full_path: str.
        :returns: Directory's attributes.
        :rtype: dict
        :raises: RuntimeError

        """
        if full_path not in self.directory_entries:
            raise KeyError(f"Could not find directory with path '{full_path}'")

        return self.directory_entries[full_path]

    def get_directory_contents(self, full_path: str) -> Iterator[Dict]:
        """Gets the contents of a directory.

        Generator.

        Args:

            full_path (str): Full path of the directory.

        Raises:
            RuntimeError: If directory with 'full_path' is not found.

        Returns:

            dict: Dictionary of file/directory attributes.
        """

        if full_path not in self.directory_entries and full_path != "/":
            raise KeyError(f"Could not find directory with path '{full_path}'")

        for values in self.directory_entries.values():
            if values['parent_path'] == full_path or (values['parent_path'] == "" and full_path == "/"): # pylint: disable=line-too-long
                yield values

    def get_file(self, full_path: str):
        """Gets file attributes.

        :param full_path: Path of file to get attributes of.
        :type full_path: str.
        :returns: File's attributes.
        :rtype: dict
        :raises: RuntimeError

        """
        if full_path not in self.directory_entries:
            raise KeyError(f"Could not find file with path '{full_path}'")

        return self.directory_entries[full_path]

    def get_file_size(self, full_path: str):
        """Gets size of file.

        :param full_path: Path of file get size of.
        :type full_path: str.
        :returns: Size of file in bytes.
        :rtype: int
        :raises: RuntimeError

        """
        if full_path not in self.directory_entries:
            raise KeyError(f"Could not find file with path '{full_path}'")

        file_attributes = self.get_file(full_path)
        return file_attributes['size']

    def get_file_inode(self, full_path: str):
        """Gets inode of file.

        :param full_path: Path of file to get inode of.
        :type full_path: str
        :returns: File's inode.
        :rtype: dict
        :raises: RuntimeError

        """
        if full_path not in self.directory_entries:
            raise KeyError(f"Could not find file with path '{full_path}'")
        file_attributes = self.get_file(full_path)
        return file_attributes['inode']

    def get_file_parts(self, full_path: str):
        """Gets file parts of file.

        :param full_path: Path of file to get parts of.
        :type full_path: str
        :returns: File's parts.
        :rtype: dict
        :raises: RuntimeError

        """
        if full_path not in self.directory_entries:
            raise KeyError(f"Could not find file with path '{full_path}'")
        file_attributes = self.get_file(full_path)
        return file_attributes['file_parts']

    def get_file_permissions(self, full_path: str) -> Dict:
        """Gets permissions of file.

        Args:

            full_path (str): Full path of file.

        Returns:

            dict: Dictionary containing file permissions.
        """

        if full_path not in self.directory_entries:
            raise KeyError(f"Could not find file with path '{full_path}'")

        file_attributes = self.get_file(full_path)

        permissions = {
            'other': {
                'read': file_attributes['S_IROTH'],
                'write': file_attributes['S_IWOTH'],
                'execute': file_attributes['S_IXOTH']
            },
            'group': {
                'read': file_attributes['S_IRGRP'],
                'write': file_attributes['S_IWGRP'],
                'execute': file_attributes['S_IXGRP']
            },
            'user': {
                'read': file_attributes['S_IRUSR'],
                'write': file_attributes['S_IWUSR'],
                'execute': file_attributes['S_IXUSR']
            },
            'setuid': file_attributes['S_ISUID'],
            'setgid': file_attributes['S_ISGID']
        }

        return permissions

    @property
    def f(self) -> io.BytesIO:
        """Filesystem file handle.
        Also sets file handle on underlying Ext processor.

        Returns:

            io.BytesIO: File handle in use.
        """

        return self.__f

    @f.setter
    def f(self, value):
        self.__f = value
        self.fs.f = value

    @property
    def superblock(self):
        """Returns filesystem superblock.

        :returns: Ext3 superblock object.
        :rtype :class:`matryoshka.Ext3Superblock`:

        """
        return self.fs.sb

    @property
    def directory_entries(self):
        """Returns dictionary of directory entries in filesystem.

        :returns: Dictionary of directory entries keyed as path.
        :setter: Sets directory entries.
        :rtype: dict

        """
        return self.dir_entries

    @directory_entries.setter
    def directory_entries(self, value):
        self.dir_entries = value

    @property
    def number_of_blocks(self) -> int:
        """Number of blocks on filesystem.

        Returns:

            int: Number of blocks present on filesystem.
        """
        return self.fs.number_of_blocks

    @property
    def number_of_inodes(self) -> int:
        """Number of inodes on filesystem.

        Returns:

            int: Number of inodes present on filesystem.
        """
        return self.fs.number_of_inodes

    @property
    def number_of_allocated_blocks(self) -> int:
        """Number of allocated blocks on filesystem.

        Returns:

            int: Number of allocated blocks present on filesystem.
        """
        return self.fs.number_of_allocated_blocks

    @property
    def number_of_unallocated_blocks(self) -> int:
        """Number of unallocated blocks on filesystem.

        Returns:

            int: Number of unallocated blocks present on filesystem.
        """
        return self.fs.number_of_unallocated_blocks

    @property
    def number_of_allocated_inodes(self) -> int:
        """Number of allocated inodes on filesystem.

        Returns:

            int: Number of allocated inodes present on filesystem.
        """
        return self.fs.number_of_allocated_inodes

    @property
    def number_of_unallocated_inodes(self) -> int:
        """Number of unallocated inodes on filesystem.

        Returns:

            int: Number of unallocated inodes present on filesystem.
        """
        return self.fs.number_of_unallocated_inodes

    @property
    def gdts(self):
        """Returns GDTs from filesystem.

        Generator

        :returns: A :class:`Ext3GDT` object.
        :rtype: :class:`Ext3GDT`

        """
        return self.fs.gdts

    @property
    def block_groups(self):
        """Returns block groups from filesystem.

        Generator

        :returns: A :class:`Ext3BlockGroup` object.
        :rtype: :class:`Ext3BlockGroup`

        """
        return self.fs.block_groups

    @property
    def files(self):
        """All files on filesystem.

        Generator.

        :returns: A file from the filesystem.
        :rtype: dict

        """
        for entry in self.directory_entries:
            if self.directory_entries[entry]['file_type_str'] == "file":
                yield self.directory_entries[entry]

    @property
    def filenames(self):
        """All filenames on filesystem.

        Generator.

        :returns: A filename from the filesystem.
        :rtype: str

        """
        for entry in self.directory_entries:
            if self.directory_entries[entry]['file_type_str'] == "file":
                yield entry

    @property
    def directories(self):
        """All directories on filesystem.

        Generator.

        :returns: A directory from the filesystem.
        :rtype: dict

        """
        for entry in self.directory_entries:
            if self.directory_entries[entry]['file_type_str'] == "directory":
                yield self.directory_entries[entry]

    @property
    def allocated_inodes(self):
        """Allocated inodes.

        Generator.

        :returns: An allocated inode from the filesystem.
        :rtype: dict

        """
        for inode in self.fs.inodes:
            if self.fs.inodes[inode].allocated == 1:
                yield self.fs.inodes[inode]

    @property
    def unallocated_inodes(self):
        """Unallocated inodes.

        Generator.

        :returns: An unallocated inode from the filesystem.
        :rtype: dict

        """
        for inode in self.fs.inodes:
            if self.fs.inodes[inode].allocated == 0:
                yield self.fs.inodes[inode]

    @property
    def allocated_blocks(self):
        """Allocated blocks.

        Generator.

        :returns: An allocated block from the filesystem.
        :rtype: dict

        """
        for block in self.fs.blocks:
            if self.fs.blocks[block].allocated == 1:
                yield self.fs.blocks[block]

    @property
    def unallocated_blocks(self):
        """Unallocated blocks.

        Generator.

        :returns: An unallocated block from the filesystem.
        :rtype: dict

        """
        for block in self.fs.blocks:
            if self.fs.blocks[block].allocated == 0:
                yield self.fs.blocks[block]

    @property
    def blocks(self):
        """Blocks.

        Generator.

        :returns: A block from the filesystem.
        :rtype: dict

        """
        for block in self.fs.blocks:
            yield self.fs.blocks[block]
