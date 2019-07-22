from elasticsearch_dsl import Document, Date, Nested, Boolean, analyzer, InnerDoc, Completion, Keyword, Text


class Collection(Document):

    class Index:
        name = 'collection'


class Object(Document):

    class Index:
        name = 'object'


class Agent(Document):

    class Index:
        name = 'agent'


class Term(Document):

    class Index:
        name = 'term'
