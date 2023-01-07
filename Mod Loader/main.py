from core import commands
import os

client = commands.Loader()

for module in os.listdir('cmds'):
    if module.startswith('_'):
        continue
    elif os.path.isdir(module):
        continue
    client.load_command(f'cmds.{module[:-3]}')
client.start()


