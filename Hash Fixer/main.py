from core import configparser

from colorama import Fore, Style
import colorama

from typing import Optional
import logging
import regex
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

RESECTION = regex.compile(r'''
    ^
    (Texture|Shader)
    Override
    .*?
    (Cards|FaceHead|VertexLimitRaise|Card[A-C])
    (Diffuse|LightMap|Shadow|ShadowRamp)?
    $
''', regex.VERBOSE | regex.IGNORECASE)


class HashFixer(object):
    config = configparser.GIMIConfigParser()
    mod_config = configparser.GIMIConfigParser(restrict=False, allow_no_header=True)

    def __init__(self, mode: Optional[str] = 'fix') -> None:
        self.mod_folder = None
        self.common_hash = None

        if mode.lower() not in ('fix', 'restore'):
            raise ValueError(f'Unknown mode {mode}')
        self.mode = mode.lower()
        self.load_config()

    @staticmethod
    def load_hash() -> set:
        if not os.path.exists('common_hash.txt'):
            open('common_hash.txt', 'w').close()
            return set()

        with open('common_hash.txt', 'r', encoding='utf-8') as file:
            common_hash = set(line.strip() for line in file.readlines())
            file.close()
        return common_hash

    def create_config(self) -> None:
        self.config.clear()
        logger.info('Creating config.ini')

        self.config.add_section('Path')
        self.config.set('Path', 'mod_folder', self.mod_folder)

        with open('config.ini', 'w', encoding='utf-8') as file:
            self.config.write(file)
            file.close()
        logger.info('config.ini created, please check the config and relaunch the tool')

    def load_config(self) -> None:
        if not os.path.exists('config.ini'):
            logger.error('config.ini not found')
            self.create_config()
            return

        try:
            self.config.read('config.ini')
            self.mod_folder = self.config.get('Path', 'mod_folder')
        except configparser.NoSectionError as e:
            logger.error(f'{e} from config.ini')
            logger.info(f'Recreating config.ini')
            self.create_config()
            return
        except configparser.NoOptionError as e:
            logger.error(f'{e} from config.ini')
            logger.info(f'Recreating config.ini')
            self.create_config()
            return
        logger.info('Config loaded')

    def get_ini_files(self) -> list:
        if not os.path.exists(self.mod_folder):
            logger.error(f'Mod folder not found -> {self.mod_folder}')
            return

        ini_files = glob.glob(f'{self.mod_folder}/**/*.ini', recursive=True)
        return ini_files

    def collect_hash(self) -> list:
        files = self.get_ini_files()
        hashes = []
        old_hashes = self.load_hash()

        for file in files:
            try:
                self.mod_config.clear()
                self.mod_config.read(file)
            except Exception as e:
                logger.error(f'{type(e).__name__} {e.args[0]} while processing file -> {file}')
                continue

            for section in self.mod_config.sections:
                if RESECTION.match(section) is None:
                    continue
                hashes.append(self.mod_config.get(section, 'hash'))
        hashes = set(hash_ for hash_ in hashes if hashes.count(hash_) > 1)
        old_hashes.update(hashes.difference(old_hashes))

        with open('common_hash.txt', 'w', encoding='utf-8') as file:
            file.write('\n'.join(old_hashes))
            file.close()
        return old_hashes

    def process(self, ini: str) -> None:
        self.mod_config.clear()
        ini_name = ini.split('\\')[-1]

        try:
            self.mod_config.read(ini)
        except Exception as e:
            logger.error(f'{type(e).__name__} {e.args[0]} while processing file -> {ini}')
            logger.info(f'Skipping {ini}')
            return

        for section in self.mod_config.sections:
            if not self.mod_config.has_option(section, 'hash') or configparser.identifier_check(section, 'comment'):
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

        with open(ini, 'w', encoding='utf-8') as file:
            self.mod_config.write(file)
            file.close()

    def start(self) -> None:
        try:
            if self.mod_folder is None:
                return
            logger.info('Starting...')
            logger.info('Scanning...')
            ini_files = self.get_ini_files()
            if ini_files is None:
                return

            logger.info('Collecting hashes...')
            self.common_hash = self.collect_hash()
            logger.info(f'Detected {len(ini_files)} ini file(s)')
        except Exception as e:
            logger.error(f'{type(e).__name__} {e.args[0]}')
            return

        for ini in ini_files:
            if 'DISABLED' in ini:
                logger.info(f'Skipping {ini}')
                continue
            logger.info('Checking {0}'.format(ini.split('\\')[-1]))

            try:
                self.process(ini=ini)
            except Exception as e:
                logger.error(f'{type(e).__name__} {e.args[0]} while processing file -> {ini}')
        logger.info('Done!')


def main() -> None:
    mode = input('Mode (fix, restore): ')
    
    try:
        chash = HashFixer(mode=mode)
    except ValueError as e:
        logger.error(e)
        return
    chash.start()


if __name__ == '__main__':
    main()
    input()
