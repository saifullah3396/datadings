"""A number of useful tools are installed with datadings.
These will be accessible on the command line as ``datadings-*``
where ``*`` is replaced with one of the submodule names,

The main tool to interact with datadings in this way is
:py:mod:`datadings-write <datadings.commands.write>`.
It finds available datasets and runs their writing scripts.

These are the available tools:

- :py:mod:`datadings-write <datadings.commands.write>`
  creates new dataset files.
- :py:mod:`datadings-cat <datadings.commands.cat>`
  prints the (abbreviated) contents of a dataset file.
- :py:mod:`datadings-shuffle <datadings.commands.shuffle>`
  shuffles an existing dataset file.
- :py:mod:`datadings-merge <datadings.commands.merge>`
  merges two or more dataset files.
- :py:mod:`datadings-split <datadings.commands.split>`
  splits a dataset file into two or more subsets.
- :py:mod:`datadings-bench <datadings.commands.bench>`
  runs some basic read performance benchmarks.

You can either call them directly or run them as modules
with ``python -m datadings.commands.*``, again with star
replaced by the name the command, e.g., ``write``.
"""
