import time
import os.path as pt
import multiprocessing as mp

from datadings.reader import MsgpackReader


def bench(infile, raw):
    r = MsgpackReader(infile)
    n = 0
    a = time.time()
    if raw:
        for _ in r.rawiter():
            n += 1
    else:
        for _ in r:
            n += 1
    d = time.time() - a
    s = n / d
    b = pt.getsize(infile) / d / 1024 / 1024
    print('%s samples read in %.2f seconds, %.2f samples/s, %.2f MB/s'
          % (n, d, s, b), end='')


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'infile',
        help='file to benchmark'
    )
    parser.add_argument(
        '-r', '--raw',
        help='do not deserialize samples',
        action='store_true'
    )
    parser.add_argument(
        '--replicas',
        default=1,
        type=int,
        help='number of processes to run parallel',
    )
    args, unknown = parser.parse_known_args()
    print('Starting %d processes' % args.replicas)
    procs = [mp.Process(target=bench, args=(args.infile, args.raw))
             for _ in range(args.replicas)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
