from colorama import Fore, Style
import colorama

from typing import Optional, Union
import configparser
import requests
import logging
import glob
import json
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
COMMON_HASH_SRC = r'https://raw.githubusercontent.com/Galactic647/GI-3DMigoto-Tools/master/Hash%20Fixer/common_hash.txt'


class CHashFix(object):
    config = configparser.ConfigParser()
    mod_config = configparser.ConfigParser()

    def __init__(self, mode: Optional[str] = 'fix') -> None:
        self.mod_folder = None
        self.hash_auto_update = False
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

    def load_config(self) -> Union[list, None]:
        if not os.path.exists('config.ini'):
            logger.error('config.ini not found')
            logger.info('Creating config.ini')

            self.config.add_section('Path')
            self.config.set('Path', 'mod_folder', None)

            self.config.add_section('Hash Auto Update')
            self.config.set('Hash Auto Update', 'enabled', json.dumps(False))

            with open('config.ini', 'w') as file:
                self.config.write(file)
                file.close()
            logger.info('config.ini created, please set the path and relaunch the tool')
            return

        self.config.read('config.ini')
        self.mod_folder = self.config.get('Path', 'mod_folder')

        try:
            self.hash_auto_update = json.loads(self.config.get('Hash Auto Update', 'enabled'))
        except configparser.NoSectionError:
            self.config.set('Hash Auto Update', 'enabled', json.dumps(False))
            with open('config.ini', 'w') as file:
                self.config.write(file)
                file.close()
                
            self.hash_auto_update = False
        logger.info('Config loaded')

    def get_ini_files(self):
        self.load_config()
        if not os.path.exists(self.mod_folder):
            logger.error(f'Mod folder not found -> {self.mod_folder}')
            return

        if self.hash_auto_update:
            self.update_hash()

        logger.info('Scanning...')
        ini_files = glob.glob(f'{self.mod_folder}/**/*.ini', recursive=True)
        logger.info(f'Detected {len(ini_files)} ini file(s)')
        return ini_files

    def update_hash(self) -> None:
        logger.info('Checking source...')
        response = requests.get(COMMON_HASH_SRC)
        if response.status_code != 200:
            logger.error(f'Unable to auto update hash with response code {response.status_code}')
            return
        else:
            check_hash = {hash_ for hash_ in response.text.split('\n') if hash_}
            with open('common_hash.txt', 'r') as file:
                current_hash = {line.strip() for line in file.readlines() if line.strip()}
                file.close()
            
            current_hash.update(check_hash.difference(current_hash))

            with open('common_hash.txt', 'w') as file:
                file.write('\n'.join(current_hash))
        logger.info('common_hash.txt updated')

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
        ini_name = ini.split('\\')[-1]

        try:
            self.mod_config.read(ini)
        except configparser.DuplicateSectionError as e:
            logger.error(e)
            self.remove_duplicate(ini)
        except configparser.DuplicateOptionError as e:
            logger.error(e)
            self.remove_duplicate(ini)
        except Exception as e:
            logger.error(f'Unexpected error {e}')
            logger.info(f'Skipping {ini}')
            return

        try:
            self.mod_config.read(ini)
        except configparser.DuplicateSectionError as e:
            logger.error('Unable to solve error')
            logger.info(f'Skipping {ini}')
            return
        except configparser.DuplicateOptionError as e:
            logger.error('Unable to solve error')
            logger.info(f'Skipping {ini}')
            return
        except Exception as e:
            logger.error(f'Unexpected error {e}')
            logger.info(f'Skipping {ini}')
            return

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

            if 'DISABLED' in ini or 'merged.ini' in ini:
                logger.info(f'Skipping {ini}')
                continue

            self.process(ini=ini)
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
