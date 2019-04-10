import json
import os
from transformer.models import *
from pisces import settings

source_filepath = 'source_data'
TYPE_MAP = {'agent_corporate_entity': [Agent, 'agent'],
            'agent_family': [Agent, 'agent'],
            'agent_person': [Agent, 'agent'],
            'archival_objects': [Object, 'object'],
            'resources': [Collection, 'collection'],
            'subjects': [Term, 'term']}

for d in os.listdir(os.path.join(settings.BASE_DIR, source_filepath)):
    if d != 'trees':
        cls = TYPE_MAP[d][0]
        key = TYPE_MAP[d][1]
        for f in os.listdir(os.path.join(settings.BASE_DIR, source_filepath, d)):
            with open(os.path.join(settings.BASE_DIR, source_filepath, d, f)) as f:
                data = json.load(f)
                obj = cls.objects.create()
                SourceData.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "data": data})
                Identifier.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "identifier": data.get('uri')})
                print("Imported {}".format(data.get('uri')))
