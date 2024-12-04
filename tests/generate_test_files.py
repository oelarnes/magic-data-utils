import os

import polars as pl

from spells import external
from . import TEST_SET_CODE, TEST_DATA_HOME

NUM_TEST_DRAFTS = 10

def __main__():
    source_path_draft = external.data_file_path(TEST_SET_CODE, 'draft')
    source_path_game = external.data_file_path(TEST_SET_CODE, 'game')
    source_path_card = external.data_file_path(TEST_SET_CODE, 'card')

    os.environ['SPELLS_DATA_HOME'] = TEST_DATA_HOME

