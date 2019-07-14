import json

from elasticsearch import Elasticsearch

from pisces import config


class Indexer:

    def __init__(self):
        self.client = Elasticsearch([config.ELASTICSEARCH['host']])

    def add(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        # TODO: figure out id generation
        # TODO: does this handle updates as well?
        return self.client.index(index=data.get('type'), doc_type=data.get('type'), body=data)

    def delete(self, data):
        # print("Deleting {} from index".format(data))
        return "{} deleted from index".format(data)
