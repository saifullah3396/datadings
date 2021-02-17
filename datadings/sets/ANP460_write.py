"""
Create ANP460 data set files.

"""
import os
import os.path as pt
import zipfile
import random
import json
from collections import defaultdict

import numpy as np

from ..writer import FileWriter
from . import ANP460Data
from . import ANP460Experiment
from ..tools import document_keys


__doc__ += document_keys(
    ANP460Data,
    postfix=document_keys(
        ANP460Experiment,
        block='',
        prefix='Each experiment has the following keys:'
    )
)


def __lines(s):
    return s.replace('\r', '').split('\n')


def __read(z, p, encoding='utf-8'):
    return z.read(p).decode(encoding)


def __iter_fixpoints(datazip, txt_files, stimuluspath):
    stimulus = pt.basename(stimuluspath)
    for exp in txt_files[stimulus]:
        f = datazip.open(exp)
        yield np.loadtxt(f, dtype=np.float32, delimiter=',')[:, 1:3]


def __get_answers(datazip, txt_files, stimuluspath):
    img = int(pt.basename(stimuluspath).partition(os.extsep)[0])
    answers = []
    for exp in txt_files['answers']:
        _, answer, delay = __lines(__read(datazip, exp))[img].split(',')
        answers.append((answer, float(delay)))
    return answers


def __get_anp_list(datazip):
    json_data = __read(datazip, 'wrangled_data/image_anp_list.json')
    anp_list = json.loads(json_data)
    return anp_list


def write_image(imagezip, datazip, anp_list, txt_files, stimuluspath, writer):
    stimulusdata = imagezip.read(stimuluspath)
    answer = __get_answers(datazip, txt_files, stimuluspath)
    anp, stimulustype = anp_list[pt.basename(stimuluspath)]
    experiments = [
        ANP460Experiment(exp, None, *answer[i])
        for i, exp in enumerate(__iter_fixpoints(datazip, txt_files, stimuluspath))
    ]
    filename = os.sep.join(stimuluspath.split(os.sep)[-2:])
    item = ANP460Data(
        filename,
        stimulusdata,
        experiments,
        anp,
        stimulustype
    )
    writer.write(item)


def __find_all_experiments(datazip):
    mapping = defaultdict(lambda: [])
    for f in datazip.namelist():
        if not f.endswith('.txt'):
            continue
        name = pt.basename(f)
        if name == 'answer.txt':
            mapping['answers'].append(f)
        elif name.endswith('.txt'):
            mapping[name.replace('.txt', '.jpg')].append(f)
    return mapping


def write_sets(indir, outdir, shuffle=True):
    imagepath = pt.join(indir, 'images_original.zip')
    datapath = pt.join(indir, 'wrangled_data.zip')
    with zipfile.ZipFile(imagepath) as imagezip:
        with zipfile.ZipFile(datapath) as datazip:
            anp_list = __get_anp_list(datazip)
            experiments = __find_all_experiments(datazip)
            names = [f for f in imagezip.namelist() if f.endswith('.jpg')]
            if shuffle:
                random.shuffle(names)
            with FileWriter(pt.join(outdir, 'ANP460.msgpack'), total=len(names)) as writer:
                for path in names:
                    write_image(imagezip, datazip, anp_list, experiments, path, writer)


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_indir
    from ..tools.argparse import argument_outdir

    parser = make_parser_simple(__doc__)
    argument_indir(parser)
    argument_outdir(parser)
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
