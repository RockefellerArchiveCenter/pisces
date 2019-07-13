import odin

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


class ArchivesSpaceNoteToNote(odin.Mapping):
    from_obj = ArchivesSpaceNote
    to_obj = Note


    # TO
    # type = odin.StringField(choices=resource_configs.NOTE_TYPE_CHOICES)
    # title = odin.StringField()
    # source = odin.StringField(choices=resource_configs.SOURCE_CHOICES)
    # subnotes = odin.ArrayOf(Subnote)


class ArchivesSpaceRightsStatementToRightsStatement(odin.Mapping):
    from_obj = ArchivesSpaceRightsStatement
    to_obj = RightsStatement


class ArchivesSpaceResourceToCollection(odin.Mapping):
    from_obj = ArchivesSpaceResource
    to_obj = Collection


class ArchivesSpaceArchivalObjectToCollection(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Collection


class ArchivesSpaceArchivalObjectToObject(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Object

    def convert_dates(dates):
        return (ArchivesSpaceDateToDate.apply(d) for d in dates)

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
        odin.define(from_field='subjects', to_field='terms'),
        odin.define(from_field='linked_agents', to_field='agents'),
        odin.define(from_field='parent', to_field='parent'),
        odin.define(from_field='dates', to_field='dates', action=convert_dates, to_list=True),
    )

    @odin.map_field
    def title(self, value):
        return value or self.source.display_string


class ArchivesSpaceSubjectToTerm(odin.Mapping):
    from_obj = ArchivesSpaceSubject
    to_obj = Term

    @odin.map_field(from_field='terms', to_field='type')
    def type(self, value):
        return next(iter(value), None).term_type


class ArchivesSpaceAgentCorporateEntityToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentCorporateEntity
    to_obj = Agent

    def convert_dates(dates):
        return (ArchivesSpaceDateToDate.apply(d) for d in dates)

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
        odin.define(from_field='dates_of_existence', to_field='dates', action=convert_dates, to_list=True)
    )


class ArchivesSpaceAgentFamilyToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentFamily
    to_obj = Agent

    def convert_dates(dates):
        return (ArchivesSpaceDateToDate.apply(d) for d in dates)

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
        odin.define(from_field='dates_of_existence', to_field='dates', action=convert_dates, to_list=True)
    )


class ArchivesSpaceAgentPersonToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentPerson
    to_obj = Agent

    def convert_dates(dates):
        return (ArchivesSpaceDateToDate.apply(d) for d in dates)

    mappings = (
        odin.define(from_field='jsonmodel_type', to_field='type'),
        odin.define(from_field='dates_of_existence', to_field='dates', action=convert_dates, to_list=True)
    )
