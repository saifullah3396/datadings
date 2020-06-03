"""Create SALICON 2015 challenge data set files.

The data set is described here:
    http://salicon.net/challenge-2017/

This tool will look for the following files in the input directory
and download them if necessary:
    - image.zip
    - fixations.zip
"""
from . import SALICON2015_write


IMAGE_URL = 'https://drive.google.com/uc?id=1g8j-hTT-51IG1UFwP0xTGhLdgIUCW5e5&export=download'
SALICON2015_write.IMAGE_URL = IMAGE_URL
FIXATIONS_URL = 'https://drive.google.com/uc?id=0B2hsWbciDVedS1lBZHprdXFoZkU&export=download'
SALICON2015_write.FIXATIONS_URL = FIXATIONS_URL


main = SALICON2015_write.main


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
