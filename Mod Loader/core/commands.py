from collections.abc import MutableMapping
from typing import Callable, Iterator
import itertools
import importlib
import inspect
import sys
import os


def _command(func, **attrs):
    predicate = Command(func, **attrs)
    predicate.__is_command__ = True
    predicate.__signature__ = inspect.signature(func)
    return predicate


def command(**attrs):
    def wrapper(func):
        return _command(func, **attrs)
    return wrapper


class Command(object):
    def __init__(self, cmd: Callable, **kwargs) -> None:
        self.name = kwargs.get('name', cmd.__name__)
        if not isinstance(self.name, str):
            raise ValueError('Invalid name')

        self.callback = cmd
        self.module = cmd.__module__
        self.enabled = kwargs.get('enabled', True)
        self.aliases = kwargs.get('aliases', [])
        if not isinstance(self.aliases, (list, tuple, set)):
            raise ValueError('Invalid alias type')

        self.hidden = kwargs.get('hidden', False)
        self.parent = None

    def __call__(self, *args, **kwargs):
        self.callback(self.parent, *args, **kwargs)


class Loader(MutableMapping):
    def __init__(self) -> None:
        self._slots = dict()
        self._commands = dict()
        self._stop = False

    @property
    def slots(self) -> list:
        return list(self._slots)

    @property
    def commands(self) -> list:
        return list(self._commands)

    def add_command(self, cmd: Callable) -> None:
        """Loading command class
        
        Only for command module
        """
        for method in dir(cmd):
            command = getattr(cmd, method)
            if not callable(command) or method.startswith('_'):
                continue
            elif hasattr(command, '__is_command__'):
                command.parent = cmd
                self._commands.update({method: command})

    def remove_command(self, cmd: str) -> None:
        """Removing command class
        
        Only for command module
        """

        if not cmd in self._commands:
            raise KeyError(cmd)
        sys.modules.pop(cmd, None)
        importlib.invalidate_caches()

    def load_command(self, cmd: str) -> None:
        cmd = importlib.import_module(cmd, '..')
        cmd.setup(self)

    def start(self) -> None:
        while not self._stop:
            consolein = input('> ')
            command, *args = consolein.split(' ')
            if not command in self.commands:
                print('No.')
                input()
                os.system('cls')
                continue
            
            self._commands[command](*args)

            os.system('cls')

    def stop(self) -> None:
        self._stop = True

    def __getitem__(self, key) -> None:
        if key in self._commands:
            return self._commands[key]
        elif key in self._slots:
            return self._slots[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if isinstance(value, str):
            pass
        # elif isinstance(value)

    def __delitem__(self, key) -> None:
        if key in self._commands:
            del self._commands[key]
        elif key in self._slots:
            del self._slots[key]
        else:
            raise KeyError(key)

    def __iter__(self) -> Iterator:
        return itertools.chain(self._slots, self._commands)

    def __len__(self) -> int:
        return len(self._commands) + len(self._slots)
