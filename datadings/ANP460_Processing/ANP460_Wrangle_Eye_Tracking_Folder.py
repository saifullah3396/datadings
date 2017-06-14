import os
import zipfile
import shutil

# We still need anp json file.

def make_dir(indir):
    writepath = os.path.join(indir, 'wrangled_data')
    if not os.path.exists(writepath):
        os.mkdir(writepath)
    anonym = ['p'+str(i) for i in range(60)]
    for dir in anonym:
        if not os.path.exists(os.path.join(writepath, dir)):
            os.mkdir(os.path.join(writepath, dir))

def wrangle_dataset(indir):
    datapath = os.path.join(indir, 'eye_tracking_data.zip')
    writepath = os.path.join(indir, 'wrangled_data')
    with zipfile.ZipFile(datapath) as datazip:
        # get directories / names
        participant_dir = [x.split(os.sep)[1] for x in datazip.namelist() if x.endswith(
            '/') & (len(x.split(os.sep)) == 3)]
        for f in datazip.namelist():
            if f.endswith('.txt') & (len(f.split(os.sep)) == 3):
                if (len(f.split(os.sep)[2]) <= 13):
                    if (f.split(os.sep)[2][0:6] == 'sample'):
                        parts = f.split(os.sep)
                        num = str(int(filter(str.isdigit, parts[2])) - 1).zfill(
                            3) + '.txt'
                        index = 'p' + str(participant_dir.index(parts[1]))
                        targetpath = os.path.join(writepath, index, num)
                        shutil.copy2(os.path.join(indir, f), targetpath)
                    if (f.split(os.sep)[2][0:6] == 'answer'):
                        parts = f.split(os.sep)
                        index = 'p' + str(participant_dir.index(parts[1]))
                        targetpath = os.path.join(writepath, index, 'answer.txt')
                        shutil.copy2(os.path.join(indir, f), targetpath)

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
    make_dir(outdir)
    wrangle_dataset(outdir)

if __name__ == '__main__':
    main()