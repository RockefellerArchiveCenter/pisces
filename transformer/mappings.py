import json

import odin
from odin.codecs import json_codec
from iso639 import languages

from .resources import *
from .resource_configs import NOTE_TYPE_CHOICES
from .mappings_helpers import ArchivesSpaceHelper


class ArchivesSpaceRefToReference(odin.Mapping):
    from_obj = ArchivesSpaceRef
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAncestorToReference(odin.Mapping):
    from_obj = ArchivesSpaceAncestor
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceLinkedAgentToReference(odin.Mapping):
    from_obj = ArchivesSpaceLinkedAgent
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceDateToDate(odin.Mapping):
    from_obj = ArchivesSpaceDate
    to_obj = Date

    mappings = (
        odin.define(from_field='date_type', to_field='type'),
    )

    @odin.map_field
    def expression(self, value):
        if not value:
            value = "{}-{}".format(self.source.begin, self.source.end) if self.source.end else "{}-".format(self.source.begin)
        return value


class ArchivesSpaceExtentToExtent(odin.Mapping):
    from_obj = ArchivesSpaceExtent
    to_obj = Extent

    mappings = (
        ('extent_type', None, 'type'),
        ('number', None, 'value')
    )


class ArchivesSpaceNoteToNote(odin.Mapping):
    from_obj = ArchivesSpaceNote
    to_obj = Note

    @odin.map_field(from_field='label', to_field='title')
    def title(self, value):
        return value if value else [v[1] for v in NOTE_TYPE_CHOICES if v[0] == self.source.type]

    @odin.map_field(from_field='jsonmodel_type', to_field='type')
    def type(self, value):
        return value.split('note_',1)[1]

    def map_subnotes(self, value):
        if value.jsonmodel_type in ['note_orderedlist', 'note_definedlist']:
            return Subnote(type=value.jsonmodel_type.split('note_')[1], content=value.items)
        elif value == 'note_bibliography':
            data = []
            data.append(Subnote(type='text', content=value.content))
            data.append(Subnote(type='orderedlist', content=value.items))
            return data
        elif value.jsonmodel_type == 'note_index':
            data = []
            l = [{'label': i.get('type'), 'value': i.get('value')} for i in value.items]
            data.append(Subnote(type='text', content=value.content))
            data.append(Subnote(type='definedlist', content=l))
            return data
        elif value.jsonmodel_type == 'note_chronology':
            m = [{'label': i.get('event_date'), 'value': ', '.join(i.get('events'))} for i in value.items]
            return Subnote(type='definedlist', content=m)
        else:
            return Subnote(type='text', content=value.content
            if isinstance(value.content, list) else [value.content])

    @odin.map_list_field(from_field='subnotes', to_field='subnotes', to_list=True)
    def subnotes(self, value):
        if self.source.jsonmodel_type in ['note_multipart', 'note_bioghist']:
            return (self.map_subnotes(v) for v in value)
        elif self.source.jsonmodel_type == 'note_singlepart':
            return [Subnote(type='text', content=self.source.content.strip("]['").split(', '))]
        elif self.source.jsonmodel_type == 'note_index':
            return [Subnote(type='orderedlist', content=self.source.items.strip("]['").split(', '))]


class ArchivesSpaceRightsStatementActToRightsGranted(odin.Mapping):
    from_obj = ArchivesSpaceRightsStatementAct
    to_obj = RightsGranted

    mappings = (
        ('act_type', None, 'act'),
        ('start_date', None, 'begin'),
        ('end_date', None, 'end'),
        ('restriction', None, 'restriction'),
        ('notes', None, 'notes')
    )


class ArchivesSpaceRightsStatementToRightsStatement(odin.Mapping):
    from_obj = ArchivesSpaceRightsStatement
    to_obj = RightsStatement

    mappings = (
        ('determination_date', None, 'determination_date'),
        ('rights_type', None, 'type'),
        ('start_date', None, 'begin'),
        ('end_date', None, 'end'),
        ('status', None, 'copyright_status'),
        ('other_rights_basis', None, 'other_basis'),
        ('jurisdiction', None, 'jurisdiction'),
        ('notes', None, 'notes'),
        ('acts', None, 'rights_granted'),
    )


class ArchivesSpaceResourceToCollection(odin.Mapping):
    from_obj = ArchivesSpaceResource
    to_obj = Collection

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        if value:
            lang_data = languages.get(part2b=value)
            return [Language(expression=lang_data.name, identifier=value)]
        return [Language(expression="English", identifier="eng")]

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='subjects', to_field='terms')
    def terms(self, value):
        return ArchivesSpaceRefToReference.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='creators')
    def creators(self, value):
        return [ArchivesSpaceLinkedAgentToReference.apply(v) for v in value if v.role == 'creator']

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return [ArchivesSpaceLinkedAgentToReference.apply(v) for v in value if v.role != 'creator']



class ArchivesSpaceArchivalObjectToCollection(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Collection

    mappings = (
        odin.define(from_field='subjects', to_field='terms'),
    )

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return ArchivesSpaceLinkedAgentToReference.apply(value)

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        value = value if value else AS().closest_parent_value(self.source.uri, 'language')
        lang_data = languages.get(part2b=value)
        return Language(expression=lang_data.name, identifier=value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceArchivalObjectToObject(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Object

    def __init__(self, *args, **kwargs):
        self.aspace_helper = ArchivesSpaceHelper()
        return super(ArchivesSpaceArchivalObjectToObject, self).__init__(*args, **kwargs)

    mappings = (
        odin.define(from_field='position', to_field='tree_position'),
    )

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        if not value:
            value = [json_codec.loads(json.dumps(d), ArchivesSpaceDate) for d in self.aspace_helper.closest_parent_value(self.source.uri, 'dates')]
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field
    def title(self, value):
        return value if value else self.source.display_string

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        value = value if value else self.aspace_helper.closest_parent_value(self.source.uri, 'language')
        lang_data = languages.get(part2b=value)
        return [Language(expression=lang_data.name, identifier=value)]

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='subjects', to_field='terms')
    def terms(self, value):
        return ArchivesSpaceRefToReference.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return ArchivesSpaceLinkedAgentToReference.apply(value)

    @odin.map_list_field(from_field='parent', to_field='parent', to_list=True)
    def parents(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='ancestors', to_field='ancestors')
    def ancestors(self, value):
        return ArchivesSpaceAncestorToReference.apply(value)


class ArchivesSpaceSubjectToTerm(odin.Mapping):
    from_obj = ArchivesSpaceSubject
    to_obj = Term

    @odin.map_field(from_field='terms', to_field='term_type')
    def type(self, value):
        return next(iter(value), None).term_type

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAgentCorporateEntityToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentCorporateEntity
    to_obj = Agent

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.assign_field(to_field='agent_type')
    def agent_types(self):
        return "organization"


class ArchivesSpaceAgentFamilyToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentFamily
    to_obj = Agent

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.assign_field(to_field='agent_type')
    def agent_types(self):
        return "family"


class ArchivesSpaceAgentPersonToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentPerson
    to_obj = Agent

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.assign_field(to_field='agent_type')
    def agent_types(self):
        return "person"