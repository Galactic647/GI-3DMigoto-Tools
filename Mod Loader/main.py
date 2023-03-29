from core import parser

from typing import Union, Optional, Iterator
from collections.abc import MutableMapping
import pathlib
import regex
import glob
import json
import os

BASIC = 0
MERGED = 1


def convert_size(size: float, size_type: int, *, place: Optional[int] = 2):
    size_types = {'0': '',
                  '1': 'K',
                  '2': 'M',
                  '3': 'G',
                  '4': 'T'}
    while size >= 1024:
        if size_type >= 4:
            break
        size_type += 1
        size /= 1024
    return f'{round(size, place)}{size_types[str(size_type)]}B'


def get_size(path: str) -> int:
    size = 0
    if os.path.isfile(path):
        size += os.path.getsize(path)
    else:
        files = glob.glob(f'{path}/**/*.*', recursive=True)
        size += sum(map(os.path.getsize, files))
    return size


class BasicMod(object):
    def __init__(self, path: Union[str, pathlib.Path]) -> None:
        self.path = path
        if isinstance(path, str):
            self.path = pathlib.Path(path)
        if self.path.name.endswith('.ini'):
            self.path = self.path.parent
        self.name = self.path.name
        self.size = get_size(self.path)

        # False flags since one of the config might be disabled/enabled
        self.active = 0
        self.configs = []
        self.get_configs()

    def get_configs(self) -> None:
        configs = glob.glob(f'{self.path}\\**\\*.ini', recursive=True)
        self.configs = [pathlib.Path(config) for config in configs]

    def activate(self):
        self.active = 1
        for config in self.configs:
            if 'disabled' not in config.name.lower():
                continue
            filename = regex.sub('^DISABLED', '', config.name, flags=regex.IGNORECASE)
            config.rename(f'{config.parent}\\{filename}')

    def deactivate(self) -> None:
        self.active = 0
        for config in self.configs:
            if 'disabled' in config.name.lower():
                continue
            config.rename(f'{config.parent}\\DISABLED{config.name}')
    
    def __repr__(self) -> str:
        return f'{__class__.__name__}({self.name})'

    __str__ = __repr__


class MergedMod(MutableMapping):
    def __init__(self, path: Union[str, pathlib.Path], childs: Optional[dict] = None) -> None:
        self.path = path
        if isinstance(path, str):
            self.path = pathlib.Path(path)
        
        self.size = get_size(self.path.parent)
        self.name = self.path.parts[-2]

        self.active = 1
        if 'disabled' in self.path.name.lower():
            self.active = 0

        self._childs = dict()
        if childs is not None:
            self._childs = childs
        self.swap_key = self.get_key()

    @property
    def childs(self) -> list:
        return list(self)

    def get_key(self) -> str:
        config = parser.ModConfigParser()
        config.read(str(self.path))
        return config.get('KeySwap', 'key')

    def add_child(self, mod: BasicMod):
        self.update({mod.name: mod})

    def add_child_by_path(self, path: Union[str, pathlib.Path]):
        self.add_child(BasicMod(path))

    def activate(self) -> None:
        for _, mod in self.items():
            mod.deactivate()
        
        if 'disabled' not in self.path.name.lower():
            return
        filename = regex.sub('^DISABLED', '', self.path.name, flags=regex.IGNORECASE)
        self.path.rename(f'{self.path.parent}\\{filename}')
    
    def deactivate(self) -> None:
        for _, mod in self.items():
            mod.deactivate()
        
        if 'disabled' in self.path.name.lower():
            return
        self.path.rename(f'{self.path.parent}\\DISABLED{self.path.name}')

    def bypass_active(self, mod: str) -> None:
        if mod not in self:
            raise KeyError
        
        for name, mobj in self.items():
            if name == mod:
                self[mod].activate()
                continue
            mobj.deactivate()

    def __setitem__(self, key, value) -> None:
        if key in self._childs and value == self._childs[key]:
            return
        self._childs[key] = value

    def __getitem__(self, key) -> BasicMod:
        if key in self._childs:
            return self._childs[key]
        raise KeyError(key)
    
    def __delitem__(self, key) -> None:
        if key in self._childs:
            del self._childs[key]
        raise KeyError(key)
    
    def __iter__(self) -> Iterator:
        return iter(self._childs)
    
    def __len__(self) -> int:
        return len(self._childs)

    def __repr__(self) -> str:
        return f'{__class__.__name__}({", ".join(self.childs)})'

    __str__ = __repr__


class ModLoader(object):
    config = parser.ModConfigParser()
    mod_config = parser.ModConfigParser(restrict=False)

    def __init__(self) -> None:
        self.migoto_path = None
        self.mod_folder = None
        self.migoto_auto_launch = False
        self.mods = dict()

    def load_config(self) -> None:
        if not os.path.exists('config.ini'):
            self.config.add_section('General')
            self.config.add_section('3DMigoto')

            self.config.set('General', 'auto_clear', json.dumps(True))
            self.config.set('General', 'auto_delete_empty_slot', json.dumps(True))

            section = self.config.get('3DMigoto', only_value=False)
            section.add_comment('if path is not specified auto_launch will be ignored')
            self.config.set('3DMigoto', '3dm_path')
            self.config.set('3DMigoto', 'auto_launch', json.dumps(False))

            with open('config.ini', 'w') as file:
                self.config.write(file)
                file.close()
            return

        self.config.read('config.ini')
        self.migoto_path = self.config.get('3DMigoto', '3dm_path')
        if not os.path.exists(self.migoto_path):
            raise FileNotFoundError('Unable to find 3DMigoto path')
        self.mod_folder = f'{self.migoto_path}\\Mods'
        if not os.path.exists(self.migoto_path):
            raise FileNotFoundError('Unable to find Mods path')
        self.migoto_auto_launch = self.config.get('3DMigoto', 'auto_launch')

    def load_slots(self) -> None:
        pass

    def scan_mods(self) -> None:
        mods = glob.glob(f'{self.mod_folder}/**/*.ini', recursive=True)
        mods = map(pathlib.Path, mods)

        lastmod = None
        parindex = None
        curmerged = None

        for file in mods:
            parent = file.parts[-2]

            if file.name == 'merged.ini':
                parindex = len(file.parts) - 2
                curmerged = MergedMod(file)
                self.mods.update({curmerged.name: curmerged})
                continue

            if curmerged is None:
                if lastmod is not None and parent == lastmod:
                    continue
                lastmod = parent
                mod = BasicMod(file)
                self.mods.update({mod.name: mod})
            else:
                if file.parts[parindex] != curmerged.name:
                    curmerged = parindex = None
                    lastmod = parent
                    mod = BasicMod(file)
                    self.mods.update({mod.name: mod})
                    continue

                if lastmod is None or parent != lastmod:
                    lastmod = parent
                    curmerged.add_child_by_path(file)
                    

def main():
    pass


if __name__ == '__main__':
    main()