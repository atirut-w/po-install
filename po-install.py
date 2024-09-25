import subprocess
from argparse import ArgumentParser, Namespace
from os import geteuid, path
from subprocess import CalledProcessError
from sys import argv


def main(args: Namespace) -> int:
    try:
        subprocess.run(["msgfmt", "--version"], check=True)
    except FileNotFoundError:
        print("msgfmt not found. Please install gettext.")
        return 1
    
    if not path.isfile(args.file):
        print("File not found.")
        return 1
    elif not path.isdir(f"/usr/share/locale/{args.locale}/LC_MESSAGES"):
        print("Locale not found.")
        return 1
    elif not path.isfile(f"/usr/share/locale/{args.locale}/LC_MESSAGES/{args.app}.mo"):
        print("App not found.")
        return 1
    
    install_path = f"/usr/share/locale/{args.locale}/LC_MESSAGES/{args.app}.mo"
    
    if geteuid() != 0:
        # "Elevate!" - That one Dalek from Doctor Who
        try:
            subprocess.run(["pkexec", "python", __file__, *argv[1:]], check=True)
        except FileNotFoundError:
            print("Unable to elevate privileges. Please manually run as root.")
        except CalledProcessError as e:
            match e.returncode:
                case 126: # Dismissed
                    return 0
                case 127: # Authentication failed
                    print("Authentication failed.")
                    return 1
        return 0
    
    if not path.isfile(f"/usr/share/locale/{args.locale}/LC_MESSAGES/{args.app}.mo.bak"):
        subprocess.run(["cp", install_path, f"{install_path}.bak"], check=True)
    
    try:
        subprocess.run(["msgfmt", "-vc", args.file, "-o", install_path], check=True)
    except CalledProcessError:
        print("Failed to install.")
        subprocess.run(["mv", f"{install_path}.bak", install_path], check=True)
        return 1

    return 0


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("file", help="PO file to install")
    parser.add_argument("app", help="App to install the PO file for")
    parser.add_argument("locale", help="Locale to install the PO file for")

    args = parser.parse_args()
    exit(main(args))
