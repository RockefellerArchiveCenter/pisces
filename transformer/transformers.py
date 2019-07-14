from dateutil import parser
import hashlib
import json
import os
from iso639 import languages

from django.utils import timezone
from odin.codecs import json_codec

from .models import *
from .resources import *
from .mappings import *


class ArchivesSpaceTransformError(Exception): pass
class CartographerTransformError(Exception): pass
class WikidataTransformError(Exception): pass
class WikipediaTransformError(Exception): pass


class CartographerDataTransformer:

    def run(self):
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

    def run(self, data):
        self.object_type = data.get('jsonmodel_type')
        data = json.dumps(data) if isinstance(data, dict) else data
        try:
            # TODO: parse out objects and collections
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

    def rights_statements(self, rights_statements):
        try:
            rights = []
            for statement in rights_statements:
                new_acts = []
                new_rights = {
                    "determinationDate": statement.get('determination_date'),
                    "rightsType": statement.get('rights_type'),
                    "dateStart": self.datetime_from_string(statement.get('start_date')),
                    "dateEnd": self.datetime_from_string(statement.get('end_date')),
                    "copyrightStatus": statement.get('status'),
                    "otherBasis": statement.get('other_rights_basis'),
                    "jurisdiction": statement.get('jurisdiction'),
                    "notes": self.notes(statement.get('notes'))}
                for act in statement.get('acts'):
                    new_acts.append({"act": act.get('act_type'),
                                     "dateStart": self.datetime_from_string(act.get('start_date')),
                                     "dateEnd": self.datetime_from_string(act.get('end_date')),
                                     "restriction": act.get('restriction'),
                                     "notes": self.notes(act.get('notes'))})
                new_rights["acts"] = new_acts
                return new_rights
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming rights: {}'.format(e))


class WikidataDataTransformer:

    def run(self):
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
                "content": [{"type": "text", "content": [sef.source_data]}]}
