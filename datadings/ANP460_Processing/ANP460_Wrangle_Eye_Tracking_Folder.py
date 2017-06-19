from __future__ import print_function, division

import os
import os.path as pt
import zipfile


def wrangle_dataset(indir, outdir):
    datapath = os.path.join(indir, 'eye_tracking_data.zip')
    targetpath = os.path.join(outdir, 'ANP460_data.zip')
    with zipfile.ZipFile(datapath) as datazip:
        # get directories / names
        participant_dirs = [x.split(os.sep)[1] for x in datazip.namelist() if x.endswith(
            '/') & (len(x.split(os.sep)) == 3)]
        participant_dirs.sort()
        # include json containing classes
        with zipfile.ZipFile(targetpath, 'w', compression=zipfile.ZIP_DEFLATED) as targetzip:
            targetzip.write(pt.join(indir, 'image_anp_list.json'), 'image_anp_list.json')
            for p, participant_dir in enumerate(participant_dirs):
                print('participant', p+1)
                answer = datazip.read(pt.join(
                    'eye_tracking_data',
                    participant_dir,
                    'answer.txt'
                ))
                targetzip.writestr(pt.join('p%02d' % p, 'answers.txt'), answer)
                for i in range(460):
                    sample = datazip.read(pt.join(
                        'eye_tracking_data',
                        participant_dir,
                        'sample%d.txt' % (i+1)
                    ))
                    targetzip.writestr(pt.join('p%02d' % p, '%03d.txt' % i), sample)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        default='.',
        help='directory that contains MIT1003 archives'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    wrangle_dataset(args.indir, outdir)


if __name__ == '__main__':
    main()
