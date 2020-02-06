import odin
from . import resource_configs

"""Lays out the ArchivesSpace resources and their fields as well as the RAC Model resources and their fields.
Used by mappings.py when transforming data from AS resources to RAC resources.
Defaults and choices chosen from resource_configs.py are included here."""

class Subnote(odin.Resource):
    """Sets the fields in the RAC subnote resource."""
    type = odin.StringField(choices=resource_configs.SUBNOTE_TYPE_CHOICES)
    content = odin.StringField()


class Note(odin.Resource):
    """Sets the fields in the RAC note resource."""
    type = odin.StringField(choices=resource_configs.NOTE_TYPE_CHOICES)
    title = odin.StringField(null=True)
    source = odin.StringField(null=True, default='archivesspace', choices=resource_configs.SOURCE_CHOICES)
    subnotes = odin.ArrayOf(Subnote)


class ExternalIdentifier(odin.Resource):
    """Sets the fields in the RAC external identifer resource."""
    identifier = odin.StringField()
    source = odin.StringField(default='archivesspace', choices=resource_configs.SOURCE_CHOICES)


class Reference(odin.Resource):
    """Sets the fields in the RAC reference resource."""
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
    order = odin.StringField(null=True)
    title = odin.StringField(null=True)
    type = odin.StringField(choices=resource_configs.REFERENCE_TYPE_CHOICES, null=True)
    uri = odin.StringField(null=True)
    relator = odin.StringField(null=True)
    role = odin.StringField(null=True)
    level = odin.StringField(null=True)
    expression = odin.StringField(null=True)
    identifier = odin.StringField(null=True)


class Date(odin.Resource):
    """Sets the fields in the RAC date resource."""
    #TODO REMOVE DEFAULT WHEN DATE PARSING IS ADDED
    begin = odin.DateTimeField(default="2019")
    end = odin.DateTimeField()
    expression = odin.StringField()
    type = odin.StringField(choices=resource_configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=resource_configs.DATE_LABEL_CHOICES)
    source = odin.StringField(null=True, default='archivesspace', choices=resource_configs.SOURCE_CHOICES)


class Extent(odin.Resource):
    """Sets the fields in the RAC extent resource."""
    value = odin.StringField()
    type = odin.StringField(choices=resource_configs.EXTENT_TYPE_CHOICES)


class Language(odin.Resource):
    """Sets the fields in the RAC language resource."""
    expression = odin.StringField()
    identifier = odin.StringField()


class Term(odin.Resource):
    """Sets the fields in the RAC term resource."""
    title = odin.StringField()
    type = odin.StringField(default="term")
    term_type = odin.StringField(choices=resource_configs.TERM_TYPE_CHOICES)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


class RightsGranted(odin.Resource):
    """Sets the fields in the RAC rights granted resource."""
    act = odin.StringField(choices=resource_configs.RIGHTS_ACT_CHOICES)
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    restriction = odin.StringField(choices=resource_configs.RIGHTS_RESTRICTION_CHOICES)
    notes = odin.ArrayOf(Note)


class RightsStatement(odin.Resource):
    """Sets the fields in the RAC rights statement resource."""
    determination_date = odin.DateTimeField()
    type = odin.StringField()
    rights_type = odin.StringField(choices=resource_configs.RIGHTS_TYPE_CHOICES)
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    copyright_status = odin.StringField(choices=resource_configs.RIGHTS_COPYRIGHT_STATUSES, null=True)
    other_basis = odin.StringField(null=True)
    jurisdiction = odin.StringField(null=True)
    notes = odin.ArrayOf(Note)
    rights_granted = odin.ArrayOf(RightsGranted)


class Collection(odin.Resource):
    """Sets the fields in the RAC collection resource."""
    title = odin.StringField()
    type = odin.StringField(default="collection")
    level = odin.StringField(choices=resource_configs.LEVEL_CHOICES)
    dates = odin.ArrayOf(Date)
    creators = odin.ArrayOf(Reference)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    agents = odin.ArrayOf(Reference)
    terms = odin.ArrayOf(Reference)
    children = odin.ArrayOf(Reference, null=True)
    ancestors = odin.ArrayOf(Reference, null=True)
    rights_statements = odin.ArrayOf(RightsStatement)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


class Object(odin.Resource):
    """Sets the fields in the RAC object resource."""
    title = odin.StringField()
    type = odin.StringField(default="object")
    dates = odin.ArrayOf(Date)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    agents = odin.ArrayOf(Reference)
    terms = odin.ArrayOf(Reference)
    ancestors = odin.ArrayOf(Reference, null=True)
    rights_statements = odin.ArrayOf(RightsStatement)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
    tree_position = odin.IntegerField()


class Agent(odin.Resource):
    """Sets the fields in the RAC agent resource."""
    title = odin.StringField()
    type = odin.StringField(default="agent")
    agent_type = odin.StringField()
    description = odin.StringField(null=True)
    dates = odin.ArrayOf(Date)
    collections = odin.ArrayOf(Reference, null=True)
    objects = odin.ArrayOf(Reference, null=True)
    notes = odin.ArrayOf(Note)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


####################################
# ArchivesSpace Resources
####################################

class ArchivesSpaceAncestor(odin.Resource):
    """Indicates the fields included in an AS ancestor resource."""
    ref = odin.StringField()
    level = odin.StringField(choices=resource_configs.LEVEL_CHOICES)


class ArchivesSpaceRef(odin.Resource):
    """Indicates the fields included in an AS ref resource."""
    ref = odin.StringField()


class ArchivesSpaceDate(odin.Resource):
    """Indicates the fields included in an AS date resource."""
    expression = odin.StringField(null=True)
    begin = odin.StringField(null=True)
    end = odin.StringField(null=True)
    date_type = odin.StringField(choices=resource_configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=resource_configs.DATE_LABEL_CHOICES)


class ArchivesSpaceExtent(odin.Resource):
    """Indicates the fields included in an AS extent resource."""
    number = odin.StringField()
    container_summary = odin.StringField(null=True)
    portion = odin.StringField(choices=(('whole', 'Whole'), ('part', 'Part'))),
    extent_type = odin.StringField(choices=resource_configs.EXTENT_TYPE_CHOICES)


class ArchivesSpaceExternalId(odin.Resource):
    """Indicates the fields included in an AS external id resource."""
    external_id = odin.StringField()
    source = odin.StringField()


class ArchivesSpaceSubcontainer(odin.Resource):
    """Indicates the fields included in an AS sub container resource."""
    indicator_2 = odin.StringField()
    type_2 = odin.StringField(choices=resource_configs.CONTAINER_TYPE_CHOICES)
    top_container = odin.DictAs(ArchivesSpaceRef)


class ArchivesSpaceInstance(odin.Resource):
    """Indicates the fields included in an AS instance resource."""
    instance_type = odin.StringField(choices=resource_configs.INSTANCE_TYPE_CHOICES)
    is_representative = odin.BooleanField()
    sub_container = odin.DictAs(ArchivesSpaceSubcontainer)


class ArchivesSpaceLinkedAgent(odin.Resource):
    """Indicates the fields included in an AS linked agent resource."""
    role = odin.StringField(choices=resource_configs.AGENT_ROLE_CHOICES)
    relator = odin.StringField(choices=resource_configs.AGENT_RELATOR_CHOICES, null=True)
    ref = odin.StringField()


class ArchivesSpaceNameBase(odin.Resource):
    """Indicates the fields included in an AS name resource. Used in Family, Corporate Entity, and Personal name resources."""
    sort_name = odin.StringField()
    authorized = odin.BooleanField()
    is_display_name = odin.BooleanField()
    use_dates = odin.ArrayOf(ArchivesSpaceDate)
    rules = odin.StringField(choices=resource_configs.NAME_RULES_CHOICES, null=True)
    source = odin.StringField(choices=resource_configs.NAME_SOURCE_CHOICES, null=True)


class ArchivesSpaceNameCorporateEntity(ArchivesSpaceNameBase):
    """Indicates the fields included in an AS corporate entity name resource."""
    primary_name = odin.StringField()


class ArchivesSpaceNameFamily(ArchivesSpaceNameBase):
    """Indicates the fields included in an AS family name resource."""
    family_name = odin.StringField()


class ArchivesSpaceNamePerson(ArchivesSpaceNameBase):
    primary_name = odin.StringField()
    rest_of_name = odin.StringField(null=True)
    name_order = odin.StringField(choices=(('direct', 'Direct'),('inverted', 'Inverted')))


class ArchivesSpaceSubnote(odin.Resource):
    """Indicates the fields included in an AS subnote resource."""
    jsonmodel_type = odin.StringField()
    content = odin.StringField(null=True)
    items = odin.StringField(null=True)


class ArchivesSpaceNote(odin.Resource):
    """Indicates the fields included in an AS note resource."""
    jsonmodel_type = odin.StringField()
    type = odin.StringField(null=True)
    label = odin.StringField(null=True)
    subnotes = odin.ArrayOf(ArchivesSpaceSubnote, null=True)
    content = odin.StringField(null=True)
    items = odin.StringField(null=True)


class ArchivesSpaceRightsStatementAct(odin.Resource):
    """Indicates the fields included in an AS rights statement act resource."""
    act_type = odin.StringField()
    start_date = odin.DateField()
    end_date = odin.DateField(null=True)
    restriction = odin.StringField()
    notes = odin.ArrayOf(ArchivesSpaceNote)


class ArchivesSpaceRightsStatement(odin.Resource):
    """Indicates the fields included in an AS rights statement resource."""
    determination_date = odin.DateField(null=True)
    rights_type = odin.StringField()
    start_date = odin.DateField()
    end_date = odin.DateField(null=True)
    status = odin.StringField(null=True)
    other_rights_basis = odin.StringField(null=True)
    jurisdiction = odin.StringField(null=True)
    notes = odin.ArrayOf(ArchivesSpaceNote)
    acts = odin.ArrayOf(ArchivesSpaceRightsStatementAct)


class ArchivesSpaceTerm(odin.Resource):
    """Indicates the fields included in an AS term resource."""
    term_type = odin.StringField(choices=resource_configs.TERM_TYPE_CHOICES)


class ArchivesSpaceSubject(odin.Resource):
    """Indicates the fields included in an AS subject resource."""
    title = odin.StringField()
    terms = odin.ArrayOf(ArchivesSpaceTerm)
    uri = odin.StringField()


class ArchivesSpaceComponentBase(odin.Resource):
    """Indicates the fields included in an AS component resource. Sets the base fields of an AS component to be used in other
    resources."""
    class Meta:
        abstract = True

    COMPONENT_TYPES = (
        ('archival_object', 'Archival Object'),
        ('resource', 'Resource')
    )

    publish = odin.BooleanField()
    title = odin.StringField(null=True)
    suppressed = odin.StringField()
    level = odin.StringField(choices=resource_configs.LEVEL_CHOICES)
    jsonmodel_type = odin.StringField(choices=COMPONENT_TYPES)
    external_ids = odin.ArrayOf(ArchivesSpaceExternalId)
    subjects = odin.ArrayOf(ArchivesSpaceRef)
    extents = odin.ArrayOf(ArchivesSpaceExtent)
    dates = odin.ArrayOf(ArchivesSpaceDate)
    rights_statements = odin.ArrayOf(ArchivesSpaceRightsStatement)
    linked_agents = odin.ArrayOf(ArchivesSpaceLinkedAgent)
    instances = odin.ArrayOf(ArchivesSpaceInstance)
    notes = odin.ArrayOf(ArchivesSpaceNote)
    uri = odin.StringField()


class ArchivesSpaceArchivalObject(ArchivesSpaceComponentBase):
    """Indicates the fields included in an AS archival object resource."""
    position = odin.IntegerField()
    ref_id = odin.StringField()
    component_id = odin.StringField(null=True)
    display_string = odin.StringField()
    language = odin.StringField(null=True)
    restrictions_apply = odin.BooleanField()
    ancestors = odin.ArrayOf(ArchivesSpaceAncestor)
    resource = odin.DictAs(ArchivesSpaceRef)
    parent = odin.DictAs(ArchivesSpaceRef, null=True)
    has_unpublished_ancestor = odin.BooleanField()


class ArchivesSpaceResource(ArchivesSpaceComponentBase):
    """Indicates the fields included in an AS resource resource."""
    restrictions = odin.BooleanField()
    ead_id = odin.StringField(null=True)
    finding_aid_title = odin.StringField(null=True)
    finding_aid_filing_title = odin.StringField(null=True)
    language = odin.StringField()
    id_0 = odin.StringField()
    id_1 = odin.StringField(null=True)
    id_0 = odin.StringField(null=True)
    tree = odin.DictAs(ArchivesSpaceRef)


class ArchivesSpaceSubject(odin.Resource):
    """Indicates the fields included in an AS subject resource."""
    title = odin.StringField()
    source = odin.StringField(choices=resource_configs.SUBJECT_SOURCE_CHOICES)
    external_ids = odin.ArrayOf(ArchivesSpaceExternalId)
    publish = odin.BooleanField()
    terms = odin.ArrayOf(ArchivesSpaceSubject)
    uri = odin.StringField()


class ArchivesSpaceAgentBase(odin.Resource):
    """Indicates the fields included in an AS agent resource. Sets the base fields of an AS component to be used in other
    agent resources."""
    class Meta:
        abstract = True

    AGENT_TYPES = (
        ('agent_corporate_entity', 'Organization'),
        ('agent_family', 'Family'),
        ('agent_person', 'Person')
    )

    publish = odin.BooleanField()
    jsonmodel_type = odin.StringField(choices=AGENT_TYPES)
    notes = odin.ArrayOf(ArchivesSpaceNote)
    dates_of_existence = odin.ArrayOf(ArchivesSpaceDate)
    title = odin.StringField()
    uri = odin.StringField()


class ArchivesSpaceAgentCorporateEntity(ArchivesSpaceAgentBase):
    """Indicates the fields included in an AS agent corporate entity resource."""
    names = odin.ArrayOf(ArchivesSpaceNameCorporateEntity)
    display_name = odin.DictAs(ArchivesSpaceNameCorporateEntity)


class ArchivesSpaceAgentFamily(ArchivesSpaceAgentBase):
    """Indicates the fields included in an AS agent family resource."""
    names = odin.ArrayOf(ArchivesSpaceNameFamily)
    display_name = odin.DictAs(ArchivesSpaceNameFamily)


class ArchivesSpaceAgentPerson(ArchivesSpaceAgentBase):
    """Indicates the fields included in an AS agent person resource."""
    names = odin.ArrayOf(ArchivesSpaceNamePerson)
    display_name = odin.DictAs(ArchivesSpaceNamePerson)
