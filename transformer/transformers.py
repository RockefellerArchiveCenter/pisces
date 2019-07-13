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
            return from_obj.convert_to(to_obj)
        except Exception as e:
            print(e)
            raise ArchivesSpaceTransformError("Error transforming {}: {}".format(self.object_type, str(e)))

    def datetime_from_string(self, date_string):
        if date_string:
            try:
                return timezone.make_aware(parser.parse(date_string))
            except Exception:
                return None
        return None

    def num_from_string(self, string):
        try:
            return int(string)
        except ValueError:
            try:
                return float(string)
            except ValueError:
                return False

    def parse_date(self, date):
        begin = self.datetime_from_string(date.get('begin'))
        end = self.datetime_from_string(date.get('end'))
        expression = date.get('expression')
        if not expression:
            expression = date.get('begin')
            if date.get('end'):
                expression = "{}-{}".format(date.get('begin'), date.get('end'))
        return (begin, end, expression)

    def parse_note_content(self, note, content=None):
        try:
            content = content if content else []
            if note.get('jsonmodel_type') in ['note_bioghist', 'note_multipart']:
                for n in note.get('subnotes'):
                    content.append(self.parse_note_content(n)[0])
            else:
                if note.get('jsonmodel_type') in ['note_orderedlist', 'note_definedlist']:
                    content.append((note.get('jsonmodel_type').split('note_')[1], note.get('items')))
                elif note.get('jsonmodel_type') == 'note_bibliography':
                    content.append(('text', note.get('content')))
                    content.append(('orderedlist', note.get('items')))
                elif note.get('jsonmodel_type') == 'note_index':
                    l = [{'label': i.get('type'), 'value': i.get('value')} for i in note.get('items')]
                    content.append(('text', note.get('content')))
                    content.append(('definedlist', l))
                elif note.get('jsonmodel_type') == 'note_chronology':
                    m = [{'label': i.get('event_date'), 'value': ', '.join(i.get('events'))} for i in note.get('items')]
                    content.append(('definedlist', m))
                else:
                    content.append(('text', (note.get('content')
                                    if isinstance(note.get('content'), list) else [note.get('content')])))
            return content
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming note content {}'.format(e))

    def parse_note(self, note):
        type = note.get('type', note.get('jsonmodel_type').split('note_',1)[1])
        title = note.get('label', 'Note')
        content = self.parse_note_content(note)
        return (type, title, content)

    def agents(self, agents, creator=False):
        try:
            agent_list = [a for a in agents if a['role'] == 'creator'] if creator else [a for a in agents if a['role'] != 'creator']
            return [agent.get('ref') for agent in agent_list]
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming agent: {}'.format(e))

    def dates(self, dates):
        try:
            new_dates = []
            for date in dates:
                parsed = self.parse_date(date)
                new_dates.append({"begin": parsed[0], "end": parsed[1],
                                  "expression": parsed[2], "label": date.get('label')})
            return new_dates
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming dates: {}'.format(e))

    def extents(self, extents):
        try:
            new_extents = []
            for extent in extents:
                if self.num_from_string(extent.get('number')):
                    new_extents.append({"value": self.num_from_string(extent.get('number')),
                                        "type": extent.get('extent_type')})
            return new_extents
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming extents: {}'.format(e))

    def languages(self, lang):
        try:
            lang_data = languages.get(part2b=lang)
            return [{"expression": lang_data.name, "identifier": lang}]
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming languages: {}'.format(e))

    def notes(self, notes):
        try:
            new_notes = []
            for note in notes:
                new_subnotes = []
                parsed = self.parse_note(note)
                new_note = {"type": parsed[0], "title": parsed[1],
                            "source": 'archivesspace', 'content': []}
                for subnote in parsed[2]:
                    new_subnotes.append({"type": subnote[0], "content": subnote[1]})
                new_note['content'].append(new_subnotes)
                new_notes.append(new_note)
            return new_notes
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming notes: {}'.format(e))

    def process_tree(self, tree, idx=0):
        try:
            identifier = tree.get('record_uri', tree.get('ref'))
            obj = (Collection.objects.get(identifier__source=Identifier.ARCHIVESSPACE,identifier__identifier=identifier)
                   if (tree.get('children') or 'resources' in identifier) else
                   Object.objects.get(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=identifier))
            obj.tree_order = idx
            obj.save()
            if tree.get('children'):
                i = 0
                for item in tree.get('children'):
                    self.process_tree(item, i)
                    i += 1
        except Exception as e:
            raise ArchivesSpaceTransformError('Error processing tree: {}'.format(e))

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

    def terms(self, terms):
        try:
            term_set = []
            for term in terms:
                term_set.append(term.get('ref'))
            return term_set
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming terms: {}'.format(e))

    def transform_to_collection(self):
        obj = {}
        try:
            obj['type'] = 'collection'
            obj['uri'] = self.source_data.get('uri') # TODO: look at ID generation
            obj['title'] = self.source_data.get('title', self.source_data.get('display_string'))
            obj['level'] = self.source_data.get('level')
            obj['dates'] = self.dates(self.source_data.get('dates'))
            obj['creators'] = self.agents(self.source_data.get('linked_agents'), creator=True)
            obj['extents'] = self.extents(self.source_data.get('extents'))
            obj['notes'] = self.notes(self.source_data.get('notes'))
            obj['rights_statements'] = self.rights_statements(self.source_data.get('rights_statements'))
            if self.source_data.get('language'):
                obj['languages'] = self.languages(self.source_data.get('language'))
            obj['terms'] = self.terms(self.source_data.get('subjects'))
            obj['agents'] = self.agents(self.source_data.get('linked_agents'))
            if (self.source_data.get('jsonmodel_type') == 'archival_object') and self.source_data.get('ancestors'):
                obj['parent'] = self.source_data.get('ancestors')[0].get('ref')
            return obj
            # if self.source_data.get('jsonmodel_type') == 'resource':
            #     self.process_tree(self.obj.source_tree)
        except Exception as e:
            print(e)
            raise ArchivesSpaceTransformError("Error transforming collection: {}".format(e))


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
