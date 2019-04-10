from dateutil import parser
import json
import os
from pycountry import languages
from uuid import uuid4

from django.utils import timezone

from .models import *


class ArchivesSpaceDataTransformer:
    def __init__(self):
        self.last_run = (TransformRun.objects.filter(status=TransformRun.FINISHED).order_by('-start_time')[0].start_time
                         if TransformRun.objects.filter(status=TransformRun.FINISHED).exists() else None)
        self.current_run = TransformRun.objects.create(status=TransformRun.RUNNING)

    def run(self):
        for cls in [(Agent, 'agent'), (Collection, 'collection'), (Object, 'object'), (Term, 'term')]:
            for obj in (cls[0].objects.filter(modified__gte=self.last_run) if self.last_run else cls[0].objects.all()):
                self.obj = obj
                self.source_data = SourceData.objects.get(**{cls[1]: self.obj, "source": SourceData.ARCHIVESSPACE}).data
                getattr(self, "transform_to_{}".format(cls[1]))()
        self.current_run.status = TransformRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()

    def parse_date(self, date_string):
        if date_string:
            try:
                return timezone.make_aware(parser.parse(date_string))
            except Exception:
                return None
        return None

    def parse_date_expression(self, date):
        if not date.get('expression'):
            if date.get('end'):
                return "{}-{}".format(date.get('begin'), date.get('end'))
            return date.get('begin')
        return date.get('expression')

    def agents(self, agents):
        agent_set = []
        creator_set = []
        for agent in agents:
            if agent['role'] != 'creator':
                if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).exists(): # TODO: remove this, for testing purposes only!
                    agent_set.append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).agent)
        self.obj.agents.clear()
        self.obj.agents.set(agent_set)

    def creators(self, agents):
        creator_set = []
        for agent in agents:
            if agent['role'] == 'creator':
                if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).exists(): # TODO: remove, for testing purposes only!!
                    creator_set.append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).agent)
        self.obj.creators.clear()
        self.obj.creators.set(creator_set)

    def dates(self, dates, relation_key):
        self.obj.date_set.clear()
        for date in dates:
            # TODO: mapping for different date types
            # TODO: normalize?
            begin = self.parse_date(date.get('begin'))
            end = self.parse_date(date.get('end'))
            expression = self.parse_date_expression(date)
            Date.objects.create(**{"begin": begin,
                                   "end": end,
                                   "expression": expression,
                                   "label": date.get('label'),
                                   relation_key: self.obj})

    def extents(self, extents, relation_key):
        self.obj.extent_set.clear()
        for extent in extents:
            # TODO: handling things that are not numbers?? WTF??
            # this just eats everything because these are strings...
            if isinstance(extent.get('number'), (float, int)):
                Extent.objects.create(**{"value": extent.get('number'),
                                         "type": extent.get('extent_type'),
                                         relation_key: self.obj})

    def identifiers(self, source, relation_key, identifier=None):
        if not Identifier.objects.filter(**{'source': source, relation_key: self.obj}).exists():
            url_prefix = 'agents'
            if relation_key in ['collection', 'object']:
                url_prefix = relation_key+'s'
            new_id = identifier if identifier else "{}/{}".format(url_prefix, str(uuid4())[:8])
            if Identifier.objects.filter(identifier=new_id, source=source).exists():
                self.identifiers(source, relation_key)
            Identifier.objects.create(**{"identifier": new_id,
                                         "source": source,
                                         relation_key: self.obj})

    def languages(self, lang):
        lang_data = languages.get(alpha_3=lang)
        l = (Language.objects.get(identifier=lang)
             if Language.objects.filter(identifier=lang, expression=lang_data.name).exists()
             else Language.objects.create(expression=lang_data.name, identifier=lang))
        self.obj.languages.clear()
        self.obj.languages.add(l)

    def notes(self, notes, relation_key):
        self.obj.notes_set.clear()
        for note in notes:
            # TODO: mapping for different note types
            Note.objects.create(**{"type": note.get('type', note.get('jsonmodel_type').split('note_',1)[1]),
                                   "title": note.get('label', "THIS DIDN'T WORK"),
                                   "content": note.get('content', "THIS DIDN'T WORK"),
                                   relation_key: self.obj})

    def rights_statements(self, rights_statements, relation_key):
        self.obj.rights_statement_set.clear()
        for statement in rights_statements:
            new_rights = RightsStatement.objects.create(**{
                "determinationDate": statement.get('determination_date'),
                "rightsType": statement.get('rights_type'),
                "dateStart": self.parse_date(statement.get('start_date')),
                "dateEnd": self.parse_date(statement.get('end_date')),
                "copyrightStatus": statement.get('status'),
                "otherBasis": statement.get('other_rights_basis'),
                "jurisdiction": statement.get('jurisdiction'),
                relation_key: self.obj})
            for rights_granted in statement.get('acts'):
                statement.rights_granted_set.clear()
                RightsGranted.objects.create(
                    rights_statement=new_rights,
                    act=rights_granted.get('act_type'),
                    dateStart=self.parse_date(rights_granted.get('start_date')),
                    dateEnd=self.parse_date(rights_granted.get('end_date')),
                    restriction=rights_granted.get('restriction'))

    def terms(self, terms):
        term_set = []
        for t in terms:
            if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=t.get('ref')).exists(): # TODO: remove, for testing only!
                term_set.append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=t.get('ref')).term)
        self.obj.terms.clear()
        self.obj.terms.set(term_set)

    def transform_to_agent(self):
        print("Agent", self.source_data.get('uri'))
        self.obj.title = self.source_data.get('display_name').get('sort_name')
        self.obj.type = self.source_data.get('jsonmodel_type')
        try:
            self.identifiers(Identifier.PISCES, 'agent')
            self.notes(self.source_data.get('notes'), 'agent')
            self.obj.save()
        except Exception as e:
            print(e)
            self.current_run.status = TransformRun.FINISHED
            self.current_run.end_time = timezone.now
            self.current_run.save()

        # TODO
        # "collections": self.agent_collections(self.source_data),
        # "objects": self.agent_objects(self.source_data)}

    def transform_to_collection(self):
        print("Collection", self.source_data.get('uri'))
        self.obj.title = self.source_data.get('title')
        self.obj.level = self.source_data.get('level')
        try:
            self.identifiers(Identifier.PISCES, 'collection')
            self.dates(self.source_data.get('dates'), 'collection')
            self.extents(self.source_data.get('extents'), 'collection')
            self.notes(self.source_data.get('notes'), 'collection')
            self.rights_statements(self.source_data.get('rights_statements'), 'collection')
            self.languages(self.source_data.get('language'))
            self.terms(self.source_data.get('subjects'))
            self.agents(self.source_data.get('linked_agents'))
            self.creators(self.source_data.get('linked_agents'))
            self.obj.save()
        except Exception as e:
            print(e)
            self.current_run.status = TransformRun.FINISHED
            self.current_run.end_time = timezone.now
            self.current_run.save()

        # TODO
        # "parents": self.parents(self.source_data),
        # "members": self.collection_members(self.source_data)}

    def transform_to_object(self):
        print("Object", self.source_data.get('uri'))
        self.obj.title = self.source_data.get('title', self.source_data.get('display_string'))
        try:
            self.identifiers(Identifier.PISCES, 'object')
            self.dates(self.source_data.get('dates'), 'object')
            self.extents(self.source_data.get('extents'), 'object')
            self.notes(self.source_data.get('notes'), 'object')
            self.rights_statements(self.source_data.get('rights_statements'), 'object')
            if self.source_data.get('language'):
                self.languages(self.source_data.get('language'))
            self.terms(self.source_data.get('subjects'))
            self.agents(self.source_data.get('linked_agents'))
            self.obj.save()
        except Exception as e:
            print(e)
            self.current_run.status = TransformRun.FINISHED
            self.current_run.end_time = timezone.now
            self.current_run.save()

        # TODO
        # "parents": self.parents(self.source_data),
        # "members": self.object_members(self.source_data)}

    def transform_to_term(self):
        print("Term", self.source_data.get('uri'))
        self.obj.title = self.source_data.get('title')
        try:
            self.identifiers(Identifier.PISCES, 'term')
            self.obj.save()
        except Exception as e:
            print(e)
            self.current_run.status = TransformRun.FINISHED
            self.current_run.end_time = timezone.now
            self.current_run.save()

        # TODO
        # "collections": self.term_collections(self.source_data),
        # "objects": self.term_objects(self.source_data)}
