from __future__ import annotations

from typing import Optional, TextIO, Iterator, Union, Any
from collections.abc import MutableMapping
import contextlib
import regex
import uuid
import configparser


def identifier_check(name: str, type_: str) -> bool:
    """Check if a string is an indentifier
    
    Returns True if a string starts with a type and ends with a uuid4 ID
    """

    pattern = r'{type_}-[\da-f]{{8}}(?:-[\da-f]{{4}}){{3}}-[\da-f]{{12}}'
    if regex.search(pattern.format(type_=type_.lower()), name):
        return True
    return False


class NoSectionError(Exception):
    """Raised when trying to get non-existent section"""

    def __init__(self, section: str) -> None:
        self.message = f'Section {section!r} does not exists'
        self.section = section
        super(NoSectionError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message

    __str__ = __repr__


class NoOptionError(Exception):
    """Raised when trying to get non-existent option"""

    def __init__(self, option: str) -> None:
        self.message = f'Option {option!r} does not exists'
        self.option = option
        super(NoOptionError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message
    
    __str__ = __repr__


class NoSectionHeaderError(Exception):
    """Raised if an option is detected outside a section"""

    def __init__(self, option: str) -> None:
        self.message = f'Option {option!r} detected outside of header'
        self.option = option
        super(NoSectionHeaderError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message

    __str__ = __repr__


class MultipleHiddenSectionError(Exception):
    """Raised if trying to create multiple hidden section"""

    def __init__(self, section: str) -> None:
        self.message = f'Cannot create hidden section {section!r} because a hidden section already exists'
        self.option = section
        super(MultipleHiddenSectionError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message

    __str__ = __repr__


class HiddenSectionNotAllowedError(Exception):
    """Raised if trying to create a hidden section without setting the flags"""

    def __init__(self, section: str) -> None:
        self.message = f'Cannot create hidden section {section!r} because it\'s not allowed'
        self.option = section
        super(HiddenSectionNotAllowedError, self).__init__(self.message)

    def __repr__(self) -> str:
        return self.message

    __str__ = __repr__


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

    __str__ = __repr__


class Comment(object):
    """Stores string as a comment, can be prefixed by ; or #"""

    PREFIX = (';', '#')

    def __init__(self, comment: str, name: Optional[str] = None, lead_space: Optional[bool] = False,
                 end_space: Optional[bool] = False) -> None:
        """Construct Comment class

        If comment doesn't start with any of the prefixes, it will use ; by default
        Comment can also have a newline before and after then comment
        """

        if name is None:
            name = f'comment-{uuid.uuid4()}'
        self._name = name

        if comment.strip()[0] not in self.PREFIX:
            comment = f'; {comment.strip()}'
        self._comment = comment.strip()

        self._lead_space = lead_space
        self._end_space = end_space

    @property
    def name(self) -> str:
        return self._name

    @property
    def comment(self) -> str:
        return self._comment

    def __repr__(self) -> str:
        prefix = '\n' if self._lead_space else ''
        suffix = '\n' if self._end_space else ''
        return f'{prefix}{self._comment}{suffix}'

    __str__ = __repr__


class Option(object):
    """Stores key, value pairs of option, or just value if not parsable
    
    Options can also be commented or using inline comments
    """

    def __init__(self, **kwargs) -> None:
        """Construct Option class

        Parameters
        ----------
        **kwargs
            value: str, default None
                The value of an option
            option: str, default None
                The name of the option
            name: str, default None
                The name of the option object

                name is equal to option if provided, if not name will be randomly generated with uuid4 ID
            comment: str, default None
                Inline comments
        """

        self._is_commented = False
        self.value = kwargs.get('value')
        self.option = kwargs.get('option')

        name = kwargs.get('name')
        if name is None:
            if self.option is None:
                name = f'item-{uuid.uuid4()}'
            else:
                name = self.option
        self.name = name
        self.inline_comment = kwargs.get('comment')

    def set(self, name: Optional[str] = None, option: Optional[str] = None, value: Optional[str] = None) -> None:
        if name is not None:
            self.name = name
        if option is not None:
            self.option = option
        self.value = value

    def comment(self) -> None:
        self._is_commented = True

    def uncomment(self) -> None:
        self._is_commented = False

    def __repr__(self) -> str:
        prefix = ''
        if self._is_commented:
            prefix = '; '

        value = ''
        if self.value is not None:
            value = self.value

        comment = ''
        if self.inline_comment is not None:
            comment = self.inline_comment

        if value is not None and identifier_check(self.name, 'item'):
            return f'{prefix}{value}{comment}'
        return f'{prefix}{self.option} = {value}{comment}'

    __str__ = __repr__


class Section(MutableMapping):
    """Section object that contains options
    
    If any of the options is not parsable, every next line until the next section
    will be added directly without parsing.
    """

    DEFAULT_HIDDEN_NAME = 'HiddenProperties'


    def __init__(self, name: str, parent: Optional[ModConfigParser] = None) -> None:
        """Construct Section class

        Parameters
        ----------
        name: str
            Name of the section
        parent: ModConfigParser, default None
            Parent of the section, optional
        
        Raises
        ------
        NoOptionError
            Raised if an option doesn't exists
        KeyError
            Raised when trying to get non-existent option
        """

        self.name = name
        if 'command' in self.name.lower():
            self.skip_parse = True
        else:
            self.skip_parse = False
        self.parent = parent
        self._options = dict()

    @property
    def options(self) -> list:
        return list(self._options)

    def get(self, option: str, *, only_value: Optional[bool] = True) -> Union[Option, Any]:
        if option not in self:
            raise NoOptionError(option)
        if only_value:
            return self[option].value
        return self[option]

    def add_option(self, name: Optional[str] = None, option: Optional[str] = None, value: Optional[str] = None, comment: Optional[str] = None) -> None:
        if option is None is value:
            return
        option = Option(name=name, option=option, value=value, comment=comment)
        self.update({option.name: option})

    def add_comment(self, comment: str, lead_space: Optional[bool] = False, end_space: Optional[bool] = False) -> None:
        comment = Comment(comment, lead_space=lead_space, end_space=end_space)
        self.update({comment.name: comment})

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

    def __setitem__(self, key: str, value: Union[Option, Comment, str]) -> None:
        if key in self._options and self._options[key] == value:
            return
        elif not isinstance(value, (Option, Comment, str)):
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
        allow_no_header = False
        if self.parent is not None:
            allow_no_header = self.parent.allow_no_header
        hidden_section = self.name == self.DEFAULT_HIDDEN_NAME
        
        if self.skip_parse or not self._options:
            if hidden_section and allow_no_header:
                return str()
            return f'[{self.name}]'
        options = '\n'.join(map(str, self._options.values()))

        if hidden_section and allow_no_header:
            return options
        return f'[{self.name}]\n{options}'

    __str__ = __repr__


class ModConfigParser(MutableMapping):
    """Custom parser for GIMI mods config files
    
    This parser also works for normal parser but not as rigid as configparser module.
    The parser is able to parse and perserve comments and commands, commands is saved in raw form
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
        (?P<option>[^=]+?)      # - Anything that isn't =
        \s*=\s*                 # - = with any number of whitespaces before and after
        (?P<value>[^;#=]+?)     # - Anything that isn't ;#=
        \s*                     # - Any number of whitespaces
        (?P<comment>[;#].*)?    # - Inline comment if any
        $
    """, regex.VERBOSE | regex.IGNORECASE)

    def __init__(self, restrict: Optional[bool] = True, allow_no_header: Optional[bool] = False) -> None:
        """Construct Parser class

        Parameters
        ----------
        restrict: bool, default True
            Flag to enable using options with the same name in a section
        allow_no_header: bool, default False
            Flag to enable using options without a section header, there can be only 1 hidden section
        
        Raises
        ------
        NoSectionError
            Raised if a section doesn't exists
        NoOptionError
            Raised if an option doesn't exists
        MultipleHiddenSectionError
            Raised if trying to create multiple hidden sections
        HiddenSectionNotAllowedError
            Raised if trying to create a hidden section with allow_no_header flag set to False
        ParseError
            Raised if unable to parse a line (Both regex has to match the same line)
        KeyError
            Raised if instance doesn't have the specified key
        """

        self._sections = dict()
        self.restrict = restrict
        self.allow_no_header = allow_no_header

    @property
    def sections(self) -> list:
        return list(self._sections)

    def set(self, section: str, option: str, value: Optional[str] = None) -> None:
        if section not in self:
            raise NoSectionError(section)
        self[section].add_option(option=option, value=value)

    def get(self, section: str, option: Optional[str] = None, *,
            only_value: Optional[bool] = True) -> Union[Section, Option, None, str]:
        if section not in self:
            raise NoSectionError(section)
        elif option is not None and option not in self[section]:
            raise NoOptionError(option)

        if option is None:
            if only_value:
                return str(self[section])
            return self[section]
        return self[section].get(option, only_value=only_value)

    def add_comment(self, comment: str, section: Optional[str] = None, lead_space: Optional[bool] = False,
                    end_space: Optional[bool] = False) -> None:
        if section is None:
            comment = Comment(comment, lead_space=lead_space, end_space=end_space)
            self.update({comment.name: comment})
        elif section not in self:
            raise NoSectionError(section)
        else:
            self[section].add_comment(comment, lead_space=lead_space, end_space=end_space)

    def add_section(self, section: Union[Section, str]) -> None:
        if isinstance(section, Section):
            self.update({section.name: section})
        else:
            self.update({section: Section(section)})

    def add_hidden_section(self, section: str):
        if self.has_section(Section.DEFAULT_HIDDEN_NAME):
            raise MultipleHiddenSectionError(section)
        elif not self.allow_no_header:
            raise HiddenSectionNotAllowedError(section)

        if section != Section.DEFAULT_HIDDEN_NAME:
            Section.DEFAULT_HIDDEN_NAME = section
        self.update({section: Section(section, parent=self)})

    def has_section(self, section: str) -> bool:
        return section in self

    def has_option(self, section: str, option: str) -> bool:
        if section not in self:
            raise NoSectionError(section)
        
        check_section = self[section]
        if isinstance(check_section, Comment):
            return option == check_section.name
        return option in check_section

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
        with open(filename, 'r', encoding='utf-8') as file:
            self.read_file(file)
            file.close()

    def read_file(self, fp: TextIO) -> None:
        """Parse a configuration file

        Each section in a config file will contain a header name inside a square brackets ('[]'),
        in each of those sections it can contains key/value options, indicated by '=' delimiter.

        Config files may also include comments, these comment can be prefixed by '#' or ';' (Default).
        Comments can also be inline with an option
        
        For example:
            enable = true ; Enable some option

        GIMI Specific config files can contains options with the same key/name, if the restrict parameter
        is set to False, the latter option will be used, if restrict is True, the first option will have the
        original key/name and the options after that will have an additional ID as the parser use
        name (by object) instead of name (by option) when parsing it.

        For example:
            opt = Arg
                {
                    Name: opt
                    Option: opt
                    Value: Arg
                }
            opt = Arg2
                {
                    Name: opt-ID
                    Option: opt
                    Value: Arg2
                }

        GIMI also have several options that does not have a section header, if allow_no_header flag is set
        to False, this will raise 'HiddenSectionNotAllowedError', if set to True, these options will be
        added to a hidden section (default name: HiddenProperties) where the name of the section will
        not get written when writing into a file.

        Parameters
        ----------
        fp: TextIO
            File object returned by open()
        
        Raises
        ------
        NoSectionError
            Raised if a section doesn't exists
        NoOptionError
            Raised if an option doesn't exists
        ParseError
            Raised if unable to parse a line (Both regex has to match the same line)
        """

        config_data = [line.replace('\n', '') for line in fp.readlines()]
        cursect = None  # None or Section
        lastsect = None  # None or Section
        lastempty = False  # True if the previous item is space

        for line in config_data:
            if not line.strip():
                lastempty = True
                continue
            if line.strip()[0] in Comment.PREFIX:
                if cursect is None:
                    self.add_comment(line.strip(), lead_space=lastempty)
                else:
                    self.add_comment(line.strip(), cursect.name, lead_space=lastempty)
                lastempty = False
                continue

            lastempty = False
            section_match = self.RESECTION.match(line.strip())
            option_match = self.REOPTION.match(line)

            if section_match and option_match:
                raise ParseError(line)
            elif section_match and option_match is None:
                section = Section(section_match.group('section'))

                if not self.has_section(section.name):
                    lastsect = cursect
                    self.add_section(section)
                    cursect = self[section.name]
                else:
                    cursect = None
            elif option_match and section_match is None:
                if cursect is None is lastsect:
                    if not self.allow_no_header:
                        raise NoSectionHeaderError(option_match.group('option'))
                    
                    if not self.has_section(Section.DEFAULT_HIDDEN_NAME):
                        self.add_hidden_section(Section.DEFAULT_HIDDEN_NAME)
                    section = self.get(Section.DEFAULT_HIDDEN_NAME, only_value=False)
                    section.add_option(**option_match.groupdict())
                    continue
                elif cursect is None is not lastsect:  # Option of duplicated sections
                    continue
                elif cursect.skip_parse:
                    cursect.add_option(value=line)
                    continue

                if not cursect.has_option(option_match.group('option')):
                    cursect.add_option(**option_match.groupdict())
                elif not self.restrict and cursect.get(option_match.group('option')) != option_match.group('value'):
                    name = f"{option_match.group('option')}-{uuid.uuid4()}"
                    cursect.add_option(name=name, **option_match.groupdict())
            elif section_match is None is option_match:  # Unparsable line
                if cursect is None is lastsect:
                    if not self.allow_no_header:
                        raise NoSectionHeaderError(line)
                    
                    if not self.has_section(Section.DEFAULT_HIDDEN_NAME):
                        self.add_hidden_section(Section.DEFAULT_HIDDEN_NAME)
                    section = self.get(Section.DEFAULT_HIDDEN_NAME, only_value=False)
                    section.add_option(value=line)
                    continue
                elif cursect is None is not lastsect:
                    continue
                cursect.add_option(value=line)
                cursect.skip_parse = True

    def write(self, fp: TextIO) -> None:
        fp.write(self.dumps(include_skip=True))

    @contextlib.contextmanager
    def _parse_check(self, section: Section, include_skip: Optional[bool] = False) -> None:
        skip_parse = section.skip_parse
        if include_skip:
            section.skip_parse = False
        yield
        section.skip_parse = skip_parse

    def dumps(self, include_skip: Optional[bool] = False) -> str:
        items = []
        comments  = []

        for name, section in self.items():
            if identifier_check(name, 'comment'):
                comments.append(section)
                continue
            if comments:
                items.append('\n'.join(map(str, comments)))
                comments.clear()

            with self._parse_check(section, include_skip):
                items.append(str(section))
        return '\n\n'.join(items)

    def __getitem__(self, key: str) -> Section:
        if key not in self._sections:
            raise KeyError(key)
        return self._sections[key]

    def __setitem__(self, key: str, value: Union[Section, Comment, str]) -> None:
        if not isinstance(value, (Section, Comment, str)):
            return NotImplemented
        elif isinstance(value, (str, Comment)) and not identifier_check(key, 'comment'):
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
