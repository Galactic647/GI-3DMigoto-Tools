# 3DMigoto mods outline setter
# Original code by silent (https://github.com/SilentNightSound/GI-Model-Importer/blob/main/Tools/genshin_set_outlines.py)


from colorama import Fore, Style
import colorama

from typing import Union
import configparser
import logging
import glob
import os

colorama.init()


class CustomFormatter(logging.Formatter):
    magenta = Fore.LIGHTMAGENTA_EX
    light_red = Fore.LIGHTRED_EX
    yellow = Fore.YELLOW
    green = Fore.GREEN
    red = Fore.RED
    reset = Fore.RESET

    format_ = f'[{{0}}%(levelname)s{Style.RESET_ALL}] [%(filename)s:%(lineno)s] %(message)s'

    FORMATS = {
        logging.DEBUG: format_.format(magenta),
        logging.INFO: format_.format(green),
        logging.WARNING: format_.format(yellow),
        logging.ERROR: format_.format(light_red),
        logging.CRITICAL: format_.format(red)
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.Logger(__name__)
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(CustomFormatter())

logger.addHandler(stream_handler)


def get_file(type_: str) -> Union[str, list, None]:
    files = None
    type_ = type_.lower()

    search = ''
    if os.path.exists('merged.ini'):
        search = '**/'

    if type_ == 'texcoord':
        files = glob.glob(f'{search}*Texcoord.buf', recursive=False)
    elif type_ == 'ini':
        files = glob.glob(f'{search}*.ini', recursive=False)

    if not files:
        logger.error(f'Unable to find {type_} file')
        return
    elif len(files) > 1 and not search:
        logger.error(f'More than one {type_} file detected')
        return
    elif search:
        seen = set()
        dupes = list()

        for path, _ in map(os.path.split, files):
            if path in seen:
                dupes.append(path)
            else:
                seen.add(path)
        
        if dupes:
            for dupe in dupes:
                logger.error(f'More than one {type_} file detected in {dupe}')
            return

    if search:
        for file in files:
            logger.info(f'{type_} file detected -> {file}')
        return files
    logger.info(f'{type_} file detected -> {files[0]}')
    return files[0]


def start(thickness: int, ini: str, texcoord: str) -> None:
    config = configparser.ConfigParser()
    try:
        config.read(ini)
        stride = int(config.get('Resource{0}'.format(texcoord.split('\\')[-1][:-4]), 'stride'))
        logger.info(f'Stride: {stride}')
    except Exception as e:
        logger.error(e)
        return

    with open(texcoord, 'rb+') as file:
        logger.info('Starting...')
        data = bytearray(file.read())

        for index in range(0, len(data), stride):
            data[index + 3] = thickness
        
        logger.info('Saving...')
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()


def main() -> None:
    try:
        thickness = input('Set outline thickness (0-255): ')
        thickness = int(thickness)
    except ValueError:
        logger.error(f'Invalid thickness value of {thickness}')
        return
    if thickness < 0 or thickness > 255:
        logger.error(f'Invalid thickness of {thickness}, choose between 0 and 255')
        return
    logger.info(f'Thickness set: {thickness}')
        
    # Separated if statement to avoid confusing log output
    ini = get_file('ini')
    if ini is None:
        return
        
    texcoord = get_file('texcoord')
    if texcoord is None:
        return
    
    if isinstance(ini, str):
        start(thickness, ini, texcoord)
    elif isinstance(ini, list):
        for i, t in zip(ini, texcoord):
            logger.info(f'Processing {t}')
            start(thickness, i, t)
    logger.info('Done!')


if __name__ == '__main__':
    main()
    input()
