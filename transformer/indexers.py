import json

from elasticsearch import Elasticsearch


class Indexer:

    def __init__(self):
        self.client = Elasticsearch(['elasticsearch'])

    def add(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        # TODO: figure out id generation
        # TODO: does this handle updates as well?
        print(data)
        return self.client.index(index=data.get('type'), doc_type=data.get('type'), body=data)
        # print("Adding {} to index".format(data))
        # return "{} added to index".format(data)

    def delete(self, data):
        # print("Deleting {} from index".format(data))
        return "{} deleted from index".format(data)
