from core import commands

import importlib

client = commands.Loader()
client.load_command('cmds.base_command')
# for i in client._commands.values():
#     print(dir(i))
client.start()


