"""
    Class for ext3 superblock
"""

import binascii
import io
import pprint
import struct

from ExtFs.util import format_like_uuid, map_bitmap

class Ext3Superblock: # pylint: disable=too-many-instance-attributes
    """Ext3Superblock.

    Class for processing an Ext Superblock.

    Example Usage:

    >>> from ExtFs.superblock import Ext3Superblock
    >>> f = open("/dev/sda1", "rb")
    >>> sb = Ext3Superblock(f)
    >>> sb.run()

    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    # pylint: disable=line-too-long,too-many-statements
    def __init__(self, f: io.BytesIO, master_offset: int = 0, magic_ignore: bool = False):
        """Read ext filesystem superblock.

        Args:

            f (io.BytesIO): File-like object of filesystem.
            master_offset (int, optional): Offset in bytes from start of file to begin. Defaults to 0.
            magic_ignore (bool, optional): Ignore invalid/bad ext magic. Defaults to False.
        """
        self.f = f
        self.master_offset = master_offset

        self.starting_offset = None
        self.magic_ignore = magic_ignore

        # Calculated later from s_log_block_size
        # 2 ** (10 + s_log_block_size)
        self.block_size = None

        # Calculated later by dividing the total number of inodes
        # by the number of inodes per group
        # Trying to deprecate 'blockgroup_count' in favor of 'block_group_count'.
        self.block_group_count = None

        # Convert uuid binary data later to a string
        self.uuid_str = None
        self.journal_uuid_str = None

        # state
        self.STATE_CLEANLY_UNMOUNTED = False
        self.STATE_ERRORS_DETECTED = False
        self.STATE_ORPHANS = False

        # feature_compat
        self.COMPAT_DIR_PREALLOC = False
        self.COMPAT_IMAGIC_INODES = False
        self.COMPAT_HAS_JOURNAL = False
        self.COMPAT_EXT_ATTR = False
        self.COMPAT_RESIZE_INODE = False
        self.COMPAT_DIR_INDEX = False
        self.COMPAT_LAZY_BG = False
        self.COMPAT_EXCLUDE_INODE = False
        self.COMPAT_EXCLUDE_BITMAP = False
        self.COMPAT_SPARSE_SUPER2 = False

        # feature_incompat
        self.INCOMPAT_COMPRESSION = False
        self.INCOMPAT_FILETYPE = False
        self.INCOMPAT_RECOVER = False
        self.INCOMPAT_JOURNAL_DEV = False
        self.INCOMPAT_META_BG = False
        self.INCOMPAT_EXTENTS = False
        self.INCOMPAT_64BITS = False
        self.INCOMPAT_MMP = False
        self.INCOMPAT_FLEX_BG = False
        self.INCOMPAT_EA_INODE = False
        self.INCOMPAT_DIRDATA = False
        self.INCOMPAT_CSUM_SEED = False
        self.INCOMPAT_LARGEDIR = False
        self.INCOMPAT_INLINE_DATA = False
        self.INCOMPAT_ENCRYPT = False

        # feature_ro_compat
        self.RO_COMPAT_SPARSE_SUPER = False
        self.RO_COMPAT_LARGE_FILE = False
        self.RO_COMPAT_BTREE_DIR = False
        self.RO_COMPAT_HUGE_FILE = False
        self.RO_COMPAT_GDT_CSUM = False
        self.RO_COMPAT_DIR_NLINK = False
        self.RO_COMPAT_EXTRA_ISIZE = False
        self.RO_COMPAT_HAS_SNAPSHOT = False
        self.RO_COMPAT_QUOTA = False
        self.RO_COMPAT_BIGALLOC = False
        self.RO_COMPAT_METADATA_CSUM = False
        self.RO_COMPAT_REPLICA = False
        self.RO_COMPAT_READONLY = False
        self.RO_COMPAT_PROJECT = False

        # def_hash_version
        self.HASH_LEGACY = False
        self.HASH_HALF_MD4 = False
        self.HASH_TEA = False
        self.HASH_LEGACY_UNSIGNED = False
        self.HASH_HALF_MD4_UNSIGNED = False
        self.HASH_TEA_UNSIGNED = False

        # default_mount_opts
        self.EXT4_DEFM_DEBUG = False
        self.EXT4_DEFM_BSDGROUPS = False
        self.EXT4_DEFM_XATTR_USER = False
        self.EXT4_DEFM_ACL = False
        self.EXT4_DEFM_UID16 = False
        self.EXT4_DEFM_JMODE_DATA = False
        self.EXT4_DEFM_JMODE_ORDERED = False
        self.EXT4_DEFM_JMODE_WBACK = False
        self.EXT4_DEFM_NOBARRIER = False
        self.EXT4_DEFM_BLOCK_VALIDITY = False
        self.EXT4_DEFM_DISCARD = False
        self.EXT4_DEFM_NODELALLOC = False

        # Superblock structure per information found at:
        # https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout
        #
        # The superblock records various information about the enclosing
        # filesystem, such as block counts, inode counts, supported features,
        # maintenance information, and more.
        #
        # If the sparse_super feature flag is set, redundant copies of the
        # superblock and group descriptors are kept only in the groups whose
        # group number is either 0 or a power of 3, 5, or 7. If the flag is not
        # set, redundant copies are kept in all groups.
        #
        # The superblock checksum is calculated against the superblock structure,
        # which includes the FS UUID.
        #
        # The ext4 superblock is laid out as follows in struct ext4_super_block:
        self.s_inodes_count = None
        self.s_blocks_count_lo = None
        self.s_r_blocks_count_lo = None
        self.s_free_blocks_count_lo = None
        self.s_free_inodes_count = None
        self.s_first_data_block = None
        self.s_log_block_size = None
        self.s_log_cluster_size = None
        self.s_blocks_per_group = None
        self.s_clusters_per_group = None
        self.s_inodes_per_group = None
        self.s_mtime = None
        self.s_wtime = None
        self.s_mnt_count = None
        self.s_max_mnt_count = None
        self.s_magic = None
        self.s_state = None
        self.s_errors = None
        self.s_minor_rev_level = None
        self.s_lastcheck = None
        self.s_checkinterval = None
        self.s_creator_os = None
        self.s_rev_level = None
        self.s_def_resuid = None
        self.s_def_resgid = None

        # This info separates these two sections

        # These fields are for EXT4_DYNAMIC_REV superblocks only.
        #
        # Note: the difference between the compatible feature set
        # and the incompatible feature set is that if there is a
        # bit set in the incompatible feature set that the kernel
        # doesn't know about, it should refuse to mount the filesystem.
        #
        # e2fsck's requirements are more strict; if it doesn't know
        # about a feature in either the compatible or incompatible
        # feature set, it must abort and not try to meddle with things
        # it doesn't understand...
        self.s_first_ino = None
        self.s_inode_size = None
        self.s_block_group_nr = None
        self.s_feature_compat = None
        self.s_feature_incompat = None
        self.s_feature_ro_compat = None
        self.s_uuid = None
        self.s_volume_name = None
        self.s_last_mounted = None
        self.s_algorithm_usage_bitmap = None
        self.s_prealloc_blocks = None
        self.s_prealloc_dir_blocks = None
        self.s_reserved_gdt_blocks = None

        # Journaling support valid if EXT4_FEATURE_COMPAT_HAS_JOURNAL set
        self.s_journal_uuid = None
        self.s_journal_inum = None
        self.s_journal_dev = None
        self.s_last_orphan = None
        self.s_hash_seed = None
        self.s_def_hash_version = None
        self.s_jnl_backup_type = None
        self.s_desc_size = None
        self.s_default_mount_opts = None
        self.s_first_meta_bg = None

        # My first version of super block parsing stopped reading after
        # s_first_meta_bg
        self.s_mkfs_time = None
        self.s_jnl_blocks = None

        # 64bit support valid if EXT4_FEATURE_COMPAT_64BIT
        self.s_blocks_count_hi = None
        self.s_r_blocks_count_hi = None
        self.s_free_blocks_count_hi = None
        self.s_min_extra_isize = None
        self.s_want_extra_isize = None
        self.s_flags = None
        self.s_raid_stride = None
        self.s_mmp_interval = None
        self.s_mmp_block = None
        self.s_raid_stripe_width = None
        self.s_log_groups_per_flex = None
        self.s_checksum_type = None
        self.s_reserved_pad = None
        self.s_kbytes_written = None
        self.s_snapshot_inum = None
        self.s_snapshot_id = None
        self.s_snapshot_r_blocks_count = None
        self.s_snapshot_list = None
        self.s_error_count = None
        self.s_first_error_time = None
        self.s_first_error_ino = None
        self.s_first_error_block = None
        self.s_first_error_func = None
        self.s_first_error_line = None
        self.s_last_error_time = None
        self.s_last_error_ino = None
        self.s_last_error_line = None
        self.s_last_error_block = None
        self.s_last_error_func = None
        self.s_mount_opts = None
        self.s_usr_quota_inum = None
        self.s_grp_quota_inum = None
        self.s_overhead_blocks = None
        self.s_backup_bgs = None
        self.s_encrypt_algos = None
        self.s_encrypt_pw_salt = None
        self.s_lpf_ino = None
        self.s_prj_quota_inum = None
        self.s_checksum_seed = None
        self.s_reserved = None
        self.s_checksum = None
    # pylint: enable=line-too-long,too-many-statements

    def run(self) -> None:
        """Start superblock read/processing."""

        # Save starting offset just in case
        self.starting_offset = self.f.tell()

        # Superblock starts 1024 (0x400) bytes from beginning of partition/fs
        seek_offset = self.master_offset + 1024

        self.f.seek(seek_offset)

        # Pre-check for ext magic unless magic_ignore is True
        if self.magic_ignore is False:
            self.__check_magic()

        # We either found ext magic or ignored it so read and process
        self.s_inodes_count = self.__le32()
        self.s_blocks_count_lo = self.__le32()
        self.s_r_blocks_count_lo = self.__le32()
        self.s_free_blocks_count_lo = self.__le32()
        self.s_free_inodes_count = self.__le32()
        self.s_first_data_block = self.__le32()
        self.s_log_block_size = self.__le32()
        self.s_log_cluster_size = self.__le32()
        self.s_blocks_per_group = self.__le32()
        self.s_clusters_per_group = self.__le32()
        self.s_inodes_per_group = self.__le32()
        self.s_mtime = self.__le32()
        self.s_wtime = self.__le32()
        self.s_mnt_count = self.__le16()
        self.s_max_mnt_count = self.__le16()
        self.s_magic = hex(self.__le16())
        self.s_state = self.__le16()
        self.s_errors = self.__le16()
        self.s_minor_rev_level = self.__le16()
        self.s_lastcheck = self.__le32()
        self.s_checkinterval = self.__le32()
        self.s_creator_os = self.__le32()
        self.s_rev_level = self.__le32()
        self.s_def_resuid = self.__le16()
        self.s_def_resgid = self.__le16()

        # This info separates these two sections

        # These fields are for EXT4_DYNAMIC_REV superblocks only.
        #
        # Note: the difference between the compatible feature set
        # and the incompatible feature set is that if there is a
        # bit set in the incompatible feature set that the kernel
        # doesn't know about, it should refuse to mount the filesystem.
        #
        # e2fsck's requirements are more strict; if it doesn't know
        # about a feature in either the compatible or incompatible
        # feature set, it must abort and not try to meddle with things
        # it doesn't understand...
        self.s_first_ino = self.__le32()
        self.s_inode_size = self.__le16()
        if self.s_inode_size == 0:
            self.s_inode_size = 128
        self.s_block_group_nr = self.__le16()
        self.s_feature_compat = self.__le32()
        self.s_feature_incompat = self.__le32()
        self.s_feature_ro_compat = self.__le32()
        self.s_uuid = self.f.read(16)
        self.s_volume_name = self.f.read(16)
        self.s_last_mounted = self.f.read(64)
        self.s_algorithm_usage_bitmap = self.__le32()
        self.s_prealloc_blocks = self.__u8()
        self.s_prealloc_dir_blocks = self.__u8()
        self.s_reserved_gdt_blocks = self.__le16()

        # Journaling support valid if EXT4_FEATURE_COMPAT_HAS_JOURNAL set
        self.s_journal_uuid = self.f.read(16)
        self.s_journal_inum = self.__le32()
        self.s_journal_dev = self.__le32()
        self.s_last_orphan = self.__le32()
        self.s_hash_seed = str(self.__le32())
        self.s_hash_seed += str(self.__le32())
        self.s_hash_seed += str(self.__le32())
        self.s_hash_seed += str(self.__le32())
        self.s_def_hash_version = self.__u8()
        self.s_jnl_backup_type = self.__u8()
        self.s_desc_size = self.__le16()
        self.s_default_mount_opts = self.__le32()
        self.s_first_meta_bg = self.__le32()

        # My first version of super block parsing stopped reading after
        # s_first_meta_bg
        self.s_mkfs_time = self.__le32()
        self.s_jnl_blocks = []
        for _ in range(0, 16):
            self.s_jnl_blocks.append(self.__le32())

        # 64bit support valid if EXT4_FEATURE_COMPAT_64BIT
        self.s_blocks_count_hi = self.__le32()
        self.s_r_blocks_count_hi = self.__le32()
        self.s_free_blocks_count_hi = self.__le32()
        self.s_min_extra_isize = self.__le16()
        self.s_want_extra_isize = self.__le16()
        self.s_flags = self.__le32()
        self.s_raid_stride = self.__le16()
        self.s_mmp_interval = self.__le16()
        self.s_mmp_block = self.__le64()
        self.s_raid_stripe_width = self.__le32()
        self.s_log_groups_per_flex = self.__u8()
        self.s_checksum_type = self.__u8()
        self.s_reserved_pad = self.__le16()
        self.s_kbytes_written = self.__le64()
        self.s_snapshot_inum = self.__le32()
        self.s_snapshot_id = self.__le32()
        self.s_snapshot_r_blocks_count = self.__le64()
        self.s_snapshot_list = self.__le32()
        self.s_error_count = self.__le32()
        self.s_first_error_time = self.__le32()
        self.s_first_error_ino = self.__le32()
        self.s_first_error_block = self.__le64()
        self.s_first_error_func = self.f.read(32)
        self.s_first_error_line = self.__le32()
        self.s_last_error_time = self.__le32()
        self.s_last_error_ino = self.__le32()
        self.s_last_error_line = self.__le32()
        self.s_last_error_block = self.__le64()
        self.s_last_error_func = self.f.read(32)
        self.s_mount_opts = self.f.read(64)
        self.s_usr_quota_inum = self.__le32()
        self.s_grp_quota_inum = self.__le32()
        self.s_overhead_blocks = self.__le32()
        self.s_backup_bgs = []
        self.s_backup_bgs.append(self.__le32())
        self.s_backup_bgs.append(self.__le32())
        self.s_encrypt_algos = []
        self.s_encrypt_algos.append(self.__u8())
        self.s_encrypt_algos.append(self.__u8())
        self.s_encrypt_algos.append(self.__u8())
        self.s_encrypt_algos.append(self.__u8())
        self.s_encrypt_pw_salt = self.f.read(16)
        self.s_lpf_ino = self.__le32()
        self.s_prj_quota_inum = self.__le32()
        self.s_checksum_seed = self.__le32()
        self.s_reserved = self.__le32()
        self.s_checksum = self.__le32()

        # Calculated later s_log_block_size
        # 2 ** (10 + s_log_block_size)
        self.block_size = 2 ** (10 + self.s_log_block_size)

        # Read all the bitmaps
        self._read_feature_compat()
        self._read_feature_incompat()
        self._read_feature_ro_compat()
        self._read_state()

        self._calculate_number_of_blockgroups()
        self._uuid_to_str()

    def __check_magic(self) -> None:
        """Check superblock magic."""

        # Superblock starts 1024 (0x400) bytes from beginning of partition/fs
        seek_offset = self.master_offset + 1024

        # Check to see if this is a sneaky snake with a partition type that does not
        # match the filesystem type.
        # TODO: Figure out a way to do this that doesn't require python-magic (libmagic1)
        # TODO: Raise a custom exception
        # self.f.seek(self.master_offset)
        # m = magic.from_buffer(self.f.read(4096))
        # if m.startswith('SGI XFS filesystem'):
        #     raise ValueError("Partition is XFS!")
        # if 'LVM' in m:
        #     raise ValueError("Partition is LVM!")

        # Can still do a Ext magic check regardless of platform
        self.f.seek(seek_offset)
        # ext magic offset is 56 (0x38) bytes from start of header
        magic_offset = 56
        # Seek forward 56 bytes
        self.f.seek(magic_offset, 1)
        magic_test = hex(self.__le16())

        # Fail, raise RuntimeError
        # TODO: Raise a custom exception
        if magic_test != "0xef53":
            raise RuntimeError(f"Expected to find extfs magic '0xef53' "
                               "but found '{magic_test}' with magic '{m}'")

        # We skipped forward 56 bytes and read 2 bytes so
        # we need to seek backwards 58 bytes to the beginning
        # of the ext header
        self.f.seek(-1 * (magic_offset + 2), 1)

    def _calculate_number_of_blockgroups(self) -> None:
        """Calculate number of blockgroups.

        The superblock structure does not have a variable for the
        number of block groups so we must calculate it ourselves.

        The number of blockgroups is calculated by dividing the
        inode count by the number of inodes per group.
        ``self.s_inodes_count / self.s_inodes_per_group``
        The number of blockgroups is then stored in ``block_group_count``.

        Currently a non-mangled function. There may be a usecase that
        requires calling by something outside this class but I have
        not encountered it yet.

        .. warning::
           :func:`Ext3InodeTable.run` must be called first to read the
           superblock contents!

        """

        self.block_group_count = self.s_inodes_count // self.s_inodes_per_group

    def _uuid_to_str(self) -> None:
        """Formats uuid's to strings"""

        self.uuid_str = format_like_uuid(binascii.hexlify(self.s_uuid))
        self.journal_uuid_str = format_like_uuid(binascii.hexlify(self.s_journal_uuid))

    def _read_feature_compat(self) -> None:
        """Read the s_feature_compat bitmap"""

        map_feature_compat = (
            (0x1, 'dir_prealloc'),
            (0x2, 'imagic_inodes'),
            (0x4, 'has_journal'),
            (0x8, 'ext_attr'),
            (0x10, 'resize_ino'),
            (0x20, 'dir_index'),
            (0x40, 'lazy_bg'),
            (0x80, 'exclude_inode'),
            (0x100, 'exclude_bitmap'),
            (0x200, 'sparse_super_block_v2')
        )

        r = map_bitmap(self.s_feature_compat, map_feature_compat)

        value_to_attr_name_mapping = {
            0x1: 'COMPAT_DIR_PREALLOC',
            0x2: 'COMPAT_IMAGIC_INODES',
            0x4: 'COMPAT_HAS_JOURNAL',
            0x8: 'COMPAT_EXT_ATTR',
            0x10: 'COMPAT_RESIZE_INODE',
            0x20: 'COMPAT_DIR_INDEX',
            0x40: 'COMPAT_LAZY_BG',
            0x80: 'COMPAT_EXCLUDE_INODE',
            0x100: 'COMPAT_EXCLUDE_BITMAP',
            0x200: 'COMPAT_SPARSE_SUPER2',
        }

        for k, v in value_to_attr_name_mapping.items():
            if k in r:
                setattr(self, v, True)


    def _read_feature_incompat(self) -> None:
        """Read the s_feature_incompat bitmap"""

        map_feature_incompat = (
            (0x1, 'compression'),
            (0x2, 'filetype'),
            (0x4, 'needs_recovery'),
            (0x8, 'separate_journal_device'),
            (0x10, 'meta_bg'),
            (0x40, 'use_extents'),
            (0x80, '64bit_filesystem'),
            (0x100, 'multiple_mount_protection'),
            (0x200, 'flexible_block_groups'),
            (0x400, 'extended_attributes'),
            (0x1000, 'data_directory'),
            (0x2000, 'metadata_checksum_in_sb'),
            (0x4000, 'large_directory'),
            (0x8000, 'data_inode'),
            (0x10000, 'encrypted')
        )

        r = map_bitmap(self.s_feature_incompat, map_feature_incompat)

        value_to_attr_name_mapping = {
            0x1: 'INCOMPAT_COMPRESSION',
            0x2: 'INCOMPAT_FILETYPE',
            0x4: 'INCOMPAT_RECOVER',
            0x8: 'INCOMPAT_JOURNAL_DEV',
            0x10: 'INCOMPAT_META_BG',
            0x40: 'INCOMPAT_EXTENTS',
            0x80: 'INCOMPAT_64BITS',
            0x100: 'INCOMPAT_MMP',
            0x200: 'INCOMPAT_FLEX_BG',
            0x400: 'INCOMPAT_EA_INODE',
            0x1000: 'INCOMPAT_DIRDATA',
            0x2000: 'INCOMPAT_CSUM_SEED',
            0x4000: 'INCOMPAT_LARGEDIR',
            0x8000: 'INCOMPAT_INLINE_DATA',
            0x10000: 'INCOMPAT_ENCRYPT',
        }

        for k, v in value_to_attr_name_mapping.items():
            if k in r:
                setattr(self, v, True)

    def _read_feature_ro_compat(self) -> None:
        """Read the s_feature_ro_compat bitmap"""

        map_feature_ro_compat = (
            (0x1, 'sparse_sb'),
            (0x2, 'largefile'),
            (0x4, 'compat_btree'),
            (0x8, 'hugefile'),
            (0x10, 'gdt_checksum'),
            (0x20, 'no_dir_nlink'),
            (0x40, 'large_inodes'),
            (0x80, 'has_snapshot'),
            (0x100, 'quota'),
            (0x200, 'bigalloc'),
            (0x400, 'metadata_checksum'),
            (0x800, 'replicas'),
            (0x1000, 'readonly'),
            (0x2000, 'project_quotas')
        )

        r = map_bitmap(self.s_feature_ro_compat, map_feature_ro_compat)

        value_to_attr_name_mapping = {
            0x1: 'RO_COMPAT_SPARSE_SUPER',
            0x2: 'RO_COMPAT_LARGE_FILE',
            0x4: 'RO_COMPAT_BTREE_DIR',
            0x8: 'RO_COMPAT_HUGE_FILE',
            0x10: 'RO_COMPAT_GDT_CSUM',
            0x20: 'RO_COMPAT_DIR_NLINK',
            0x40: 'RO_COMPAT_EXTRA_ISIZE',
            0x80: 'RO_COMPAT_HAS_SNAPSHOT',
            0x100: 'RO_COMPAT_QUOTA',
            0x200: 'RO_COMPAT_BIGALLOC',
            0x400: 'RO_COMPAT_METADATA_CSUM',
            0x800: 'RO_COMPAT_REPLICA',
            0x1000: 'RO_COMPAT_READONLY',
            0x2000: 'RO_COMPAT_PROJECT',
        }

        for k, v in value_to_attr_name_mapping.items():
            if k in r:
                setattr(self, v, True)

    def _read_state(self) -> None:
        """Read the s_state bitmap"""

        if self.s_state == 1:
            self.STATE_CLEANLY_UNMOUNTED = True

    def clean_for_pickle(self) -> None:
        """Clean for pickle.

        Cleans out cruft so class can be pickled.
        """

        self.f = None

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
