from typing import Optional, TextIO, Union, Any
from collections.abc import Mapping
import random
import string
import regex


class NoSectionHeaderError(Exception):
    """Raised if an option is detected outside a section"""


class ParseError(Exception):
    """Raised when unable to parse a line"""


def get_random_id(k: Optional[int] = 16) -> str:
    return ''.join(random.choices(string.hexdigits, k=k))


class Option(object):
    """Stores key, value pairs of option, or just value if not parsable"""

    def __init__(self, **kwargs) -> None:
        self.name = kwargs.get('option')
        self.value = kwargs.get('value')

    def add_option(self, name: str, value: str) -> None:
        self.name = name
        self.value = value

    def add_value(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        if self.value is not None and self.name is None:
            return self.value
        return f'{self.name} = {self.value}'

    __str__ = __repr__


class Section(Mapping):
    """Section object that contains options
    
    If any of the options is not parsable, every next line until the next section
    will be added directly without parsing.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.skip_parse = False
        self.options = dict()
    
    def set_option(self, option: Union[Option, str] = None, value: Optional[str] = '') -> None:
        if isinstance(option, Option):
            if option.name is None:
                self.options.update({f'item-{get_random_id()}': option})
                return
            self.options.update({option.name: option})
        elif option is None:
            option = Option(value=value)
            self.options.update({f'item-{get_random_id()}': option})
        else:
            option = Option(option=option, value=value)
            self.options.update({option.name: option})

    def remove_option(self, option: str) -> None:
        if not option in self.options:
            raise KeyError(option)
        del self.options[option]

    def has_option(self, option: str) -> bool:
        return option in self.options

    def get_value(self, option: str):
        if option in self.options:
            return self.options[option].value
        raise KeyError(option)

    def __getitem__(self, key: str) -> Option:
        if key in self.options:
            return self.options[key]
        raise KeyError(key)

    def __iter__(self) -> iter:
        return iter(self.options)

    def __len__(self) -> int:
        return len(self.options)

    def __repr__(self) -> str:
        if self.skip_parse or not self.options:
            return f'[{self.name}]'
        options = '\n'.join(map(str, self.options.values()))
        return f'[{self.name}]\n{options}'

    __str__ = __repr__


class ModConfigParser(Mapping):
    """Custom parser for GIMI mods config files
    
    Able to parse and perserve comments and commands, commands is save in raw form
    since it was unparseable (intended).
    """
    RESECTION = regex.compile(r'^\[(?P<section>.+?)\]$')
    REOPTION = regex.compile(r"""
        ^
        (?!
            \s+
        |
            if 
        |
            else if
        |
            endif
        )
        (?P<option>[^=]+?)
        \s*=\s*
        (?P<value>[^=]+?)
        $
    """, regex.VERBOSE | regex.IGNORECASE)
    COMMENT_PREFIX = ';'

    def __init__(self) -> None:
        self.sections = dict()

    def set(self, section: str, option: str, value: Optional[str] = '') -> None:
        self[section].set_option(option, value)

    def get(self, section: str, option: Optional[str] = None) -> Union[Section, Any]:
        if option is None:
            return self[section]
        return self[section][option].value

    def add_section(self, section: Section) -> None:
        self.sections.update({section.name: section})

    def add_comment(self, comment: str) -> None:
        self.sections.update({f'comment-{get_random_id()}': comment})

    def has_section(self, section: str) -> bool:
        return section in self

    def remove_section(self, section: str) -> None:
        if not section in self:
            raise KeyError(section)
        del self[section]

    def remove_option(self, section: str, option: str) -> None:
        if not section in self:
            raise KeyError(section)
        elif not section in self[section]:
            raise KeyError(option)
        del self[section][option]

    def read(self, filename: str) -> None:
        with open(filename, 'r') as file:
            self.read_file(file)
            file.close()

    def read_file(self, fp: TextIO) -> None:
        config_data = [line.replace('\n', '') for line in fp.readlines()]
        cursect: Section = None  # None or Section
        lastsect: Section = None  # None or Section

        for line in config_data:
            if not line:
                continue
            elif line.startswith(self.COMMENT_PREFIX):
                self.add_comment(line)
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
                    cursect.set_option(value=line)
                    continue

                option = Option(**option_match.groupdict())
                if not cursect.has_option(option.name):
                    cursect.set_option(option)
            elif section_match is None is option_match:
                if cursect is None is lastsect:
                    raise NoSectionHeaderError(option_match.group('option'))
                elif cursect is None is not lastsect:
                    continue
                cursect.set_option(value=line)
                cursect.skip_parse = True

    def write(self, fp: TextIO) -> None:
        for section in self:
            if section.startswith('comment-'):
                continue
            self[section].skip_parse = False
        fp.write('\n\n'.join(map(str, self.values())))

    def __getitem__(self, key: str) -> Section:
        if key in self.sections:
            return self.sections[key]
        raise KeyError(key)

    def __iter__(self) -> iter:
        return iter(self.sections)

    def __len__(self) -> int:
        return len(self.sections)
