from __future__ import annotations

from typing import Callable, Iterator, Optional, Union
from collections.abc import MutableMapping
import configparser
import itertools
import importlib
import inspect
import regex
import json
import sys
import os

SLOT = 0
NORMAL = 1
UNIVERSAL = 2


class OutOfScopeError(Exception):
    pass


def command(**attrs):
    def wrapper(func):
        predicate = Command(func, **attrs)
        predicate.__signature__ = inspect.signature(func)
        return predicate
    return wrapper


class Command(object):
    VALID_ATTRS = (
        'name', 'aliases', 'scope',
        'brief', 'description', 'usage'
        'hidden'
    )

    def __new__(cls, *__, **kwargs) -> Command:
        self = super().__new__(cls)
        
        for attr in kwargs:
            if attr in self.VALID_ATTRS:
                continue
            kwargs.pop(attr)
        self.__original_kwargs__ = kwargs.copy()
        return self

    def __init__(self, cmd: Callable, **kwargs) -> None:
        self.name = kwargs.get('name', cmd.__name__)

        if not isinstance(self.name, str):
            raise ValueError('Invalid name')
        elif regex.search(r'\s', self.name):
            raise ValueError('Name cannot have whitespaces')

        self.aliases = kwargs.get('aliases', [])

        if not isinstance(self.aliases, (list, tuple, set)):
            raise ValueError('Invalid alias type')
        for alias in self.aliases:
            if regex.search(r'\s', alias):
                raise ValueError(f'Alias cannot have whitespaces')

        self.callback = cmd
        self.module = cmd.__module__
        self.scope = kwargs.get('scope', NORMAL)

        if self.scope not in range(3):
            raise ValueError('Invalid scope range')

        self.brief = kwargs.get('brief', None)
        self.description = kwargs.get('description', self.brief)

        self._usage = kwargs.get('usage', None)
        self.hidden = kwargs.get('hidden', False)
        self._signature = inspect.signature(cmd)
        self._parameters = self._signature.parameters.copy()

        # parent is added when adding command to loader
        self.parent = None

    @property
    def usage(self) -> str:
        if self._usage is None:
            return f'{self.name} {self.signature}'
        return self._usage

    @property
    def signature(self) -> str:
        if self._usage is not None:
            return self._usage
        result = list()

        for name, param in self._parameters.items():
            if name in ('self', 'con'):
                continue
            if param.default is not param.empty:
                if param.default is None:
                    result.append(f'[{name}]')
                else:
                    result.append(f'[{name}={param.default}]')
            elif self._is_optional(param.annotation):
                result.append(f'[{name}]')
            else:
                result.append(f'<{name}>')
        return ' '.join(result)
    
    @staticmethod
    def _is_optional(annotation: type) -> bool:
        try:
            origin = annotation.__origin__
        except AttributeError:
            return False
        
        if origin is not Union:
            return False
        return origin.__args__[-1] is type(None)

    def __call__(self, con: Console, *args, **kwargs):
        # TODO add 'con' context to call
        if self.scope not in (con.scope, UNIVERSAL):
            raise OutOfScopeError(self.name, con.scope)
        self.callback(self.parent, con, *args, **kwargs)


class Console(object):
    def __init__(self, loader: Loader) -> None:
        self.scope = NORMAL
        self.curslot = None
        self.cmd_called = None
        self.loader = loader

    @staticmethod
    def _digest_arguments(args) -> list:
        return [arg.strip() for arg in args.split('"') if arg.strip()]

    def get_input(self):
        command = None
        args = None
        curslot = self.curslot

        if curslot is None:
            curslot = ''
        else:
            curslot += ' '
        user_input = input(f'{curslot}> ').strip()

        if not len(user_input.split(' ')) == 1:
            command, args = user_input.split(' ', maxsplit=1)
            args = self._digest_arguments(args)
        else:
            command = user_input
        return command, args

    def enter_slot(self, slot: str) -> None:
        if slot not in self.loader:
            raise KeyError(slot)
        self.curslot = slot
        self.scope = SLOT

    def exit_slot(self) -> None:
        self.curslot = None
        self.scope = NORMAL

    def message(self, msg) -> None:
        print(msg)
        input()


class Slot(object):
    def __init__(self, name: str, mods: dict, hidden: Optional[bool] = False) -> None:
        self.name = name
        self.mods = mods
        self.hidden = hidden

        if not self.name:
            raise ValueError('Name cannot be empty')
        elif not isinstance(self.name, str):
            raise ValueError(self.name)
        elif not isinstance(self.mods, dict):
            raise ValueError(self.mods)
        elif not isinstance(self.hidden, bool):
            raise ValueError(hidden)


class Loader(MutableMapping):
    def __init__(self) -> None:
        self._slots = dict()
        self._alises = dict()
        self._commands = dict()
        self._command_module = dict()
        self._stop = False
        self._auto_clear = True

        self._console = Console(self)
        self._current_scope = NORMAL
        self._slot_scope = None

        self.load_config()

    @property
    def slots(self) -> list:
        return list(self._slots)

    @property
    def commands(self) -> list:
        return list(self._commands)

    def load_config(self):
        if not os.path.exists('config.ini'):
            raise FileNotFoundError('config.ini does not exists')

        parser = configparser.ConfigParser()
        parser.read('config.ini')
        self._auto_clear = json.loads(parser.get('General', 'auto_clear'))

    def add_slot(self, **kwargs) -> None:
        if kwargs.get('slot') is not None:
            slot = kwargs['slot']
            self[slot.name] = slot
            return

        name = kwargs.get('name', None)
        self[name] = Slot(**kwargs)

    def remove_slot(self, name: str) -> None:
        if not name in self:
            raise KeyError(name)
        del self[name]

    def add_command(self, cmd: Callable) -> None:
        """Loading command class
        
        Only for command module
        """

        for method in dir(cmd):
            command = getattr(cmd, method)
            if not isinstance(command, Command):
                continue
            command.parent = cmd
            if command.aliases:
                for alias in command.aliases:
                    # No setter for alias
                    self._alises[alias] = method
            self.update({method: command})

    def remove_command(self, cmd: str) -> None:
        """Removing command class
        
        Only for command module
        """

        if not cmd in self.commands:
            raise KeyError(cmd)
        sys.modules.pop(cmd, None)
        importlib.invalidate_caches()

    def load_command(self, module: str) -> None:
        module = importlib.import_module(module)
        if module in self._command_module:
            return
        self._command_module.update({module.__name__: module})
        module.setup(self)

    def unload_command(self, module: str) -> None:
        if module not in self._command_module:
            raise KeyError(f'Command module {module} does not exists')
        module = self._command_module[module]
        if module.endswith('.base_command'):
            raise KeyError('Unable to unload base command')
        module.teardown(self)

    def reload_command(self, module: str) -> None:
        if module not in self._command_module:
            raise KeyError(f'Command module {module} does not exists')
        self.unload_command(module)
        self.load_command(module)

    @staticmethod
    def _message(msg: str) -> None:
        print(msg)
        input()
        os.system('cls')

    def _start(self) -> None:
        command, args = self._console.get_input()

        if not command in self.commands and not command in self._alises:
            self._message(f'Command {command!r} does not exists')
            return

        cmd = self[command]
        if cmd.scope not in (self._console.scope, UNIVERSAL):
            self._message(f'Command {command!r} does not exists')
            return
        
        if args is not None:
            cmd(self._console, *args)
        else:
            cmd(self._console)
        os.system('cls')

    def start(self) -> None:
        while not self._stop:
            self._start()

    def stop(self) -> None:
        # TODO recheck if need further checks before shutting down
        self._stop = True

    def __getitem__(self, key) -> None:
        if key in self._alises:
            method = self._alises[key]
            return self._commands[method]
        elif key in self._commands:
            return self._commands[key]
        elif key in self._slots:
            return self._slots[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if isinstance(value, Slot):
            if key in self._slots and value == self._slots[key]:
                return
            self._slots[key] = value
        elif isinstance(value, Command):
            if key in self._commands and value == self._commands[key]:
                return
            self._commands[key] = value

    def __delitem__(self, key) -> None:
        if key in self._alises:
            method = self._alises[key]
            reference_aliases = [alias for alias, value in self._alises.items() if value == method]

            del self._commands[method]
            for alias in reference_aliases:
                del self._alises[alias]
        elif key in self._commands:
            del self._commands[key]
        elif key in self._slots:
            del self._slots[key]
        else:
            raise KeyError(key)

    def __iter__(self) -> Iterator:
        return itertools.chain(self._slots, self._commands)

    def __len__(self) -> int:
        return len(self._commands) + len(self._slots)
