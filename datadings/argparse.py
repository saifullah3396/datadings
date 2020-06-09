import argparse
from functools import partial
from multiprocessing import cpu_count


def make_parser(
        description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    return argparse.ArgumentParser(
        description=description,
        formatter_class=formatter_class,
        **kwargs,
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


argument_calculate_weights = __make_argument(
    '--calculate-weights',
    action='store_true',
    help='Calculate median-frequency class weights.'
)


class ThreadAction(argparse.Action):
    max_threads = None

    def __call__(self, parser, namespace, threads, option_string=None):
        threads = max(1, threads or self.max_threads)
        threads = min(threads, self.max_threads)
        setattr(namespace, self.dest, threads)


def argument_threads(parser, default=1, max_threads=0):
    """
    Add threads argument to parser.

    :param parser: Argument is added here.
    :param default: Default number of threads.
    :param max_threads: Maximum number of threads.
                        If >0, use given number.
                        If 0 use ``cpu_count()``.
                        if <0, use ``-max_threads*cpu_count()``
    """
    if max_threads < 0:
        cpus = cpu_count() * -max_threads
    else:
        cpus = max_threads or cpu_count()

    class MaxThreadAction(ThreadAction):
        max_threads = cpus

    default = min(default, cpus)
    parser.add_argument(
        '-t', '--threads',
        default=default,
        metavar='0-%d' % cpus,
        type=int,
        action=MaxThreadAction,
        help='Number of threads for conversion. '
             '0 uses all available CPUs (default %d).' % default
    )
