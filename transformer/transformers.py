import json
import os
from pycountry import languages

from django.utils import timezone

from .models import *

# (RAC data model type, URL prefix)
OBJECT_MAP = (('organization', 'organizations'),
              ('family', 'families'),
              ('person', 'people'),
              ('software', 'software'),
              ('collection', 'collections'),
              ('object', 'objects'))


class ArchivesSpaceDataTransformer:
    def __init__(self):
        self.last_run = TransformRun.objects.order_by('-run_time')[0].run_time if len(TransformRun.objects.all()) else 0
        self.run_time = timezone.now

    def run(self):
        for cls in [(Agent, 'agent'), (Collection, 'collection'), (Object, 'object'), (Term, 'term')]:
            for obj in cls[0].objects.filter(modified__lte=self.last_run):
                self.obj = obj
                self.source_data = SourceData.objects.get(cls[1]=self.obj, source=SourceData.ARCHIVESSPACE).data
                getattr(self, "transform_to_{}".format(self.destination_type))()
        TransformRun.objects.create(run_time=self.run_time)

    def agents(self, agents):
        agent_set = []
        creator_set = []
        for agent in agents:
            if agent['role'] != 'creator':
                agent_set.append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).agent)
        self.object.agents.clear()
        self.objects.agents.set(agent_set)

    def creators(self, agents):
        creator_set = []
        for agent in agents:
            if agent['role'] == 'creator':
                creator_set.append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).agent)
        self.object.creators.clear()
        self.object.creators.set(creator_set)

    def dates(self, dates, relation_key):
        for date in dates:
            Date.objects.create(begin=date.get('begin'),
                                end=date.get('end'),
                                expression=date.get('expression'),
                                label=date.get('label'),
                                relation_key=self.obj)

    def extents(self, extents, relation_key):
        for extent in extents:
            Extent.ojects.create(value=extent.get('number'),
                                 type=extent.get('extent_type'),
                                 relation_key=self.obj)

    def identifiers(self, source, relation_key, identifier=None):
        new_id = identifier if identifier else "{}/{}".format([t[1] for t in OBJECT_MAP if t[0] == relation_key], uuid4())
        if Identifier.objects.filter(identifier=new_id, source=source).exists():
            self.identifiers(source, relation_key)
        Identifier.objects.create(identifier=new_id,
                                  source=source,
                                  relation_key=self.obj)

    def languages(self, lang):
        lang_data = languages.get(alpha_3=lang)
        l = (Language.objects.get(identifier=lang)
             if Language.objects.filter(identifier=l, expression=lang_data.name).exists()
             else Language.objects.create(expression=lang_data.name, identifier=l))
        self.object.languages.clear()
        self.object.languages.add(l)

    def notes(self, notes, relation_key):
        for note in notes:
            Note.objects.create(type=note.get('type'),
                                title=note.get('label'),
                                content=note.get('content')
                                relation_key=self.obj)

    def rights_statements(self, rights_statements, relation_key):
        for statement in rights_statements:
            new_rights = RightsStatement.objects.create(
                determinationDate=statement.get('determination_date'),
                rightsType=statement.get('rights_type'),
                dateStart=statement.get('start_date'),
                dateEnd=statement.get('end_date'),
                copyrightStatus=statement.get('status'),
                otherBasis=statement.get('other_rights_basis'),
                jurisdiction=statement.get('jurisdiction'),
                relation_key=self.obj)
            for rights_granted in statement.get('acts'):
                RightsGranted.objects.create(
                    rights_statement=new_rights,
                    act=rights_granted.get('act_type')
                    dateStart=rights_granted.get('start_date')
                    dateEnd=rights_granted.get('end_date')
                    restriction=rights_granted.get('restriction'))

    def terms(self, terms):
        term_set = []
        for t in terms:
            term_set.append(Term.objects.get(title=t.title))
        self.object.terms.clear()
        self.object.terms.set(term_set)

    def transform_to_agent(self, agent_type):
        self.obj.title = self.source_data.get('display_name').get('sort_name')
        self.obj.type = getattr(Agent, agent_type.upper())
        try:
            self.identifiers('pisces', 'agent')
            self.identifiers(self.source_data['display_name'].get('rules', 'local'), 'agent', self.source_data['display_name'].get('authority_id'))
            self.notes(self.source_data.get('notes'), 'agent')
        self.obj.save()

        # CAN WE ASSUME THESE RELATIONSHIPS WILL EXIST ALREADY?
        # "collections": self.agent_collections(self.source_data),
        # "objects": self.agent_objects(self.source_data)}

    def transform_to_family(self):
        self.transform_to_agent('family')

    def transform_to_organization(self):
        self.transform_to_agent('organization')

    def transform_to_person(self):
        self.transform_to_agent('person')

    def transform_to_collection(self):
        self.obj.title = self.source_data.get('title')
        self.obj.level = self.source_data.get('level')
        try:
            self.identifiers('pisces', 'collection')
            self.dates(self.source_data.get('dates'), 'collection')
            self.extents(self.source_data.get('extents'), 'collection')
            self.languages(self.source_data.get('language'), 'collection')
            self.notes(self.source_data.get('notes'), 'collection')
            self.rights_statements(self.source_data.get('rights_statements'), 'collection')
            self.terms(self.source_data.get('subjects'), 'collection')
            self.agents(self.source_data.get('linked_agents'))
            self.creators(self.source_data.get('linked_agents'))
        self.obj.save()

        # CAN WE ASSUME THESE RELATIONSHIPS WILL EXIST ALREADY?
        # "parents": self.parents(self.source_data),
        # "members": self.collection_members(self.source_data)}

    def transform_to_object(self):
        self.obj.title = self.source_data.get('title')
        try:
            self.identifiers('pisces', 'object')
            self.dates(self.source_data.get('dates'), 'object')
            self.extents(self.source_data.get('extents'), 'object')
            self.notes(self.source_data.get('notes'), 'object')
            self.rights_statements(self.source_data.get('rights_statements'), 'object')
            self.languages(self.source_data.get('language'))
            self.terms(self.source_data.get('subjects'))
            self.agents(self.source_data.get('linked_agents'))
        self.obj.save()

        # CAN WE ASSUME THESE RELATIONSHIPS WILL EXIST ALREADY?
        # "parents": self.parents(self.source_data),
        # "members": self.object_members(self.source_data)}

    def transform_to_term(self):
        self.obj.title = self.source_data.get('title')
        try:
            self.identifiers('pisces', 'term')
            self.identifiers(self.source_data.get('source'), 'term', self.source_data.get('authority_id'))
        self.obj.save()

        # CAN WE ASSUME THESE RELATIONSHIPS WILL EXIST ALREADY?
        # "collections": self.term_collections(self.source_data),
        # "objects": self.term_objects(self.source_data)}
