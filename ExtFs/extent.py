"""Ext4 extent.
"""

import io
import pprint

class Ext4ExtentDocumentation:
    """Ext4ExtentDocumentation.

    Class for ext4 extent.
    """

    __slots__ = ['f', 'util', 'unpack']
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self, f: io.BytesIO = None):
        self.f = f

        self.util = None

        # https://ext4.wiki.kernel.org/index.php/Ext4_Design
        # /*
        #  * This is the extent on-disk structure.
        #  * It's used at the bottom of the tree.
        #  */
        # struct ext4_extent {
        #         __le32  ee_block;       /* first logical block extent covers */
        #         __le16  ee_len;         /* number of blocks covered by extent */
        #         __le16  ee_start_hi;    /* high 16 bits of physical block */
        #         __le32  ee_start_lo;    /* low 32 bits of physical block */
        # };

        # /*
        #  * This is index on-disk structure.
        #  * It's used at all the levels except the bottom.
        #  */
        # struct ext4_extent_idx {
        #         __le32  ei_block;       /* index covers logical blocks from 'block' */
        #         __le32  ei_leaf_lo;     /* pointer to the physical block of the next *
        #                                  * level. leaf or next index could be there */
        #         __le16  ei_leaf_hi;     /* high 16 bits of physical block */
        #         __u16   ei_unused;
        # };

        # https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout
        # In ext4, the file to logical block map has been replaced with an extent tree.
        # Under the old scheme, allocating a contiguous run of 1,000 blocks requires an
        # indirect block to map all 1,000 entries; with extents, the mapping is reduced to
        # a single struct ext4_extent with ee_len = 1000. If flex_bg is enabled, it is
        # possible to allocate very large files with a single extent, at a considerable
        # reduction in metadata block use, and some improvement in disk efficiency. The
        # inode must have the extents flag (0x80000) flag set for this feature to be in use.

        # Extents are arranged as a tree. Each node of the tree begins with a
        # struct ext4_extent_header. If the node is an interior node (eh.eh_depth > 0),
        # the header is followed by eh.eh_entries instances of struct ext4_extent_idx;
        # each of these index entries points to a block containing more nodes in the extent tree.
        # If the node is a leaf node (eh.eh_depth == 0), then the header is followed by
        # eh.eh_entries instances of struct ext4_extent; these instances point to the file's
        # data blocks. The root node of the extent tree is stored in inode.i_block, which
        # allows for the first four extents to be recorded without the use of extra metadata blocks.

class Ext4ExtentHeader:
    """Ext4ExtentHeader.

    Ext4 extent header
    """

    __slots__ = [
        'eh_entries',
        'eh_max',
        'eh_depth',
        'eh_generation',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self))

    # def __repr__(self):
    #     return pprint.pformat(vars(self))

    def __init__(self, entries=None, maximum=None, depth=None, generation=None):
        self.eh_entries = entries
        self.eh_max = maximum
        self.eh_depth = depth
        self.eh_generation = generation

class Ext4ExtentIdx:
    """Ext4ExtentIdx.

    Ext4 extent idx
    """

    __slots__ = [
        'ei_block',
        'ei_leaf_lo',
        'ei_leaf_hi',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self))

    # def __repr__(self):
    #     return pprint.pformat(vars(self))

    def __init__(self, block=None, leaf_lo=None, leaf_hi=None):
        self.ei_block = block
        self.ei_leaf_lo = leaf_lo
        self.ei_leaf_hi = leaf_hi

class Ext4Extent:
    """Ext4Extent.

    Ext4 extent.
    """

    __slots__ = [
        'ee_block',
        'ee_len',
        'ee_start_hi',
        'ee_start_lo',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self))

    # def __repr__(self):
    #     return pprint.pformat(vars(self))

    def __init__(self, block=None, length=None, start_hi=None, start_lo=None):
        self.ee_block = block
        self.ee_len = length
        self.ee_start_hi = start_hi
        self.ee_start_lo = start_lo

class Ext4ExtentTail:
    """Ext4ExtentTail.

    Ext4 extent tail.
    """

    __slots__ = ['eb_checksum']

    # def __str__(self):
    #     return pprint.pformat(vars(self))

    # def __repr__(self):
    #     return pprint.pformat(vars(self))

    def __init__(self, checksum=None):
        self.eb_checksum = checksum

    def checksum_calculate(self, uuid, inum, igeneration, extentblock):
        """Generate crc32c checksum.

        uuid+inum+igeneration+extentblock
        """
        # TODO: Implement this