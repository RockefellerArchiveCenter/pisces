import odin

from .resources import *


class ArchivesSpaceResourceToCollection(odin.Mapping):
    from_obj = ArchivesSpaceResource
    to_obj = Collection


class ArchivesSpaceArchivalObjectToCollection(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Collection


class ArchivesSpaceArchivalObjectToObject(odin.Mapping):
    from_obj = ArchivesSpaceArchivalObject
    to_obj = Object


class ArchivesSpaceSubjectToTerm(odin.Mapping):
    from_obj = ArchivesSpaceSubject
    to_obj = Term


class ArchivesSpaceAgentCorporateEntityToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentCorporateEntity
    to_obj = Agent


class ArchivesSpaceAgentFamilyToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentFamily
    to_obj = Agent


class ArchivesSpaceAgentPersonToAgent(odin.Mapping):
    from_obj = ArchivesSpaceAgentPerson
    to_obj = Agent
