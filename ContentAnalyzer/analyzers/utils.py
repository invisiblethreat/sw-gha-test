"""State utils"""

from typing import Dict

def get_column_start_end(text: str, kvp: Dict) -> Dict:
    """Get column start and end from text from a kvp"""

    start_line = text.rfind('\n', 0, kvp['start_pos']) + 1
    start_column = (kvp['start_pos'] - start_line) + 1
    end_column = len(kvp['value'].rstrip().split('\n')[-1]) + start_column
    positions = dict(start_column=start_column, end_column=end_column)
    return positions

class State:
    """State"""

    def __init__(self):
        self.key: str = None
        self.value: str = None
        self.start_pos: int = None
        self.end_pos: int = None
        self.start_line: int = None
        self.end_line: int = None
        self.start_column: int = None
        self.end_column: int = None
        self.have_operator: bool = False
        self.lineno: int = 1
        self.pending_line_count: int = 0

    def update_linenumber_state(self, value: str):
        """Update linenumber state"""
        self.lineno += self.pending_line_count
        line_count = str(value).count("\n")
        self.pending_line_count = line_count

    def set_key(self, key: str):
        """Set key value"""
        self.key = key

    def set_value(self, value: str, strip_quotes: bool = False):
        """Set value's value.

        Args:

            value (str): Value for value.
            strip_quotes (bool, optional): Strip leading and ending quotes. Defaults to False.
        """
        if strip_quotes:
            if value.startswith(("\"", "'")):
                value = value[1:]
            if value.endswith(("\"", "'")):
                value = value[0:-1]
        self.start_line = self.lineno
        self.end_line = self.lineno + max(0, value.count("\n") - 1)
        self.value = value

    def set_pos(self, start_pos: int, end_pos: int = None):
        """Set starting pos.

        Can't set starting pos before setting value!

        Args:

            start_pos (int): Starting position.
            end_pos (int, optional): Ending position. Defaults to None.
        """
        self.start_pos = start_pos
        if isinstance(end_pos, int):
            self.end_pos = end_pos
        else:
            if self.value is None:
                raise ValueError("Must set a value for value before setting pos if not providing an end_pos!") # pylint: disable=line-too-long
            self.end_pos = start_pos + len(self.value)

    def reset_state(self):
        """Reset state"""

        self.key = None
        self.value = None
        self.start_pos = None
        self.end_pos = None
        self.start_line = None
        self.end_line = None
        self.start_column = None
        self.end_column = None
        self.have_operator = False

    def ready_for_value(self) -> bool:
        """Whether or not state is ready to accept a value.

        This usually means we have a key and an operator."""

        if self.key is None or not self.have_operator:
            return False
        return True

    def ready_for_operator(self) -> bool:
        """Whether or not state is ready to accept an operator.

        This usually means we have a key and are pending an operator."""

        if self.key is None:
            return False
        return True

    def to_dict(self):
        """To dict"""

        return {
            'key': self.key,
            'value': self.value,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'start_column': self.start_column,
            'end_column': self.end_column,
        }

class GoState(State):
    """State"""

    def __init__(self):
        super().__init__()
        self.has_second_var: bool = False

    def reset_state(self):
        """Reset state"""

        super().reset_state()
        self.has_second_var = False

    def ready_for_value(self) -> bool:
        """Whether or not state is ready to accept a value.

        This usually means we have a key and an operator."""

        if self.key is None:
            return False
        if self.have_operator:
            return True
        return False
