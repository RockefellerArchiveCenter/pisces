import json

from elasticsearch import Elasticsearch

from pisces import config


class Indexer:

    def __init__(self):
        self.client = Elasticsearch([config.ELASTICSEARCH['host']])

    def add(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        # TODO: get id from external id, if none exists create a new one
        return self.client.index(index=data.get('type'), doc_type=data.get('type'), body=data)

    def delete(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        return True
        # return self.client.delete(index=data.get('type'), doc_type=data.get('type'), id='1')
