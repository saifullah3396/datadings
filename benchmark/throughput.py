import sys
import time
import json
import multiprocessing as mp
from statistics import mean
from statistics import stdev

from datadings.reader import MsgpackReader
from datadings.reader import ZipFileReader
from datadings.reader import DirectoryReader


def bench(infile, raw, type_):
    if type_ == 'msgpack':
        r = MsgpackReader(infile)
    elif type_ == 'zip':
        r = ZipFileReader(infile)
    elif type_ == 'dir':
        r = DirectoryReader((infile,))
    else:
        raise ValueError('unknown reader type %r' % type_)
    n = 0
    read_bytes = 0
    a = time.time()
    if raw:
        for sample in r.rawiter():
            n += 1
            read_bytes += len(sample)
    else:
        for sample in r:
            n += 1
            read_bytes += sys.getsizeof(sample) \
                       + sum(sys.getsizeof(v) for v in sample.values)
    d = time.time() - a
    s = n / d
    b = read_bytes / d / 1024 / 1024
    return n, d, s, b


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
        nargs='+',
        help='number of processes to run parallel',
    )
    parser.add_argument(
        '--type',
        default='msgpack',
        choices=('msgpack', 'zip', 'dir'),
        type=str
    )
    parser.add_argument(
        '-o', '--output',
        default='throughput_results.json',
        type=str
    )
    args, unknown = parser.parse_known_args()
    results = {
        'infile': args.infile,
        'raw': args.raw,
        'type': args.type,
        'replicas': {}
    }
    for n in args.replicas:
        print(f'Starting {n} processes')
        pool = mp.Pool(n, maxtasksperchild=1)
        kw = {
            'infile': args.infile,
            'raw': args.raw,
            'type_': args.type
        }
        times = pool.map(bench, [kw]*n)
        num, delta, speed, throughput = zip(*times)
        results['replicas'][n] = {
            'num': num,
            'delta': delta,
            'speed': speed,
            'throughput': throughput
        }
        if not all([n == max(num) for n in num]):
            raise RuntimeError('Processes read unequal number of samples: '
                               f'{", ".join(num)}')
        if n > 1:
            print(f'{max(num)} samples read '
                  f'in {mean(delta):.2f} (± {stdev(delta):.2f}) seconds, '
                  f'{mean(speed):.2f} (± {stdev(speed):.2f}) samples/s, '
                  f'{mean(throughput):.2f} (± {stdev(throughput):.2f}) MB/s')
        else:
            print(f'{max(num)} samples read '
                  f'in {mean(delta):.2f} seconds, '
                  f'{mean(speed):.2f} samples/s, '
                  f'{mean(throughput):.2f} MB/s')
    with open(args.output, 'w') as f:
        json.dump(results, f)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
