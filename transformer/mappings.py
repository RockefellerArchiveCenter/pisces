import json
from ast import literal_eval

import odin
from asterism.resources import archivesspace
from iso639 import languages
from odin.codecs import json_codec

from .mappings_helpers import ArchivesSpaceHelper
from .resource_configs import NOTE_TYPE_CHOICES
from .resources import (Agent, Collection, Date, Extent, ExternalIdentifier,
                        Language, Note, Object, Reference, RightsGranted,
                        RightsStatement, Subnote, Term)


class ArchivesSpaceRightsStatementActToRightsGranted(odin.Mapping):
    """Maps AS RightsStatements Acts to Rights Granted object."""
    from_obj = archivesspace.ArchivesSpaceRightsStatementAct
    to_obj = RightsGranted

    mappings = (
        ('act_type', None, 'act'),
        ('start_date', None, 'begin'),
        ('end_date', None, 'end'),
        ('restriction', None, 'restriction'),
    )

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def rights_notes(self, value):
        return ArchivesSpaceNoteToNote.apply(value)


class ArchivesSpaceRightsStatementToRightsStatement(odin.Mapping):
    """Maps AS RightsStatements Statement to Rights Statement object."""
    from_obj = archivesspace.ArchivesSpaceRightsStatement
    to_obj = RightsStatement

    mappings = (
        ('start_date', None, 'begin'),
        ('end_date', None, 'end'),
        ('status', None, 'copyright_status'),
        ('other_rights_basis', None, 'other_basis'),
    )

    @odin.map_list_field(from_field="notes", to_field="rights_notes", to_list=True)
    def rights_notes(self, value):
        return ArchivesSpaceNoteToNote.apply(value)

    @odin.map_list_field(from_field='acts', to_field='rights_granted', to_list=True)
    def rights_granted(self, value):
        return ArchivesSpaceRightsStatementActToRightsGranted.apply(value)


class ArchivesSpaceRefToReference(odin.Mapping):
    """Maps ASRef to Reference object."""
    from_obj = archivesspace.ArchivesSpaceRef
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAncestorToReference(odin.Mapping):
    """Maps ASAncestor to Reference object."""
    from_obj = archivesspace.ArchivesSpaceAncestor
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceLinkedAgentToReference(odin.Mapping):
    """Maps ASAgents to Reference object."""
    from_obj = archivesspace.ArchivesSpaceLinkedAgent
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceDateToDate(odin.Mapping):
    """Maps ASDate to Date object."""
    from_obj = archivesspace.ArchivesSpaceDate
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
    """Maps ASExtent to Extent object."""
    from_obj = archivesspace.ArchivesSpaceExtent
    to_obj = Extent

    mappings = (
        ('extent_type', None, 'type'),
        ('number', None, 'value')
    )


class ArchivesSpaceNoteToNote(odin.Mapping):
    """Maps ASNotes to Note object."""
    from_obj = archivesspace.ArchivesSpaceNote
    to_obj = Note

    @odin.map_field(from_field='type', to_field='title')
    def title(self, value):
        if self.source.label:
            title = self.source.label
        elif value:
            title = [v[1] for v in NOTE_TYPE_CHOICES if v[0] == value][0]
        else:
            title = [v[1] for v in NOTE_TYPE_CHOICES if v[0] == self.source.jsonmodel_type.split('note_')[1]][0]
        return title

    @odin.map_field(from_field='jsonmodel_type', to_field='type')
    def type(self, value):
        return value.split('note_', 1)[1]

    def map_subnotes(self, value):
        """Maps different AS Subnotes to different values based on the note type."""
        if value.jsonmodel_type in ['note_orderedlist', 'note_definedlist']:
            # items is an odin.StringField so we need to re-convert to a dict here
            items = literal_eval(value.items)
            return Subnote(type=value.jsonmodel_type.split('note_')[1], content=items)
        elif value == 'note_bibliography':
            return self.bibliograpy_subnotes(value.content, value.items)
        elif value.jsonmodel_type == 'note_index':
            return self.index_subnotes(value.content, value.items)
        elif value.jsonmodel_type == 'note_chronology':
            return self.chronology_subnotes(value.items)
        else:
            return Subnote(type='text', content=value.content
                           if isinstance(value.content, list) else [value.content])

    @odin.map_list_field(from_field='subnotes', to_field='subnotes', to_list=True)
    def subnotes(self, value):
        if self.source.jsonmodel_type in ['note_multipart', 'note_bioghist']:
            return (self.map_subnotes(v) for v in value)
        elif self.source.jsonmodel_type in ['note_singlepart', 'note_rights_statement', 'note_rights_statement_act']:
            return [Subnote(type='text', content=self.source.content.strip("]['").split(', '))]
        elif self.source.jsonmodel_type == 'note_index':
            return self.index_subnotes(self.source.content, self.source.items)
        elif self.source.jsonmodel_type == 'note_bibliography':
            return self.bibliograpy_subnotes(self.source.content, self.source.items)
        elif self.source.jsonmodel_type == 'note_chronology':
            return self.chronology_subnotes(self.source.items)

    def bibliograpy_subnotes(self, content, items):
        data = []
        data.append(Subnote(type='text', content=json.loads(content)))
        data.append(Subnote(type='orderedlist', content=json.loads(items)))
        return data

    def index_subnotes(self, content, items):
        data = []
        # items is an odin.StringField so we need to re-convert to a dict here
        items_dict = literal_eval(items)
        items_list = [{'label': i.get('type'), 'value': i.get('value')} for i in items_dict]
        data.append(Subnote(type='text', content=json.loads(content)))
        data.append(Subnote(type='definedlist', content=items_list))
        return data

    def chronology_subnotes(self, items):
        # items is an odin.StringField so we need to re-convert to a dict here
        items = literal_eval(items)
        content = [{'label': i.get('event_date'), 'value': i.get('events')} for i in items]
        return Subnote(type='definedlist', content=content)


class ArchivesSpaceResourceToCollection(odin.Mapping):
    """Maps ASResources to Collection object."""
    from_obj = archivesspace.ArchivesSpaceResource
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

    @odin.map_list_field(from_field='rights_statements', to_field='rights')
    def rights(self, value):
        return ArchivesSpaceRightsStatementToRightsStatement.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='creators')
    def creators(self, value):
        return [ArchivesSpaceLinkedAgentToReference.apply(v) for v in value if v.role == 'creator']

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return [ArchivesSpaceLinkedAgentToReference.apply(v) for v in value if v.role != 'creator']


class ArchivesSpaceArchivalObjectToCollection(odin.Mapping):
    """Maps ASArchivalObjects to Collection object."""
    from_obj = archivesspace.ArchivesSpaceArchivalObject
    to_obj = Collection

    def __init__(self, *args, **kwargs):
        self.aspace_helper = ArchivesSpaceHelper()
        return super(ArchivesSpaceArchivalObjectToCollection, self).__init__(*args, **kwargs)

    @odin.map_field
    def title(self, value):
        return value if value else self.source.display_string

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        value = value if value else self.aspace_helper.closest_parent_value(self.source.uri, 'language')
        lang_data = languages.get(part2b=value)
        return [Language(expression=lang_data.name, identifier=value)]

    @odin.map_list_field(from_field='subjects', to_field='terms')
    def terms(self, value):
        return ArchivesSpaceRefToReference.apply(value)

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        if not value:
            value = [json_codec.loads(json.dumps(d), archivesspace.ArchivesSpaceDate) for d in self.aspace_helper.closest_parent_value(self.source.uri, 'dates')]
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_list_field(from_field='rights_statements', to_field='rights')
    def rights(self, value):
        return ArchivesSpaceRightsStatementToRightsStatement.apply(value)

    @odin.map_list_field(from_field='extents', to_field='extents')
    def extents(self, value):
        if not value:
            value = [json_codec.loads(json.dumps(d), archivesspace.ArchivesSpaceExtent) for d in self.aspace_helper.closest_parent_value(self.source.uri, 'extents')]
        return ArchivesSpaceExtentToExtent.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='creators')
    def creators(self, value):
        if not value:
            value = [json_codec.loads(json.dumps(d), archivesspace.ArchivesSpaceLinkedAgent) for d in self.aspace_helper.closest_parent_value(self.source.uri, 'linked_agents')]
        if len([v for v in value if v.role == 'creator']) > 0:
            return [ArchivesSpaceLinkedAgentToReference.apply(v) for v in value if v.role == 'creator']
        else:
            creators = [json_codec.loads(json.dumps(d), archivesspace.ArchivesSpaceLinkedAgent) for d in self.aspace_helper.closest_creators(self.source.uri)]
            return [ArchivesSpaceLinkedAgentToReference.apply(c) for c in creators]

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return [ArchivesSpaceLinkedAgentToReference.apply(v) for v in value if v.role != 'creator']

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='ancestors', to_field='ancestors')
    def ancestors(self, value):
        return ArchivesSpaceAncestorToReference.apply(value)


class ArchivesSpaceArchivalObjectToObject(odin.Mapping):
    """Maps ASArchivalObjects to Objects object."""
    from_obj = archivesspace.ArchivesSpaceArchivalObject
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
            value = [json_codec.loads(json.dumps(d), archivesspace.ArchivesSpaceDate) for d in self.aspace_helper.closest_parent_value(self.source.uri, 'dates')]
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

    @odin.map_list_field(from_field='rights_statements', to_field='rights')
    def rights(self, value):
        return ArchivesSpaceRightsStatementToRightsStatement.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return ArchivesSpaceLinkedAgentToReference.apply(value)

    @odin.map_list_field(from_field='ancestors', to_field='ancestors')
    def ancestors(self, value):
        return ArchivesSpaceAncestorToReference.apply(value)


class ArchivesSpaceSubjectToTerm(odin.Mapping):
    """Maps ASSubject to Term object."""
    from_obj = archivesspace.ArchivesSpaceSubject
    to_obj = Term

    @odin.map_field(from_field='terms', to_field='term_type')
    def type(self, value):
        return next(iter(value), None).term_type

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAgentCorporateEntityToAgent(odin.Mapping):
    """Maps ASAgent Corporate Entities to Agent object."""
    from_obj = archivesspace.ArchivesSpaceAgentCorporateEntity
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
    """Maps ASAgent Family to Agent object."""
    from_obj = archivesspace.ArchivesSpaceAgentFamily
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
    """Maps ASAgent Person to Agent object."""
    from_obj = archivesspace.ArchivesSpaceAgentPerson
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
