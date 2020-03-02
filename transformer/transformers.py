import hashlib
import json

from asterism.resources import archivesspace
from fetcher.helpers import send_post_request
from odin.codecs import json_codec
from pisces import settings
from requests.exceptions import ConnectionError

from .mappings import (ArchivesSpaceAgentCorporateEntityToAgent,
                       ArchivesSpaceAgentFamilyToAgent,
                       ArchivesSpaceAgentPersonToAgent,
                       ArchivesSpaceArchivalObjectToCollection,
                       ArchivesSpaceArchivalObjectToObject,
                       ArchivesSpaceResourceToCollection,
                       ArchivesSpaceSubjectToTerm)
from .mappings_helpers import ArchivesSpaceHelper


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


class ArchivesSpaceDataTransformer:
    """Stores each objects jsonmodel type and then checks the type and transforms the from_obj data to the to_obj
    format based on mappings.py and resources.py Sends a get request for each archival object checking the tree_node
    endpoint for children. If there are more than 0 children, transform it to a resource."""

    def run(self, data):
        self.object_type = self.get_object_type(data)
        identifier = data.get("uri")
        try:
            TYPE_MAP = (
                ("agent_person", archivesspace.ArchivesSpaceAgentPerson, ArchivesSpaceAgentPersonToAgent),
                ("agent_corporate_entity", archivesspace.ArchivesSpaceAgentCorporateEntity, ArchivesSpaceAgentCorporateEntityToAgent),
                ("agent_family", archivesspace.ArchivesSpaceAgentFamily, ArchivesSpaceAgentFamilyToAgent),
                ("resource", archivesspace.ArchivesSpaceResource, ArchivesSpaceResourceToCollection),
                ("archival_object", archivesspace.ArchivesSpaceArchivalObject, ArchivesSpaceArchivalObjectToObject),
                ("archival_object_collection", archivesspace.ArchivesSpaceArchivalObject, ArchivesSpaceArchivalObjectToCollection),
                ("subject", archivesspace.ArchivesSpaceSubject, ArchivesSpaceSubjectToTerm))
            from_type, from_resource, mapping = [t for t in TYPE_MAP if t[0] == self.object_type][0]
            from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
            transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
            send_post_request(settings.DELIVERY_URL, transformed)
            return json.dumps(transformed)
        except ConnectionError:
            raise ArchivesSpaceTransformError("Could not connect to {}".format(settings.DELIVERY_URL))
        except Exception as e:
            raise ArchivesSpaceTransformError("Error transforming {} {}: {}".format(self.object_type, identifier, str(e)))

    def get_object_type(self, data):
        if data.get("jsonmodel_type") == "archival_object":
            if ArchivesSpaceHelper().has_children(data['uri']):
                return "archival_object_collection"
        return data.get("jsonmodel_type")


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
