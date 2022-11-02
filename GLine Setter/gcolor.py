# 3DMigoto mods color setter
# Forcibly sets the COLOR of a texcoord output to a certain value
# Original code by silent (https://github.com/SilentNightSound/GI-Model-Importer/blob/main/Tools/genshin_set_color.py)


from colorama import Fore, Style
import colorama

from typing import Union
import configparser
import logging
import glob

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


def get_file(type_: str) -> Union[str, None]:
    files = None
    type_ = type_.lower()

    if type_ == 'texcoord':
        files = glob.glob('*Texcoord.buf', recursive=False)
    elif type_ == 'ini':
        files = glob.glob('*.ini', recursive=False)

    if not files:
        logger.error(f'Unable to find {type_} file')
        return
    elif len(files) > 1:
        logger.error(f'More than one {type_} file detected')
        return

    logger.info(f'{type_} file detected -> {files[0]}')
    return files[0]


def main() -> None:
    config = configparser.ConfigParser()
    colors = {
        'R': None,
        'G': None,
        'B': None,
        'A': None
    }
    texcoord = get_file('texcoord')
    ini = get_file('ini')

    if ini is None or texcoord is None:
        return

    try:
        config.read(ini)
        stride = int(config.get(f'Resource{texcoord[:-4]}', 'stride'))
        logger.info(f'Stride: {stride}')
    except Exception as e:
        logger.error(e)

    for color in colors:
        value = input(f'{color} color value (0 - 255, Default none): ')
        
        if not value or value.lower() == 'none':
            colors[color] = None
        else:
            try:
                value = int(value)
            except ValueError:
                logger.error(f'Invalid value of {value} for color {color}')
                return

            if value < 0 or value > 255:
                logger.error('Value must be between 0 and 255')
                return
            
            colors[color] = value

    for color, value in colors.items():
        logger.info(f'Set color {color} value: {value}')

    with open(texcoord, 'rb+') as file:
        logger.info('Setting Color Values...')
        data = bytearray(file.read())

        for index in range(0, len(data), stride):
            for offset, value in enumerate(colors.values()):
                if value is not None:
                    data[index + offset] = value
        
        logger.info('Saving...')
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()
    logger.info('Done!')


if __name__ == '__main__':
    main()
    input()
