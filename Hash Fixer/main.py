from core import parser

from colorama import Fore, Style
import colorama

from typing import Optional, Union
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
    config = parser.ModConfigParser()
    mod_config = parser.ModConfigParser()

    def __init__(self, mode: Optional[str] = 'fix') -> None:
        self.mod_folder = None
        self.common_hash = None

        if mode.lower() not in ('fix', 'restore'):
            raise ValueError(f'Unknown mode {mode}')
        self.mode = mode.lower()
        self.load_config()

    @staticmethod
    def load_hash() -> Union[list, None]:
        if not os.path.exists('common_hash.txt'):
            logger.error('common_hash.txt not found')
            return

        with open('common_hash.txt', 'r') as file:
            common_hash = [line.strip() for line in file.readlines()]
            file.close()
        logger.info('Hashes loaded')
        return common_hash

    def create_config(self) -> None:
        self.config.clear()
        logger.info('Creating config.ini')

        self.config.add_section('Path')
        self.config.set('Path', 'mod_folder', '')

        with open('config.ini', 'w') as file:
            self.config.write(file)
            file.close()
        logger.info('config.ini created, please set the path and relaunch the tool')

    def load_config(self) -> None:
        if not os.path.exists('config.ini'):
            logger.error('config.ini not found')
            self.create_config()
            return

        try:
            self.config.read('config.ini')
            self.mod_folder = self.config.get('Path', 'mod_folder')
        except parser.NoSectionError:
            logger.error(f'Section missing from config.ini')
            logger.info(f'Recreating config.ini')

            self.create_config()
            return
        logger.info('Config loaded')

    def get_ini_files(self) -> list:
        if not os.path.exists(self.mod_folder):
            logger.error(f'Mod folder not found -> {self.mod_folder}')
            return

        logger.info('Scanning...')
        ini_files = glob.glob(f'{self.mod_folder}/**/*.ini', recursive=True)
        logger.info(f'Detected {len(ini_files)} ini file(s)')
        return ini_files

    def process(self, ini: str) -> None:
        self.mod_config.clear()
        ini_name = ini.split('\\')[-1]

        try:
            self.mod_config.read(ini)
        except Exception as e:
            logger.error(f'Unexpected error {e}')
            logger.info(f'Skipping {ini}')
            return

        for section in self.mod_config:
            if not self.mod_config.has_option(section, 'hash') or section.startswith('comment-'):
                continue

            hash_ = self.mod_config.get(section, 'hash')
            if not hash_ in self.common_hash:
                continue

            has_match_priority = self.mod_config.has_option(section, 'match_priority')
            has_allow_duplicate = self.mod_config.has_option(section, 'allow_duplicate_hash')

            if 'shaderoverride' in section.lower():
                if not has_allow_duplicate and self.mode == 'fix':
                    self.mod_config.set(section, 'allow_duplicate_hash', 'true')
                    logger.info(f"Config {ini_name}: adding option 'allow_duplicate_hash' to section -> {section}")

                elif has_allow_duplicate and self.mode == 'restore':
                    self.mod_config.remove_option(section, 'allow_duplicate_hash')
                    logger.info(f"Config {ini_name}: deleting 'allow_duplicate_hash' from section -> {section}")
            else:
                if not has_match_priority and self.mode == 'fix':
                    self.mod_config.set(section, 'match_priority', '0')
                    logger.info(f"Config {ini_name}: adding option 'match_priority' to section -> {section}")

                elif has_match_priority and self.mode == 'restore':
                    self.mod_config.remove_option(section, 'match_priority')
                    logger.info(f"Config {ini_name}: deleting 'match_priority' from section -> {section}")

        with open(ini, 'w') as file:
            self.mod_config.write(file)
            file.close()

    def start(self) -> None:
        try:
            if self.mod_folder is None:
                return
            logger.info('Starting...')
            self.common_hash = self.load_hash()
            ini_files = self.get_ini_files()

            if ini_files is None:
                return
        except Exception as e:
            logger.error(f'Unexpected error {e}')
            return

        for ini in ini_files:
            if 'DISABLED' in ini:
                logger.info(f'Skipping {ini}')
                continue
            logger.info('Checking {0}'.format(ini.split('\\')[-1]))

            try:
                self.process(ini=ini)
            except Exception as e:
                logger.error(f'Unexpected error {e}')
        logger.info('Done!')


def main() -> None:
    mode = input('Mode (fix, restore): ')
    
    try:
        chash = CHashFix(mode=mode)
    except ValueError as e:
        logger.error(e)
        return
    chash.start()


if __name__ == '__main__':
    main()
    input()
