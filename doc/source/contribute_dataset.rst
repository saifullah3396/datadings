.. _contributing-dataset:

Contributing a dataset
======================

To contribute a new dataset to datadings, please follow the steps
below and create a
`merge request <https://gitlab.com/jfolz/datadings/-/merge_requests/new>`_
in our Gitlab repository.

Each dataset defines modules to read and write in the
:py:mod:`datadings.sets` package.
Typically the read module contains additional meta-data
that is common for all samples, like class labels or
distributions.
The convention is that for a dataset called ``FOO``,
these modules are called ``FOO`` and ``FOO_write``.



Metadata
--------

Small amounts of data or data that is not available for download
should be added to datadings directly.
Examples for this are class labels/distributions/weights/colors,
file lists, etc.
Anything more than a 1 kiB should be included as
`zopfli <https://github.com/google/zopfli>`_ or xz compressed text,
JSON or msgpack files to reduce the size of the repository and
distributed wheels.
zopfli may give slightly better compression for very small files,
while xz is vastly superior for larger files.
Keep in mind that higher xz levels can require considerable amounts
of memory for decompression.
This shell script will try ``gzip -9``, ``zopfli`` (if available),
and all ``xz`` levels 0 to 9e and report file size and
memory used (kiB) for decompression::

    #!/bin/bash
    set -e

    echo -e "comp\tmemory\tsize"
    bytes=$(stat -c %s "$FILE")
    echo -e "none\t-\t$bytes"

    gzip -9 -k -f "$FILE"
    bytes=$(ls -l "$FILE.gz" | cut -d " " -f 5)
    mem=$( 2>&1 /usr/bin/time -f "%M" gunzip -f -k "$FILE.gz")
    echo -e "gzip -9\t$mem\t$bytes"

    if command -v zopfli &> /dev/null; then
        zopfli -k -f "$FILE"
        bytes=$(ls -l "$FILE.gz" | cut -d " " -f 5)
        mem=$( 2>&1 /usr/bin/time -f "%M" gunzip -f -k "$FILE.gz")
        echo -e "zopfli\t$mem\t$bytes"
    fi

    for LEVEL in 0 0e 1 1e 2 2e 3 3e 4 4e 5 5e 6 6e 7 7e 8 8e 9 9e; do
        xz -$LEVEL -k -f "$FILE"
        bytes=$(ls -l "$FILE.xz" | cut -d " " -f 5)
        mem=$( 2>&1 /usr/bin/time -f "%M" unxz -f -k "$FILE.xz")
        echo -e "xz -$LEVEL\t$mem\t$bytes"
    done

For example here's the sorted output for ``ILSVRC2012_val.txt``::

    $ FILE=ILSVRC2012_val.txt ./testcomp.sh | sort -n -t $'\t' -k 3
    comp    memory  size
    xz -6   5068    123436
    xz -7   4616    123436
    xz -8   5140    123436
    xz -9   3824    123436
    xz -0e  2652    123540
    xz -1e  3432    123540
    xz -2e  4020    123540
    xz -4e  4496    123540
    xz -6e  5576    123540
    xz -7e  5760    123540
    xz -8e  6008    123540
    xz -9e  5092    123540
    xz -3e  4388    123680
    xz -5e  4012    123680
    xz -5   4320    125460
    xz -2   3952    166608
    xz -3   4016    167436
    xz -1   3224    167828
    xz -0   2720    168588
    xz -4   3796    168924
    zopfli  3120    201604
    gzip -9 3292    229789
    none    -       1644500

Surprisingly ``xz -0e`` is the clear winner here, giving excellent
compression ratio with very low memory requirements.



Read module
-----------

Add a module called ``FOO`` to the :py:mod:`datadings.sets`
package and add/load available meta-data, if any.
With less complex datasets this module may be empty,
but should be added anyway.



More complex datasets
^^^^^^^^^^^^^^^^^^^^^

For some datasets it simply does not make sense to convert them
to the datadings file format.
Typically conversion requires (at least temporarily) roughly twice
the space as the original data.
Other examples are be large video files that should really be
streamed while decoding instead of loading all of the data at once,
which datadings does not yet support.
For these and similar cases it (at least currently) does not make
sense to use the datadings msgpack format with the
:py:class:`MsgpackReader <datadings.reader.msgpack.MsgpackReader>`.
Instead, we recommend the ``FOO`` module provide a ``FOOReader``
class that extends :py:class:`datadings.reader.Reader` or one of its
subclasses.
An effort should be made to reduce processing times.
The ``FOOReader`` should read directly from the source files of the
dataset and perform limited pre-processing.
This slow process of analyzing every image was performed offline
to speed up subsequent iterations of the dataset.



Write module
------------

Now add another module called ``FOO_write``.
This will be an executable that writes dataset files.
There are generally four steps to the writing process:

- Argument parsing.
- Download and verify source files.
- Locate and load sample data.
- Convert and write samples to dataset.

If you prefer to learn from code, the
:py:mod:`CAT2000_write <datadings.sets.CAT2000_write>` module
is a relatively simple, yet full-featured example.



Argument parsing
^^^^^^^^^^^^^^^^

Scripts typically lean heavily on the :py:mod:`datadings.argparse`
module to parse command line arguments.
It provides utility functions like
:py:mod:`make_parser <datadings.argparse.make_parser>` to create
argument parsers with sensible default settings and a lot of commonly
used arguments already added.
For example, most datasets need an ``indir`` argument, where source
files are located, as well as an optional ``outdir`` argument, which
is where the dataset files will be written.
The :py:mod:`datadings.argparse` module also provides functions to
add a lesser-used arguments in a single line, including descriptive
help text.
By convention a function called ``argument_indir`` adds the ``indir``
argument to the given parser, including additional configuration and
help text.

For a simple dataset with no additional arguments, a main function
might begin like this::

    def main():
        from ..argparse import make_parser
        from ..argparse import argument_threads
        from ..tools import prepare_indir

        parser = make_parser(__doc__)
        argument_threads(parser)
        args = parser.parse_args()
        outdir = args.outdir or args.indir



Download and verify
^^^^^^^^^^^^^^^^^^^

If possible, datadings should download source files.
This is not possible for all datasets, because data might only be
available on request or after registration.
If that is the case, add a description to the docstring on how to
download the data.
Manual pre-processing steps, like unpacking archives, should be
avoided if at all possible.
The only exception to this rule is if Python is ill-equipped to
handle the source file format, e.g., some unusual compression scheme
like 7zip.

If downloading is possible, datadings provides some convenient tools
to do so.
First, define which files are required in a global variable called
``FILES``, for example for the Pascal VOC 2012 dataset::

    BASE_URL = 'http://saliency.mit.edu/'
    FILES = {
        'train': {
            'path': 'trainSet.zip',
            'url': BASE_URL+'trainSet.zip',
            'md5': '56ad5c77e6c8f72ed9ef2901628d6e48',
        },
        'test': {
            'path': 'testSet.zip',
            'url': BASE_URL+'testSet.zip',
            'md5': '903ec668df2e5a8470aef9d8654e7985',
        }
    }

Our example defines ``"train"`` and ``"test"`` files, with a relative
path, a URL to download them from and and MD5 hash to verify their
integrity.
The verification step is especially important, since we want to
support the reuse of previously downloaded files.
So we need to make sure that the file we are using is actually
what we expect to find.

This dictionary of file definitions can now be given to helper
functions from the :py:mod:`datadings.tools` module.
Most convenient is
:py:func:`prepare_indir <datadings.tools.prepare_indir>`, which
first attempts to download (if URL is given) and verify each file.
If successful, it then returns a dict where all paths are replaced
with the true location of each file.

Our main function now looks like this::

    def main():
        from ..argparse import make_parser
        from ..argparse import argument_threads
        from ..tools import prepare_indir

        parser = make_parser(__doc__)
        argument_threads(parser)
        args = parser.parse_args()
        outdir = args.outdir or args.indir

        files = prepare_indir(FILES, args)



Locate, load, and write data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These steps heavily depend on the structure of the dataset and this
guide can only provide general guidelines.
We recommended to first define a generator, which loads and yields
one sample at a time::

    def yield_samples(stuff):
        samples = []  # find samples in stuff
        for sample in samples:
            # load data from source file
            yield SampleType(data, metadata, etc)

Instead of returning individual values it is recommended to use one
of the provided type functions from :py:mod:`datadings.sets.types`.
New types can be added if none of them fits your dataset.
Type functions are generated by the ``generate_types.py`` script from
the definitions in  ``generate_types.json``.

The generator is used by a ``write_set`` function, which is called
once per split of the dataset.
Here, create a :py:class:`FileWriter <datadings.writer.FileWriter>`
with the desired output path and pass samples to it::

    def write_set(split, stuff, outdir, args):
        gen = yield_samples(stuff)
        outfile = pt.join(outdir, split + '.msgpack')
        writer = FileWriter(outfile, total=num_samples, overwrite=args.no_confirm)
        with writer:
            for sample in gen:
                writer.write(sample)


.. important::
    Samples must have a unique ``"key"``.
    An exception will be raised if keys are repeated.

.. note::
    If the ``overwrite`` parameter of the writer is ``False``, the
    user will be prompted to overwrite an existing file.
    The user can now:

    - Accept to overwrite the file.
    - Decline, which raises a :py:class:`FileExistsError`.
      The program should continue as if writing had finished.
    - Abort, which raises a :py:class:`KeyboardInterrupt`.
      The program should abort immediately.

    The default argument parser accepts a ``no_confirm`` argument,
    which is passed to the ``overwrite`` parameter.

The final function ``write_sets`` will call ``write_set`` once per
split of the dataset::

    def write_sets(files, outdir, args):
        for split in ('train', 'test'):
            try:
                write_set(split, files[split]['path'], outdir)
            except FileExistsError:
                continue
            except KeyboardInterrupt:
                break

.. note::
    We catch the :py:class:`FileExistsError` and
    :py:class:`KeyboardInterrupt`, which may be raised by the writer.

The final main function now looks like this.
We call ``write_sets`` and wrap the main function itself to catch
keyboard interrupts by the user::

    def main():
        from ..argparse import make_parser
        from ..tools import prepare_indir

        parser = make_parser(__doc__)
        args = parser.parse_args()
        outdir = args.outdir or args.indir

        files = prepare_indir(FILES, args)

        write_sets(files, outdir, args)


    if __name__ == '__main__':
        try:
            main()
        except KeyboardInterrupt:
            pass
        finally:
            print()



Writing faster
--------------

Since datadings is all about speed and convenience, which are
high related when it comes to writing datasets, you may want to
optimize your program to increase the write speed.
Two relatively simple optimizations are recommended to speed up the
process.

First, the generator can be wrapped with the
:py:func:`datadings.tools.yield_threaded` function, which runs the
generator in a background thread.
This effectively decouples filesystem read and write operations,
but does not help if the CPU is the bottleneck.

In those cases where the bottleneck is neither reading nor writing,
but a costly conversion (e.g., transcoding images), a thread or
process pool can be used to parallelize this step::

    def write_set(split, stuff, outdir, args):
        gen = yield_threaded(yield_samples(stuff))

        def costly_conversion(sample):
            # do something that you want parallelized
            return sample

        outfile = pt.join(outdir, split + '.msgpack')
        writer = FileWriter(outfile, total=num_samples, overwrite=args.no_confirm)
        pool = ThreadPool(args.threads)
        with writer:
            for sample in pool.imap_unordered(create_sample, gen):
                writer.write(sample)

.. note::
    Add :py:func:`datadings.tools.argument_threads` to the parser to
    allow users to control the number of threads.

.. note::
    :py:meth:`imap_unordered <multiprocessing.pool.Pool.imap_unordered>`
    makes no guarantees about the order of the returned samples.
    If the order is important, consider using a different method
    like :py:meth:`imap <multiprocessing.pool.Pool.imap>`.
    Beware though that this may use substantially more memory, as
    samples are stored in memory until they can be returned in the
    correct order.
