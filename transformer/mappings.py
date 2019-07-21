import odin
from iso639 import languages

from .resources import *


class ArchivesSpaceRefToRef(odin.Mapping):
    from_obj = ArchivesSpaceRef
    to_obj = Ref


class ArchivesSpaceAncestorToRef(odin.Mapping):
    from_obj = ArchivesSpaceAncestor
    to_obj = Ref


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


class ArchivesSpaceSubnoteToSubnote(odin.Mapping):
    from_obj = ArchivesSpaceSubnote
    to_obj = Subnote

    @odin.map_field(from_field='jsonmodel_type')
    def type(self, value):
        if value:
            if value in ['note_orderedlist', 'note_definedlist']:
                return Subnote(type=value.split('note_')[1], content=self.source.items)
            elif value == 'note_bibliography':
                data = []
                data.append(Subnote(type='text', content=self.source.content))
                data.append(Subnote(type='orderedlist', content=self.source.items))
                return data
            elif value == 'note_index':
                data = []
                l = [{'label': i.get('type'), 'value': i.get('value')} for i in self.source.items]
                data.append(Subnote(type='text', content=self.source.content))
                data.append(Subnote(type='definedlist', content=l))
                return data
            elif value == 'note_chronology':
                m = [{'label': i.get('event_date'), 'value': ', '.join(i.get('events'))} for i in self.source.items]
                return Subnote(type='definedlist', content=m)
            else:
                return Subnote(type='text', content=self.source.content
                               if isinstance(self.source.content, list) else [self.source.content])


class ArchivesSpaceNoteToNote(odin.Mapping):
    from_obj = ArchivesSpaceNote
    to_obj = Note

    @odin.map_field(from_field='label', to_field='title')
    def title(self, value):
        return value if value else 'Note'

    @odin.map_field(from_field='jsonmodel_type', to_field='type')
    def type(self, value):
        return value.split('note_',1)[1]

    @odin.map_list_field(from_field='subnotes', to_field='subnotes', to_list=True)
    def subnotes(self, value):
        if value:
            return (ArchivesSpaceSubnoteToSubnote.apply(v) for v in value)

    @odin.map_field(from_field='content', to_field='subnotes', to_list=True)
    def subnotes(self, value):
        if value:
            return Subnote(type='text', content=value)

    @odin.map_field(from_field='items', to_field='subnotes', to_list=True)
    def subnotes(self, value):
        if value:
            return Subnote(type='orderedlist', content=value)


class ArchivesSpaceRightsStatementActToRightsGranted(odin.Mapping):
    from_obj = ArchivesSpaceRightsStatementAct
    to_obj = RightsGranted

    mappings = (
        ('act_type', None, 'act'),
        ('start_date', None, 'dateStart'),
        ('end_date', None, 'dateEnd'),
        ('restriction', None, 'restriction'),
        ('notes', None, 'notes')
    )


class ArchivesSpaceRightsStatementToRightsStatement(odin.Mapping):
    from_obj = ArchivesSpaceRightsStatement
    to_obj = RightsStatement

    mappings = (
        ('determination_date', None, 'determinationDate'),
        ('rights_type', None, 'type'),
        ('start_date', None, 'dateStart'),
        ('end_date', None, 'dateEnd'),
        ('status', None, 'copyrightStatus'),
        ('other_rights_basis', None, 'otherBasis'),
        ('jurisdiction', None, 'jurisdiction'),
        ('notes', None, 'notes'),
        ('acts', None, 'rights_granted'),
    )


class ArchivesSpaceResourceToCollection(odin.Mapping):
    from_obj = ArchivesSpaceResource
    to_obj = Collection

    mappings = (
        odin.define(from_field='subjects', to_field='terms'),
        odin.define(from_field='linked_agents', to_field='agents'),
    )

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceArchivalObjectToCollection(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Collection

    mappings = (
        odin.define(from_field='subjects', to_field='terms'),
        odin.define(from_field='linked_agents', to_field='agents'),
    )

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        if value:
            lang_data = languages.get(part2b=value)
            return Language(expression=lang_data.name, identifier=value)
        return []

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceArchivalObjectToObject(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Object

    mappings = (
        odin.define(from_field='position', to_field='tree_position'),
        odin.define(from_field='subjects', to_field='terms'),
        odin.define(from_field='linked_agents', to_field='agents'),
        odin.define(from_field='parent', to_field='parent'),
    )

    @odin.map_list_field(from_field='dates', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field
    def title(self, value):
        return value if value else self.source.display_string

    @odin.map_field(from_field='language', to_field='languages', to_list=True)
    def languages(self, value):
        if value:
            lang_data = languages.get(part2b=value)
            return Language(expression=lang_data.name, identifier=value)
        return []

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceSubjectToTerm(odin.Mapping):
    from_obj = ArchivesSpaceSubject
    to_obj = Term

    @odin.map_field(from_field='terms', to_field='type')
    def type(self, value):
        return next(iter(value), None).term_type

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAgentCorporateEntityToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentCorporateEntity
    to_obj = Agent

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
    )

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAgentFamilyToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentFamily
    to_obj = Agent

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
    )

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]


class ArchivesSpaceAgentPersonToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentPerson
    to_obj = Agent

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
    )

    @odin.map_list_field(from_field='dates_of_existence', to_field='dates')
    def dates(self, value):
        return ArchivesSpaceDateToDate.apply(value)

    @odin.map_field(from_field='uri', to_field='external_identifiers', to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source='archivesspace')]
