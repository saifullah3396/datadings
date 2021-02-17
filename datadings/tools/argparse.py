"""
A collection of useful helper functions to create argument parsers.
Using pre-defined arguments ensures that arguments are consistent
across different tools in datadings.

All helper functions in this module follow the convention that a
function called ``argument_indir`` adds the ``indir`` argument to
the given parser, including additional configuration and help text.

Note:
    Any of the default arguments given by the ``argument_*``
    functions can be overwritten.
    For example, ``argument_shuffle`` defines
    ``choices = ['yes', 'no']``.
    If those are too formal for your liking, you can also use
    ``argument_shuffle(parser, choices=['yeah', 'naw']``.
    But please don't.
"""

import argparse
from functools import partial
from multiprocessing import cpu_count


class YesNoAction(argparse.Action):
    """
    Action like ``store_true`` that checks if ``value == yes``.
    """
    def __call__(self, parser, namespace, yesno, option_string=None):
        setattr(namespace, self.dest, yesno == 'yes')


class MinMaxAction(argparse.Action):
    """
    Action to clamp value between given min and max values.
    Create subclass to set ``min_value`` and ``max_value``::

        class Action(MinMaxAction):
            min_value = 1
            max_value = 7

        parser.add_argument('onetoseven', action=Action)
    """
    min_value = None
    max_value = None

    def __call__(self, parser, namespace, value, option_string=None):
        value = max(self.min_value, value or self.max_value)
        value = min(value, self.max_value)
        setattr(namespace, self.dest, value)


def make_parser(
        description,
        indir=True,
        outdir=True,
        no_confirm=True,
        skip_verification=True,
        shuffle=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        **kwargs
) -> argparse.ArgumentParser:
    """
    Create an ``ArgumentParser`` with a set of common arguments.

    Parameters:
        description: Description text displayed before arguments.
                     Usually ``__doc__`` is fine.
        indir: If True, add ``indir`` argument.
        outdir: If True, add ``outdir`` argument.
        no_confirm: If True, add ``no_confirm`` argument.
        skip_verification: If True, add ``skip_verification`` argument.
        shuffle: If True, add ``shuffle`` argument.
        formatter_class: Description formatter, defaults to raw.
        kwargs: kwargs given to ``ArgumentParser``.

    Returns:
        ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=formatter_class,
        **kwargs,
    )
    if indir:
        argument_indir(parser)
    if outdir:
        argument_outdir(parser)
    if no_confirm:
        argument_no_confirm(parser)
    if skip_verification:
        argument_skip_verification(parser)
    if shuffle:
        argument_shuffle(parser)
    return parser


def make_parser_simple(
        description,
        indir=False,
        outdir=False,
        no_confirm=False,
        skip_verification=False,
        shuffle=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        **kwargs
) -> argparse.ArgumentParser:
    """
    Same as :py:func:`make_parser`, but add no arguments by default.
    """
    return make_parser(
        description,
        indir=indir,
        outdir=outdir,
        no_confirm=no_confirm,
        skip_verification=skip_verification,
        shuffle=shuffle,
        formatter_class=formatter_class,
        **kwargs
    )


def __add_argument(parser_pos, *args, **kwargs):
    parser = args[parser_pos]
    args = args[:parser_pos] + args[parser_pos+1:]
    parser.add_argument(*args, **kwargs)


def __make_argument(*args, **kwargs):
    p = partial(__add_argument, len(args), *args, **kwargs)
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


argument_outfile_positional = __make_argument(
        'outfile',
        type=str,
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


argument_no_confirm = __make_argument(
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


argument_shuffle = __make_argument(
    '--shuffle',
    default='yes',
    choices=['yes', 'no'],
    action=YesNoAction,
    help='Write samples in random order. (default: yes)'
)


argument_calculate_weights = __make_argument(
    '--calculate-weights',
    action='store_true',
    help='Calculate median-frequency class weights.'
)


def argument_threads(parser, default=1, max_threads=0):
    """
    Add threads argument to parser.

    Parameters:
        parser: Argument is added here.
        default: Default number of threads.
        max_threads: Maximum number of threads.
                     If >0, use given number.
                     If 0 use ``cpu_count()``.
                     if <0, use ``-max_threads*cpu_count()``
    """
    if max_threads < 0:
        cpus = cpu_count() * -max_threads
    else:
        cpus = max_threads or cpu_count()

    class Action(MinMaxAction):
        min_value = 1
        max_value = cpus

    default = min(default, cpus)
    parser.add_argument(
        '-t', '--threads',
        default=default,
        metavar='0-%d' % cpus,
        type=int,
        action=Action,
        help='Number of threads for conversion. '
             '0 uses all available CPUs (default %d).' % default
    )
