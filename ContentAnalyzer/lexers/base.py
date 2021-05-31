"""Lexer related stuff."""

import re
from typing import Dict, Iterable, List, Tuple, Union

import attr

FORMAT_STRIPPED = "stripped"
FORMAT_STRING = "string"
FORMAT_QUOTE_REMOVAL = "quote_removal"
FORMAT_QUOTE_REMOVAL_STRIP = "quote_removal_strip"


def _read_file_contents(filename: str, binary: bool = False) -> Union[str, bytes]:
    """Read the contents of a file."""

    if binary:
        f = open(filename, 'rb')
    else:
        f = open(filename, 'r', encoding='utf-8')

    data = f.read()
    f.close()
    return data


@attr.s(kw_only=True, slots=True, frozen=True)
class KeyValuePair:
    """KeyValuePair.

    BEWARE! There is a near duplicate of this class in ContentAnalyzer.base!
    """

    key_token = attr.ib(default=None)
    value_token = attr.ib(default=None)
    raw: Dict = attr.ib(default=None)

    def get_key(self):
        """Get key"""
        return self.key

    def get_value(self):
        """Get value"""
        return self.value

    def get_key_start_pos(self) -> int:
        """Get key start_pos"""
        return self._get_location_property(self.key_token, 'start_pos')

    def get_key_start_line(self) -> int:
        """Get key start_line"""
        return self._get_location_property(self.key_token, 'start_line')

    def get_key_start_column(self) -> int:
        """Get key start_column"""
        return self._get_location_property(self.key_token, 'start_column')

    def get_key_end_pos(self) -> int:
        """Get key end_pos"""
        return self._get_location_property(self.key_token, 'end_pos')

    def get_key_end_line(self) -> int:
        """Get key end_line"""
        return self._get_location_property(self.key_token, 'end_line')

    def get_key_end_column(self) -> int:
        """Get key end_column"""
        return self._get_location_property(self.key_token, 'end_column')

    def get_value_start_pos(self) -> int:
        """Get value start_pos"""
        return self._get_location_property(self.value_token, 'start_pos')

    def get_value_start_line(self) -> int:
        """Get value start_line"""
        return self._get_location_property(self.value_token, 'start_line')

    def get_value_start_column(self) -> int:
        """Get value start_column"""
        return self._get_location_property(self.value_token, 'start_column')

    def get_value_end_pos(self) -> int:
        """Get value end_pos"""
        return self._get_location_property(self.value_token, 'end_pos')

    def get_value_end_line(self) -> int:
        """Get value end_line"""
        return self._get_location_property(self.value_token, 'end_line')

    def get_value_end_column(self) -> int:
        """Get value end_column"""
        return self._get_location_property(self.value_token, 'end_column')

    def _get_document_position(self, where):
        if hasattr(where, 'get_document_position'):
            return where.get_document_position()

    def _get_location_property(self, where, name, default_value=0):
        if hasattr(where, name):
            return getattr(where, name)

        document_position = self._get_document_position(where)
        if document_position is None:
            return default_value

        if hasattr(document_position, name):
            return getattr(document_position, name)
        else:
            return default_value


    def to_dict(self) -> Dict:
        """Serialize class to dict"""

        if isinstance(self.raw, dict):
            return self.raw.copy()

        elif isinstance(self.key_token, dict):
            value = {
                'key': self.key_token['value'],
                'value': self.value_token['value'],
                'start_pos': self.value_token['start_pos'],
                'end_pos': self.value_token['end_pos'],
                'start_line': self.value_token['start_line'],
                'end_line': self.value_token['end_line'],
                'start_column': self.value_token['start_column'],
                'end_column': self.value_token['end_column'],
            }
            return value

        value = {
            'key': self.get_key(),
            'value': self.get_value(),
            'start_pos': self.get_value_start_pos(),
            'end_pos': self.get_value_end_pos(),
            'start_line': self.get_value_start_line(),
            'end_line': self.get_value_end_line(),
            'start_column': self.get_value_start_column(),
            'end_column': self.get_value_end_column(),
        }

        return value


    def get_leak_kwargs(self) -> Dict:
        """Get a dict suitable to instantiate a Leak as kwargs.

        Use 'to_dict()' instead.

        TODO: Deprecate this!
        """
        return self.to_dict()


    def get_leak_position_kwargs(self) -> Dict:
        """Get a dict suitable to instantiate a Leak as kwargs.

        Use 'to_dict()' instead.

        TODO: Deprecate this!
        """
        return self.get_leak_kwargs()


    @property
    def key(self) -> str:
        """Returns key value."""

        return self.key_token.get_value(format_type=FORMAT_QUOTE_REMOVAL_STRIP)


    @property
    def value(self) -> str:
        """Returns value value."""

        return self.value_token.get_value(format_type=FORMAT_QUOTE_REMOVAL_STRIP)


    @classmethod
    def from_tokens(cls, key_token, value_token):
        """Docstring."""

        instance = cls(key_token=key_token, value_token=value_token)
        return instance


@attr.s(kw_only=True, slots=True, frozen=True)
class DocumentPosition:
    """DocumentPosition."""

    start_pos: int = attr.ib(default=None)
    end_pos: int = attr.ib(default=None)
    start_line: int = attr.ib(default=None)
    end_line: int = attr.ib(default=None)
    start_column: int = attr.ib(default=None)
    end_column: int = attr.ib(default=None)


    def to_dict(self, exclude: Union[List[str], None] = None) -> Dict:
        """Convert class to a dictionary.

        Args:
            exclude (list, optional): Defaults to None. List of keys to omit.

        Returns:
            dict: Dictionary of class values.
        """

        exclude = exclude or list()
        converted = attr.asdict(self, filter=lambda attr, value: attr.name not in exclude)
        return converted


@attr.s(kw_only=True, slots=True, frozen=True)
class Line:
    """Line."""

    start_pos: int = attr.ib(default=None)
    end_pos: int = attr.ib(default=None)
    number: int = attr.ib(default=None)


    def belongs(self, pos: int) -> bool:
        """Does this position belong to this line?

        Args:

            pos (int): Position within file.

        Returns:

            bool: Whether or not this position belongs to this line.
        """

        return pos >= self.start_pos and pos <= self.end_pos


    def to_dict(self, exclude: Union[List[str], None] = None) -> Dict:
        """Convert class to a dictionary.

        Args:

            exclude (list, optional): Defaults to None. List of keys to omit.

        Returns:

            Dict: Dictionary of class values.
        """

        exclude = exclude or list()
        converted = attr.asdict(self, filter=lambda attr, value: attr.name not in exclude)
        return converted


# pylint: disable=line-too-long
@attr.s(kw_only=True)
class LexerMatchBase:
    """LexerMatchBase.

    Provides a base for Lexers.

    Methods:

        _get_field_to_kind(field: str) -> List[str]: Gets token kind mapping for a fieldname.
        _make_token_tuple(start_pos: int, kind: str, value: str) -> Tuple[int, str, str]: Get a token tuple for start_pos, kind, value.
    """
# pylint: enable=line-too-long


    # pylint: disable=no-member
    def _get_field_to_kind(self, field: str) -> List[str]:
        """Gets token kind from field name."""

        return self._token_kind_mapping[field]
    # pylint: enable=no-member


    @staticmethod
    def _make_token_tuple(start_pos: int, kind: str, value: str) -> Tuple[int, str, str]:
        """Make a token tuple of start_pos, token kind, token value.

        Args:

            start_pos (int): Starting position of token.
            kind (str): Token kind.
            value (str): Value of token.

        Returns:

            Tuple[int, str, str]: Tuple of start_pos, token kind, token value.
        """

        return start_pos, kind, value


@attr.s(kw_only=True, slots=True)
class LexerToken:
    """LexerToken.

    Attributes:

        start_pos (int): Start position of token.
        end_pos (int): End position of token.
        length (int): Length of token contents.
        kind (str): Token kind.
        value (str): Token value.
        number (int?): Token number
        document_position (DocumentPosition): DocumentPosition of token.
    """

    start_pos: int = attr.ib(default=None)
    end_pos: int = attr.ib(default=None)
    length: int = attr.ib(default=None)
    kind: str = attr.ib(default=None)
    value = attr.ib(default=None)
    number: int = attr.ib(default=0)
    document_position: DocumentPosition = attr.ib(default=None)


    def get_value(self, format_type: str = None) -> str:
        """Get value of token as a string.

        Args:

            format_type (str, optional): Format in which to return string.

        Returns:

            str: Value of token as string.
        """

        return_value = self.value

        if format_type == FORMAT_STRIPPED:
            # Return as a string that is strip'ed
            return_value = str(self.value).strip()

        elif format_type == FORMAT_STRING:
            # Return as a string
            return_value = str(self.value)

        elif format_type == FORMAT_QUOTE_REMOVAL:
            # Return string removed of any surrounding quotes
            value_string = str(self.value)
            if (value_string.startswith("'") and value_string.endswith("'")) or \
                (value_string.startswith('"') and value_string.endswith('"')):
                return_value = value_string[1:-1]

        elif format_type == FORMAT_QUOTE_REMOVAL_STRIP:
            # Return string with surrounding quotes removed and strip'ed
            without_quotes = self.get_value(format_type=FORMAT_QUOTE_REMOVAL)
            return_value = without_quotes.strip()

        else:
            raise ValueError("Unknown format_type '%s'" % format_type)

        return return_value


    def update_value(self, value: str, update_position: bool = True) -> None:
        """Update value of token after it has been set.

        Args:

            value (str): Token value.
            update_position (bool, optional): Defaults to True. Update all position data.

        Returns:

            None.
        """

        # Update value
        self.value = value

        # Convert existing DocumentPosition to dict since it is frozen
        document_dict = self.document_position.to_dict()

        # Update position values to accomodate for the size of the new value
        if update_position:
            value_length = len(value)
            additional_length = value_length - len(self.value)
            # Add additional length to end position
            self.end_pos += additional_length
            # Update our length
            self.length = value_length
            # Add additional length to document position end_column
            document_dict['end_column'] += additional_length

        # Create and store new DocumentPosition
        new_document_position = DocumentPosition(**document_dict)
        self.document_position = new_document_position


    def get_document_position(self) -> DocumentPosition:
        """Get document position.

        Returns:

            DocumentPosition: DocumentPosition for token.
        """
        return self.document_position


    @classmethod
    def from_lexer(cls, data: Union[List, Tuple], number: int = None) -> 'LexerToken':
        """Instantiate class from an unprocessed lexer token."""

        # TODO: Fix this. length below raises a TypeError with the following token:
        # (-1, ['analyzer', 'Key'], None)
        # Perhaps if a token has no value then it should be None and the length should be 0?
        kind = ".".join(data[1])
        length = len(data[2])
        value = data[2]
        kwargs = {
            'start_pos': data[0],
            'end_pos': data[0] + length,
            'length': length,
            'kind': kind,
            'value': value,
        }
        token = cls(**kwargs)
        if number is not None:
            token.number = number
        return token


@attr.s(kw_only=True, slots=True)
class NewLinePositions:
    """NewLinePositions"""

    newlines = attr.ib(factory=list)


    def parse(self, data: str) -> None:
        """Calculate new line positions.

        Args:

            data (str): Data to parse.

        Returns:

            None.
        """

        matches = re.finditer(r"\n", data, re.MULTILINE)

        # Initial position is 0
        last_start_pos = 0
        last_end_pos = None
        last_match_number = None
        end_pos = len(data)

        for match_number, match in enumerate(matches, start=1):
            # End position is this position
            last_end_pos = match.start()
            self.__add_newline(start_pos=last_start_pos, end_pos=last_end_pos, number=match_number)

            # The new starting position for the next match is this position
            last_start_pos = last_end_pos

            # Clear last end position
            last_end_pos = None

            # Last match number is this match number minus 1. The first match will always
            # be '1' but the first line in a document is always '0'.
            last_match_number = match_number - 1

        # Add the last line with end position
        if last_end_pos is None:
            self.__add_newline(start_pos=last_start_pos, end_pos=end_pos, number=last_match_number)


    def __add_newline(self, **kwargs) -> None:
        line = Line(**kwargs)
        self.newlines.append(line)


    def get_position_for_token(self, token: LexerToken) -> DocumentPosition:
        """Get position data for a token.

        Args:

            token (LexerToken): Token from Lexer.

        Returns:

            DocumentPosition: DocumentPosition instance for LexerToken.
        """

        line = self.get_line_for_pos(token.start_pos)
        start_line = line.number
        start_column = token.start_pos - line.start_pos

        line = self.get_line_for_pos(token.end_pos)
        end_line = line.number
        end_column = token.end_pos - line.start_pos

        pos_kwargs = {
            'start_pos': token.start_pos,
            'end_pos': token.end_pos,
            'start_line': start_line,
            'end_line': end_line,
            'start_column': start_column,
            'end_column': end_column,
        }

        pos = DocumentPosition(**pos_kwargs)

        return pos

    def get_line_for_pos(self, pos: int) -> Line:
        """Get line for a position.

        Args:
            pos (int): Position within file.

        Raises:
            RuntimeError: If no line can be found.

        Returns:
            Line: Line instance.
        """

        found_line = None

        for line in self.newlines:
            if line.belongs(pos):
                found_line = line

        if not found_line:
            raise RuntimeError("Could not find position for '%s'" % pos)

        return found_line


    def get_line_number(self, pos: int) -> int:
        """Get the line number for a position.

        Args:

            pos (int): Position within file.

        Returns:

            int: Line number of position.
        """

        line = self.get_line_for_pos(pos)
        return line.number


    def to_dict(self, exclude: Union[List[str], None] = None) -> Dict:
        """Convert class to a dictionary.

        Args:

            exclude (list, optional): Defaults to None. List of keys to omit.

        Returns:

            Dict: Dictionary of class values.
        """

        exclude = exclude or list()
        converted = attr.asdict(self, filter=lambda attr, value: attr.name not in exclude)
        return converted


@attr.s(kw_only=True, slots=True)
class Document:
    """Document."""

    filename: str = attr.ib(default=None)
    text: str = attr.ib(default=None, repr=False)
    tokens = attr.ib(factory=dict, repr=False)
    all_tokens = attr.ib(factory=list, repr=False)
    newlines: NewLinePositions = attr.ib(factory=NewLinePositions, repr=False)
    lexer = attr.ib(default=None)

    kvps = attr.ib(factory=list, type=list, repr=False, hash=False)
    _parsed_tree = attr.ib(default=None, repr=False, hash=False)


    def parse(self, text: str) -> None:
        """Parse document and generate all tokens.

        Args:

            text (str): Text to parse for document.

        Returns:

            None
        """

        if self.lexer is None:
            raise ValueError("self.lexer is unset!")

        for i, unprocessed_token in enumerate(self.lexer.get_tokens_unprocessed(text)):
            if unprocessed_token is None:
                continue
            token = LexerToken.from_lexer(unprocessed_token, number=i)
            if token.kind not in self.tokens:
                self.tokens[token.kind] = []

            self.tokens[token.kind].append(token)
            self.all_tokens.append(token)

        self.parse_newlines(text=text)
        self.update_token_positions()


    def set_lexer(self, name: str) -> None:
        """Set pygments lexer to be used.

        Args:

            name (str): Name of lexer.

        Returns:

            None.
        """

        from ContentAnalyzer.base import get_lexer_by_name
        self.lexer = get_lexer_by_name(name)


    # pylint: disable=no-member
    def parse_newlines(self, text: str = None) -> None:
        """Parse newlines.

        Args:

            text (str): Text to parse.

        Returns:

            None.
        """

        text = text or self.text
        self.newlines.parse(text)
    # pylint: enable=no-member


    # pylint: disable=no-member
    def update_token_positions(self) -> None:
        """Update tokens with position data.

        Returns:

            None.
        """

        for v in self.tokens.values():
            for token in v:
                document_position = self.newlines.get_position_for_token(token)
                token.document_position = document_position
    # pylint: enable=no-member


    def get_tokens(self, kind: str = None) -> Iterable:
        """Get tokens.

        Args:

            kind (str, optional): Defaults to None. Token type/kind to get.

        Yields:

            LexerToken: Token for 'kind'.
        """

        for k, v in self.tokens.items():
            if kind is not None and kind == k:
                for token in v:
                    yield token
            elif kind is None:
                for token in v:
                    yield token


    def get_token_kinds(self) -> List[str]:
        """Return a list of all LexerToken kinds.

        Returns:

            List[str]: List of LexerToken kinds.
        """

        return list(self.tokens.keys())


    def get_key(self, name: str) -> List[str]:
        """Gets all values for a key name.

        Returns:

            List[str]: List of values for key name.
        """

        values = [kv_pair.value for kv_pair in self.get_kvps() if kv_pair.key == name]

        return values


    def get_kvps(self) -> List[KeyValuePair]:
        """Get key/value pairs as list of KeyValuePair.

        Returns:

            List[KeyValuePair]: List of KeyValuePairs.
        """
        return self.kvps.copy()


    @property
    def keys(self) -> List:
        """Keys.

        Returns:

            List: List of keys.
        """

        keys = [kv_pair.key for kv_pair in self.kvps]
        return keys


    @property
    def values(self) -> List:
        """Values.

        Returns:

            List: List of values.
        """

        values = [kv_pair.value for kv_pair in self.kvps]
        return values
