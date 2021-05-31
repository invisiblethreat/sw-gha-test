"""Ext3 directory classes.
"""

import io
import struct
from typing import Union

import more_itertools

D_FILE_TYPE = {
    0: 'unknown',
    1: 'file',
    2: 'directory',
    3: 'character_device',
    4: 'block_device',
    5: 'fifo',
    6: 'socket',
    7: 'symlink',
}

UNPACK_DIRECTORY_HASH_BLOCK = struct.Struct("<II")
UNPACK_LE32 = struct.Struct("<I")
UNPACK_U8 = struct.Struct("<B")
UNPACK_LE16 = struct.Struct("<H")

class Ext3DirectoryHashTreeRoot:
    """Ext3DirectoryHashTreeRoot.

    Class for Ext3DirectoryHashTreeRoot
    """

    __slots__ = [
        'dot_inode',
        'dot_rec_len',
        'dot_name_len',
        'dot_file_type',
        'dot_name',
        'dotdot_inode',
        'dotdot_rec_len',
        'dotdot_name_len',
        'dotdot_file_type',
        'dotdot_name',
        'dx_root_info_reserved_zero',
        'dx_root_info_hash_version',
        'dx_root_info_info_length',
        'dx_root_info_indirect_levels',
        'dx_root_info_unused_flags',
        'limit',
        'count',
        'block',
        'unpack',
        'INCOMPAT_LARGEDIR',
        'block_location',
        'block_size',
        'f',
        'byte_start',
        'byte_end',
        'byte_len',
        'entries',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self, block_location: int = None, block_size: int = None, f: io.BytesIO = None):
        # if block_location is None:
        #     raise ValueError("Must provide a positive integer value for block_location!")
        if block_size is None:
            raise ValueError("Must provide a positive integer value for block_size!")
        self.f = f

        self.INCOMPAT_LARGEDIR = False

        self.block_location = block_location
        self.block_size = block_size

        # If block_location is None then assume that the file handle
        # pointer is currently where it needs to be
        if self.block_location is None:
            self.byte_start = self.f.tell()
        else:
            self.byte_start = block_location * block_size
        self.byte_end = self.byte_start + block_size
        self.byte_len = self.block_size

        self.dot_inode = None
        self.dot_rec_len = None
        self.dot_name_len = None
        self.dot_file_type = None
        self.dot_name = None
        self.dotdot_inode = None
        self.dotdot_rec_len = None
        self.dotdot_name_len = None
        self.dotdot_file_type = None
        self.dotdot_name = None
        self.dx_root_info_reserved_zero = None
        self.dx_root_info_hash_version = None
        self.dx_root_info_info_length = None
        self.dx_root_info_indirect_levels = None
        self.dx_root_info_unused_flags = None
        self.limit = None
        self.count = None
        self.block = None
        # struct dx_entry looks like
        # struct dx_entry
        # {
        # 	__le32 hash;
        # 	__le32 block;
        # };
        self.entries = list()

    def run(self) -> None:
        """Run.
        """

        # Go to the byte offset. This will won't seek if block_location
        # was none when the constructor was called.
        self.f.seek(self.byte_start)
        # start_offset = self.f.tell()

        self.dot_inode = UNPACK_LE32.unpack(self.f.read(4))[0]
        self.dot_rec_len = UNPACK_LE16.unpack(self.f.read(2))[0]
        self.dot_name_len = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dot_file_type = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dot_name = self.f.read(4).decode('utf-8')
        self.dotdot_inode = UNPACK_LE32.unpack(self.f.read(4))[0]
        self.dotdot_rec_len = UNPACK_LE16.unpack(self.f.read(2))[0]
        self.dotdot_name_len = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dotdot_file_type = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dotdot_name = self.f.read(4).decode('utf-8')
        self.dx_root_info_reserved_zero = UNPACK_LE32.unpack(self.f.read(4))[0]
        self.dx_root_info_hash_version = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dx_root_info_info_length = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dx_root_info_indirect_levels = UNPACK_U8.unpack(self.f.read(1))[0]
        self.dx_root_info_unused_flags = UNPACK_U8.unpack(self.f.read(1))[0]
        self.limit = UNPACK_LE16.unpack(self.f.read(2))[0]
        self.count = UNPACK_LE16.unpack(self.f.read(2))[0]
        self.block = UNPACK_LE32.unpack(self.f.read(4))[0]

        # Perform some sanity checks to verify if this is
        # a hashed entry or not.
        if not self.__check_tree():
            return False

        for _ in range(0, self.count - 1):
            entry = {}
            # entry['hash'] = self.__le32()
            # entry['block'] = self.__le32()
            entry['hash'], entry['block'] = UNPACK_DIRECTORY_HASH_BLOCK.unpack(self.f.read(8))
            self.entries.append(entry)

        return True

    def __check_tree(self) -> bool:
        """Checks directory entry to verify that it is a hashed tree.
        """

        # struct dx_root_info.reserved_zero must be zero!
        if self.dx_root_info_reserved_zero != 0:
            # Not an index!
            return False

        # struct dx_root_info.info_length must be 0x8
        if self.dx_root_info_info_length != 0x8:
            # Not an index!
            return False

        # struct dx_root_info.indirect_levels can not be larger than
        # 2 unless INCOMPAT_LARGEDIR is set in which case it can be
        # no larger than 3
        if self.INCOMPAT_LARGEDIR:
            if self.dx_root_info_indirect_levels > 3:
                # Not an index!
                return False
        else:
            if self.dx_root_info_indirect_levels > 2:
                # Not an index!
                return False

        # Check limit size. Limit size should be block_size - the header (0x28 bytes)
        # that we just processed divided by 8 (the size of dx_entry) plus 1
        limit_size = ((self.block_size - 0x28) / 8) + 1
        if limit_size != self.limit:
            # Not an index!
            return False

        return True


class Ext3DirectoryEntryVersion2:
    """Ext3DirectoryEntryVersion2.

    Class for Ext3DirectoryEntryVersion2
    """

    __slots__ = [
        'inode',
        'rec_len',
        'name_len',
        'file_type',
        'file_type_str',
        'name',
        'byte_start',
        'byte_end',
        'byte_len',
        'byte_start_hex',
        'notes',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self):

        self.inode = None
        self.rec_len = None
        self.name_len = None
        self.file_type = None
        self.file_type_str = None
        self.name = None

        self.byte_start = None
        self.byte_end = None
        self.byte_len = None
        self.byte_start_hex = None
        self.notes = None

        # TODO: See if this is neccesary. I don't think it is.
        # self.tail_det_reserved_zero1 = None
        # self.tail_det_rec_len = None
        # self.tail_det_reserved_zero2 = None
        # self.tail_det_reserved_ft = None
        # self.tail_det_checksum = None


class Ext3DirectoryClassic:
    """Ext3DirectoryClassic.

    Class for Ext3DirectoryClassic.
    """

    __slots__ = [
        'f',
        'unpack',
        'blocks',
        'block_location',
        'block_size',
        'inode_info',
        'byte_start',
        'byte_end',
        'byte_len',
        'entries',
        '__INCOMPAT_FILETYPE',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # pylint: disable=line-too-long
    def __init__(self, block_location: int = None, block_size: int = None, blocks=None, inode_info=None, f: io.BytesIO = None):
        """Read and process a classic directory entry.

        Args:

            block_location (int): Block number where directory resides.
            block_size (int): Size of blocks on filesystem according to the superblock.
            blocks ([type], optional): [description]. Defaults to None.
            inode_info ([type], optional): [description]. Defaults to None.
            f (io.BytesIO): File-like object containing directory.
        """
        if block_location is None:
            raise ValueError("Must provide a positive integer value for block_location!")
        if block_size is None:
            raise ValueError("Must provide a positive integer value for block_size!")
        self.f = f


        self.blocks = blocks
        self.block_location = block_location
        self.block_size = block_size
        self.inode_info = inode_info
        # self.link_count = self.inode_info.i_links_count
        self.byte_start = block_location * block_size
        self.byte_end = self.byte_start + block_size
        self.byte_len = self.block_size
        self.entries = None
        self.__INCOMPAT_FILETYPE = False
    # pylint: enable=line-too-long

    @property
    def INCOMPAT_FILETYPE(self) -> bool:
        """Has file type in directory.

        Value from superblock that indicates that the file type
        information is stored with in the directory. When this flag
        is True the struct for the directory is different.
        When True:
        * ```name_len``` is unsigned 8 bits (1 byte)
        * ```file_type``` is unsigned 8 bits (1 byte)
        When False:
        * ```name_len``` is unsigned 16 bites (2 bytes)
        * No file_type field exists.

        Returns:

            bool: Whether or not filesystem has file type in directory.
        """
        return self.__INCOMPAT_FILETYPE

    @INCOMPAT_FILETYPE.setter
    def INCOMPAT_FILETYPE(self, value: bool):
        if isinstance(value, bool) is False:
            raise ValueError("INCOMPAT_FILETYPE must be True/False!")
        self.__INCOMPAT_FILETYPE = value

    def __get_adjusted_offset(self, block_number: int, relative_offset: int) -> int:
        block_adjusted = block_number * self.block_size
        return block_adjusted + relative_offset

    def run(self) -> None:
        """Read directory contents."""

        original_starting_offset = (self.blocks[0] * self.block_size) - self.block_size
        # Only seek to zero since we are using a cache
        self.f.seek(0)

        # for i, block in enumerate(self.blocks):
        for _ in self.blocks:
            # Just seek forward i number of self.block_size
            # self.f.seek((i * self.block_size))
            # relative_start_offset = self.f.tell()

            block_bytes_read = 0
            block_bytes_remaining = self.block_size
            entry_number = 0
            while True:
                # start_offset = self.f.tell()
                start_offset = original_starting_offset + self.f.tell()
                inode = UNPACK_LE32.unpack(self.f.read(4))[0]
                rec_len = UNPACK_LE16.unpack(self.f.read(2))[0]
                if not self.INCOMPAT_FILETYPE:
                    # name_len is le16 and there is no file_type!
                    name_len = UNPACK_LE16.unpack(self.f.read(2))[0]
                    file_type = None
                elif self.INCOMPAT_FILETYPE:
                    # name_len is u8 and there is file_type!
                    name_len = UNPACK_U8.unpack(self.f.read(1))[0]
                    file_type = UNPACK_U8.unpack(self.f.read(1))[0]
                    # Check to see if file_type is a legal value
                    if file_type < 0 or file_type > 7:
                        # 2019-11-19: Not entirely sure what this means when this branch
                        # of code is reached but I've seen this occur when the directory
                        # entries of INCOMPAT_FILETYPE have finished yet reading of the
                        # directory entry continues to happen. I'm going to go ahead and
                        # assume that getting this error is OK as it indicates we've reached
                        # the end of the directory listings.
                        # raise RuntimeError(msg)
                        break
                else:
                    msg = "INCOMPAT_FILETYPE not True/False! Is: %s!\n" % self.INCOMPAT_FILETYPE
                    raise RuntimeError(msg)
                if rec_len == 0:
                    self.f.seek(-7, 1)
                    break
                if name_len == 0:
                    self.f.seek(-8, 1)
                    break

                e = Ext3DirectoryEntryVersion2()
                e.byte_start = start_offset
                e.inode = inode
                e.rec_len = rec_len
                e.byte_end = e.byte_start + e.rec_len
                e.byte_len = e.rec_len
                e.byte_start_hex = hex(e.byte_start)
                e.name_len = name_len
                e.file_type = file_type
                if self.INCOMPAT_FILETYPE:
                    # Only need to convert filetype to string if INCOMPAT_FILETYPE is True
                    e.file_type_str = D_FILE_TYPE[e.file_type]
                e.name = self.f.read(e.name_len).decode('utf-8')

                current_offset = self.f.tell()
                # bytes_read = current_offset - start_offset
                bytes_read = current_offset - (start_offset - original_starting_offset)
                bytes_remaining = e.rec_len - bytes_read
                if bytes_read != e.rec_len:
                    self.f.seek(bytes_remaining, 1)
                block_bytes_read += bytes_read
                block_bytes_read += bytes_remaining

                if self.entries is None:
                    self.entries = []
                self.entries.append(e)
                entry_number += 1

                if block_bytes_remaining < e.rec_len:
                    break
                block_bytes_remaining -= bytes_read
                block_bytes_remaining -= bytes_remaining

                if block_bytes_remaining == 0:
                    # No more bytes to read from this block so break
                    break

        return


class Ext3Directory:
    """Ext3Directory.

    Ext3 Directory.

    Main class to determine if a directory is a hash
    index or if it is a classic and read linear. When
    COMPAT_DIR_INDEX is True and an inode EXT4_INDEX_FL
    is True we look for a hashed index at that
    inode's direct blocks.
    """

    __slots__ = [
        'f',
        'block_size',
        'inode_info',
        'util',
        'blocks',
        'entries',
        '__hash_root',
        '__COMPAT_DIR_INDEX',
        '__INCOMPAT_FILETYPE',
        'block_location_f',
        'blocks_f',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # pylint: disable=line-too-long
    def __init__(self, f: io.BytesIO = None, block_size: int = None, inode_info: 'Ext3Inode' = None):
        """Read and process an ext directory.

        Args:

            f (io.BytesIO): File-like object containing directory.
            block_size (int): Block size of filesystem.
            inode_info (Ext3Inode): Ext3Inode instance containing directory.
        """
        self.f = f
        self.block_size = block_size
        self.inode_info = inode_info

        self.util = None

        self.blocks = None
        self.entries = list()
        self.__hash_root = None
        # Superblock feature indicating that directory indexing is enabled
        self.__COMPAT_DIR_INDEX = False
        # Superblock feature indicating that the file type is stored
        # with the directory information. This makes the directory struct
        # slightly different.
        self.__INCOMPAT_FILETYPE = False
        self.block_location_f = None
        self.blocks_f = None
    # pylint: enable=line-too-long

    @property
    def COMPAT_DIR_INDEX(self) -> bool:
        """Has directory indices.

        Value from superblock that indicates that the filesystem
        has directory indicies. When this flag is True and an inode
        EXT4_INDEX_FL is True we look for a hashed index at that
        inode's direct blocks.


        Returns:

            bool: Whether or not filesystem has directory indicies.
        """
        return self.__COMPAT_DIR_INDEX

    @COMPAT_DIR_INDEX.setter
    def COMPAT_DIR_INDEX(self, value: bool):
        if isinstance(value, bool) is False:
            raise ValueError("COMPAT_DIR_INDEX must be True/False!")
        self.__COMPAT_DIR_INDEX = value

    @property
    def INCOMPAT_FILETYPE(self) -> bool:
        """Has file type in directory.

        Value from superblock that indicates that the file type
        information is stored with in the directory. When this flag
        is True the struct for the directory is different.
        When True:
        * ```name_len``` is unsigned 8 bits (1 byte)
        * ```file_type``` is unsigned 8 bits (1 byte)
        When False:
        * ```name_len``` is unsigned 16 bites (2 bytes)
        * No file_type field exists.

        Returns:

            bool: Whether or not filesystem has file type in directory.
        """
        return self.__INCOMPAT_FILETYPE

    @INCOMPAT_FILETYPE.setter
    def INCOMPAT_FILETYPE(self, value: bool):
        if isinstance(value, bool) is False:
            raise ValueError("INCOMPAT_FILETYPE must be True/False!")
        self.__INCOMPAT_FILETYPE = value

    def run(self) -> None:
        """Run"""

        if self.blocks is None:
            self.blocks = self.inode_info.dblocks

        # Expecting self.blocks to be a list from either i_block or extents via dblocks
        if isinstance(self.blocks, list):
            # Check first if we even have blocks
            if not self.blocks:
                return
            # First block in inode should be the has tree root entry
            block_location = self.blocks[0]
        else:
            # Expecting list but try this anyway
            block_location = self.blocks

        self.block_location_f = io.BytesIO(self.__seek_and_read_block(block_location))
        self.__seek_to_block(block_location)

        # Seek and read all the block data
        self.blocks_f = io.BytesIO(b"")
        for group in more_itertools.consecutive_groups(self.blocks):
            group_blocks = list(group)
            self.__seek_to_block(group_blocks[0])
            self.blocks_f.write(self.f.read(self.block_size * len(group_blocks)))

        self.blocks_f.seek(0)

        # If COMPAT_DIR_INDEX is in use then check for a hash table first
        if self.COMPAT_DIR_INDEX is True and self.inode_info.EXT4_INDEX_FL is True:
            dir_ent = self.__check_for_hash_tree()
            if dir_ent is not None:
                # We ARE a hash tree
                self.__hash_root = dir_ent
                self.__read_hash_tree()
            else:
                # We ARE NOT a hash tree
                # Do a straight linear read
                dir_ent = self.__read_linear(block_location)

                # Add entries if there are any to add
                if dir_ent is not None:
                    if dir_ent.entries is None:
                        raise RuntimeError("Did not find any entries in directory!")
                    self.entries.extend(dir_ent.entries)

        else:
            # Do a straight linear read if COMPAT_DIR_INDEX is False
            dir_ent = self.__read_linear(block_location)

            # Add entries if there are any to add
            if dir_ent is not None:
                if dir_ent.entries is None:
                    raise RuntimeError("Did not find any entries in directory!")
                self.entries.extend(dir_ent.entries)

        self.block_location_f.close()

    def __check_for_hash_tree(self) -> Union[Ext3DirectoryHashTreeRoot, None]:
        """Check for hash tree.

        Checks for a hash tree using cache stored in self.block_location_f.

        Returns:

            Ext3DirectoryHashTreeRoot or None: Ext3DirectoryHashTreeRoot or None.
        """

        dir_ent = Ext3DirectoryHashTreeRoot(f=self.block_location_f, block_location=None,
                                            block_size=self.block_size)

        hash_status = dir_ent.run()
        if hash_status is True:
            # Hash!
            return dir_ent
        else:
            # Not!
            self.f.seek(-0x28, 1)

    def __read_hash_tree(self) -> None:
        """Read the hash tree"""

        levels = self.__hash_root.dx_root_info_indirect_levels

        # Some sanity checks
        if levels > 0:
            raise NotImplementedError("Indirect levels above 0 not supported!")

        block_count = 0
        last_block = None
        for block in self.blocks:
            if block_count == 0:
                # Skip first block, we looked at that already
                block_count += 1
                last_block = block
                continue
            dir_ent = self.__read_linear(block)
            if dir_ent.entries is None:
                raise RuntimeError(f"dir_ent.entries is None while reading block {block} for inode {self.inode_info.inode_number}!\nLast block: {last_block}") # pylint: disable=line-too-long
            self.entries.extend(dir_ent.entries)
            last_block = block
            block_count += 1

    # pylint: disable=unused-variable
    def __read_linear(self, block_location: int) -> Ext3DirectoryClassic:
        """Read linear directory structure.

        Args:

            block_location (int): Not sure???

        Returns:

            Ext3DirectoryClassic: Ext3DirectoryClassic object.
        """

        dir_ent = Ext3DirectoryClassic(f=self.blocks_f, block_location=block_location,
                                       blocks=self.blocks,
                                       block_size=self.block_size,
                                       inode_info=self.inode_info)

        dir_ent.INCOMPAT_FILETYPE = self.INCOMPAT_FILETYPE
        dir_ent.run()

        return dir_ent
    # pylint: enable=unused-variable

    def __seek_to_block(self, block_number: int) -> Union[int, None]:
        """Seek to a block adjusted for master_offset.

        Args:

            block_number (int): Seek to block.

        Returns:

            Union[int, None]: New offset or None depending on the underlying handle.
        """
        return self.f.seek((block_number * self.block_size))

    def __read_block_size(self) -> bytes:
        """Read exactly one block of data determined by self.block_size

        Returns:

            bytes: Byte data.
        """
        return self.f.read(self.block_size)

    def __seek_and_read_block(self, block_number: int) -> bytes:
        """Seek to the offset adjusted location of block_number and return its data.

        Args:

            block_number (int): Seek to block.

        Returns:

            bytes: Byte data.
        """
        self.__seek_to_block(block_number)
        return self.__read_block_size()
