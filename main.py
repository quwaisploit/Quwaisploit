from core.console import QuwaisploitConsole
from core.program.version import *
from core.banner import *

if __name__ == '__main__':
    try:
        console = QuwaisploitConsole()
        console.start()
    except KeyboardInterrupt:
        print("\nExiting...")
