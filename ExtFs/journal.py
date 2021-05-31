"""Ext3 journal.
"""

# NOTE: No real logic has been implemented here. Mostly
# just the data model of the journal.

import pprint


class Unpacker:
    """Unpacker.

    TODO: Move journal code to struct unpacking.
    """

    def be32(self) -> str:
        """be32"""
        return "be32"

class Ext3Journal:
    """Ext3Journal.

    Class for ext3 journal
    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self, f, journal_inode, sb=None, master_offset=0):
        self.f = f
        self.sb = sb
        self.journal_inode = journal_inode
        self.master_offset = master_offset

        self.unpack = Unpacker(f=f)
        self.blocks = []

    # pylint: disable=line-too-long
    def run(self) -> None:
        """Run"""
        # 0x0	__be32	h_magic	jbd2 magic number, 0xC03B3998.
        # 0x4	__be32	h_blocktype	Description of what this block contains. See the jbd2_blocktype table below.
        # 0x8	__be32	h_sequence	The transaction ID that goes with this block.
        self.f.seek(self.master_offset + self.journal_inode.dblocks[0])
        magic = self.unpack.be32()
        print("magic:", magic)
    # pylint: enable=line-too-long

class Ext3JournalSuperblock:
    """Ext3JournalSuperblock.

    Class for ext3 journal super block.
    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self):
        self.version = None
        self.inode = None
        self.backup = None
        self.features = None
        self.size = None
        self.length = None
        self.sequence = None
        self.start = None


class Ext3JournalBlockDescriptor:
    """Ext3JournalBlockDescriptor.

    Class for ext3 journal descriptor block
    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self):
        self.journal_block_number = None
        self.seq = None
        self.allocated = None
        # Delete this when json import can be unfucked
        self.sec = None
        self.fs_block = None


class Ext3JournalBlockFs:
    """Ext3JournalBlockFS.

    Class for ext3 journal fs block.
    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self):
        self.journal_block_number = None
        self.fs_block = None
        self.allocated = None
        # Delete this when json import can be unfucked
        self.sec = None
        self.seq = None


class Ext3JournalBlockCommit:
    """Ext3JournalBlockCommit.

    Class for ext3 journal commit block.
    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self):
        self.journal_block_number = None
        self.seq = None
        self.sec = None
        self.allocated = None
        # Delete this when json import can be unfucked
        self.fs_block = None


class Ext3JournalBlockRevoke:
    """Ext3JournalBlockRevoke.

    Class for ext3 journal revoke block
    """
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)

    def __init__(self):
        self.block_number = None
        self.seq = None
        self.allocated = None
        # Delete this when json import can be unfucked
        self.sec = None
        self.fs_block = None
