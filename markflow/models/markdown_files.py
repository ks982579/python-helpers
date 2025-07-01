from pathlib import Path


class MarkdownFile:
    def __init__(self, file_path: Path, *args, **kwargs):
        abs_file_path = file_path.absolute()
        if not abs_file_path.exists():
            raise FileNotFoundError(f"{file_path}")
        self.file_path = abs_file_path

        with open(abs_file_path, 'r') as file:
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
