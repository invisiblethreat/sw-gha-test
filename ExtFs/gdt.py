"""Ext3 group descriptor table class
"""

import io
import struct
from ExtFs.util import map_bitmap

class Ext3Gdt:
    """Ext3Gdt.

    Class for ext3 gdt.
    """

    __slots__ = [
        'f',
        '__sb',
        'group_number',
        'fs_parent_id',
        'location_bitmap_block',
        'location_bitmap_inode',
        'location_table_inode',
        'count_block_free',
        'count_inode_free',
        'count_directories',
        'flags_blockgroup',
        'location_bitmap_snapshot_exclusion',
        'bitmap_block_checksum',
        'bitmap_inode_checksum',
        'count_inode_unused',
        'gdt_checksum',
        'bg_block_bitmap_lo',
        'bg_inode_bitmap_lo',
        'bg_inode_table_lo',
        'bg_free_blocks_count_lo',
        'bg_free_inodes_count_lo',
        'bg_used_dirs_count_lo',
        'bg_flags',
        'bg_exclude_bitmap_lo',
        'bg_block_bitmap_csum_lo',
        'bg_inode_bitmap_csum_lo',
        'bg_itable_unused_lo',
        'bg_checksum',
        'bg_block_bitmap_hi',
        'bg_inode_bitmap_hi',
        'bg_inode_table_hi',
        'bg_free_blocks_count_hi',
        'bg_free_inodes_count_hi',
        'bg_used_dirs_count_hi',
        'bg_itable_unused_hi',
        'bg_exclude_bitmap_hi',
        'bg_block_bitmap_csum_hi',
        'bg_inode_bitmap_csum_hi',
        'bg_reserved',
        '__EXT4_BG_INODE_UNINIT',
        '__EXT4_BG_BLOCK_UNINIT',
        '__EXT4_BG_INODE_ZEROED',
        'bits',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self, sb: 'Ext3Superblock' = None, f: io.BytesIO = None, group_number: int = None):
        """Create and read Gdt for a group.

        Args:

            sb (Ext3Superblock): Ext3Superblock instance for filesystem.
            f (io.BytesIO): File-like object for filesystem.
            group_number (int): Group number of Gdt.
        """
        self.f = f
        self.__sb = sb

        self.group_number = group_number
        self.fs_parent_id = None

        # 32-bit mode (struct size 32 bytes)
        self.location_bitmap_block = None
        self.location_bitmap_inode = None
        self.location_table_inode = None
        self.count_block_free = None
        self.count_inode_free = None
        self.count_directories = None
        self.flags_blockgroup = None
        self.location_bitmap_snapshot_exclusion = None
        self.bitmap_block_checksum = None
        self.bitmap_inode_checksum = None
        self.count_inode_unused = None
        self.gdt_checksum = None

        # Actual struct names
        # 32-bit mode (struct size 32 bytes)
        self.bg_block_bitmap_lo = None
        self.bg_inode_bitmap_lo = None
        self.bg_inode_table_lo = None
        self.bg_free_blocks_count_lo = None
        self.bg_free_inodes_count_lo = None
        self.bg_used_dirs_count_lo = None
        self.bg_flags = None
        self.bg_exclude_bitmap_lo = None
        self.bg_block_bitmap_csum_lo = None
        self.bg_inode_bitmap_csum_lo = None
        self.bg_itable_unused_lo = None
        self.bg_checksum = None

        # 64-bit mode (struct size 64 bytes)
        self.bg_block_bitmap_hi = None
        self.bg_inode_bitmap_hi = None
        self.bg_inode_table_hi = None
        self.bg_free_blocks_count_hi = None
        self.bg_free_inodes_count_hi = None
        self.bg_used_dirs_count_hi = None
        self.bg_itable_unused_hi = None
        self.bg_exclude_bitmap_hi = None
        self.bg_block_bitmap_csum_hi = None
        self.bg_inode_bitmap_csum_hi = None
        self.bg_reserved = None

        # Flags. Lazy Block Group Initialization.
        # The superblock feature flag indicating this may also be
        # RO_COMPAT_GDT_CSUM
        # Both UNINITS mean that the inode and block bitmaps can be
        # calculated and therefore the on-disk bitmap blocks are
        # not initialized. This is generally the case for an empty
        # block group or a block group containing only fixed-location
        # block group metadata.
        self.__EXT4_BG_INODE_UNINIT = False
        self.__EXT4_BG_BLOCK_UNINIT = False
        # ZEROED flag means that the inode table has been initialized.
        # The kernel will initialize the inode tables in the background.
        self.__EXT4_BG_INODE_ZEROED = False

        self.bits = 32
        if sb is not None:
            # Set some options from superblock
            if sb.s_desc_size is not None and sb.s_desc_size > 32:
                # s_desc_size from superblock tells us the size of
                # a GDT in bytes. Default being 32 bytes and
                # should be 64 bytes in 64-bit mode. 64-bit mode
                # should be indicated by the INCOMPAT_64BIT flag
                # from the superblock.
                self.bits = 64

    @property
    def EXT4_BG_INODE_UNINIT(self) -> bool:
        """This GDT's Inode table and bitmap are not initialized.

        The inode and block bitmap can be calculated
        and therefore the on-disk bitmap blocks are
        not initialized. This is generally the case for
        an empty block group or a block group containing
        only fixed-location block group metadata.


        Returns:

            bool: State of EXT4_BG_INODE_UNINIT for GDT.
        """
        return self.__EXT4_BG_INODE_UNINIT

    @property
    def EXT4_BG_BLOCK_UNINIT(self) -> bool:
        """This GDT's block bitmap is not initialized.

        The block bitmap can be calculated
        and therefore the on-disk bitmap blocks are
        not initialized. This is generally the case for
        an empty block group or a block group containing
        only fixed-location block group metadata.

        Returns:

            bool: State of EXT4_BG_BLOCK_UNINIT for GDT.
        """
        return self.__EXT4_BG_BLOCK_UNINIT

    @property
    def EXT4_BG_INODE_ZEROED(self) -> bool:
        """This GDT's inode table is zeroed.

        The inode table has been initialized and the
        kernel will initialize the inode tables in the background.

        Returns:

            bool: State of EXT4_BG_INODE_ZEROED for GDT.
        """
        return self.__EXT4_BG_INODE_ZEROED

    def __le_uint(self) -> int:
        """Get little endian unsigned int.
        """
        return struct.unpack("<I", self.f.read(4))[0]

    def __le_ushort(self) -> int:
        """Get little endian unsigned short.
        """
        return struct.unpack("<H", self.f.read(2))[0]

    def run(self) -> None:
        """Reads the GDT from file handle f.
        """

        # Read 32 bytes regardless
        self.location_bitmap_block = self.__le_uint()
        self.bg_block_bitmap_lo = self.location_bitmap_block

        self.location_bitmap_inode = self.__le_uint()
        self.bg_inode_bitmap_lo = self.location_bitmap_inode

        self.location_table_inode = self.__le_uint()
        self.bg_inode_table_lo = self.location_bitmap_inode

        self.count_block_free = self.__le_ushort()
        self.bg_free_blocks_count_lo = self.count_block_free

        self.count_inode_free = self.__le_ushort()
        self.bg_free_inodes_count_lo = self.count_inode_free

        self.count_directories = self.__le_ushort()
        self.bg_used_dirs_count_lo = self.count_directories

        self.flags_blockgroup = self.__le_ushort()
        self.bg_flags = self.flags_blockgroup

        self.location_bitmap_snapshot_exclusion = self.__le_uint()
        self.bg_exclude_bitmap_lo = self.location_bitmap_snapshot_exclusion

        self.bitmap_block_checksum = self.__le_ushort()
        self.bg_block_bitmap_csum_lo = self.bitmap_block_checksum

        self.bitmap_inode_checksum = self.__le_ushort()
        self.bg_inode_bitmap_csum_lo = self.bitmap_inode_checksum

        self.count_inode_unused = self.__le_ushort()
        self.bg_itable_unused_lo = self.count_inode_unused

        self.gdt_checksum = self.__le_ushort()
        self.bg_checksum = self.gdt_checksum

        if self.bits == 64:
            # Read the extra 32 bytes
            self.bg_block_bitmap_hi = self.__le_uint()
            self.bg_inode_bitmap_hi = self.__le_uint()
            self.bg_inode_table_hi = self.__le_uint()
            self.bg_free_blocks_count_hi = self.__le_ushort()
            self.bg_free_inodes_count_hi = self.__le_ushort()
            self.bg_used_dirs_count_hi = self.__le_ushort()
            self.bg_itable_unused_hi = self.__le_ushort()
            self.bg_exclude_bitmap_hi = self.__le_uint()
            self.bg_block_bitmap_csum_hi = self.__le_ushort()
            self.bg_inode_bitmap_csum_hi = self.__le_ushort()
            self.bg_reserved = self.f.read(4)

        gdt_flags = (
            (0x1, 'EXT4_BG_INODE_UNINIT'),
            (0x2, 'EXT4_BG_BLOCK_UNINIT'),
            (0x4, 'EXT4_BG_INODE_ZEROED')
            )

        r = map_bitmap(self.bg_flags, gdt_flags)

        # Attribute name must contain the class name due to
        # some AttributeError when using slots and "private"
        # variable names (starting with '__').
        value_to_attr_name_mapping = {
            0x1: '_Ext3Gdt__EXT4_BG_INODE_UNINIT',
            0x2: '_Ext3Gdt__EXT4_BG_BLOCK_UNINIT',
            0x4: '_Ext3Gdt__EXT4_BG_INODE_ZEROED',
        }

        for k, v in value_to_attr_name_mapping.items():
            if k in r:
                setattr(self, v, True)


        self.__sb = None
