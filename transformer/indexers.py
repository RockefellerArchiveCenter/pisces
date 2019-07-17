import json
import shortuuid

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from pisces import config


class Indexer:

    def __init__(self):
        self.client = Elasticsearch([config.ELASTICSEARCH['host']])

    def generate_id(self):
        return shortuuid.uuid()

    def add(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        identifier = [i['identifier'] for i in data['external_identifiers'] if i['source'] == 'archivesspace'][0]
        s = Search(using=self.client).query('match_phrase', external_identifiers__identifier=identifier)
        response = s.execute()
        if len(response) == 1:
            es_id = response[0].meta.id
        es_id = self.generate_id()
        return self.client.index(index=data.get('type'), doc_type=data.get('type'), id=es_id, body=data)
        # TODO: handle cases where there is more than one hit

    def delete(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        identifier = [i['identifier'] for i in data['external_identifiers'] if i['source'] == 'archivesspace'][0]
        s = Search(using=self.client).query('match_phrase', external_identifiers__identifier=identifier)
        response = s.execute()
        deleted = []
        for hit in response:
            d = self.client.delete(index=data.get('type'), doc_type=data.get('type'), id=hit.meta.id)
            deleted.append(d)
        return deleted
