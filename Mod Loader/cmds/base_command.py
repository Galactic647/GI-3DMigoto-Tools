import core.container as container
import core.commands as commands

from typing import Optional


class BaseCommand(container.CMDContainer):
    def __init__(self, loader: commands.Loader) -> None:
        self.loader = loader

    @commands.command()
    def create(self, con, slot: str, hidden: Optional[bool] = False) -> None:
        if slot in self.loader:
            con.message(f'Slot {slot} already exists')
            return
        self.loader.add_slot(name=slot, mods=dict())
        con.message(f'Creating slot {slot}')
        con.enter_slot(slot)
    
    @commands.command()
    def switch(self, con, slot: str) -> None:
        pass

    @commands.command()
    def edit(self, con, slot: str) -> None:
        pass

    @commands.command()
    def remove(self, con, slot: str) -> None:
        pass

    @commands.command()
    def reload(self, con, slot: Optional[str] = None) -> None:
        pass

    @commands.command()
    def listslot(self, con) -> None:
        con.message(dir(self))
        con.message(self.__cont_name__)
        con.message(self.__cont_commands__)

    @commands.command()
    def activeslot(self, con) -> None:
        pass

    @commands.command(scope=commands.UNIVERSAL)
    def listcommand(self, con: commands.Console) -> None:
        con.message('\n'.join(self.loader.commands))

    @commands.command(scope=commands.UNIVERSAL)
    def help(self, con, cmd: Optional[str] = None) -> None:
        pass

    @commands.command(scope=commands.UNIVERSAL)
    def usage(self, con, cmd) -> None:
        command = self.loader[cmd]
        con.message(command.usage)

    @commands.command(scope=commands.UNIVERSAL, aliases=('exit', 'terminate', 'close'))
    def stop(self, con, force: Optional[bool] = False) -> None:
        if con.scope == commands.SLOT and not force:
            con.message("Cannot exit while in editing mode, use 'force' to force exit")
            return
        self.loader.stop()


def setup(loader):
    loader.add_command(BaseCommand(loader))


def teardown(loader):
    loader.remove_command(__name__)
