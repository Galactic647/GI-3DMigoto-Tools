from collections.abc import MutableMapping
from typing import Callable, Iterator
import itertools
import importlib
import inspect
import sys
import os


def command(**attrs):
    def wrapper(func):
        predicate = Command(func, **attrs)
        predicate.__signature__ = inspect.signature(func)
        return predicate
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

        # parent is added when adding command to loader
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
            if not isinstance(command, Command):
                continue
            command.parent = cmd
            self.update({method: command})

    def remove_command(self, cmd: str) -> None:
        """Removing command class
        
        Only for command module
        """

        if not cmd in self.commands:
            raise KeyError(cmd)
        sys.modules.pop(cmd, None)
        importlib.invalidate_caches()

    def load_command(self, cmd: str) -> None:
        cmd = importlib.import_module(cmd, '..')
        cmd.setup(self)

    @staticmethod
    def _message(msg: str) -> None:
        print(msg)
        input()
        os.system('cls')

    @staticmethod
    def _digest_arguments(args) -> list:
        return [arg.strip() for arg in args.split('"') if arg.strip()]

    def _start(self) -> None:
        command = None
        args = None
        consolein = input('> ').strip()

        if not len(consolein.split(' ')) == 1:
            command, args = consolein.split(' ', maxsplit=1)
            args = self._digest_arguments(args)
        else:
            command = consolein

        if not command in self.commands:
            self._message(f'Command {command!r} does not exists')
            return
        
        if args is not None:
            self[command](*args)
        else:
            self[command]()
        os.system('cls')

    def start(self) -> None:
        while not self._stop:
            self._start()

    def stop(self) -> None:
        # TODO recheck if need further checks before shutting down
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
            if key in self._slots and value == self._slots[key]:
                return
            self._slots[key] = value
        elif isinstance(value, Command):
            if key in self._commands and value == self._commands[key]:
                return
            self._commands[key] = value

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
