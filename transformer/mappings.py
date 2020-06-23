import json

import odin
from iso639 import languages

from .resources.configs import NOTE_TYPE_CHOICES
from .resources.rac import (Agent, Collection, Date, Extent,
                            ExternalIdentifier, Language, Note, Object,
                            Reference, RightsGranted, RightsStatement, Subnote,
                            Term)
from .resources.source import (SourceAgentCorporateEntity, SourceAgentFamily,
                               SourceAgentPerson, SourceAncestor,
                               SourceArchivalObject, SourceDate, SourceExtent,
                               SourceLinkedAgent, SourceNote, SourceRef,
                               SourceResource, SourceRightsStatement,
                               SourceRightsStatementAct, SourceSubject)


def transform_language(value, lang_materials):
    langz = []
    if value:
        lang_data = languages.get(part2b=value)
        langz.append(Language(expression=lang_data.name, identifier=value))
    elif lang_materials:
        for lang in [l for l in lang_materials if l.language_and_script]:
            langz += transform_language(lang.language_and_script.language, None)
    return langz if len(langz) else Language(expression="English", identifier="eng")


class SourceRightsStatementActToRightsGranted(odin.Mapping):
    """Maps SourceRightsStatementsAct to RightsGranted object."""
    from_obj = SourceRightsStatementAct
    to_obj = RightsGranted

    mappings = (
        ('act_type', None, 'act'),
        ('start_date', None, 'begin'),
        ('end_date', None, 'end'),
        ('restriction', None, 'restriction'),
    )

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def rights_notes(self, value):
        return SourceNoteToNote.apply(value)


class SourceRightsStatementToRightsStatement(odin.Mapping):
    """Maps SourceRightsStatement to RightsStatement object."""
    from_obj = SourceRightsStatement
    to_obj = RightsStatement

    mappings = (
        ('start_date', None, 'begin'),
        ('end_date', None, 'end'),
        ('status', None, 'copyright_status'),
        ('other_rights_basis', None, 'other_basis'),
    )

    @odin.map_list_field(from_field="notes", to_field="rights_notes", to_list=True)
    def rights_notes(self, value):
        return SourceNoteToNote.apply(value)

    @odin.map_list_field(from_field='acts', to_field='rights_granted', to_list=True)
    def rights_granted(self, value):
        return SourceRightsStatementActToRightsGranted.apply(value)


class SourceRefToReference(odin.Mapping):
    """Maps SourceRef to Reference object."""
    from_obj = SourceRef
    to_obj = Reference

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class SourceAncestorToReference(odin.Mapping):
    """Maps SourceAncestor to Reference object."""
    from_obj = SourceAncestor
    to_obj = Reference

    mappings = (
        ('type', None, 'type'),
    )

    @odin.map_field(from_field="title", to_field="title")
    def title(self, value):
        return value.strip() if value else None

    @odin.map_field(from_field="order", to_field="order")
    def order(self, value):
        if value:
            return int(value)

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class SourceLinkedAgentToReference(odin.Mapping):
    """Maps SourceLinkedAgent to Reference object."""
    from_obj = SourceLinkedAgent
    to_obj = Reference

    mappings = (
        ('ref', None, 'title'),
    )

    @odin.map_list_field(from_field='ref', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class SourceDateToDate(odin.Mapping):
    """Maps SourceDate to Date object."""
    from_obj = SourceDate
    to_obj = Date

    mappings = (
        odin.define(from_field='date_type', to_field='type'),
    )

    @odin.map_field
    def expression(self, value):
        if not value:
            value = "{}-{}".format(self.source.begin, self.source.end) if self.source.end else "{}-".format(self.source.begin)
        return value


class SourceExtentToExtent(odin.Mapping):
    """Maps SourceExtent to Extent object."""
    from_obj = SourceExtent
    to_obj = Extent

    mappings = (
        ('extent_type', None, 'type'),
        ('number', None, 'value')
    )


class SourceNoteToNote(odin.Mapping):
    """Maps SourceNote to Note object."""
    from_obj = SourceNote
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
        """Maps Subnotes to values based on the note type."""
        if value.jsonmodel_type == 'note_definedlist':
            subnote = Subnote(type="definedlist", items=value.items)
        elif value.jsonmodel_type == 'note_orderedlist':
            items_list = [{idx: item} for idx, item in enumerate(value.items)]
            subnote = Subnote(type="orderedlist", items=items_list)
        elif value == 'note_bibliography':
            subnote = self.bibliograpy_subnotes(value.content, value.items)
        elif value.jsonmodel_type == 'note_index':
            subnote = self.index_subnotes(value.content, value.items)
        elif value.jsonmodel_type == 'note_chronology':
            subnote = self.chronology_subnotes(value.items)
        else:
            subnote = Subnote(
                type='text', content=value.content
                if isinstance(value.content, list) else [value.content])
        return subnote

    @odin.map_list_field(from_field='subnotes', to_field='subnotes', to_list=True)
    def subnotes(self, value):
        """Handles different note types."""
        if self.source.jsonmodel_type in ['note_multipart', 'note_bioghist']:
            subnotes = (self.map_subnotes(v) for v in value)
        elif self.source.jsonmodel_type in ['note_singlepart', 'note_rights_statement', 'note_rights_statement_act']:
            # Here content is a list passed as a string, so we have to reconvert.
            content = [self.source.content.strip('][\"')]
            subnotes = [Subnote(type='text', content=content)]
        elif self.source.jsonmodel_type == 'note_index':
            subnotes = self.index_subnotes(self.source.content, self.source.items)
        elif self.source.jsonmodel_type == 'note_bibliography':
            subnotes = self.bibliograpy_subnotes(self.source.content, self.source.items)
        elif self.source.jsonmodel_type == 'note_chronology':
            subnotes = self.chronology_subnotes(self.source.items)
        return subnotes

    def bibliograpy_subnotes(self, content, items):
        data = []
        # Here content is a list passed as a string, so we have to reconvert.
        content = list(self.source.content.strip("]["))
        data.append(Subnote(type='text', content=content))
        data.append(Subnote(type='orderedlist', content=json.loads(items)))
        return data

    def index_subnotes(self, content, items):
        data = []
        items_list = [{'label': i.get('type'), 'value': i.get('value')} for i in items]
        data.append(Subnote(type='text', content=json.loads(content)))
        data.append(Subnote(type='definedlist', items=items_list))
        return data

    def chronology_subnotes(self, items):
        items_list = [{'label': i.get('event_date'), 'value': i.get('events')} for i in items]
        return Subnote(type='definedlist', items=items_list)


class SourceResourceToCollection(odin.Mapping):
    """Maps SourceResource to Collection object."""
    from_obj = SourceResource
    to_obj = Collection

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        return transform_language(value, self.source.lang_materials)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='subjects', to_field='terms')
    def terms(self, value):
        return SourceRefToReference.apply(value)

    @odin.map_list_field(from_field='rights_statements', to_field='rights')
    def rights(self, value):
        return SourceRightsStatementToRightsStatement.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='creators')
    def creators(self, value):
        return [SourceLinkedAgentToReference.apply(v) for v in value if v.role == 'creator']

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return [SourceLinkedAgentToReference.apply(v) for v in value if v.role != 'creator']


class SourceArchivalObjectToCollection(odin.Mapping):
    """Maps SourceArchivalObject to Collection object."""
    from_obj = SourceArchivalObject
    to_obj = Collection

    @odin.map_field
    def title(self, value):
        return value.strip() if value else self.source.display_string.strip()

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        return transform_language(value, self.source.lang_materials)

    @odin.map_list_field(from_field='subjects', to_field='terms')
    def terms(self, value):
        return SourceRefToReference.apply(value)

    # @odin.map_list_field(from_field='dates', to_field='dates')
    # def dates(self, value):
    #     return SourceDateToDate.apply(value)

    @odin.map_list_field(from_field='rights_statements', to_field='rights')
    def rights(self, value):
        return SourceRightsStatementToRightsStatement.apply(value)

    # @odin.map_list_field(from_field='extents', to_field='extents')
    # def extents(self, value):
    #     return SourceExtentToExtent.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='creators')
    def creators(self, value):
        return [SourceLinkedAgentToReference.apply(v) for v in value if v.role == 'creator']

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return [SourceLinkedAgentToReference.apply(v) for v in value if v.role != 'creator']

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='ancestors', to_field='ancestors')
    def ancestors(self, value):
        return SourceAncestorToReference.apply(value)


class SourceArchivalObjectToObject(odin.Mapping):
    """Maps SourceArchivalObject to Objects object."""
    from_obj = SourceArchivalObject
    to_obj = Object

    mappings = (
        odin.define(from_field='position', to_field='tree_position'),
    )

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field
    def title(self, value):
        return value.strip() if value else self.source.display_string.strip()

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        return transform_language(value, self.source.lang_materials)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.map_list_field(from_field='subjects', to_field='terms')
    def terms(self, value):
        return SourceRefToReference.apply(value)

    @odin.map_list_field(from_field='rights_statements', to_field='rights')
    def rights(self, value):
        return SourceRightsStatementToRightsStatement.apply(value)

    @odin.map_list_field(from_field='linked_agents', to_field='agents')
    def agents(self, value):
        return SourceLinkedAgentToReference.apply(value)

    @odin.map_list_field(from_field='ancestors', to_field='ancestors')
    def ancestors(self, value):
        return SourceAncestorToReference.apply(value)


class SourceSubjectToTerm(odin.Mapping):
    """Maps SourceSubject to Term object."""
    from_obj = SourceSubject
    to_obj = Term

    @odin.map_field(from_field='terms', to_field='term_type')
    def type(self, value):
        return next(iter(value), None).term_type

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class SourceAgentCorporateEntityToAgent(odin.Mapping):
    """Maps SourceAgentCorporateEntity to Agent object."""
    from_obj = SourceAgentCorporateEntity
    to_obj = Agent

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.assign_field(to_field='agent_type')
    def agent_types(self):
        return "organization"


class SourceAgentFamilyToAgent(odin.Mapping):
    """Maps SourceAgentFamily to Agent object."""
    from_obj = SourceAgentFamily
    to_obj = Agent

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.assign_field(to_field='agent_type')
    def agent_types(self):
        return "family"


class SourceAgentPersonToAgent(odin.Mapping):
    """Maps SourceAgentPerson to Agent object."""
    from_obj = SourceAgentPerson
    to_obj = Agent

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]

    @odin.assign_field(to_field='agent_type')
    def agent_types(self):
        return "person"
