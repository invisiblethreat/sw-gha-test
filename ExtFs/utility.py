"""Ext utilities
"""

# import pprint
import io
import struct
from typing import List

class Ext3Utility:
    """Ext3Utility.

    Ext3 utilities.
    """

    # def __str__(self):
    #     return pprint.pformat(vars(self), indent=4)

    # def __repr__(self):
    #     return pprint.pformat(vars(self), indent=4)

    def __init__(self, f: io.BytesIO, block_size: int = None, offset: int = 0):
        self.f = f
        self.block_size = block_size
        self.master_offset = offset


    def hexdump_block(self, block_num: int) -> str:
        """Hexdump block number 'block_num'.
        """

        byte_offset = self.master_offset + block_num * self.block_size
        self.f.seek(byte_offset)
        block_contents = self.f.read(self.block_size)

        # return hexdump(block_contents)
        return "blah hexdump"

    def decode_si_block(self, block_num: int) -> List[int]:
        """Decode single indirect block numbers.

        Args:

            block_num (int): Block number containing single indirects.

        Returns:

            List[int]: List of decoded block numbers.
        """

        byte_offset = self.master_offset + block_num * self.block_size
        self.f.seek(byte_offset)

        values = list()
        unpack_str = f"<{'I' * (self.block_size // 4)}"
        values = [n for n in struct.unpack(unpack_str, self.f.read(self.block_size)) if n != 0]

        return values

    def decode_di_block(self, block_num: int) -> List[int]:
        """Decode double indirect blocks.

        Args:

            block_num (int): Block number containing double indirects.

        Returns:

            List[int]: List of decoded block numbers.
        """

        byte_offset = self.master_offset + block_num * self.block_size
        self.f.seek(byte_offset)

        values = list()
        unpack_str = f"<{'I' * (self.block_size // 4)}"
        values = [n for n in struct.unpack(unpack_str, self.f.read(self.block_size)) if n != 0]

        return values

    def decode_ti_block(self, block_num: int) -> List[int]:
        """Decode triple indirect blocks.

        Args:

            block_num (int): Block number containing triple indirects.

        Returns:

            List[int]: List of decoded block numbers.
        """

        byte_offset = self.master_offset + block_num * self.block_size
        self.f.seek(byte_offset)

        unpack_str = f"<{'I' * (self.block_size // 4)}"
        values = [n for n in struct.unpack(unpack_str, self.f.read(self.block_size)) if n != 0]

        return values

    def resolve_indirects(self, block_num: int, indirect_type: int) -> List[int]:
        """Resolve an indirect block of any type to a list of direct blocks.

        Args:

            block_num (int): Block number to resolve.
            indirect_type (str): Indirect type. "single", "double", "triple".

        Returns:

            List[int]: List of resolved block number.
        """

        d_blocks = None
        # If there are any triple indirect blocks with the inode then resolve those
        # all the way to direct blocks
        if indirect_type == "triple":
            di_blocks = self.decode_ti_block(block_num)
            # Double Indirect -> Single Indirect
            for di in di_blocks:
                si_blocks = self.decode_di_block(di)
                # Single Indirect -> Direct
                for si in si_blocks:
                    if d_blocks is None:
                        d_blocks = list()
                    d_blocks += self.decode_si_block(si)

        # If there are any double indirect blocks with the inode then resolve those
        # all the way to direct blocks
        if indirect_type == "double":
            si_blocks = self.decode_di_block(block_num)
            # Single Indirect -> Direct
            for si in si_blocks:
                if d_blocks is None:
                    d_blocks = list()
                d_blocks += self.decode_si_block(si)

        if indirect_type == "single":
            if d_blocks is None:
                d_blocks = list()
            d_blocks += self.decode_si_block(block_num)

        # Sort blocks numerically so we can evaluate if they are contigious
        # d_blocks.sort()

        return d_blocks

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
