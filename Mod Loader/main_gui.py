from core import parser
import appui

from typing import Optional, Union, Iterator
from collections.abc import MutableMapping
import pathlib
import glob
import json
import sys
import os


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


class Mod(object):
    MERGED = 'merged'
    NORMAL = 'normal'

    def __init__(self, type_: str, path: Union[str, pathlib.Path], *, is_child: Optional[bool] = False) -> None:
        self.type_ = type_
        self.is_child = is_child
        if self.type_ not in (self.MERGED, self.NORMAL):
            raise ValueError(type_)

        if isinstance(path, str):
            self.path = pathlib.Path(path)
        else:
            self.path = path

        if not is_child:
            self.name = self.path.parts[self.path.parts.index('Mods') + 1]
        else:
            self.name = self.path.parts[-2]
        self.size = os.path.getsize(path)
        self.key = self.get_key()
        self.children_mods = dict()

    def add_child(self, mod) -> None:
        self.children_mods.update({mod.name: mod})

    def get_key(self) -> str:
        # config = parser.ModConfigParser()
        # config.read(str(self.path))
        # TODO check for KeySwap
        return 'yeet'

    def __repr__(self):
        if self.is_child:
            return self.name
        return f'{self.name}({self.children_mods})'


class ModContainer(MutableMapping):
    def __init__(self) -> None:
        self._mods = dict()

    @property
    def mods(self) -> list:
        return list(self._mods)

    def digest(self, path: Union[str, pathlib.Path]) -> None:
        mods = glob.glob(f'{path}/**/*.ini', recursive=True)
        mods = [pathlib.Path(mod) for mod in mods]

        parent = None  # None or Mod
        curpar = None  # None or pathlib.Path
        for mod in mods:
            par_index = mod.parts.index('Mods') + 1

            if mod.parts[par_index] == curpar:
                if not parent.type_ == Mod.MERGED:
                    parent.type_ = Mod.MERGED
                child = Mod(Mod.NORMAL, mod, is_child=True)
                parent.add_child(child)
            else:
                curpar = mod.parts[par_index]
                parent = Mod(Mod.NORMAL, mod)
                self.update({parent.name: parent})

    def __setitem__(self, key, value) -> None:
        if key in self._mods and value == self._mods[key]:
            return
        self._mods[key] = value

    def __getitem__(self, key):
        if key in self._mods:
            return self._mods[key]
        raise KeyError(key)

    def __delitem__(self, key) -> None:
        if key in self._mods:
            del self._mods[key]
        raise KeyError(key)

    def __iter__(self) -> Iterator:
        return iter(self._mods)

    def __len__(self) -> int:
        return len(self._mods)


class ModLoader(appui.ModLoaderUI):
    config = parser.ModConfigParser()
    mod_config = parser.ModConfigParser()

    MOD_TYPE = ('normal', 'merged')

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.migoto_path = None
        self.mod_folder = None
        self.migoto_auto_launch = False

        # self.load_config()

    def load_config(self) -> None:
        if not os.path.exists('config.ini'):
            self.config.add_section('General')
            self.config.add_section('3DMigoto')

            self.config.set('General', 'auto_clear', json.dumps(True))
            self.config.set('General', 'auto_delete_empty_slot', json.dumps(True))

            section = self.config.get('3DMigoto', only_value=False)
            section.add_comment('; if path is not specified auto_launch becomes irrelevant')
            self.config.set('3DMigoto', '3dm_path', '')
            self.config.set('3DMigoto', 'auto_launch', json.dumps(False))

            with open('config.ini', 'w') as file:
                self.config.write(file)
                file.close()
            return

        self.config.read('config.ini')
        self.migoto_path = self.config.get('3DMigoto', '3dm_path')
        if not os.path.exists(self.migoto_path):
            raise FileNotFoundError('Unable to find path')
        self.mod_folder = f'{self.migoto_path}\\Mods'
        self.migoto_auto_launch = self.config.get('3DMigoto', 'auto_launch')

    def load_slots(self) -> None:
        pass

    def load_data(self) -> None:
        pass

    def set_mod_info(self, type_: str, size: Union[int, str], key: Optional[str] = None) -> None:
        if isinstance(size, int):
            size = convert_size(size, 0)
        elif type_.lower() not in self.MOD_TYPE:
            raise ValueError('Invalid type')

        if key is None:
            key = 'None'
        self.mod_type.setText(type_.capitalize())
        self.mod_size.setText(size)
        self.mod_key.setText(key.capitalize())


def main():
    app = appui.QApplication()
    window = ModLoader()
    window.show()
    sys.exit(app.exec_())
    # container = ModContainer()
    # container.digest(window.mod_folder)
    # print('\n'.join(map(str, container._mods.items())))


if __name__ == '__main__':
    main()
