from typing import Optional, TextIO, Iterator, Union, Any
from collections.abc import MutableMapping
import random
import string
import regex


class NoSectionError(Exception):
    """Raised when trying to get non-existent section"""

    def __init__(self, section: str) -> None:
        self.message = f'Section {section!r} does not exists'
        self.section = section
        super(NoSectionError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message


class NoOptionError(Exception):
    """Raised when trying get non-existent option"""

    def __init__(self, option: str) -> None:
        self.message = f'Option {option!r} does not exists'
        self.option = option
        super(NoOptionError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message


class NoSectionHeaderError(Exception):
    """Raised if an option is detected outside a section"""

    def __init__(self, option: str) -> None:
        self.message = f'Option {option!r} detected outside of header'
        self.option = option
        super(NoSectionHeaderError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message


class ParseError(Exception):
    """Raised when unable to parse a line
    
    If this is raised then there is a problem with the regex
    """

    def __init__(self, line: str) -> None:
        self.message = f'Unable to parse {line!r}'
        self.line = line
        super(ParseError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message


def get_random_id(k: Optional[int] = 16) -> str:
    return ''.join(random.choices(string.hexdigits, k=k))


class Option(object):
    """Stores key, value pairs of option, or just value if not parsable"""

    def __init__(self, **kwargs) -> None:
        self._name = None
        self._value = None

        self.name = kwargs.get('option')
        if self.name is None:
            self.name = kwargs.get('name')
        self.value = kwargs.get('value')

    @property
    def name(self) -> Union[None, str]:
        return self._name

    @name.setter
    def name(self, value: Optional[str] = None) -> None:
        if value is None or isinstance(value, str):
            self._name = value
            return
        raise TypeError(f"Expected type {'str'!r} got {type(value).__name__!r} instead")

    @property
    def value(self) -> Union[None, str]:
        return self._value

    @value.setter
    def value(self, value: Optional[str] = None) -> None:
        if value is None or isinstance(value, str):
            self._value = value
            return
        raise TypeError(f"Expected type {'str'!r} got {type(value).__name__!r} instead")

    def set(self, name: Optional[str] = None, value: Optional[str] = None) -> None:
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        if self.value is not None and self.name is None or self.name.startswith('item-'):
            return self.value
        return f'{self.name} = {self.value}'

    __str__ = __repr__


class Section(MutableMapping):
    """Section object that contains options
    
    If any of the options is not parsable, every next line until the next section
    will be added directly without parsing.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.skip_parse = False
        self._options = dict()

    @property
    def options(self) -> list:
        return list(self._options)

    def get(self, option: str, only_value: Optional[bool] = True):
        if option not in self:
            raise NoOptionError(option)
        if only_value:
            return self[option].value
        return self[option]

    def add_option(self, option: Union[Option, str] = None, value: Optional[str] = '') -> None:
        if option is None and not value:
            return

        if isinstance(option, Option):
            self.update({option.name: option})
            return
        if option is None:
            option = f'item-{get_random_id()}'
        option = Option(name=option, value=value)
        self.update({option.name: option.value})

    def has_option(self, option: str) -> bool:
        return option in self

    def remove_option(self, option: str) -> None:
        if option not in self:
            raise NoOptionError(option)
        del self[option]

    def __getitem__(self, key: str) -> Option:
        if key not in self._options:
            raise KeyError(key)
        return self._options[key]

    def __setitem__(self, key: str, value: Union[Option, str]) -> None:
        if key in self._options and self._options[key] == value:
            return
        elif not isinstance(value, (Option, str)):
            return NotImplemented

        if isinstance(value, str):
            self._options[key] = Option(name=key, value=value)
            return
        self._options[key] = value

    def __delitem__(self, key: str) -> None:
        if key not in self._options:
            raise KeyError(key)
        del self._options[key]

    def __iter__(self) -> Iterator:
        return iter(self._options)

    def __len__(self) -> int:
        return len(self._options)

    def __repr__(self) -> str:
        if self.skip_parse or not self._options:
            return f'[{self.name}]'
        options = '\n'.join(map(str, self._options.values()))
        return f'[{self.name}]\n{options}'

    __str__ = __repr__


class ModConfigParser(MutableMapping):
    """Custom parser for GIMI mods config files
    
    This parser also works for normal parser but not as rigid as configparser module.
    The parser is able to parse and perserve comments and commands, commands is save in raw form
    since it was unparseable (intended).
    """

    RESECTION = regex.compile(r'^\[(?P<section>.+?)\]$')
    REOPTION = regex.compile(r"""
        ^
        (?!                     # Don't match if
            \s+                 # - Start with whitespaces
        |
            if\s                # - Start with if
        |
            else if             # - Start with else if
        |
            endif               # - Start with endif
        )                       # Match line that
        (?P<option>[^=]+?)      # - Start with anything that isn't "="
        \s*=\s*                 # - Have a delimiter of "=" with any amount of whitespaces before and after
        (?P<value>[^=]+?)       # - End with anything that isn't "="
        $
    """, regex.VERBOSE | regex.IGNORECASE)
    COMMENT_PREFIX = (';', '#')

    def __init__(self) -> None:
        self._sections = dict()

    @property
    def sections(self) -> list:
        return list(self._sections)

    def set(self, section: str, option: str, value: Optional[str] = '') -> None:
        if section not in self:
            raise NoSectionError(section)
        self[section].add_option(option, value)

    def get(self, section: str, option: Optional[str] = None) -> Union[Section, None, str]:
        if section not in self:
            raise NoSectionError(section)
        elif option is not None and option not in self[section]:
            raise NoOptionError(option)

        if option is None:
            return self[section]
        return self[section].get(option)

    def add_comment(self, comment: str) -> None:
        if comment.strip()[0] not in self.COMMENT_PREFIX:
            comment = f'; {comment}'
        self.update({f'comment-{get_random_id()}': comment})

    def add_section(self, section: Union[Section, str]) -> None:
        if isinstance(section, Section):
            self.update({section.name: section})
        else:
            self.update({section: Section(section)})

    def has_section(self, section: str) -> bool:
        return section in self

    def has_option(self, section: str, option: str) -> bool:
        if section not in self:
            raise NoSectionError(section)
        return option in self[section]

    def remove_section(self, section: str) -> None:
        if section not in self:
            raise NoSectionError(section)
        del self[section]

    def remove_option(self, section: str, option: str) -> None:
        if section not in self:
            raise NoSectionError(section)
        elif option not in self[section]:
            raise NoOptionError(option)
        del self[section][option]

    def read(self, filename: str) -> None:
        with open(filename, 'r') as file:
            self.read_file(file)
            file.close()

    def read_file(self, fp: TextIO) -> None:
        config_data = [line.replace('\n', '') for line in fp.readlines()]
        cursect = None  # None or Section
        lastsect = None  # None or Section
        comment_line = False  # True if current line is comment

        for line in config_data:
            for prefix in self.COMMENT_PREFIX:
                if not line.strip().startswith(prefix):
                    continue
                self.add_comment(line.strip())
                comment_line = True
                break
            if not line or comment_line:
                comment_line = False
                continue

            section_match = self.RESECTION.match(line)
            option_match = self.REOPTION.match(line)

            if section_match and option_match:
                raise ParseError(line)
            elif section_match and option_match is None:
                section = Section(section_match.group('section'))

                if 'command' in section.name.lower():
                    section.skip_parse = True
                
                if not self.has_section(section.name):
                    lastsect = cursect
                    self.add_section(section)
                    cursect = self[section.name]
                else:
                    cursect = None
            elif option_match and section_match is None:
                if cursect is None is lastsect:
                    raise NoSectionHeaderError(option_match.group('option'))
                elif cursect is None is not lastsect:
                    continue
                elif cursect.skip_parse:
                    cursect.add_option(value=line)
                    continue

                option = Option(**option_match.groupdict())
                if not cursect.has_option(option.name):
                    cursect.add_option(option)
            elif section_match is None is option_match:
                if cursect is None is lastsect:
                    raise NoSectionHeaderError(option_match.group('option'))
                elif cursect is None is not lastsect:
                    continue
                cursect.add_option(value=line)
                cursect.skip_parse = True

    def write(self, fp: TextIO) -> None:
        for section in self:
            if section.startswith('comment-'):
                continue
            self[section].skip_parse = False
        fp.write('\n\n'.join(map(str, self.values())))

    def dumps(self) -> str:
        return '\n\n'.join(map(str, self.values()))

    def __getitem__(self, key: str) -> Section:
        if key not in self._sections:
            raise KeyError(key)
        return self._sections[key]

    def __setitem__(self, key: str, value: Union[Section, str]) -> None:
        if not isinstance(value, (Section, str)):
            return NotImplemented
        elif isinstance(value, str) and not key.startswith('comment-'):
            return
        self._sections[key] = value

    def __delitem__(self, key: str) -> None:
        if key not in self._sections:
            raise KeyError(key)
        del self._sections[key]

    def __iter__(self) -> Iterator:
        return iter(self._sections)

    def __len__(self) -> int:
        return len(self._sections)
