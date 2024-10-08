import json
import logging
import datetime
from functools import lru_cache
from importlib import resources

import requests
import pymongo

from mdu.config.scryfall_cfg import OVERRIDES
from mdu.card import Card

API_URL = 'https://api.scryfall.com/bulk-data/default_cards'

class Scryfall:
    def __init__(self, sets=None):
        self._client = pymongo.MongoClient()
        self._cards_en = self._client.scryfall.cards_en
        self._sets = sets # only query for these sets
    
    @staticmethod
    def _fetch_cards():
        bulk_data_result = requests.get(API_URL)
        download_uri = bulk_data_result.json()['download_uri']

        download = requests.get(download_uri)
        cards = download.json()
        
        print('{} pulled'.format(len(cards)))
        return cards

    def _clear_cache(self):
        deleted = self._cards_en.delete_many({})
        print(f'{deleted.deleted_count} cards deleted')
        
    def refresh_cache(self):
        cards = self._fetch_cards()
        self._clear_cache()
        self._cards_en.insert_many(cards)
        self._cards_en.create_index('mtgo_id')
        self._cards_en.create_index('name')
        self._client.scryfall.import_metadata.update_one(
            {}, 
            {   
                '$set': {
                    'as_of': f'{datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds")}Z'
                }
            }, 
            upsert=True
        )

        print(f'{self._cards_en.count_documents({})} cards inserted')
    
    def get_card(self, card_name, set=None):
        card_name = OVERRIDES['names'].get(card_name, card_name)

        base_query = {
            'frame_effects': {'$nin': ['showcase', 'extendedart', 'borderless']},
        }

        if set is not None:
            base_query['set'] = set
        elif self._sets is not None:
            base_query['set'] = {'$in': self._sets}
        else:
            base_query['set_type'] = {'$in': ['draft_innovation', 'expansion', 'commander', 'core', 'starter', 'funny']}

        query = {'name': card_name}
        query.update(base_query)

        card = self._cards_en.find_one(query, sort=[('released_at', pymongo.ASCENDING)])

        if card is None:
            # separate this query since it will make it slower to combine
            query = {            
                'card_faces': {
                    '$elemMatch': {
                        'name': card_name
                    }
                },
            }
            query.update(base_query)

            card = self._cards_en.find_one(query, sort=[('released_at', pymongo.ASCENDING)])

        if card is None:
            query = {
                '$or': [
                    {
                        'name': card_name,
                    },
                    {
                        'card_faces': {
                            '$elemMatch': {
                                'name': card_name
                            }
                        }
                    }
                ],
                'set_type' : {
                    '$ne': 'memorabilia'
                }
            }                

            if set is not None:
                query['set'] = set
            elif self._sets is not None:
                query['set'] = {'$in': self._sets}

            card = self._cards_en.find_one(query, sort=[('released_at', pymongo.ASCENDING), ('collector_number', pymongo.ASCENDING)])

        if card is None:
            error_message = 'No match for card name {}'.format(card_name)
            if set is not None:
                error_message = error_message + ' and set {}'.format(set)
            logging.warning(error_message)
            return Card({'name': card_name})

        return Card(card)
    

    def get_card_by_id(self, mtgo_id):
        cards_en = self._cards_en

        query = {
            '$or': [
                {'mtgo_id': int(mtgo_id)},
                {'mtgo_foil_id': int(mtgo_id)}
            ]
        }

        card = cards_en.find_one(query)

        if card is None:
            error_message = 'No match for card id {}'.format(mtgo_id)
            logging.error(error_message)

        return Card(card)

def cube_attr_line(card_input):
    split = card_input.strip('\n').split('|')
    card_name = split[0].strip()

    if len(split) >= 2:
        set = split[1]
    else:
        set = None
    
    scryfall = Scryfall()

    card = scryfall.get_card(card_name, set=set)
    return card.cube_attr_line

