from colorama import Fore, Style
import colorama

from typing import Optional, Union
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


class CHashFix(object):
    config = configparser.ConfigParser()
    mod_config = configparser.ConfigParser()

    def __init__(self, mode: Optional[str] = 'fix') -> None:
        self.mod_folder = None
        self.common_hash = None
        self.mode = mode.lower()

    def load_hash(self) -> Union[list, None]:
        if not os.path.exists('common_hash.txt'):
            logger.error('common_hash.txt not found')
            return

        with open('common_hash.txt', 'r') as file:
            common_hash = [line.strip() for line in file.readlines()]
            file.close()
        logger.info('Hashes loaded')
        return common_hash

    def get_ini_files(self) -> Union[list, None]:
        if not os.path.exists('config.ini'):
            logger.error('config.ini not found')
            return

        self.config.read('config.ini')
        self.mod_folder = self.config.get('Path', 'mod_folder')
        logger.info('Config loaded')

        if not os.path.exists(self.mod_folder):
            logger.error(f'Mod folder not found -> {self.mod_folder}')
            return

        logger.info('Scanning...')
        ini_files = glob.glob(f'{self.mod_folder}/**/*.ini', recursive=True)
        logger.info(f'Detected {len(ini_files)} ini file(s)')
        return ini_files

    def remove_duplicate(self, ini: str) -> None:
        # There might be a better way to do this but I choose this because of safer option
        filtered_data = dict()
        formatted = list()
        section = None

        logger.info(f'Removing duplicates for file -> {ini}')
        with open(ini, 'r') as file:
            data = [line.strip() for line in file.readlines()]
            file.close()

        for line in data:
            if line.startswith(';') or not line:
                continue
            elif line.startswith('[') and line in filtered_data:
                continue
            elif line.startswith('[') and line not in filtered_data:
                section = line
                filtered_data[section] = dict()
                continue

            key, value = [item.strip() for item in line.split('=')]
            if key not in filtered_data[section]:
                filtered_data[section][key] = value

        for key, value in filtered_data.items():
            formatted.append(key)
            for item_key, item_value in value.items():
                formatted.append(f'{item_key} = {item_value}')
            formatted.append('')
        
        with open(ini, 'w') as file:
            file.write('\n'.join(formatted))
            file.close()
        logger.info('Duplicates removed!')

    def process(self, ini: str) -> None:
        self.mod_config.clear()
        self.mod_config.read(ini)
        ini_name = ini.split('\\')[-1]

        for section in self.mod_config.sections():
            if not self.mod_config.has_option(section, 'hash'):
                continue

            hash_ = self.mod_config.get(section, 'hash')
            has_match_priority = self.mod_config.has_option(section, 'match_priority')

            if hash_ in self.common_hash and not has_match_priority and self.mode == 'fix':
                self.mod_config.set(section, 'match_priority', '0')
                logger.info(f"Config {ini_name}: adding option 'match_priority' to section -> {section}")

            elif hash_ in self.common_hash and has_match_priority and self.mode == 'restore':
                self.mod_config.remove_option(section, 'match_priority')
                logger.info(f"Config {ini_name}: deleting 'match_priority' from section -> {section}")

        with open(ini, 'w') as file:
            self.mod_config.write(file)
            file.close()

    def start(self) -> None:
        try:
            logger.info('Starting...')
            self.common_hash = self.load_hash()
            ini_files = self.get_ini_files()

            if ini_files is None:
                return
        except Exception as e:
            logger.error(e)
            return

        for ini in ini_files:
            logger.info('Checking {0}'.format(ini.split('\\')[-1]))

            if 'DISABLED' in ini or 'merged' in ini:
                logger.info(f'Skipping {ini}')

            try:
                self.process(ini=ini)
            except configparser.DuplicateSectionError as e:
                logger.info(e)
                self.remove_duplicate(ini=ini)
                self.process(ini=ini)
            except configparser.DuplicateOptionError as e:
                logger.info(e)
                self.remove_duplicate(ini=ini)
                self.process(ini=ini)
            except Exception as e:
                logger.error(e)
        logger.info('Done!')


def main() -> None:
    mode = input('Mode (fix, restore): ')
    if (mode := mode.lower()) not in ('fix', 'restore'):
        logger.error(f'Unknown mode {mode}')
        return
    chash = CHashFix(mode=mode)
    chash.start()


if __name__ == '__main__':
    main()
    input()
