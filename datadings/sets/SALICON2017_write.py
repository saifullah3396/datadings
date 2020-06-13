"""Create SALICON 2015 challenge data set files.

The data set is described here:
    http://salicon.net/challenge-2017/

This tool will look for the following files in the input directory
and download them if necessary:
    - image.zip
    - fixations.zip
"""
from . import SALICON2015_write


BASE_URL = 'https://drive.google.com/uc?id='
SALICON2015_write.FILES = {
    'images': {
        'path': 'image.zip',
        'url': BASE_URL+'1g8j-hTT-51IG1UFwP0xTGhLdgIUCW5e5&export=download',
        'md5': 'eb2a1bb706633d1b31fc2e01422c5757',
    },
    'fixations': {
        'path': 'fixations.zip',
        'url': BASE_URL+'0B2hsWbciDVedS1lBZHprdXFoZkU&export=download',
        'md5': '462b70f4f9e8ea446ac628e46cea8d3d',
    }
}


main = SALICON2015_write.main


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
