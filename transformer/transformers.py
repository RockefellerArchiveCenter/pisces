import hashlib
import json

from odin.codecs import json_codec

from .resources import Agent, Collection, Object, Term, ArchivesSpaceAgentPerson, ArchivesSpaceAgentCorporateEntity, ArchivesSpaceAgentFamily, ArchivesSpaceResource, ArchivesSpaceArchivalObject, ArchivesSpaceSubject
# not sure why we need to import mappings here, but we do
from .mappings import *


class ArchivesSpaceTransformError(Exception):
    """Sets up the error messaging for AS transformations."""
    pass


class CartographerTransformError(Exception):
    """Sets up the error messaging for Cartographer transformations."""
    pass


class WikidataTransformError(Exception):
    """Sets up the error messaging for WikiData transformations."""
    pass


class WikipediaTransformError(Exception):
    """Sets up the error messaging for Wikipedia transformations."""
    pass


class CartographerDataTransformer:
    """Transforms cartographer data. Sets title and uri based on source data titles and refs. Checks for parents and children
    and adds the title, parent, ref, and any children to a dictionary."""

    def run(self, data):
        self.source_data = data
        obj = {}
        try:
            obj['title'] = self.source_data.get('title')
            obj['uri'] = self.source_data.get('ref')
            if self.source_data.get('parent'):
                obj['parent'] = self.parent(self.source_data['parent'].get('ref'))
            if self.source_data.get('children'):
                obj['children'] = self.children(self.source_data.get('children'), obj, [])
            #     if not self.obj.parent:
            #         self.process_tree(self.source_data)
            return obj
        except Exception as e:
            print(e)
            raise CartographerTransformError(e)

    def children(self, children, parent, data):
        for child in children:
            data.append({"title": child.get("title"), "parent": parent.get("ref"), "children": []})
            if child.get('children'):
                self.children(child.get("children"), child, data)
        return data

    def process_tree(self, data, idx=0):
        try:
            c = Collection.objects.get(identifier__identifier=data.get('ref'))
            c.tree_order = idx
            c.save()
            if data.get('children'):
                i = 0
                for item in data.get('children'):
                    self.process_tree(item, i)
                    i += 1
        except Exception as e:
            raise CartographerTransformError('Error processing tree: {}'.format(e))


class ArchivesSpaceDataTransformer:
    """Stores each objects jsonmodel type and then checks the type and transforms the from_obj data to the to_obj
    format based on mappings.py and resources.py Sends a get request for each archival object checking the tree_node
    endpoint for children. If there are more than 0 children, transform it to a resource."""

    def run(self, data):
        self.object_type = data.get('jsonmodel_type')
        data = json.dumps(data) if isinstance(data, dict) else data
        try:
            # TODO: parse out objects and collections. The tree/node endpoint looks promising
            TYPE_MAP = (
                ("agent_person", "agent", ArchivesSpaceAgentPerson, Agent),
                ("agent_corporate_entity", "agent", ArchivesSpaceAgentCorporateEntity, Agent),
                ("agent_family", "agent", ArchivesSpaceAgentFamily, Agent),
                ("resource", "collection", ArchivesSpaceResource, Collection),
                ("archival_object", "object", ArchivesSpaceArchivalObject, Object),
                ("subject", "term", ArchivesSpaceSubject, Term))
            from_obj = json_codec.loads(data, resource=[t[2] for t in TYPE_MAP if t[0] == self.object_type][0])
            to_obj = [t[3] for t in TYPE_MAP if t[0] == self.object_type][0]
            return json_codec.dumps(from_obj.convert_to(to_obj))
        except Exception as e:
            print(e)
            raise ArchivesSpaceTransformError("Error transforming {}: {}".format(self.object_type, str(e)))


class WikidataDataTransformer:
    """"Transforms WikiData content obtained through the WikiData fetcher and sets the source to wikidata. Transforms
    descriptions to an abstract note and stores an image url from Wikipedia Commons."""

    def run(self, data):
        self.source_data = data
        try:
            obj = {}
            if self.source_data.get('descriptions').get('en'):
                obj['notes'] = self.notes('abstract', self.source_data.get('descriptions').get('en')['value'])
            obj['image_url'] = self.image_url(self.source_data.get('claims').get('P18'))
            return obj
        except Exception as e:
            print(e)
            raise WikidataTransformError(e)

    def notes(self, note_type, content):
        return {"type": note_type, "title": "Abstract", "source": "wikidata",
                "content": [{"type": "text", "content": [content]}]}

    def image_url(self, image_prop):
        # https://stackoverflow.com/questions/34393884/how-to-get-image-url-property-from-wikidata-item-by-api
        # Do we want the actual image binary?
        if image_prop:
            filename = image_prop[0]['mainsnak']['datavalue']['value'].replace(" ", "_")
            md5 = hashlib.md5(filename.encode()).hexdigest()
            return "https://upload.wikimedia.org/wikipedia/commons/{}/{}/{}".format(md5[:1], md5[:2], filename)


class WikipediaDataTransformer:
    """"Takes Wikipedia description content from the fetchers and transforms any data to a bioghist note."""

    def run(self, data):
        self.source_data = data
        obj = {}
        try:
            obj['notes'] = self.notes('bioghist')
        except Exception as e:
            print(e)
            raise WikipediaTransformError(e)

    def notes(self, note_type):
        return {"type": note_type, "title": "Description", "source": "wikipedia",
                "content": [{"type": "text", "content": [self.source_data]}]}
