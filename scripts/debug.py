import os
import platform
import inspect
from . import config

try:
    from colorama import init as colorama_init, Fore, Back, Style
except:
    try:
        from .colorama import init as colorama_init, Fore, Back, Style
    except:
        pass
finally:
    try:
        colorama_init(autoreset=True)
        class colors:
            HEADER = Fore.MAGENTA + Style.BRIGHT
            OKBLUE = Fore.BLUE + Style.BRIGHT
            OKGREEN = Fore.GREEN + Style.BRIGHT
            WARNING = Fore.YELLOW + Style.BRIGHT
            FAIL = Fore.RED + Style.BRIGHT
            RESET = Style.RESET_ALL
            BOLD = Style.BRIGHT
            UNDERLINE = '\033[4m'
    except NameError:
        class colors:
            HEADER = ''
            OKBLUE = ''
            OKGREEN = ''
            WARNING = ''
            FAIL = ''
            RESET = ''
            BOLD = ''
            UNDERLINE = ''
    finally:
        config.debug and print(colors.HEADER + "=== DEBUG ENABLED ===")

def fnCall():
    """
    Prints filename:line:function for parent and grandparent.
    """

    if not config.debug: return

    print(colors.OKGREEN + colors.BOLD + "=== DEBUG === | %s:%d:%s() called from %s:%d:%s()" % (
        inspect.stack()[1][1].split(os.sep)[-1],
        inspect.stack()[1][2],
        inspect.stack()[1][3],
        inspect.stack()[2][1].split(os.sep)[-1],
        inspect.stack()[2][2],
        inspect.stack()[2][3],
        )+colors.RESET)

