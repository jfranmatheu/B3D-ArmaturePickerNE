from ._globals import GLOBALS
import pprint


def print_debug(*args) -> None:
    if GLOBALS.IN_DEVELOPMENT:
        print(f'[{GLOBALS.ADDON_MODULE.upper()}]', *args)


def pprint_debug(title: str, d: dict, sort: bool = False) -> None:
    if GLOBALS.IN_DEVELOPMENT:
        print_debug('\n+++', title, '++++++++++++++++++++++++++++++++')
        pprint.pprint(d, indent=4, sort_dicts=sort)
        print_debug('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')


class CM_PrintDebug:
    def __init__(self, title: str) -> None:
        self.use_debug = GLOBALS.IN_DEVELOPMENT
        if self.use_debug:
            print_debug('\n---', title, '----------------------------')

    def __enter__(self):
        def print_indent(msg: str, indent: int = 1, prefix: str = '>'):
            if self.use_debug:
                t_char = '\t'
                print(f"{''.join([t_char for i in range(indent)])}{prefix} {msg}")
        return print_indent

    def __exit__(self, exc_type, exc_value, trace):
        print_debug('----------------------------------------------------------------------------\n')
