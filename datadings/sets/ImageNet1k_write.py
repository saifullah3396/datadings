from . import ILSVRC2012_write
from .ILSVRC2012_write import *


__doc__ = ILSVRC2012_write.__doc__


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
