#!/usr/bin/env python3
import logging
import subprocess
from argparse import ArgumentParser, Namespace
from os import geteuid, path
from shutil import copyfile, move
from subprocess import DEVNULL, CalledProcessError
from sys import argv


def main(args: Namespace) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        subprocess.run(["msgfmt", "--version"], check=True, stdout=DEVNULL)
    except FileNotFoundError:
        logging.error("msgfmt not found. Please install gettext.")
        return 1
    
    locale_dir = path.join("/usr/share/locale", args.locale, "LC_MESSAGES")
    install_path = path.join(locale_dir, f"{args.app}.mo")
    backup_path = f"{install_path}.bak"

    if not path.isfile(args.file):
        logging.error("File not found.")
        return 1
    elif not path.isdir(locale_dir):
        logging.error("Locale not found.")
        return 1
    elif not path.isfile(install_path):
        logging.error("App not found.")
        return 1

    if geteuid() != 0:
        # "Elevate!" - That one Dalek from Doctor Who
        try:
            subprocess.run(["pkexec", argv[0], *argv[1:]], check=True, stdout=DEVNULL, stderr=DEVNULL)
        except FileNotFoundError:
            try:
                subprocess.run(["sudo", argv[0], *argv[1:]], check=True)
            except FileNotFoundError:
                logging.error("Unable to elevate privileges. Please manually run as root.")
                return 1
            except CalledProcessError:
                return 1
        except CalledProcessError as e:
            match e.returncode:
                case 126:  # Dismissed
                    logging.info("Authentication dismissed.")
                    return 0
                case 127:  # Authentication failed
                    logging.error("Authentication failed.")
                    return 1
        return 0

    if not path.isfile(backup_path):
        copyfile(install_path, backup_path)

    try:
        subprocess.run(["msgfmt", "-vc", args.file, "-o", install_path], check=True)
    except CalledProcessError:
        logging.error("Failed to install.")
        move(backup_path, install_path)
        return 1

    return 0


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("file", help="PO file to install")
    parser.add_argument("app", help="App to install the PO file for")
    parser.add_argument("locale", help="Locale to install the PO file for")

    args = parser.parse_args()
    exit(main(args))
