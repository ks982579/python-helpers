from pathlib import Path
from abc import ABC, abstractmethod


class MarkdownFile:
    def __init__(self, file_path: Path, *args, **kwargs):
        abs_file_path = file_path.absolute()
        if not abs_file_path.exists():
            raise FileNotFoundError(f"{file_path}")
        self.file_path = abs_file_path

        with open(abs_file_path, 'r', encoding="UTF-8") as file:
            self.__raw_content = file.read()

    # @property
    def _get_content(self):
        return self.__raw_content

    # @property.setter
    def _set_content(self, _):
        print("Exception: Cannot set content once read")

    # @property.deleter
    def _del_content(self):
        del self.__raw_content

    content = property(
        fget=_get_content,
        fset=_set_content,
        fdel=_del_content,
        doc="Raw content from Markdown File"
    )

# TODO: Make ABC -> Then have Specific sections with specific rules
# But each section reacts to CLI input - hence ABC


class AbstractMarkdownSection(ABC):
    """
    Abstract class so each section has similar details

    No abstract methods yet...
    """

    def _get_content(self):
        return self.__raw_content

    def _set_content(self, value):
        raise Exception("Cannot set value.")

    def _del_content(self):
        del self.__raw_content

    content = property(
        fget=_get_content,
        fset=_set_content,
        fdel=_del_content,
        doc="Raw content from Markdown File"
    )


class MarkdownSection(AbstractMarkdownSection):
    def __init__(self, text: str):
        self.__raw_content = text
