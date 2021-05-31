"""Class for ext3 filesystem
"""

import io
import math
# import pprint
import struct
from typing import Dict, Iterator, List

import more_itertools

from ExtFs.block import Ext3BlockBitmap, Ext3BlockGroup
from ExtFs.directory import Ext3Directory
from ExtFs.gdt import Ext3Gdt
from ExtFs.inode import Ext3InodeBitmap, Ext3InodeTable
from ExtFs.superblock import Ext3Superblock
from ExtFs.utility import Ext3Utility


class Ext3Filesystem:
    """Ext3Filesystem.

    Ext3Filesystem class.
    """

    __slots__ = [
        'sector_size',
        'util',
        'read_blocks',
        'read_root_directory',
        'filename',
        'image_offset',
        'magic_ignore',
        'f',
        'sb',
        'gdts',
        'inode_tables',
        'inode_bitmaps',
        'inode_bitmap',
        'block_groups',
        'block_bitmaps',
        'block_bitmap',
        '__number_of_allocated_inodes',
        '__number_of_allocated_blocks',
        '__number_of_zeroed_inodes',
        'dirs',
        'inodes',
        '__zeroed_inodes',
        'blocks',
        'master_offset',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self, f: io.BytesIO = None, master_offset: int = 0):
        self.sector_size = 512


        self.util = None

        self.read_blocks = True
        self.read_root_directory = True
        # Do not support anything other than an image on the FS for now
        self.filename = None
        self.image_offset = 0
        self.magic_ignore = False

        self.f = f
        self.sb: Ext3Superblock = None
        self.gdts = dict()
        self.inode_tables = dict()
        self.inode_bitmaps = dict()
        self.inode_bitmap = dict()
        self.block_groups = dict()
        self.block_bitmaps = dict()
        self.block_bitmap = dict()

        self.__number_of_allocated_inodes = 0
        self.__number_of_allocated_blocks = 0
        self.__number_of_zeroed_inodes = 0
        # Apparently a dict of directories? key is inode number, value is Ext3Directory object
        self.dirs = None
        self.inodes = {}
        self.__zeroed_inodes = {}
        self.blocks = {}
        self.master_offset = master_offset


    def get_inode(self, inode_number: int) -> 'Ext3Inode':
        """Returns a :class:`Ext3Inode` object for inode number :var:`inode_number`.

        Args:

            inode_number (int): Inode number.

        Returns:

            Ext3Inode: Ext3Inode instance for inode number.
        """

        # inode_number = int(inode_number)
        if inode_number == 0:
            raise ValueError("0 is not a valid inode number!")
        if inode_number in self.inodes:
            return self.inodes[inode_number]

        inode_table = self.get_inode_table_for_inode(inode_number)
        inode = inode_table.get_inode(inode_number)
        self.inodes[inode_number] = inode
        return inode

    def get_inode_table(self, inode_table_number: int) -> Ext3InodeTable:
        """Returns a :class:`Ext3InodeTable` object for inode table :var`inode_table_number`.

        Args:

            inode_table_number (int): Inode table number.

        Returns:

            Ext3InodeTable: Ext3InodeTable instance for inode table number.
        """

        if self.sb is None:
            raise RuntimeError("ondemand_run() must be called before doing this!")
        inode_table_number = int(inode_table_number)
        if inode_table_number < 0:
            raise ValueError("inode_table_number must be >= 0!")
        if inode_table_number > self.sb.block_group_count:
            raise ValueError(f"inode_table_number must be <= block_group_count ({self.sb.block_group_count})!") # pylint: disable=line-too-long
        if inode_table_number in self.inode_tables:
            return self.inode_tables[inode_table_number]
        else:
            # We should only get here if the table wasn't found but
            # is still a valid table number.
            gdt = self.get_gdt(inode_table_number)
            inode_tbl = self.read_inode_table(gdt)
            return inode_tbl
        # raise RuntimeError("ondemand_run() must be called before doing this!")

    def get_gdt(self, gdt_number: int) -> Ext3Gdt:
        """Returns a :class:`Ext3GDT` object for GDT :var`gdt_number`.

        Args:

            gdt_number (int): GDT group number.

        Returns:

            Ext3Gdt: Ext3Gdt instance for inode table number.
        """

        gdt_number = int(gdt_number)
        if gdt_number < 0:
            raise ValueError("gdt_number must be >= 0!")
        if gdt_number > self.sb.block_group_count:
            raise ValueError(f"gdt_number must be <= block_group_count ({self.sb.block_group_count})!") # pylint: disable=line-too-long
        return self.gdts[gdt_number]
        # raise RuntimeError(f"Could not find GDT {gdt_number}!")

    def get_inode_table_for_inode(self, inode_number: int) -> Ext3InodeTable:
        """Get the inode table object for an inode.

        Args:

            inode_number (int): Inode number.

        Returns:

            Ext3InodeTable: Ext3InodeTable instance for inode number.
        """
        inode_number = int(inode_number)
        table_number = self.get_inode_table_number_for_inode(inode_number)
        return self.get_inode_table(table_number)

    def get_inode_table_number_for_inode(self, inode_number: int) -> int:
        """Get the inode table number for an inode.

        Args:

            inode_number (int): Inode number.

        Returns:

            int: The inode table number for the inode.
        """
        inode_number = int(inode_number)
        table_number = math.floor((inode_number - 1) / self.sb.s_inodes_per_group)
        return int(table_number)

    def read_block(self, block_number: int) -> bytes:
        """Reads a block from the file handle.

        Args:

            block_number (int): Block number.

        Returns:

            bytes: The contents of the block from the file handle.
        """

        block_number = int(block_number)
        if block_number < 0:
            raise ValueError("block number must be greater than 0!")
        if block_number > self.sb.s_blocks_count_lo:
            raise ValueError("block number must be less than total number of blocks!")
        block_offset = (self.sb.block_size * block_number) + self.master_offset
        self.f.seek(block_offset)
        buf = self.f.read(self.sb.block_size)
        return buf

    def get_block(self, block_number: int) -> 'Ext3Block':
        """Returns a :class:`Ext3Block` object for block number :var:`block_number`.

        Args:

            block_number (int): Block number.

        Returns:

            Ext3Block: Ext3Block instance.
        """

        block_number = int(block_number)
        if block_number in self.blocks:
            return self.blocks[block_number]

        block_group = self.get_block_group_for_block(block_number)
        block = block_group.get_block(block_number)
        self.blocks[block_number] = block
        return block

    def get_block_group(self, group_number: int, exists_check: bool = False) -> Ext3BlockGroup:
        """Get a block group.

        Args:

            group_number (int): Block group number.
            exists_check (bool, optional): Return None if group doesn't exist. Defaults to False.

        Return:

            Ext3BlockGroup: Block group instance.
        """

        group_number = int(group_number)
        if group_number in self.block_groups:
            return self.block_groups[group_number]
        else:
            gdt = self.get_gdt(group_number)
            block_group = self.create_block_group(gdt)
            return block_group
        if exists_check is True:
            return
        # We should only get here if the table wasn't found but
        # is still a valid table number.
        raise RuntimeError("ondemand_run() must be called before doing this!")

    def get_block_group_allocated_blocks(self, block_group_number: int) -> List[int]:
        """Get allocated blocks of a block group.

        Args:

            block_group_number (int): Block group number.

        Raises:
            ValueError: If a block bitmap can not be found for group number.

        Returns:

            List[int]: List of allocated block numbers.
        """

        block_group_number = int(block_group_number)
        block_bitmap = self.get_block_bitmap(block_group_number)
        if block_bitmap is None:
            raise ValueError(f"Could not find block bitmap for group: {block_group_number}")

        return list(block_bitmap.allocated_blocks)

    def get_block_group_unallocated_blocks(self, block_group_number: int) -> List[int]:
        """Get unallocated blocks of a block group.

        Args:

            block_group_number (int): Block group number.

        Raises:
            ValueError: If a block bitmap can not be found for group number.

        Returns:

            List[int]: List of allocated block numbers.
        """

        block_group_number = int(block_group_number)
        block_bitmap = self.get_block_bitmap(block_group_number)
        if block_bitmap is None:
            raise ValueError(f"Could not find block bitmap for group: {block_group_number}")

        return list(block_bitmap.allocated_blocks)

    def get_block_group_for_block(self, block_number: int) -> Ext3BlockGroup:
        """Get the block group object for an block.

        Args:

            block_number (int): Block number.

        Returns:

            Ext3BlockGroup: Block group instance.
        """

        block_number = int(block_number)
        group_number = self.get_block_group_number_for_block(block_number)
        return self.get_block_group(group_number)

    def get_block_group_number_for_block(self, block_number: int) -> int:
        """Get the block group number for an block.

        Args:

            block_number (int): Block number.

        Returns:

            int: The block group number for the block.
        """

        block_number = int(block_number)
        if block_number == 0 or block_number == 1:
            return 0
        group_number = math.floor((block_number - 1) / self.sb.s_blocks_per_group)
        return int(group_number)

    def get_inode_bitmap(self, bitmap_number: int) -> Ext3InodeBitmap:
        """Gets a inode bitmap.

        Args:

            bitmap_number (int): Bitmap number to retrieve.

        Returns:

            Ext3InodeBitmap: Inode bitmap.
        """
        bitmap_number = int(bitmap_number)
        if bitmap_number in self.inode_bitmaps:
            return self.inode_bitmaps[bitmap_number]
        else:
            # Need to process bitmap
            gdt = self.get_gdt(bitmap_number)
            inode_bitmap = self.read_inode_bitmap(gdt)
            return inode_bitmap

    def get_block_bitmap(self, bitmap_number: int, process: bool = True) -> 'Ext3BlockBitmap':
        """Gets a block bitmap.

        Args:

            bitmap_number (int): Bitmap number to retrieve.
            process (bool, optional): Whether or not to process a missing entry.

        Return:

            Ext3BlockBitmap: Ext3BlockBitmap instance.
        """
        if self.sb is None:
            raise RuntimeError("run() or ondemand_run() must be called before doing this!")
        bitmap_number = int(bitmap_number)
        if bitmap_number < 0:
            raise ValueError("bitmap_number must be >= 0!")

        if bitmap_number in self.block_bitmaps:
            return self.block_bitmaps[bitmap_number]
        else:
            # Need to process bitmap
            gdt = self.get_gdt(bitmap_number)
            block_bitmap = self.read_block_bitmap(gdt)
            return block_bitmap

        # We should only get here if the table wasn't found but
        # is still a valid table number.
        raise RuntimeError("ondemand_run() must be called before doing this!")

    def read_super_block(self) -> None:
        """Read the filesystem superblock.
        """

        self.sb = Ext3Superblock(self.f, self.master_offset)

        self.sb.run()

        # TODO: Why is this here?
        # if self.sb.INCOMPAT_FLEX_BG is True:
        #     raise RuntimeError("Flex Blockgroup not supported!")

        if self.sb.INCOMPAT_META_BG is True:
            raise RuntimeError("Meta Block Groups (META_BG) not supported!")

    def read_inode_table(self, gdt: Ext3Gdt) -> Ext3InodeTable:
        """Read the inode table for a gdt.

        Args:

            gdt (Ext3Gdt): Gdt to read inode table of.

        Returns:

            Ext3InodeTable: Ext3InodeTable instance for matching gdt.
        """
        table_number = gdt.group_number
        inode_tbl = Ext3InodeTable(sb=self.sb, gdt=gdt, f=self.f)

        # Provide a copy of the inode bitmap so an inode can check its allocation status
        inode_tbl.inode_bitmap = self.get_inode_bitmap(table_number).bitmap
        inode_tbl.run()

        if self.inodes is None:
            self.inodes = dict()

        if table_number not in self.inode_tables:
            self.__number_of_allocated_inodes += inode_tbl.number_of_allocated_inodes
            self.__number_of_zeroed_inodes += inode_tbl.number_of_zeroed_inodes
        self.inode_tables[table_number] = inode_tbl
        return inode_tbl

    def read_inode_tables(self) -> None:
        """Read inode table.

        Iterates through list of GDTs in ```gdts```. Calculates Inode table offset,
        seeks to Inode table offset, and creates a new :class:`Ext3InodeTable`
        object. ```inode_bitmap```, table offset, ```master_offset``` are passed
        to the :class:`Ext3InodeTable` object prior to calling ```run()```.

        The :class:`Ext3InodeTable` object is stored in ```inode_tables```
        and each of its inodes is iterated and stored in ```inodes``` which
        is a ```dict``` with inode number as key and :class:`Ext3Inode` as
        value.

        """

        for gdt in self.gdts.values():
            self.read_inode_table(gdt)

    def read_inode_bitmap(self, gdt: Ext3Gdt) -> Ext3InodeBitmap:
        """Read inode bitmap for a gdt.

        Args:

            gdt (Ext3Gdt): Gdt to read bitmap of.

        Returns:

            Ext3InodeBitmap: Ext3InodeBitmap instance for matching gdt.
        """
        inode_bitmap = Ext3InodeBitmap(sb=self.sb, gdt=gdt, f=self.f)
        inode_bitmap.run()
        self.inode_bitmaps[gdt.group_number] = inode_bitmap
        return inode_bitmap

    def read_inode_bitmaps(self) -> None:
        """Read inode bitmaps.

        Iterates through all gdts and reads each gdt's inode bitmap.
        Bitmaps are stored in ```self.inode_bitmaps```.
        """

        # Iterate over each gdt and create/read a block bitmap.
        # Store bitmap in self.block_bitmaps.
        for gdt in self.gdts.values():
            self.read_inode_bitmap(gdt)

    def read_block_bitmap(self, gdt: Ext3Gdt) -> Ext3BlockBitmap:
        """Read block bitmap for a gdt.

        Args:

            gdt (Ext3Gdt): Gdt to read bitmap of.

        Returns:

            Ext3BlockBitmap: Ext3BlockBitmap instance for matching gdt.
        """
        block_bitmap = Ext3BlockBitmap(sb=self.sb, gdt=gdt, f=self.f)
        block_bitmap.run()
        self.block_bitmaps[gdt.group_number] = block_bitmap
        return block_bitmap

    def read_block_bitmaps(self) -> None:
        """Read block bitmaps.

        Iterates through all gdts and reads each gdt's block bitmap.
        Bitmaps are stored in ```self.block_bitmaps```.
        """
        # Iterate over each gdt and create/read a block bitmap.
        # Store bitmap in self.block_bitmaps.
        for gdt in self.gdts.values():
            self.read_block_bitmap(gdt)

        # self.block_bitmaps = [Ext3BlockBitmap(sb=self.sb, gdt=gdt, f=self.f).run() for gdt in gdt]

    def create_block_group(self, gdt: Ext3Gdt) -> Ext3BlockGroup:
        """Create a block group for a gdt.

        Args:

            gdt (Ext3Gdt): Gdt to create block group for.

        Returns:

            Ext3BlockGroup: Ext3BlockGroup instance for matching gdt.
        """
        group_number = gdt.group_number
        block_group = Ext3BlockGroup(sb=self.sb, gdt=gdt)

        # Provide a copy of the block bitmap so an block can check its allocation status
        block_group.block_bitmap = self.get_block_bitmap(group_number).bitmap

        if group_number not in self.block_groups:
            self.__number_of_allocated_blocks += block_group.number_of_allocated_blocks

        if self.blocks is None:
            self.blocks = dict()

        self.block_groups[group_number] = block_group
        return block_group

    def create_block_groups(self) -> None:
        """Creates block group objects.
        """

        for gdt in self.gdts.values():
            self.create_block_group(gdt)

    def read_group_descriptor_table(self) -> None:
        """Read Group Descriptor Table
        """

        # Seek to correct offset for GDT
        if self.sb.block_size == 1024:
            # Seek for block size of 1024
            gdt_seek = self.sb.block_size + 1024
        elif self.sb.block_size == 2048:
            # Not implemented so raise an exception for now
            raise NotImplementedError("Block size of 2048 not supported!")
        elif self.sb.block_size == 4096:
            # Seek for block size of 4096
            gdt_seek = self.sb.block_size
        else:
            raise RuntimeError(f"block_size {self.sb.block_size} not supported!")

        self.f.seek(gdt_seek)
        for x in range(0, self.sb.block_group_count):
            my_gdt = Ext3Gdt(sb=self.sb, f=self.f, group_number=x)
            my_gdt.run()
            self.gdts[x] = my_gdt

    def walk_root_directory(self, inode_num: int = 2) -> None:
        """Walk root directory at a given inode number.

        By default, ext implementations generally have their root
        directory located at inode 2.

        Args:

            inode_num (int, optional): Starting inode number for walk. Defaults to 2.
        """

        directory_inode = self.get_inode(inode_num)

        root = Ext3Directory(block_size=self.sb.block_size, inode_info=directory_inode,
                             f=self.f)
        root.COMPAT_DIR_INDEX = self.sb.COMPAT_DIR_INDEX
        root.INCOMPAT_FILETYPE = self.sb.INCOMPAT_FILETYPE
        root.run()
        if self.dirs is None:
            self.dirs = {}
        self.dirs[inode_num] = root

    def run(self) -> None:
        """Runs the Ext filesystem processing.

        Checks to see if a file-like object ```f``` is set. If ```f``` is not set
        then ```filename``` will be opened and stored in ```f``` prior to running
        ```read_super_block()```.

        After reading the superblock, the GDTs are read, then Inode Bitmaps,
        Inode Tables, Block Bitmaps, Block Groups, and finally the root directory
        at Inode 2 is read if ```read_root_directory``` is ```True``` (default).

        """
        if self.f is None:
            self.f = open(self.filename, "rb")

        self.read_super_block()

        self.util = Ext3Utility(self.f, block_size=self.sb.block_size)

        self.read_group_descriptor_table()

        # self.read_inode_bitmaps()

        # self.read_inode_tables()

        # if self.read_blocks is True:
        # self.read_block_bitmaps()

        # self.create_block_group()

        self.walk_root_directory(2)

    @property
    def zeroed_inodes(self) -> Dict:
        """Inode zeroed inventory.

        An inventory of all inodes that are zeroed and contain no data.

        Returns:

            Dict: Dictionary of all zeroed inodes.
        """
        return self.__zeroed_inodes

    @zeroed_inodes.setter
    def zeroed_inodes(self, value: Dict):
        self.__zeroed_inodes = value

    @property
    def number_of_inodes(self) -> int:
        """Number of inodes on filesystem.

        Returns:

            int: Number of inodes present on filesystem.
        """
        return self.sb.s_inodes_count

    @property
    def number_of_allocated_inodes(self) -> int:
        """Number of allocated inodes on filesystem.

        Returns:

            int: Number of allocated inodes on filesystem.
        """

        return self.__number_of_allocated_inodes

    @property
    def number_of_unallocated_inodes(self) -> int:
        """Number of unallocated inodes on filesystem.

        Returns:

            int: Number of unallocated inodes on filesystem.
        """
        return self.sb.s_free_inodes_count

    @property
    def number_of_zeroed_inodes(self) -> int:
        """Number of zeroed inodes on filesystem.

        Returns:

            int: Number of zeroed inodes on filesystem.
        """
        return self.__number_of_zeroed_inodes

    @property
    def number_of_blocks(self) -> int:
        """Number of blocks on filesystem.

        Returns:

            int: Number of blocks on filesystem.
        """
        return self.sb.s_blocks_count_lo

    @property
    def number_of_allocated_blocks(self) -> int:
        """Number of allocated blocks on filesystem.

        Returns:

            int: Number of allocated blocks on filesystem.
        """
        return self.__number_of_allocated_blocks

    @property
    def number_of_unallocated_blocks(self) -> int:
        """Number of unallocated blocks on filesystem.

        Returns:

            int: Number of unallocated blocks on filesystem.
        """
        return self.sb.s_free_blocks_count_lo

    @property
    def number_of_block_groups(self) -> int:
        """Number of block groups.

        Read from the superblock.

        Returns:

            int: Number of block groups.
        """
        return self.sb.block_group_count

    @property
    def allocated_blocks(self) -> Iterator[int]:
        """Allocated blocks.

        Generator. Iterates through each block_bitmap and
        gets allocated blocks.

        Returns:

            int: An allocated block number from the filesystem.
        """

        for group_number in range(0, self.sb.block_group_count):
            block_bitmap = self.get_block_bitmap(group_number)
            if block_bitmap is None:
                continue
            for block in block_bitmap.allocated_blocks:
                yield block

    @property
    def unallocated_blocks(self) -> Iterator[int]:
        """Unallocated blocks.

        Generator. Iterates through each block_bitmap and
        gets unallocated blocks.

        Returns:

            int: An unallocated block number from the filesystem.
        """

        for group_number in range(0, self.sb.block_group_count):
            block_bitmap = self.get_block_bitmap(group_number)
            if block_bitmap is None:
                continue
            for block in block_bitmap.unallocated_blocks:
                yield block

    @property
    def unallocated_block_ranges(self) -> Iterator:
        """Unallocated block ranges.

        Generator. Gets all unallocated blocks and groups consecutive
        entries.

        Returns:

            Generator: A group of consecutive block numbers.
        """
        for group in more_itertools.consecutive_groups(self.unallocated_blocks):
            yield list(group)

    def __le_uint(self) -> int:
        """Get little endian unsigned int.
        """
        return struct.unpack("<I", self.f.read(4))[0]

    def is_inode_zeroed(self, inode_number: str) -> bool:
        """Check if an inode is zeroed.

        Checks to see if an inode is zeroed. If an inode is zeroed we can create a basic
        empty inode object on the fly pretty easily.

        Returns:

            bool: Whether or not an inode is zeroed.
        """
        return inode_number in self.zeroed_inodes
