import json
import os
from asnake.aspace import ASpace
aspace = ASpace(
              baseurl='http://192.168.50.7:8089',
              user='admin',
              password='admin'
              )
repo = aspace.repositories(2)


def process_map_child(child):
    if child.get('ref'):
        resource = repo.resources(child.get('ref').split('repositories/2/resources/')[-1])
        process_as_child(resource)
    if child.get('children'):
        for child in child.get('children'):
            process_map_child(child)


def process_as_child(child):
    save_data("{}s".format(child.jsonmodel_type), child)
    save_related('agents', child.linked_agents)
    save_related('subjects', child.subjects)
    if child.jsonmodel_type == 'resource':
        for c in child.tree.walk:
            if c.jsonmodel_type != 'resource':
                process_as_child(c)


def save_related(object_type, related_objects):
    for obj in related_objects:
        save_data(object_type, obj)


def save_data(object_type, object, identifier=None):
    path = object.jsonmodel_type if (object_type == 'agents') else object_type
    outpath = os.path.join(path, "{}.json".format(identifier)) if identifier else os.path.join(path, "{}.json".format(object.uri.split('/')[-1]))
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(outpath, 'w+') as outfile:
        json.dump(object.json(), outfile, indent=2)
    print(outpath)
    if object_type == 'resources':
        save_data('trees', object.tree, identifier=object.id)


with open(os.path.join('maps', '1.json')) as map_json:
    map = json.load(map_json)

    for child in map.get('children'):
        process_map_child(child)
