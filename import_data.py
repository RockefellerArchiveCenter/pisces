import json
import objectpath
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
                if d == 'archival_objects':
                    resource_id = data.get('resource').get('ref').split('/')[-1]
                    with open(os.path.join(settings.BASE_DIR, source_filepath, 'trees', '{}.json'.format(resource_id))) as tf:
                        tree_data = json.load(tf)
                        full_tree = objectpath.Tree(tree_data)
                        partial_tree = full_tree.execute("$..children[@.record_uri is '{}']".format(data.get('uri')))
                        # Tree.execute() is a generator function so we have to loop through the results
                        for p in partial_tree:
                            if p.get('has_children'):
                                key = 'collection'
                                obj = Collection.objects.create(tree=p)
                            else:
                                key = 'object'
                                obj = cls.objects.create()
                elif d == 'resources':
                    resource_id = data.get('uri').split('/')[-1]
                    with open(os.path.join(settings.BASE_DIR, source_filepath, 'trees', '{}.json'.format(resource_id))) as tf:
                        tree_data = json.load(tf)
                        obj = cls.objects.create(tree=tree_data)
                else:
                    obj = cls.objects.create()
                SourceData.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "data": data})
                Identifier.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "identifier": data.get('uri')})
                print("Imported {}".format(data.get('uri')))
