from typing import Optional


class ConsoleColors:
    """
    https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
    """

    OFF = 0
    
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    PURPLE = 5
    CYAN = 6
    WHITE = 7

    # need to put this somewhere
    CLEAR = "\033[H\033[J"

    @classmethod
    def escape(
            cls,
            fore: Optional[int] = None,
            back: Optional[int] = None,
            bright: bool = True,
    ):
        args = []
        if fore:
            args.append(fore + (90 if bright else 30))
        if back:
            args.append(back + (100 if bright else 40))

        if not (fore or back):
            args.append(0)

        return "\033[%sm" % ";".join(str(a) for a in args)


def print_colors(file=None):
    for bright in (False, True):
        for fg in range(8):
            for bg in range(8):
                print(ConsoleColors.escape(fg, bg, bright) + f" {fg:2},{bg:2} ", end="", file=file)
            print(ConsoleColors.escape(), file=file)
        print(file=file)


if __name__ == "__main__":
    print_colors()
