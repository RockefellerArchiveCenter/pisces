import json
import os

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
                self.source_data = SourceData.objects.get(cls[1]=self.obj, source=SourceData.ARCHIVESSPACE)
                getattr(self, "transform_to_{}".format(self.destination_type))(self.obj)
        TransformRun.objects.create(run_time=self.run_time)

    def find_in_dict(dict, val):
        reverse_linked_q = list()
        reverse_linked_q.append((list(), dict))
        while reverse_linked_q:
            this_key_chain, this_v = reverse_linked_q.pop()
            if this_v == val:
                return this_key_chain
            try:
                items = this_v.items()
            except AttributeError:
                continue
            for k, v in items:
                reverse_linked_q.append((this_key_chain + [k], v))
        raise KeyError

    def id_from_as_uri(self, uri):
        return int(uri.split('/',)[-1])

    def agents(self, source_agents):
        agents = []
        for agent in source_agents: # TODO: REVIEW MAPPING
            if agent['role'] != 'creator':
                new_agent = {"type": self.agent_type(agent),
                             "role": agent.get('role'),
                             "relator": agent.get('relator'),
                             "ref": self.agent_ref(agent)}
                agents.append(new_agent)
        return agents

    def agent_ref(self, agent):
        path = [t[2] for t in OBJECT_MAP if t[0] == agent.get('jsonmodel_type')][0] # TODO: this is wrong
        return "/{}/{}".format(path, self.id_from_as_uri(agent.get('uri'))) # TODO: replace this with a call to identifier service

    def agent_type(self, agent):
        return [t[1] for t in OBJECT_MAP if t[0] == agent.get('jsonmodel_type')][0] # TODO: this is wrong

    def creators(self, source_creators):
        creators = []
        for creator in source_creators: # TODO: review mapping
            if creator['role'] == 'creator':
                new_creator = {"type": self.agent_type(agent),
                               "ref": self.agent_ref(agent)}
                creators.append(new_creator)
        return creators

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

    def languages(self, languages, relation_key):
        for language in languages:
            # TODO: check if in DB first
            Language.objects.create(expression="", # TODO: write function
                                    identifier=language, # TODO: write function
                                    relation_key=self.obj)

    def notes(self, notes, relation_key):
        for note in notes:
            Note.objects.create(type=note.get('type'),
                                title=note.get('label'),
                                content=note.get('content')
                                relation_key=self.obj)

    def rights_statements(self, rights_statements, relation_key): # TODO: figure out mapping
        for statement in rights_statements:
            new_rights = RightsStatement.objects.create(
                relation_key=self.obj
            )
            for rights_granted in statement.get(rights_granted):
                RightsGranted.objects.create(
                    rights_statement=new_rights
                )

    def terms(self, terms, relation_key):
        for term in terms:
            # TODO: check if in DB first
            Terms.objects.create(title=term.title,
                                 ref=term.get('ref'), # TODO: this is not right
                                 relation_key=self.obj)

    def transform_to_agent(self, obj, agent_type):
        obj.title = self.source_data.get('display_name').get('sort_name')
        try:
            self.identifiers('pisces', 'agent')
            self.identifiers(self.source_data['display_name'].get('rules', 'local'), 'agent', self.source_data['display_name'].get('authority_id'))
            self.notes(self.source_data.get('notes'), 'agent')

        # "collections": self.agent_collections(self.source_data),
        # "objects": self.agent_objects(self.source_data)}

    def transform_to_family(self, obj):
        return self.transform_to_agent(obj, 'family')

    def transform_to_organization(self, obj):
        return self.transform_to_agent(obj, 'organization')

    def transform_to_person(self, obj):
        return self.transform_to_agent(obj, 'person')

    def transform_to_collection(self, obj):
        obj.title = self.source_data.get('title')
        obj.level = self.source_data.get('level')
        try:
            self.identifiers('pisces', 'collection')
            self.dates(self.source_data.get('dates'), 'collection')
            self.extents(self.source_data.get('extents'), 'collection')
            self.languages(self.source_data.get('language'), 'collection')
            self.notes(self.source_data.get('notes'), 'collection')
            self.rights_statements(self.source_data.get('rights_statements'), 'collection')
            self.terms(self.source_data.get('subjects'), 'collection')

        obj.save()

        # "creators": self.creators(self.source_data.get('linked_agents')),
        # "agents": self.agents(self.source_data.get('linked_agents')),
        # "parents": self.parents(self.source_data),
        # "members": self.collection_members(self.source_data)}

    def transform_to_object(self, obj):
        obj.title = self.source_data.get('title')
        try:
            self.identifiers('pisces', 'object')
            self.dates(self.source_data.get('dates'), 'object')
            self.extents(self.source_data.get('extents'), 'object')
            self.languages(self.source_data.get('language'), 'object')
            self.notes(self.source_data.get('notes'), 'object')
            self.rights_statements(self.source_data.get('rights_statements'), 'object')
            self.terms(self.source_data.get('subjects'), 'object')

        obj.save()

        # "agents": self.agents(self.source_data.get('linked_agents')),
        # "parents": self.parents(self.source_data),
        # "members": self.object_members(self.source_data)}

    def transform_to_term(self, obj):
        obj.title = self.source_data.get('title')
        try:
            self.identifiers('pisces', 'term')
            self.identifiers(self.source_data.get('source'), 'term', self.source_data.get('authority_id'))

        # "collections": self.term_collections(self.source_data),
        # "objects": self.term_objects(self.source_data)}
