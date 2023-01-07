import core.container as container
import core.commands as commands


class BaseSlotCommand(container.CMDContainer, scope=commands.SLOT):
    def __init__(self, loader: commands.Loader) -> None:
        self.loader = loader

    @commands.command()
    def add_mod(self, con, name: str) -> None:
        pass

    @commands.command()
    def remove_mod(self, con, name: str) -> None:
        pass

    @commands.command()
    def exitedit(self, con) -> None:
        # TODO Add check if current slot is modified or not before exit
        # TODO Auto delete if slot is new and empty
        con.exit_slot()


def setup(loader: commands.Loader):
    loader.add_command(BaseSlotCommand(loader))


def teardown(loader: commands.Loader):
    loader.remove_command(__name__)
