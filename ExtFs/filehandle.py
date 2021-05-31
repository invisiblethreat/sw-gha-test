"""File handle"""

import copy

# WARNING: Old (possibly deprecated/unused) magic be here!

class BucketHandle:
    """BucketHandle.
    """

    def __init__(self, f, bucket_number, byte_start, parts):
        if not isinstance(bucket_number, int):
            try:
                bucket_number = int(bucket_number)
            except TypeError:
                raise TypeError("Tried convering bucket_number: %s to int but failed!" % bucket_number)
        if not isinstance(byte_start, int):
            try:
                byte_start = int(byte_start)
            except TypeError:
                raise TypeError("Tried convering byte_start: %s to int but failed!" % byte_start)
        self.__f = None
        self.f = f
        self.bucket_number = bucket_number
        self.parts_byte_start = parts['byte_start']
        self.parts_byte_len = parts['byte_len']
        self.parts_byte_len = parts['byte_start'] + parts['byte_len']
        self.parts_sparse = parts['sparse']
        self.byte_start = byte_start
        self.byte_end = byte_start + parts['byte_len']
        self.byte_len = parts['byte_len']
        self.sparse = parts['sparse']

    @property
    def f(self):
        """Gets/sets file handle.

        For some reason a lot of file handles are bound functions and
        so the setter trys to run the value being set as a function before assigning.
        """
        return self.__f

    # pylint: disable=line-too-long
    @f.setter
    def f(self, value):
        # TODO: For some reason f is now a bound function of something like PartitionEntryMBR handle method
        # Example: ExtFs: filehandle.py: BucketHandle().__init__(): f is: <bound method PartitionEntry.handle of <PartitionEntryMBR: ...
        try:
            # Try f as a function first
            self.__f = value()
        except TypeError:
            # Ok f is not a function, just assign it
            self.__f = value
    # pylint: enable=line-too-long

    def is_me(self, value):
        """Returns whether or not bucket is responsible for an offset.

        Args:
            value (int): Offset in bytes.

        Returns:
            bool: Whether or not bucket is responsible for offset.
        """

        if value >= self.byte_start and value < self.byte_end:
            return True
        return False

    def boolean_read_exceeds(self, start, count):
        """Returns whether or not a read of count bytes will exceed bucket's boundary.

        Args:
            start (int): Starting read offset in bytes.
            count (int): Number of bytes to read.

        Returns:
            bool: Whether or not a read will exceed bucket's boundary
        """

        if start + count >= self.byte_end:
            return True
        return False

    def how_many_read_bytes(self, start, count):
        """Returns how many bytes will be read from bucket given starting offset and count.

        Args:
            start (int): Starting read offset in bytes.
            count (int): Number of bytes to read.

        Returns:
            int: Number of bytes that would be read.
        """

        # Given an a starting offset and a count find out how many
        # max bytes we will read from this bucket
        exceeds = self.boolean_read_exceeds(start, count)
        if exceeds:
            return self.byte_end - start
        return count

    def read_exceeds_boundary(self, start, count):
        """Returns whether or not a read of count bytes at start offset will exceed
        bucket's boundary. If it exceeds a tuple of bool, number of bytes exceeded
        will be returned. If not exceeded a tuple of bool, remaining bytes will be
        returned.

        Args:
            start (int): Starting read offset in bytes.
            count (int): Number of bytes that would be read.

        Returns:
            tuple: Tuple of bool, bytes.
        """

        new_offset = start + count
        if new_offset >= self.byte_end:
            return True, new_offset - self.byte_end

        return False, self.byte_end - new_offset

    def read(self, start, count):
        """Reads count bytes at starting offset.

        Args:
            start (int): Starting read offset in bytes.
            count (int): Number of bytes to read.

        Returns:
            bytes: Byte data.
        """

        if count == 0:
            print("Bucket returning empty")
            return b""

        exceeds = self.boolean_read_exceeds(start, count)
        if self.sparse:
            if exceeds:
                amount = self.how_many_read_bytes(start, count)
                print("Bucket returning sparse amount")
                return b"\x00" * amount
            print("Bucket returning sparse count")
            return b"\x00" * count
        self.f.seek(self.handle_adjusted_offset(start))
        if exceeds:
            # Goes beyond boundary
            amount = self.how_many_read_bytes(start, count)
            # print("reading %s amount bytes" % (amount))
            return self.f.read(amount)
        # print("reading %s count bytes" % (count))
        return self.f.read(count)

    def my_relative_offset(self, offset):
        """Returns relative offset of offset within bucket's boundary.

        Args:
            offset (int): Offset in bytes.

        Raises:
            RuntimeError: If offset is outside of bucket boundary.

        Returns:
            int: Relative offset of offset within bucket.
        """

        # This will calculate how many bytes we are into our bucket
        # e.g. If bucket start_byte is 0 and end_byte is 100
        # offset 50 will tell us we are 50 bytes into our bucket.
        # e.g. If bucket start_byte is 100 and end_byte is 200
        # offset 150 will tell us we are 50 bytes into our bucket.
        if offset > self.byte_end:
            # Goes beyond boundary
            raise RuntimeError("Offset: %s exceeds boundary: start: %s end: %s" %
                               (offset, self.byte_start, self.byte_end))
        return offset - self.byte_start

    def adjusted_offset(self, offset):
        """Returns adjusted offset of offset accounting for the file's
        position on the underlying filesystem.

        Args:
            offset (int): Offset in bytes.

        Returns:
            int: Adjusted offset in bytes.
        """

        # This will give us the adjusted offset neccesary to line up the
        # underlying file handle reads.
        # e.g. If bucket start_byte is 0 and end_byte is 100
        # offset 50 will tell us we are 50 bytes into our bucket.
        # If part_start_byte is 1000 and part_end_byte is 2000
        # our adjusted offset will be 1050.
        relative_offset = self.my_relative_offset(offset)
        adjusted = self.parts_byte_start + relative_offset
        return adjusted

    def handle_adjusted_offset(self, offset):
        """Returns adjusted offset of offset accounting for both the
        file's position on the underlying filesystem AND the filesystem's
        position relative to all of its underlying abstraction layers.

        Args:
            offset (int): Offset in bytes.

        Returns:
            int: Adjusted offset in bytes.
        """

        # Factors in underlying file handle's reference_offset
        # in addition to our own
        return self.adjusted_offset(offset)

class ExtFsFileHandle:
    """ExtFsFileHandle
    """
    def __init__(self, f, name, size, parts, debug=False):

        self.f = f
        self.filename = name
        self.size = size
        self.debug = debug

        self.our_offset = 0
        self._id = None

        self.parts = copy.copy(parts)
        self.number_of_buckets = len(self.parts)
        self.bucket_number = 0
        self.buckets = []

        our_byte_start = 0
        seq_no = 0
        for seq_no in sorted(self.parts):
            our_byte_len = self.parts[seq_no]['byte_len']
            our_byte_end = our_byte_start + our_byte_len
            self.buckets.append(BucketHandle(self.f, seq_no,
                                             our_byte_start, self.parts[seq_no]))
            our_byte_start = our_byte_end
        # print("has %s parts" % (seq_no))

    # pylint: disable=broad-except
    def read(self, count=None):
        """Read count bytes.
        If count is None then the remaining amount of the file will be read.

        Args:
            count (int, optional): Defaults to None. Number of bytes to read.
                Will read entire contents if None or -1.

        Raises:
            ValueError: If count is less than -1.

        Returns:
            bytes: Byte data.
        """

        if count is None or count == -1:
            count = self.size - self.our_offset

        if count < 0:
            raise ValueError("count (%s) can not be less than -1!" % count)

        # If reading count bytes will put our offset over our size then the
        # amount of bytes we return should be size - our offset
        if self.our_offset + count > self.size:
            count = self.size - self.our_offset

        if count == 0 or self.size == 0:
            return b""

        buf = b""
        violation = self.get_current_bucket().boolean_read_exceeds(self.our_offset, count)
        if violation:
            # We exceeded this bucket's size
            while True:
                # Find out how many bytes we will read from this bucket
                num_bytes = self.get_current_bucket().how_many_read_bytes(self.our_offset, count)
                if num_bytes == 0:
                    if self.on_last_bucket():
                        if self.our_offset != self.size:
                            # Possibly sparse at the end here
                            return b"\x00" * (self.size - self.our_offset)
                try:
                    buf += self.get_current_bucket().read(self.our_offset, count)
                except Exception as e:
                    print("FH Exception! %s" % (e))

                # Adjust our offset to increase by the number of bytes we just read
                self.our_offset += num_bytes
                # Increase our bucket number. Probably more performant than self.set_bucket_number
                if not self.get_current_bucket().is_me(self.our_offset):
                    self.increment_bucket_number()
                # Decrease count by the number of bytes we just read
                count -= num_bytes
                # print("Read %s bytes, %s bytes remaining" % (num_bytes, count))
                if count == 0:
                    break
                elif count < 0:
                    raise RuntimeError("count < 0! value: %s" % count)

        else:
            # We are still inside this bucket
            buf += self.get_current_bucket().read(self.our_offset, count)
            self.our_offset += count

        return buf
    # pylint: enable=broad-except

    def tell(self):
        """Returns our current offset.

        Returns:
            int: Current offset.
        """

        return self.our_offset

    # pylint: disable=broad-except
    def seek(self, offset, whence=0):
        """Seeks to a position in file with given offset and whence.

        Args:
            offset (int): Offset in bytes.
            whence (int, optional): Defaults to 0. Where to seek relative to.

        Returns:
            int: New seek'ed position.
        """

        if self.size == 0:
            return 0

        if whence == 0:
            new_offset = self.our_offset + offset
            if new_offset > self.size:
                self.our_offset = self.size
                return self.our_offset
            self.our_offset = offset
            return self.our_offset

        new_offset = self.our_offset + offset
        if whence == 1:
            # Check to make sure we don't seek past boundry
            if new_offset > self.size:
                # If the calculated new offset is bigger than our length
                # then seek to the end.
                self.our_offset = self.size
            elif new_offset < 0:
                # If the calculated new offset is less than 0 then seek to 0
                self.our_offset = 0
            return self.our_offset
        elif whence == 2:
            if offset >= 0:
                # Can't seek a positive number beyond the end of the file
                self.our_offset = self.size
                return self.our_offset
            else:
                # Calculate offset from end of file. Offset will be a negative
                # number so we are adding it.
                new_offset = self.size + offset
                if new_offset > self.size:
                    # One last sanity check
                    raise ValueError("new_offset is greater than end_offset!")
                    # self.our_offset = self.size
                self.our_offset = self.size + offset
                if self.our_offset > self.size:
                    raise RuntimeError("our_offset > size!")
                return self.our_offset
            # return self.our_offset
    # pylint: enable=broad-except

    def get_current_bucket(self):
        """Returns the current bucket for our current offset.

        Returns:
            BucketHandle: BucketHandle object.
        """

        return self.buckets[self.bucket_number]

    def on_last_bucket(self):
        """Is current bucket the last bucket?

        Returns:
            bool: Whether or not current bucket is the last bucket.
        """

        if self.bucket_number == self.number_of_buckets - 1:
            return True
        return False

    def increment_bucket_number(self, number=1):
        """Increment bucket number by number.
            number (int, optional): Defaults to 1. How much to increment.
        """

        if self.bucket_number + number >= self.number_of_buckets:
            return
        self.bucket_number += number

    def set_bucket(self, offset):
        """Set's the current bucket to be the bucket responsible for
        the given offset.

        Args:
            offset (int): Offset in bytes.
        """

        bucket = self.find_bucket(offset)
        self.bucket_number = bucket.bucket_number

    def find_bucket(self, offset):
        """Finds a bucket for a given offset.

        Args:
            offset (int): Offset in bytes.

        Raises:
            RuntimeError: If a bucket for offset could not be found.

        Returns:
            BucketHandle: BucketHandle object.
        """

        for bucket in self.buckets:
            if bucket.is_me(offset):
                return bucket
        raise RuntimeError("Could not find bucket for offset: %s" % offset)

    def close(self) -> None:
        """Closes the file's underlying handle.
        """

        return self.f.close()

    @property
    def length(self) -> int:
        """Wrapper to size.

        Returns:

            int: Size of file in bytes.
        """

        return self.size

    @property
    def len(self) -> int:
        """Wrapper to size.

        Returns:

            int: Size of file in bytes.
        """

        return self.size
