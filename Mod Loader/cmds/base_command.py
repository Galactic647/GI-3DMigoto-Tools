from typing import Optional
import importlib

commands = importlib.import_module('core.commands', '..')
container = importlib.import_module('core.container', '..')


class BaseCommand(object):
    def __init__(self, loader: commands.Loader) -> None:
        self.loader = loader

    @commands.command()
    def create(self, slot: str) -> None:
        pass
    
    @commands.command()
    def switch(self, slot: str) -> None:
        pass

    @commands.command()
    def edit(self, slot: str) -> None:
        pass

    @commands.command()
    def remove(self, slot: str) -> None:
        pass

    @commands.command()
    def reload(self, slot: Optional[str] = None) -> None:
        pass

    @commands.command()
    def listslot(self) -> None:
        pass

    @commands.command()
    def activeslot(self) -> None:
        pass

    @commands.command()
    def reloadcmd(self) -> None:
        pass

    @commands.command()
    def help(self, cmd: Optional[str] = None) -> None:
        pass

    @commands.command()
    def stop(self) -> None:
        self.loader.stop()


def setup(loader):
    loader.add_command(BaseCommand(loader))


def teardown(loader):
    loader.remove_command(__name__)
