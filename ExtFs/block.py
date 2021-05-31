"""Ext3 block classes
"""

import io
import pprint
import struct
from typing import AnyStr, Dict, Iterator

from ExtFs.util import map_bitmap


class Ext3BlockBitmap:
    """Ext3BlockBitmap.

    Ext3 Block Bitmap.

    Reads the contents of a block bitmap and determines which blocks
    are allocated and unallocated. Will seek to the block bitmap table
    location according to the GDT passed in the constructor.

    The block bitmap is read from a file-like object designated as :attr:`f`.
    The table contents are read from :attr:`f` into a :class:`io.BytesIO`
    object to avoid 1 - 4 byte read hits. If the bitmap size is a multiple of
    4 then the bitmap is unpacked 4 bytes at a time. If the table is NOT a
    multiple of 4 then it will be processed 1 byte at a time and a warning
    message will be displayed to the console.

    """

    __slots__ = [
        'f',
        '__sb',
        '__gdt',
        'num_blocks',
        'start_block',
        'bitmap_number',
        'location_block',
        'location_bytes',
        'size_bytes',
        'blocks'
    ]

    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self, sb: 'Ext3Superblock' = None, f: io.BytesIO = None, gdt: 'Ext3Gdt' = None):
        """Read and process ext block bitmap.

        Args:

            sb (Ext3Superblock): Ext3Superblock object for the filesystem superblock.
            f (io.BytesIO): File-like object containing inode table.
            gdt (Ext3Gdt): Ext3GDT object for the GDT for the block bitmap.
        """
        if sb is None:
            raise ValueError("Must provide superblock object!")
        if gdt is None:
            raise ValueError("Must provide gdt object!")
        self.f = f
        self.__sb = sb
        self.__gdt = gdt


        self.num_blocks = sb.s_blocks_per_group
        # According to dumpe2fs, group 0 is blocks 0-32767 and therefore,
        # the 1 shouldn't be added. Block 0 is the superblock.
        # self.start_block = (gdt.group_number * sb.s_blocks_per_group) + 1
        self.start_block = gdt.group_number * sb.s_blocks_per_group
        self.bitmap_number = gdt.group_number
        self.location_block = gdt.location_bitmap_block
        self.location_bytes = sb.master_offset + (self.location_block * sb.block_size)
        # One block per bit so 8 blocks per byte.
        # Double slash (//) is integer division and the modulo addition will
        # do the same as math.ceil()
        self.size_bytes = self.num_blocks // 8 + (self.num_blocks % 8 > 0)
        self.blocks = {}
        if self.bitmap_number == 0:
            self.blocks[0] = 1

    @property
    def number_of_blocks(self) -> int:
        """Number of blocks assigned to this group.

        :returns: Number of blocks assigned to this group.
        :rtype: int

        """
        return self.num_blocks

    @property
    def starting_block_number(self) -> int:
        """Starting block number of this group.

        :returns: Starting block number of this group.
        :rtype: int

        """
        return self.start_block

    @property
    def bitmap_size_bytes(self) -> int:
        """Bitmap size in bytes.

        :returns: Bitmap size in bytes.
        :rtype: int

        """
        return self.size_bytes

    @property
    def bitmap(self) -> Dict:
        """Bitmap.

        :returns: Bitmap contents as a dict.
        :rtype: dict

        """
        return self.blocks

    @property
    def allocated_blocks(self) -> Iterator[int]:
        """Allocated blocks.

        Generator.

        Returns:

            int: An allocated block number from the block group bitmap.
        """
        for block_number in self.blocks:
            if self.blocks[block_number] == 1:
                yield block_number

    @property
    def unallocated_blocks(self) -> Iterator[int]:
        """Unallocated blocks.

        Generator.

        Returns:

            int: An unallocated block number from the block group bitmap.
        """
        for block_number in self.blocks:
            if self.blocks[block_number] == 0:
                yield block_number

    def run(self) -> None:
        """Read block bitmap.
        """

        if self.__sb is None:
            raise ValueError("Must provide superblock object!")
        if self.__gdt is None:
            raise ValueError("Must provide gdt object!")
        if self.f is None:
            raise ValueError("Must provide file-like object for f!")

        # Check to see if the block bitmap is uninitialized according to the superblock.
        # If it is, then there is no point seeking to the bitmap location as we will
        # not be reading anything.
        if self.__gdt is not None:
            # Having INODE_UNINIT test was making blocks show unallocated when they were
            # actually allocated
            # if self.__gdt.EXT4_BG_INODE_UNINIT is True or self.__gdt.EXT4_BG_BLOCK_UNINIT is True:
            if self.__gdt.EXT4_BG_BLOCK_UNINIT:
                # Block bitmap is uninitialized so we need create one full of zeros
                for x in range(self.start_block, self.start_block + self.num_blocks):
                    self.blocks[x] = 0
                self.__sb = None
                self.__gdt = None
                return

        # Block bitmap is initialized so seek to its location according to the GDT.
        self.f.seek(self.location_bytes)

        # If the bitmap is a multiple of 4 then read it 4 bytes at a time
        # as this is supposed to make it faster...
        if self.size_bytes % 4 == 0:
            x = 0
            for _ in range(0, self.size_bytes // 4):
                # Read in 4 byte increments
                # conv_tuple = self.unpack.u8u8u8u8()
                conv_tuple = struct.unpack("<BBBB", self.f.read(4))
                for conv in conv_tuple:
                    self.__do_conv(conv, x)
                    x += 1
        else:
            # Read only 1 byte at a time.
            # Can be slow depending on the backing of the file-like object.
            for x in range(0, self.size_bytes):
                conv = self.__u8()
                self.__do_conv(conv, x)

        self.__sb = None
        self.__gdt = None

    def __do_conv(self, conv: AnyStr, x: int) -> None:
        """conv.

        Calculates which values in the a singular byte of a bitmap
        are allocated/unallocated. Results get stored in self.blocks.
        Block number is calculated as:
        ```start_block + ((x * 8) + y)```
        Where ```y``` is the bit in the byte, ```x``` being the iteration
        number, typically the byte number we are on.

        If the starting block number were 0 then for the first byte:
        ```0 + ((0 * 8) + y)```
        Would yield values 0 - 7 and the second iteration:
        ```0 + ((1 * 8) + y)```
        Would yield values 8-15.


        Args:

            conv (AntStr): Byte value to look at.
            x (int): Iteration number.
        """
        if conv == 0x00:
            # Byte is 0x00 so all blocks are unallocated.
            # Create block entries assigned as 0 so we can
            # look up their allocated status later.
            for y in range(0, 8):
                # block_num = self.start_block + ((x * 8) + y) + 1
                # 8191 unallocated.
                # 8192 set unallocated but actually allocated.
                # 8193 allocated.
                # 8192 should be allocated but is reflected in 8193.
                # 262144 IndexError
                # Need to shift allocations down by 1.
                block_num = self.start_block + ((x * 8) + y)
                self.blocks[block_num] = 0
            return

        alloc = map_bitmap(conv, (
            (0x1, 0),
            (0x2, 1),
            (0x4, 2),
            (0x8, 3),
            (0x10, 4),
            (0x20, 5),
            (0x40, 6),
            (0x80, 7)
        ))

        for y in range(0, 8):
            # block_num = self.start_block + ((x * 8) + y) + 1
            block_num = self.start_block + ((x * 8) + y)
            if y in alloc:
                status = 1
            else:
                status = 0
            self.blocks[block_num] = status

    def clean_for_pickle(self) -> None:
        """Clean for pickle.

        Cleans out cruft so class can be pickled.
        """
        self.f = None
        self.__sb = None
        self.__gdt = None

    def __le_char(self) -> int:
        """Get signed char(1 byte/8bits)
        """
        return struct.unpack("<b", self.f.read(1))[0]

    def __le_uchar(self) -> int:
        """Get unsigned char (1 byte/8bits)
        """
        return struct.unpack("<B", self.f.read(1))[0]

    def __le_uint(self) -> int:
        """Get little endian unsigned int.
        """
        return struct.unpack("<I", self.f.read(4))[0]

    def __le_ushort(self) -> int:
        """Get little endian unsigned short.
        """
        return struct.unpack("<H", self.f.read(2))[0]

    def __le_ulonglong(self) -> int:
        """Get little endian unsigned long long (8 bytes/64 bits)
        """
        return struct.unpack("<Q", self.f.read(8))[0]

    def __u8(self) -> int:
        return self.__le_uchar()

    def __le32(self) -> int:
        return self.__le_uint()

    def __le16(self) -> int:
        return self.__le_ushort()

    def __le64(self) -> int:
        return self.__le_ulonglong()


class Ext3Block:
    """Ext3Block.

    Ext3 block class
    """

    __slots__ = ['f', 'block_number', 'group_number', 'fs_parent_id', 'allocated']

    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self, f: io.BytesIO = None):
        self.f = f

        self.block_number = None
        self.group_number = None
        self.fs_parent_id = None
        self.allocated = None


class Ext3BlockGroup:
    """Ext3BlockGroup.

    Ext3 Block Group.

    Stores the contents of a block bitmap and provides a frontend/api
    for interacting with the data.

    Information from the superblock for each group is also stored here.

    Any requests for blocks are generated from here as well.

    Information to be found here (on a per-group basis):
        * Number of blocks
        * Number of allocated blocks
        * Number of unallocated blocks
        * Generator for allocated blocks
        * Generator for unallocated blocks
        * Method to retrieve individual :class:`Ext3Block` objects per block.
    """

    __slots__ = [
        'block_size',
        'group_number',
        'num_blocks',
        'start_block',
        'end_block',
        'blocks',
        'start_offset',
        'fs_parent_id',
        'block_bitmap',
        'number_of_allocated_blocks',
        'number_of_unallocated_blocks'
    ]

    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self, sb: 'Ext3Superblock' = None, gdt: 'Ext3Gdt' = None):
        """Ext3 block group.

        Args:

            sb (Ext3Superblock): Ext3Superblock object for the filesystem superblock.
            gdt (Ext3Gdt): Ext3GDT object for the GDT for the block bitmap.

        """
        if sb is None:
            raise ValueError("Must provide superblock object!")
        if gdt is None:
            raise ValueError("Must provide gdt object!")

        #
        # self.__debug = debug
        self.block_size = sb.block_size
        self.group_number = gdt.group_number
        if self.group_number == sb.block_group_count - 1:
            # We are the last group so we get whatever number of blocks are left over.
            # We calculate this by subtracting the sum of all the other groups number
            # of blocks from the total number of blocks reported by the superblock.
            used_blocks = self.group_number * sb.s_blocks_per_group
            remaining_blocks = sb.s_blocks_count_lo - used_blocks
            self.num_blocks = remaining_blocks
        else:
            self.num_blocks = sb.s_blocks_per_group

        self.start_block = gdt.group_number * sb.s_blocks_per_group
        self.end_block = self.start_block + self.num_blocks

        self.blocks = {}
        self.start_offset = None
        self.fs_parent_id = None
        self.block_bitmap = {}

        self.number_of_allocated_blocks = self.num_blocks - gdt.bg_free_blocks_count_lo
        self.number_of_unallocated_blocks = gdt.bg_free_blocks_count_lo


    @property
    def number_of_blocks(self) -> int:
        """Number of blocks assigned to this group.

        Returns:

            int: Number of blocks assigned to this group.
        """
        return self.num_blocks

    @property
    def allocated_blocks(self) -> Iterator[int]:
        """Allocated block inventory.

        Generator.

        Returns:

            int: Generator of all allocated block numbers.
        """

        for block in self.block_bitmap:
            if self.block_bitmap[block] == 1:
                yield block

    @property
    def unallocated_blocks(self) -> Iterator[int]:
        """Unallocated block inventory.

        Generator.

        Returns:

            int: Generator of all unallocated block numbers.
        """

        for block in self.block_bitmap:
            if self.block_bitmap[block] == 0:
                yield block

    def get_block(self, block_number: int) -> Ext3Block:
        """Gets a block instance for a block number.

        If object exists already in ```self.blocks``` then that
        object will be returned. If not, a new one is generated
        and the resulting object is stored in ```self.blocks```.

        Args:

            block_number (int): Block number.

        Returns:

            Ext3Block: Ext3Block instance for block number.
        """

        block_number = int(block_number)
        if block_number in self.blocks:
            return self.blocks[block_number]

        b = Ext3Block()
        b.block_number = block_number
        try:
            b.allocated = self.block_bitmap[block_number]
        except KeyError as e: # pylint: disable=unused-variable
            raise RuntimeError(f"Could not find block in block bitmap for block {block_number}!")
        b.group_number = self.group_number

        self.blocks[block_number] = b
        return b
