import random
from pathlib import Path
import zipfile
import pickle

from datadings.writer import FileWriter


ROOT = Path(__file__).parent / 'data'
PICKLE_PATH = ROOT / 'test_dataset.pkl'
ZIP_PATH = ROOT / 'test_dataset.zip'
MSGPACK_PATH = ROOT / 'test_dataset.msgpack'
DIRECTORY_PATH = ROOT / 'test_dataset'


def make_key(i):
    return f'sample_{i}.txt'


def make_data(i, sample_size=50*1024):
    return (i % 255).to_bytes(1, 'little') * sample_size


def create_samples(number=10101, labels=10):
    for i in range(number):
        label = random.randrange(labels)
        yield {
            'key': make_key(i),
            'data': make_data(i),
            'label': 'label_%d' % label,
            'label_index': label,
        }


def create_dataset():
    samples = list(create_samples())
    keys = [sample['key'] for sample in samples]
    # pickle original
    with PICKLE_PATH.open('wb') as f:
        pickle.dump((keys, samples), f)

    z = zipfile.ZipFile(ZIP_PATH, 'w')
    w = FileWriter(MSGPACK_PATH, overwrite=True)
    with z, w:
        for sample in samples:
            p = Path(sample['label'], sample['key'])
            # directory
            (DIRECTORY_PATH / p).parent.mkdir(parents=True, exist_ok=True)
            with (DIRECTORY_PATH / p).open('wb') as f:
                f.write(sample['data'])
            # ZIP file
            z.writestr(str(p), sample['data'])
            # msgpack
            sample['label'] = sample.pop('label_index')
            w.write(sample)
    return keys, samples


def load_dataset():
    if PICKLE_PATH.exists():
        with PICKLE_PATH.open('rb') as f:
            return pickle.load(f)
    else:
        return create_dataset()


KEYS, SAMPLES = load_dataset()
