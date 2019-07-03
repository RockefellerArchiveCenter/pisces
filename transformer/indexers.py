from elasticsearch import Elasticsearch


class Indexer:

    def __init__(self):
        self.client = Elasticsearch()

    def add_single(self, data):
        print(data)
        # TODO: figure out id generation
        # TODO: does this handle updates as well?
        # return self.client.index(index=data.get('type'), doc_type=data.get('type'), id=data['uri'].split('/')[-1], body=data)
        return "{} added to index".format(data.get('uri'))

    def delete_single(self, uri):
        print("Deleting {} from index".format(uri))
        return "{} deleted from index".format(uri)
