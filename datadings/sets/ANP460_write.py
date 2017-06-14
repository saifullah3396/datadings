"""
Create ANP460 data set files.
"""
from __future__ import print_function, division

import os
import os.path as pt
import zipfile
import random
from collections import defaultdict
import numpy as np

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import ANP460Data
from datadings.sets import ANP460Experiment
import csv
import yaml


with open('/Users/magnus/Downloads/ANP400/image_anp_list.json') as json_data:
    anp_list = yaml.safe_load(json_data)
    anp_list['455.jpg'][0] = 'rough_road'

def __iter_fixpoints(datazip, txt_files, stimuluspath):
    stimulus = stimuluspath.split(os.sep)[1]
    for exp in txt_files[stimulus]:
        csv_data = datazip.read(exp)
        csv_list = list(csv.reader(csv_data.split('\r\n'), delimiter=','))
        points = [np.asarray(map(float, point[0:3])) for point in csv_list]
        yield points

def __get_answer(datazip, txt_files, stimuluspath):
    img = int(stimuluspath.split(os.sep)[1][0:3])
    answer = []
    for exp in txt_files['answer.txt']:
        data = datazip.read(exp).split('\r\n')[img].split(',')[1:]
        answer.append(data)
    return answer

def write_image(imagezip, datazip, txt_files, stimuluspath, writer):
    stimulusdata = imagezip.read(stimuluspath)
    answer = __get_answer(datazip, txt_files, stimuluspath)
    anp, stimulustype = anp_list[stimuluspath.split(os.sep)[1]]
    experiments = [
        ANP460Experiment(exp, None, answer[i])
        for i,exp in enumerate(__iter_fixpoints(datazip, txt_files, stimuluspath))
    ]
    filename = os.sep.join(stimuluspath.split(os.sep)[-2:])
    item = ANP460Data(
        stimulusdata,
        experiments,
        filename,
        anp,
        stimulustype
    )
    writer.write(item)

def __find_all_experiments(datazip):
    csvfiles = []
    for f in datazip.namelist():
        if len(f.split(os.sep)) == 3:
            if f.endswith('.txt') & f.split(os.sep)[2][0:3].isdigit():
                csvfiles.append(f)
            if f.endswith('answer.txt'):
                csvfiles.append(f)
    mapping = defaultdict(lambda: [])
    for csv in csvfiles:
        parts = csv.split(os.sep)
        if (len(parts) == 3) & parts[2][0:3].isdigit():
            mapping[parts[2].split('.')[0] + '.jpg'].append(csv)
        if parts[2] == 'answer.txt':
            mapping[parts[2]].append(csv)
    return mapping


def write_sets(indir, outdir, shuffle=True):
    imagepath = pt.join(indir, 'images_original.zip')
    datapath = pt.join(indir, 'wrangled_data.zip')
    printer = FrequencyPrinter()
    with zipfile.ZipFile(imagepath) as imagezip:
        with zipfile.ZipFile(datapath) as datazip:
            experiments = __find_all_experiments(datazip)
            with FileWriter(pt.join(outdir, 'ANP460.msgpack')) as writer:
                names = [f for f in imagezip.namelist() if f.endswith('.jpg')]
                if shuffle:
                    random.shuffle(names)
                for path in names:
                    write_image(imagezip, datazip, experiments, path, writer)
                    printer.update()
    printer.print_total_updates()


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
        help='directory that contains ANP460 archives'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
