import argparse as __argparse
from functools import partial as __partial


def make_parser(
        description,
        formatter_class=__argparse.RawDescriptionHelpFormatter,
        **kwargs
):
    """
    Create an ``ArgumentParser``.

    :param description: Description text displayed before arguments.
                        Usually ``__doc__`` is fine.
    :param formatter_class: Description formatter, defaults to raw.
    :param kwargs: kwargs given to ``ArgumentParser``.
    :return:
    """
    return __argparse.ArgumentParser(
        description=description,
        formatter_class=formatter_class,
        **kwargs,
    )


def __add_argument(parser_pos, *args, **kwargs):
    parser = args[parser_pos]
    args = args[:parser_pos] + args[parser_pos+1:]
    parser.add_argument(*args, **kwargs)


def __make_argument(*args, **kwargs):
    p = __partial(__add_argument, len(args), *args, **kwargs)
    p.__doc__ = \
        """Add the following argument to the given ``ArgumentParser``:

.. code-block::
    parser.add_argument(
        {args},
        {kwargs}
    )


Parameters:
    parser: Call add_argument on this ``ArgumentParser``.
    args: Additional positional arguments for add_argument.
    kwargs: Additional keyword arguments for add_argument.
            Can override keyword arguments specified above.
""".format(args=', '.join(map(repr, args)),
           kwargs='\n        '.join('%s=%r,' % arg for arg in kwargs.items()))
    return p


argument_indir = __make_argument(
    'indir',
    type=str,
    default='.',
    metavar='INDIR',
    help='Directory that contains dataset source files.'
)


argument_outdir = __make_argument(
    '-o', '--outdir',
    type=str,
    default=None,
    metavar='PATH',
    help='Output directory. Defaults to indir.',
)


argument_infile = __make_argument(
        'infile',
        type=str,
        default=None,
        help='Input file.',
)


argument_outfile = __make_argument(
        '-o', '--outfile',
        type=str,
        default=None,
        metavar='PATH',
        help='Output file.',
)


argument_outfiles = __make_argument(
        '-o', '--outfiles',
        type=str,
        default=None,
        metavar='PATH',
        help='Output files.',
        nargs='+'
)


argument_noconfirm = __make_argument(
    '-y', '--no-confirm',
    dest='no_confirm',
    action='store_true',
    help='Don’t require user interaction.',
)


argument_skip_verification = __make_argument(
    '-s', '--skip-verification',
    action='store_true',
    help='Skip verification of source files.'
)
