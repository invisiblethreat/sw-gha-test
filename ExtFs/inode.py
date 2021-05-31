"""Ext3 Inode classes.
"""

# pylint: disable=too-many-lines

import io
import struct
from typing import Any, Dict, Iterator, List, Tuple

from ExtFs.extent import Ext4Extent, Ext4ExtentHeader, Ext4ExtentIdx
from ExtFs.utility import Ext3Utility


UNPACK_LE32 = struct.Struct("<I")
UNPACK_U8 = struct.Struct("<B")
UNPACK_LE16 = struct.Struct("<H")
UNPACK_EXTENT_HEADER = struct.Struct("<HHHI")
UNPACK_EXTENT = struct.Struct("<IHHI")
UNPACK_EXTENT_IDX = struct.Struct("<IIHH")
UNPACK_INODE_HEADER = struct.Struct("<HHIIIIIHHII")
UNPACK_INODE_DBLOCKS = struct.Struct("<IIIIIIIIIIII")

class Ext3InodeBitmap:
    """Ext3InodeBitmap.

    Class for processing an Ext Inode Bitmap.
    """

    __slots__ = [
        'f',
        '__sb',
        '__gdt',
        'num_inodes',
        'start_inode',
        '__bitmap_number',
        '__location_block',
        '__location_bytes',
        'size_bytes',
        'inodes',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self, sb: 'Ext3Superblock' = None, f: io.BytesIO = None, gdt: 'Ext3Gdt' = None):
        """Read and process an ext3 inode bitmap.

        Args:

            sb (Ext3Superblock): Ext3Superblock object for the filesystem superblock.
            f (io.BytesIO): File-like object to read bitmap from.
            gdt (Ext3GDT): `Ext3GDT` object for the GDT for the block bitmap.

        """
        if sb is None:
            raise ValueError("Must provide superblock object!")
        if gdt is None:
            raise ValueError("Must provide gdt object!")
        self.f = f
        self.__sb = sb
        self.__gdt = gdt

        self.num_inodes = sb.s_inodes_per_group
        self.start_inode = gdt.group_number * sb.s_inodes_per_group
        self.__bitmap_number = gdt.group_number
        self.__location_block = gdt.location_bitmap_inode
        self.__location_bytes = self.__location_block * sb.block_size
        # One inode per bit so 8 inodes per byte.
        # Double slash (//) is integer division and the modulo addition will
        # do the same as math.ceil()
        self.size_bytes = self.num_inodes // 8 + (self.num_inodes % 8 > 0)
        self.inodes = {}

    @property
    def number_of_inodes(self) -> int:
        """Number of inodes assigned to this group.

        Returns:

            int: Number of inodes assigned to this group.
        """
        return self.num_inodes

    @property
    def starting_inode_number(self) -> int:
        """Starting inode number of this group.

        Returns:

            int: Starting inode number of this group.
        """
        return self.start_inode

    @property
    def bitmap_size_bytes(self) -> int:
        """Bitmap size in bytes.

        Returns:

            int: Bitmap size in bytes.
        """
        return self.size_bytes

    @property
    def location_block(self) -> int:
        """Location block.

        Block number where bitmap is located.

        Returns:

            int: Block number where bitmap is located.
        """
        return self.__location_block

    @property
    def location_bytes(self) -> int:
        """Location bytes.

        Offset in bytes where bitmap is located.

        Returns:

            int: Offset in bytes where bitmap is located.
        """
        return self.__location_bytes


    @property
    def bitmap(self) -> Dict:
        """Bitmap.

        Returns:

            Dict: Bitmap contents as a dict.
        """
        return self.inodes

    @property
    def bitmap_number(self) -> int:
        """Bitmap number.

        Which group number bitmap belongs to.

        Returns:

            int: Bitmap group number.
        """
        return self.__bitmap_number

    @property
    def allocated_inodes(self) -> Iterator[int]:
        """Allocated inodes.

        Generator.

        Returns:

            int: An allocated inode number from the inode bitmap.
        """
        for inode_number in self.inodes:
            if self.inodes[inode_number] == 1:
                yield inode_number

    @property
    def unallocated_inodes(self) -> Iterator[int]:
        """Unallocated inodes.

        Generator.

        Returns:

            int: An unallocated inode number from the inode bitmap.
        """
        for inode_number in self.inodes:
            if self.inodes[inode_number] == 0:
                yield inode_number

    def __le_char(self) -> int:
        """Get little endian char.
        """
        return struct.unpack("<c", self.f.read(1))[0]

    def __le_uchar(self) -> int:
        """Get little endian unsigned char.
        """
        return struct.unpack("<B", self.f.read(1))[0]

    def __map_bitmap(self, value: int, mapping: Tuple[int, str]) -> List:
        """Make human readable.
        """
        return [t[1] for t in mapping if value & t[0]]

    # pylint: disable=line-too-long,unused-variable
    def run(self) -> None:
        """Read inode bitmap.
        """

        if self.__sb is None:
            raise ValueError("Must provide superblock object!")
        if self.__gdt is None:
            raise ValueError("Must provide gdt object!")
        if self.f is None:
            raise ValueError("Must provide file-like object for f!")

        # Check to see if the inode bitmap is uninitialized according to the superblock.
        # If it is, then there is no point seeking to the bitmap location as we will
        # not be reading anything.

        if self.__gdt is not None:
            if self.__gdt.EXT4_BG_INODE_UNINIT is True:
                # Inode and block bitmaps are uninitialized so we need to
                # create one full of zeros
                # self.__log.debug("GDT is EXT4_BG_INODE_UNINIT. Creating bitmap...")
                for x in range(self.start_inode + 1, self.start_inode + 1 + self.num_inodes):
                    self.inodes[x] = 0
                # self.__log.debug("Creating bitmap... Done! Returning...")
                self.__sb = None
                self.__gdt = None
                return

        # Block bitmap is initialized so seek to its location according to the GDT.
        self.f.seek(self.location_bytes)

        # We read the entire contents of the bitmap at once and create
        # an io.BytesIO object instead of hitting the disk/file handle
        # to read 1 byte at a time.
        # Get the size in bytes that the table cache should be
        table_cache_size = self.size_bytes
        # Read the table into buffer
        table_cache = self.f.read(table_cache_size)
        # Make stream
        table_cache_f = io.BytesIO(table_cache)

        # Read table byte by byte
        for x in range(0, self.size_bytes):
            # value = self.f.read(1)
            value = table_cache_f.read(1)
            conv = struct.unpack("<B", value)[0]
            if conv == 0x00:
                # Create inode entries assigned as 0 so we can
                # look up their allocated status later.
                for y in range(0, 8):
                    inode_num = self.start_inode + ((x * 8) + y) + 1
                    self.inodes[inode_num] = 0
                continue

            alloc = self.__map_bitmap(conv, (
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
                inode_num = self.start_inode + ((x * 8) + y) + 1
                if y in alloc:
                    status = 1
                else:
                    status = 0
                self.inodes[inode_num] = status

        self.__gdt = None
    # pylint: enable=line-too-long,unused-variable

class Ext3Inode:
    """Ext3Inode.

    Ext3 inode class.
    """

    __slots__ = [
        'f',
        'byte_start',
        'byte_end',
        'byte_count',
        'block_size',
        '__dblocks',
        '__eblocks',
        '__sparse',
        'offset',
        'util',
        'inode_number',
        'inode_table',
        'fs_parent_id',
        'allocated',
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
        'i_block',
        'extents',
        'i_generation',
        'i_file_acl_lo',
        'i_size_high',
        'i_dir_acl',
        'i_obso_faddr',
        'union_osd2',
        'i_extra_size',
        'i_checksum_hi',
        'i_ctime_extra',
        'i_mtime_extra',
        'i_atime_extra',
        'i_crtime',
        'i_crtime_extra',
        'i_version_hi',
        'i_projid',
        'file_type',
        'EXT4_SECRM_FL',
        'EXT4_UNRM_FL',
        'EXT4_COMPR_FL',
        'EXT4_SYNC_FL',
        'EXT4_IMMUTABLE_FL',
        'EXT4_APPEND_FL',
        'EXT4_NODUMP_FL',
        'EXT4_NOATIME_FL',
        'EXT4_DIRTY_FL',
        'EXT4_COMPRBLK_FL',
        'EXT4_NOCOMPR_FL',
        'EXT4_ENCRYPT_FL',
        '__EXT4_INDEX_FL',
        'EXT4_IMAGIC_FL',
        'EXT4_JOURNAL_DATA_FL',
        'EXT4_NOTAIL_FL',
        'EXT4_DIRSYNC_FL',
        'EXT4_TOPDIR_FL',
        'EXT4_HUGE_FILE_FL',
        'EXT4_EXTENTS_FL',
        'EXT4_EA_INODE_FL',
        'EXT4_EOFBLOCKS_FL',
        'EXT4_SNAPFILE_FL',
        'EXT4_SNAPFILE_DELETED_FL',
        'EXT4_SNAPFILE_SHRUNK_FL',
        'EXT4_INLINE_DATA_FL',
        'EXT4_PROJINHERIT_FL',
        'EXT4_RESERVED_FL',
        'S_IXOTH',
        'S_IWOTH',
        'S_IROTH',
        'S_IXGRP',
        'S_IWGRP',
        'S_IRGRP',
        'S_IXUSR',
        'S_IWUSR',
        'S_IRUSR',
        'S_IREAD',
        'S_ISVTX',
        'S_ISGID',
        'S_ISUID',
        'S_IFIFO',
        'S_IFCHR',
        'S_IFDIR',
        'S_IFBLK',
        'S_IFREG',
        'S_IFLNK',
        'S_IFSOCK',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self, f: io.BytesIO = None):
        self.f = f

        self.byte_start = None
        self.byte_end = None
        self.byte_count = None
        self.block_size = None
        self.__dblocks = None
        self.__eblocks = list()
        self.__sparse = None
        self.offset = 0
        self.util = None

        self.inode_number = None
        self.inode_table = None
        self.fs_parent_id = None
        self.allocated = None
        # struct ext4_inode from linux kernel
        self.i_mode = None
        self.i_uid = None
        self.i_size_lo = None
        self.i_atime = None
        self.i_ctime = None
        self.i_mtime = None
        self.i_dtime = None
        self.i_gid = None
        self.i_links_count = None
        self.i_blocks_lo = None
        self.i_flags = None
        self.union_osd1 = None
        # offset 0x28, size 60 bytes. i_block[EXT4_N_BLOCKS=15]
        # Block map or extent tree
        self.i_block = None
        self.extents = None
        self.i_generation = None
        self.i_file_acl_lo = None
        # ext4 - file/directory size
        self.i_size_high = None
        # ext2/3 - usually set to zero and never used
        self.i_dir_acl = None
        # (Obsolete) fragment address
        self.i_obso_faddr = None
        # Union osd2 - 12 bytes
        self.union_osd2 = None
        self.i_extra_size = None
        self.i_checksum_hi = None
        self.i_ctime_extra = None
        self.i_mtime_extra = None
        self.i_atime_extra = None
        self.i_crtime = None
        self.i_crtime_extra = None
        self.i_version_hi = None
        self.i_projid = None

        # i_mode (file mode)
        self.file_type = None

        self.EXT4_SECRM_FL = False
        self.EXT4_UNRM_FL = False
        self.EXT4_COMPR_FL = False
        self.EXT4_SYNC_FL = False
        self.EXT4_IMMUTABLE_FL = False
        self.EXT4_APPEND_FL = False
        self.EXT4_NODUMP_FL = False
        self.EXT4_NOATIME_FL = False
        self.EXT4_DIRTY_FL = False
        self.EXT4_COMPRBLK_FL = False
        self.EXT4_NOCOMPR_FL = False
        self.EXT4_ENCRYPT_FL = False
        self.__EXT4_INDEX_FL = False
        self.EXT4_IMAGIC_FL = False
        self.EXT4_JOURNAL_DATA_FL = False
        self.EXT4_NOTAIL_FL = False
        self.EXT4_DIRSYNC_FL = False
        self.EXT4_TOPDIR_FL = False
        self.EXT4_HUGE_FILE_FL = False
        self.EXT4_EXTENTS_FL = False
        self.EXT4_EA_INODE_FL = False
        self.EXT4_EOFBLOCKS_FL = False
        self.EXT4_SNAPFILE_FL = False
        self.EXT4_SNAPFILE_DELETED_FL = False
        self.EXT4_SNAPFILE_SHRUNK_FL = False
        self.EXT4_INLINE_DATA_FL = False
        self.EXT4_PROJINHERIT_FL = False
        self.EXT4_RESERVED_FL = False

        # permissions and such
        self.S_IXOTH = False
        self.S_IWOTH = False
        self.S_IROTH = False
        self.S_IXGRP = False
        self.S_IWGRP = False
        self.S_IRGRP = False
        self.S_IXUSR = False
        self.S_IWUSR = False
        self.S_IRUSR = False
        self.S_IREAD = False
        self.S_ISVTX = False
        self.S_ISGID = False
        self.S_ISUID = False

        self.S_IFIFO = False
        self.S_IFCHR = False
        self.S_IFDIR = False
        self.S_IFBLK = False
        self.S_IFREG = False
        self.S_IFLNK = False
        self.S_IFSOCK = False

    @property
    def EXT4_INDEX_FL(self) -> bool:
        """Directory has hashed indexes.

        True if directory has hashed indexes.
        False if directory is "classic" and
        is read linear.

        Inode flag (i_flags) value 0x100.

        Returns:

            bool: If directory has hashed indexes.
        """
        return self.__EXT4_INDEX_FL

    @EXT4_INDEX_FL.setter
    def EXT4_INDEX_FL(self, value: bool):
        if isinstance(value, bool) is False:
            raise ValueError("EXT4_INDEX_FL must be True/False!")
        self.__EXT4_INDEX_FL = value

    # pylint: disable=line-too-long
    @property
    def dblocks(self) -> List:
        """List of inode's direct blocks regardless of underlying addressing mechanism.

        A list of all the fully resolved blocks lives here. These are *DIRECT* blocks and
        require no further "resolution" regardless of use indirects, double indirects, extents, etc.

        :getter: If :py:attr:`~dblocks` is ``None`` then :func:`Ext3Inode.dblocks_resolve` will be called to resolve all the blocks and store the result in :py:attr:`~dblocks`.
        :setter: Sets :py:attr:`~dblocks` to given value.
        :type: list

        """
        if self.__dblocks is None:
            try:
                self.__dblocks = self.dblocks_resolve()
            except Exception as e: # pylint: disable=broad-except,unused-variable,try-except-raise
                raise
        return self.__dblocks
    # pylint: enable=line-too-long

    @dblocks.setter
    def dblocks(self, value):
        self.__dblocks = value

    @property
    def eblocks(self):
        """Extent blocks.

        """
        if self.__dblocks is None:
            try:
                self.__dblocks = self.dblocks_resolve()
            except Exception as e:  # pylint: disable=broad-except,unused-variable,try-except-raise
                # self.__log.exception("Exception dump. Inode: %s\nException: %s", self, str(e), exc_info=True)
                raise
        return self.__eblocks

    @eblocks.setter
    def eblocks(self, value):
        self.__eblocks = value

    @property
    def sparse(self) -> bool:
        """Is this a sparse file/inode?

        Returns:

            bool: Whether or not file/inode is sparse.
        """
        return self.__sparse

    def dblocks_resolve(self) -> List:
        """Resolves extents or i_block into a list of blocks.

        If inode has ``EXT4_EXTENTS_FL`` set to ``True`` then
        :func:`Ext3Inode.dblocks_resolve_extents` will be used.
        Otherwise, an instance of :class:`Ext3Utility` using :func:`Ext3Utility.resolve_indirects`
        will resolve the contents of i_block to direct blocks.

        Returns:

            List: List of direct blocks for inode.
        """

        if self.EXT4_EXTENTS_FL is True:
            # Uses extents
            return self.dblocks_resolve_extents()
        elif self.EXT4_EXTENTS_FL is False:
            # Uses i_block
            # TODO: Add sanity checks here to make that the values of i_block are not None.
            if not isinstance(self.i_block, dict):
                raise ValueError("i_block is not a dictionary! Is: %s" % type(self.i_block))
            self.util = Ext3Utility(self.f, block_size=self.block_size, offset=0)
            dblocks = self.i_block['direct']
            if self.i_block['indirect'] != 0:
                dblocks += self.util.resolve_indirects(self.i_block['indirect'], "single")
            if self.i_block['double_indirect'] != 0:
                dblocks += self.util.resolve_indirects(self.i_block['double_indirect'], "double")
            if self.i_block['triple_indirect'] != 0:
                dblocks += self.util.resolve_indirects(self.i_block['triple_indirect'], "triple")
            return dblocks
        else:
            # Not set
            raise ValueError("EXT4_EXTENTS_FL is neither True or False!")

    def dblocks_resolve_extents(self) -> Any:
        """Resolves extents into blocks.

        Seeks 0x28 (40) bytes into ``self.f`` and calls :func:`Ext3Inode.extent_process`.

        Returns:

            Any: Return value from :func:`Ext3Inode.extent_process`.
        """
        self.f.seek(self.byte_start + 0x28)
        return self.extent_process()

    def extent_process(self, block: int = None, block_size: int = None) -> List[int]:
        """Handles all the extent stuff.

        If ``block`` and ``block_size`` are provided then ``self.f`` will
        be seeked to ``(block * block_size) + self.master_offset``.

        Args:

            block (int, optional): Block number to process. Defaults to None.
            block_size (int, optional): Size of blocks in bytes. Defaults to None.

        Raises:
            RuntimeError: If extent header depth exceeeds 5 levels.

        Returns:

            None or List[int]: List of all direct block numbers belonging to
                inode or None if error reading extent.
        """

        if block is not None and block_size is not None:
            seek_pos = block * block_size
            self.f.seek(seek_pos)
        extent_header = self.extent_header_read()

        if extent_header is None:
            return

        # First entry in our extent list should be the header
        entries = list()
        entries.append(extent_header)
        dblocks = list()
        last_ee_block = 0
        sparse_block_number = -1

        # Process each entry in the extent_header.eh_entries
        for _ in range(0, extent_header.eh_entries):
            entry = None
            blocks = list()
            if extent_header.eh_depth == 0:
                # This extent node points to data blocks, not other extent nodes
                # Let's read Ext4Extent now
                entry = self.extent_read()

                # Extent entries give a starting block number and length of the extent.
                # So our direct blocks start at entry.ee_start_lo and continue
                # for entry.ee_len blocks.
                # Loop over this range and append each block to the blocks list.
                for x in range(0, entry.ee_len):
                    block = entry.ee_start_lo + x
                    ee_block = entry.ee_block + x

                    # Only look for previous sparse blocks if we are
                    # processing the first block in the extent record
                    if x == 0:
                        # Check to see if our current ee_block is
                        # last_ee_block + 1... if so then the last
                        # block is contigous with us.
                        if ee_block != last_ee_block + 1:
                            # If we are the first block (0) then don't do anything
                            if ee_block == 0:
                                pass
                            else:
                                # We are sparse
                                self.__sparse = True

                                # Calculate the number of blocks we are missing.
                                # This should be last_ee_block + 1 since we actually
                                # did process last_ee_block.
                                sparse_blocks = ee_block - (last_ee_block + 1)
                                # self.__log.debug("ee_block: %s last_ee_block: %s", ee_block, last_ee_block)

                                # Iterate through the number of blocks we are missing
                                # and append a negative number in its place to indicate
                                # it is a sparse block
                                for _ in range(0, sparse_blocks):
                                    self.__eblocks.append(sparse_block_number)
                                    sparse_block_number -= 1
                                    last_ee_block += 1
                                # self.__log.debug("number of sparse blocks: %s", sparse_blocks)
                    last_ee_block = ee_block
                    self.__eblocks.append(block)

                    blocks.append(block)
            elif extent_header.eh_depth > 0 and extent_header.eh_depth <= 5:
                # This extent node points to extent leaf nodes which me must process and
                # recursively resolve all of the leaf's leaf nodes.
                # Let's read Ext4ExtentIdx now
                # First save our current offset so we can seek back to it once the leaf
                # nodes have finished.
                save_pos = self.f.tell()
                entry = self.extent_idx_read()
                dblocks = self.extent_process(entry.ei_leaf_lo, self.block_size)
                # Resume position is save_pos + 12 bytes (size of extent record)
                resume_pos = save_pos + 12
                self.f.seek(resume_pos)

            else:
                # eh_depth can not be greater than 5
                raise RuntimeError(f"eh_depth greater than 5! Value: {str(extent_header.eh_depth)}")
            dblocks.extend(blocks)

        return dblocks

    def extent_header_read(self) -> 'Ext4ExtentHeader':
        """Reads an extent header.

        First checks for extent magic number (0xf30a). If magic number is found then
        returns :class:`Ext4ExtentHeader`.

        .. warning::
           ``file`` object ``self.f`` must be "pre-seeked"
           to the appropriately location for reading. No attempt to seek to the
           correct location is made with this function!

        Raises:
            RuntimeError: If extent magic (0xf30a) is not found.

        Returns:

            Ext4ExtentHeader: Ext4ExtentHeader if valid header found.
        """

        # Looking for header
        try:
            magic = hex(UNPACK_LE16.unpack(self.f.read(2))[0])
        except struct.error as e:  # pylint: disable=broad-except,unused-variable,try-except-raise
            raise

        # TODO: Return a custom exception.
        if magic != "0xf30a":
            raise RuntimeError("Extent magic not found!")

        extent_header = Ext4ExtentHeader()

        extent_header.eh_entries, extent_header.eh_max, extent_header.eh_depth, extent_header.eh_generation = UNPACK_EXTENT_HEADER.unpack(self.f.read(10)) # pylint: disable=line-too-long
        return extent_header

    # TODO: Is this needed anymore?
    def dblock_resolve_iblocks(self) -> None:
        """Resolves iblocks into blocks.
        """

    def extent_idx_read(self) -> 'Ext4ExtentIdx':
        """Reads an ext4 idx extent

        Extent is already tested for validity before calling this function.

        .. warning::
           ``file`` object ``self.f`` must be "pre-seeked"
           to the appropriately location for reading. No attempt to seek to the
           correct location is made with this function!

        Returns:

            Ext4ExtentIdx: Ext4ExtentIdx.
        """

        extent = Ext4ExtentIdx()
        # extent.ei_block = self.__le32()
        # extent.ei_leaf_lo = self.__le32()
        # extent.ei_leaf_hi = self.__le16()
        # Padding
        # self.__le16()
        extent.ei_block, extent.ei_leaf_lo, extent.ei_leaf_hi, _ = UNPACK_EXTENT_IDX.unpack(self.f.read(12)) # pylint: disable=line-too-long

        return extent

    def extent_read(self) -> 'Ext4Extent':
        """Reads an ext4 extent.

        Extent is already tested for validity before calling this function.

        .. warning::
           ``file`` object ``self.f`` must be "pre-seeked"
           to the appropriately location for reading. No attempt to seek to the
           correct location is made with this function!

        Returns:

            Ext4Extent: Ext4 extent.
        """

        extent = Ext4Extent()
        extent.ee_block, extent.ee_len, extent.ee_start_hi, extent.ee_start_lo = UNPACK_EXTENT.unpack(self.f.read(12)) # pylint: disable=line-too-long

        # Number of blocks covered by extent.
        # If the value of this field is <= 32768, the extent is initialized.
        # If the value of the field is > 32768, the extent is uninitialized and
        # the actual extent length is ee_len - 32768. Therefore, the maximum length
        # of a initialized extent is 32768 blocks, and the maximum length of
        # an uninitialized extent is 32767
        if extent.ee_len > 32768:
            # uninitialized
            extent.ee_len = extent.ee_len - 32768

        return extent

    def to_dict(self) -> Dict:
        """Serialize class to dictionary.

        Returns:

            Dict: Dictionary of class values.
        """
        return {n: getattr(self, n, None) for n in self.__slots__}

    def __le_uint(self) -> int:
        """Get little endian unsigned int.
        """
        return struct.unpack("<I", self.f.read(4))[0]

    def __le_ushort(self) -> int:
        """Get little endian unsigned short.
        """
        return struct.unpack("<H", self.f.read(2))[0]

    def __le32(self) -> int:
        return self.__le_uint()

    def __le16(self) -> int:
        return self.__le_ushort()


class Ext3InodeTable:
    """Ext3InodeTable.

    Class for processing an Ext Inode table.
    """

    __slots__ = [
        'block_size',
        'f',
        '__sb',
        '__gdt',
        'debug',
        'inode_size',
        'num_inodes',
        'start_inode',
        'INCOMPAT_EXTENTS',
        'end_inode',
        'table_number',
        'inodes',
        'start_offset',
        'fs_parent_id',
        'inode_bitmap',
        'adjust_offset',
        '__zeroed',
        '__number_of_allocated_inodes',
        '__number_of_unallocated_inodes',
        '__location_block',
        '__location_bytes',
        '__le32_struct',
    ]

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # pylint: disable=line-too-long
    def __init__(self, f: io.BytesIO = None, sb: 'Ext3Superblock' = None, gdt: 'Ext3Gdt' = None, mp=False, adjust_offset: bool = False):
        """Read and parse inode table.

        Args:

            f (io.BytesIO): File-like object containing inode table.
            sb (Ext3Superblock): Ext3Superblock object for the filesystem superblock.
            gdt (Ext3Gdt): Ext3GDT object for the GDT for the block bitmap.
            mp (bool, optional): Deprecated. Use multiprocessing. Defaults to False.
            adjust_offset (bool, optional): [description]. Defaults to False.

        Example usage:

            >>> my_inode_tbl = Ext3InodeTable(sb=superblock, gdt=desc_table, f=f)
            >>> # Provide a copy of the inode bitmap so an inode can check its allocation status
            >>> my_inode_tbl.inode_bitmap = self.inode_bitmap
            >>> my_inode_tbl.start_offset = tbl_location_bytes
            >>> my_inode_tbl.master_offset = self.master_offset
            >>> my_inode_tbl.run()

        """
        if sb is None:
            raise ValueError("Must provide superblock object!")
        if gdt is None:
            raise ValueError("Must provide gdt object!")
        self.block_size = sb.block_size
        self.f = f

        self.__sb = sb
        self.__gdt = gdt

        self.inode_size = sb.s_inode_size
        self.num_inodes = sb.s_inodes_per_group
        self.start_inode = (gdt.group_number * sb.s_inodes_per_group) + 1
        self.INCOMPAT_EXTENTS = sb.INCOMPAT_EXTENTS
        self.end_inode = self.start_inode + self.num_inodes
        self.table_number = gdt.group_number
        self.inodes = dict()
        self.start_offset = None
        self.fs_parent_id = None
        self.inode_bitmap = dict()
        self.adjust_offset = adjust_offset
        self.__zeroed = dict()

        self.__number_of_allocated_inodes = sb.s_inodes_per_group - gdt.bg_free_inodes_count_lo
        self.__number_of_unallocated_inodes = gdt.bg_free_inodes_count_lo

        self.__location_block = gdt.location_table_inode
        self.__location_bytes = (self.__location_block * sb.block_size)


        self.__le32_struct = None
    # pylint: enable=line-too-long

    @property
    def location_block(self) -> int:
        """Location block.

        Block number where bitmap is located.

        :returns: Block number where bitmap is located.
        :rtype: int

        """
        return self.__location_block

    @property
    def location_bytes(self) -> int:
        """Location bytes.

        Offset in bytes where bitmap is located.

        :returns: Offset in bytes where bitmap is located.
        :rtype: int

        """
        return self.__location_bytes

    @property
    def zeroed(self) -> Dict:
        """Inode zeroed inventory.

        An inventory of all inodes that are zeroed and contain no data.

        Returns:

            Dict: Dictionary of all zeroed inodes.
        """
        for inode in self.__zeroed:
            yield inode

    @zeroed.setter
    def zeroed(self, value: Dict):
        self.__zeroed = value

    @property
    def number_of_zeroed_inodes(self) -> int:
        """Number of zeroed inodes.

        Returns:

            int: Number of zeroed inodes.
        """
        return len(self.__zeroed)

    @property
    def allocated_inodes(self) -> Iterator[int]:
        """Allocated inode inventory.

        Generator.

        Returns:

            int: Generator of all allocated inode numbers.
        """

        for inode in self.inode_bitmap:
            if self.inode_bitmap[inode] == 1:
                yield inode

    @property
    def unallocated_inodes(self) -> Iterator[int]:
        """Unallocated inode inventory.

        Generator.

        Returns:

            int: Generator of all unallocated inode numbers.
        """

        for inode in self.inode_bitmap:
            if self.inode_bitmap[inode] == 0:
                yield inode

    @property
    def number_of_allocated_inodes(self) -> int:
        """Number of allocated inodes in inode table.

        Returns:

            int: Number of allocated inodes in inode table.
        """
        return self.__number_of_allocated_inodes

    @property
    def number_of_unallocated_inodes(self) -> int:
        """Number of unallocated inodes in inode table.

        Returns:

            int: Number of unallocated inodes in inode table.
        """
        return self.__number_of_unallocated_inodes

    def is_zeroed(self, inode_number: int) -> bool:
        """Check if an inode is zeroed.

        Checks to see if an inode is zeroed. If an inode is zeroed we can create a basic
        empty inode object on the fly pretty easily.

        Returns:

            bool: Whether or not an inode is zeroed.
        """
        if inode_number in self.__zeroed:
            return True
        return False

    def get_zeroed_inode(self, inode_number: int) -> Ext3Inode:
        """Returns a zeroed inode object.

        Returns:

            Ext3Inode: Zeroed Ext3Inode instance for inode number.
        """
        inode_number = int(inode_number)
        i = Ext3Inode(f=self.f)
        i.block_size = self.block_size
        i.inode_number = inode_number
        i.allocated = self.inode_bitmap[inode_number]
        i.inode_table = self.table_number
        i.EXT4_EXTENTS_FL = False
        i.i_block = {
            'direct': list(),
            'indirect': 0,
            'double_indirect': 0,
            'triple_indirect': 0,
        }
        return i

    def get_inode(self, inode_number: int):
        """Returns an inode.

        Return an inode and inode is zeroed will return a zeroed
        object for it.

        Returns:

            Ext3Inode: Ext3Inode instance for inode number.
        """

        if inode_number in self.inodes:
            inode = self.inodes[inode_number]
            inode.f = self.f
            return inode
        elif inode_number not in self.inodes:
            # pr = cProfile.Profile()
            # pr.enable()
            inode = self.read_inode(inode_number)
            # pr.disable()
            # s = io.StringIO()
            # ps = pstats.Stats(pr, stream=s).sort_stats('cumtime', 'name')
            # ps.print_stats()
            # print(s.getvalue())
            # pr.dump_stats("qcow2_profile.prof")

            self.inodes[inode_number] = inode
            inode.f = self.f
            return inode
        elif self.is_zeroed(inode_number):
            inode = self.get_zeroed_inode(inode_number)
            inode.f = self.f
            self.inodes[inode_number] = inode
        else:
            msg = "Could not find inode %s in table %s! " % (inode_number, self.table_number)
            msg += "Valid table inode range: %s - %s\n" % (self.start_inode, self.end_inode)
            msg += "Table dump:\n%s" % (self)
            raise RuntimeError(msg)

    def __map_bitmap(self, value: int, mapping: Tuple[int, str]):
        """
            Make human readable
        """
        return ' '.join([t[1] for t in mapping if value & t[0]]) or 'none'

    def __map_bitmap_exclusive(self, value: int, mapping: Tuple[int, str]):
        """
            Make human readable
        """
        for t in mapping:
            if value & t[0]:
                return t[1]

    def __le_uint(self) -> int:
        """Get little endian unsigned int.
        """
        return struct.unpack("<I", self.f.read(4))[0]

    def __le_ushort(self) -> int:
        """Get little endian unsigned short.
        """
        return struct.unpack("<H", self.f.read(2))[0]

    def __le32(self) -> int:
        return self.__le_uint()

    def __le16(self) -> int:
        return self.__le_ushort()

    # pylint: disable=line-too-long
    def read_inode(self, inode_number: int) -> Ext3Inode:
        """Read an inode.

        Args:

            inode_number (int): Inode number to read.

        Returns:

            Ext3Inode. Ext3Inode instance for inode number.
        """
        inode_offset = self.location_bytes + ((inode_number - self.start_inode) * self.__sb.s_inode_size)
        self.f.seek(inode_offset)
        start_offset = self.f.tell()

        handle = io.BytesIO(self.f.read(self.__sb.s_inode_size))
        handle.seek(0)

        # buf = handle.read(self.__sb.s_inode_size)
        allocated = self.inode_bitmap[inode_number]


        i_mode, i_uid, i_size_lo, i_atime, i_ctime, i_mtime, i_dtime, i_gid, i_links_count, i_blocks_lo, i_flags = UNPACK_INODE_HEADER.unpack(handle.read(36))
        hashed_indexes = i_flags & 0x1000
        inode_uses_extents = i_flags & 0x80000

        zeroed = True
        if allocated:
            zeroed = False
        elif i_mode != 0:
            zeroed = False
        elif i_uid != 0:
            zeroed = False
        elif i_size_lo != 0:
            zeroed = False
        elif i_atime != 0:
            zeroed = False
        elif i_ctime != 0:
            zeroed = False
        elif i_mtime != 0:
            zeroed = False
        elif i_dtime != 0:
            zeroed = False
        elif i_gid != 0:
            zeroed = False
        elif i_links_count != 0:
            zeroed = False
        elif i_blocks_lo != 0:
            zeroed = False
        elif hashed_indexes:
            zeroed = False
        elif inode_uses_extents:
            zeroed = False

        if zeroed:
            end_offset = handle.tell()
            num_bytes_read = end_offset - start_offset
            amount_left_to_seek = self.inode_size - num_bytes_read
            # if inode_number == 2:
            #     self.__log.critical("inode 2 is zeroed! Typically inode 2 is the root",
            #                "directory and should not be zeroed!")

            handle.seek(amount_left_to_seek, 1)
            self.__zeroed[inode_number] = True
            return

        i = Ext3Inode(f=self.f)
        i.block_size = self.block_size
        i.inode_number = inode_number
        i.allocated = self.inode_bitmap[inode_number]
        i.inode_table = self.table_number
        i.i_mode = i_mode
        i.i_uid = i_uid
        i.i_size_lo = i_size_lo
        i.i_atime = i_atime
        i.i_ctime = i_ctime
        i.i_mtime = i_mtime
        i.i_dtime = i_dtime
        i.i_gid = i_gid
        i.i_links_count = i_links_count
        # Lower 32-bits of "block" count.
        # If the huge_file feature flag is not set on the filesystem,
        # the file consumes i_blocks_lo 512-byte blocks on disk.
        # If huge_file is set and EXT4_HUGE_FILE_FL is NOT set in inode.i_flags,
        # then the file consumes i_blocks_lo + (i_blocks_hi << 32) 512-byte blocks on disk.
        # If huge_file is set and EXT4_HUGE_FILE_FL IS set in inode.i_flags,
        # then this file consumes (i_blocks_lo + i_blocks_hi << 32) filesystem blocks on disk.
        i.i_blocks_lo = i_blocks_lo
        i.i_flags = i_flags

        if hashed_indexes != 0:
            i.EXT4_INDEX_FL = True
        else:
            i.EXT4_INDEX_FL = False

        # TODO: Process this union.
        i.union_osd1 = UNPACK_LE32.unpack(handle.read(4))[0]

        # Block map or extent tree
        i.i_block = {}
        if inode_uses_extents != 0:
            # Use extents rather than block pointers
            # Don't read the extents right now
            i.EXT4_EXTENTS_FL = True
            # self.__log.debug("inode uses extents!")
            # self.f.seek(start_offset + 0x64)
            # When using a cache/buffer
            handle.seek(0x64)
        else:
            # Use block pointers
            i.EXT4_EXTENTS_FL = False
            i.i_block['direct'] = [n for n in UNPACK_INODE_DBLOCKS.unpack(handle.read(48)) if n != 0]
            i.i_block['indirect'] = UNPACK_LE32.unpack(handle.read(4))[0]
            i.i_block['double_indirect'] = UNPACK_LE32.unpack(handle.read(4))[0]
            i.i_block['triple_indirect'] = UNPACK_LE32.unpack(handle.read(4))[0]
            # direct_blocks = struct.unpack("<IIIIIIIIIIII", handle.read(48))
            # indirect, double_indirect, triple_indirect = struct.unpack("<III", handle.read(12))
        i.i_generation = UNPACK_LE32.unpack(handle.read(4))[0]
        i.i_file_acl_lo = UNPACK_LE32.unpack(handle.read(4))[0]
        # ext4 - file/directory size
        i.i_size_high = UNPACK_LE32.unpack(handle.read(4))[0]
        # ext2/3 - usually set to zero and never used
        i.i_dir_acl = i.i_size_high
        # (Obsolete) fragment address
        i.i_obso_faddr = UNPACK_LE32.unpack(handle.read(4))[0]
        # Union osd2 - 12 bytes
        # TODO: Process this union.
        # i.union_osd2 = handle.read(12)
        i.union_osd2 = handle.read(12)
        # i.i_frag = self.__le_uchar()
        # i.i_fsize = self.__le_uchar()
        # handle.read(2)
        # i.i_uid_high = self.__le_ushort()
        # i.i_gid_high = self.__le_ushort()
        # handle.read(4)

        # # inode_size of 128 has ended here!
        # if self.inode_size != 128:
        #     i.i_extra_size = self.__le16()
        #     i.i_checksum_hi = self.__le16()
        #     i.i_ctime_extra = self.__le32()
        #     i.i_mtime_extra = self.__le32()
        #     i.i_atime_extra = self.__le32()
        #     i.i_crtime = self.__le32()
        #     i.i_crtime_extra = self.__le32()
        #     i.i_version_hi = self.__le32()
        #     # struct.unpack("<HHIIIIII", handle.read(42))
        #     # i.i_projid = self.__le_uint()

        # inode_mode = (
        #     (0x1, 'S_IXOTH'),
        #     (0x2, 'S_IWOTH'),
        #     (0x4, 'S_IROTH'),
        #     (0x8, 'S_IXGRP'),
        #     (0x10, 'S_IWGRP'),
        #     (0x20, 'S_IRGRP'),
        #     (0x40, 'S_IXUSR'),
        #     (0x80, 'S_IWUSR'),
        #     (0x100, 'S_IRUSR'),
        #     (0x200, 'S_ISVTX'),
        #     (0x400, 'S_ISGID'),
        #     (0x800, 'S_ISUID'),
        #     (0x1000, 'S_IFIFO'),
        #     (0x2000, 'S_IFCHR'),
        #     (0x4000, 'S_IFDIR'),
        #     (0x6000, 'S_IFBLK'),
        #     (0x8000, 'S_IFREG'),
        #     (0xA000, 'S_IFLNK'),
        #     (0xC000, 'S_IFSOCK')
        # )

        # r = map_bitmap(i.i_mode, inode_mode)

        # if 0x1 in r:
        #     i.S_IXOTH = True
        # if 0x2 in r:
        #     i.S_IWOTH = True
        # if 0x4 in r:
        #     i.S_IROTH = True
        # if 0x8 in r:
        #     i.S_IXGRP = True
        # if 0x10 in r:
        #     i.S_IWGRP = True
        # if 0x20 in r:
        #     i.S_IRGRP = True
        # if 0x40 in r:
        #     i.S_IXUSR = True
        # if 0x80 in r:
        #     i.S_IWUSR = True
        # if 0x100 in r:
        #     i.S_IRUSR = True
        # if 0x200 in r:
        #     i.S_ISVTX = True
        # if 0x400 in r:
        #     i.S_ISGID = True
        # if 0x800 in r:
        #     i.S_ISUID = True

        i.file_type = self.__map_bitmap_exclusive(i.i_mode, (
            (0x1000, "fifo"),
            (0x2000, "character_device"),
            (0x4000, "directory"),
            (0x6000, "block_device"),
            (0x8000, "file"),
            (0xA000, "symlink"),
            (0xC000, "socket")
            ))

        value_to_attr_name_mapping = {
            'fifo': 'S_IFIFO',
            'character_device': 'S_IFCHR',
            'directory': 'S_IFDIR',
            'block_device': 'S_IFBLK',
            'file': 'S_IFREG',
            'symlink': 'S_IFLNK',
            'socket': 'S_IFSOCK',
        }

        attr_name = value_to_attr_name_mapping.get(i.file_type, None)
        if attr_name is not None:
            setattr(i, attr_name, True)

        i.byte_start = start_offset

        self.inodes[inode_number] = i
        return i
    # pylint: enable=line-too-long

    # TODO: Is this needed anymore?
    def run(self) -> None:
        """Read inode table and create inodes.

        Reads entire inode table and creates a :class:`Ext3Inode` object for each
        inode belonging to the table. Inode objects are stored in ``self.inodes``
        which is a ``list``.

        """

        return
