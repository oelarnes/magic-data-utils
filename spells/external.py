"""
download public data sets from 17Lands.com and generate a card
file containing card attributes using MTGJSON
"""

import csv
import gzip
import os
import re
import shutil
import urllib.request
from enum import Enum

from spells import cards
from spells import cache
from spells.enums import View


DATA = "data"
EXTERNAL = "external"

URL_TEMPLATE = (
    "https://17lands-public.s3.amazonaws.com/analysis_data/{dataset_type}_data/"
    + "{dataset_type}_data_public.{set_code}.{event_type}.csv.gz"
)


class EventType(Enum):
    PREMIER = "PremierDraft"
    TRADITIONAL = "TradDraft"


def _external_set_path(set_code):
    return os.path.join(cache.data_dir_path(EXTERNAL), set_code)

def data_file_path(set_code, dataset_type: str, event_type=EventType.PREMIER, zipped=False):
    if dataset_type == "card":
        return os.path.join(_external_set_path(set_code), f"{set_code}_card.csv")

    return os.path.join(
        _external_set_path(set_code),
        f"{set_code}_{event_type.value}_{dataset_type}.csv{'.gz' if zipped else ''}",
    )


def _process_zipped_file(target_path_zipped, target_path):
    with gzip.open(target_path_zipped, 'rb') as f_in:
       with open(target_path, 'wb') as f_out:
           shutil.copyfileobj(f_in, f_out)  

    os.remove(target_path_zipped)


def download_data_set(
    set_code, dataset_type: View, event_type=EventType.PREMIER, force_download=False, clear_set_cache=True
):
    if clear_set_cache:
        cache.clear_cache(set_code)
    target_dir = cache.data_dir_path(EXTERNAL)
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    target_path_zipped = data_file_path(set_code, dataset_type, zipped=True)
    target_path = data_file_path(set_code, dataset_type)

    if os.path.isfile(target_path) and not force_download:
        print("file %(target_path) already exists, rerun with force_download=True, flag -f, or command refresh to download")
        return

    urllib.request.urlretrieve(
        URL_TEMPLATE.format(
            set_code=set_code, dataset_type=dataset_type, event_type=event_type.value
        ),
        target_path_zipped,
    )

    _process_zipped_file(target_path_zipped, target_path)

def write_card_file(draft_set_code: str):
    """
    Write a csv containing basic information about draftable cards, such as rarity,
    set symbol, color, mana cost, and type.
    """
    draft_filepath = data_file_path(draft_set_code, View.DRAFT)

    if not os.path.isfile(draft_filepath):
        print(f"No draft file for set {draft_set_code}")

    with open(draft_filepath, encoding="utf-8") as f:
        columns = csv.DictReader(f).fieldnames

    if columns is None:
        raise ValueError("no columns found!")

    pattern = "^pack_card_"
    names = (re.split(pattern, name)[1] for name in columns if re.search(pattern, name) is not None)

    csv_lines = cards.card_file_lines(draft_set_code, names)

    card_filepath = data_file_path(draft_set_code, View.CARD)

    with open(card_filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in csv_lines:
            writer.writerow(row)

    print(f"Wrote {len(csv_lines)} lines to file {card_filepath}")
