"""Source resources and their fields.

The resources in this file come from RAC data sources, including ArchivesSpace
and Cartographer, as well as external sources such as Wikipedia and Wikidata.
It is assumed that data from multiple sources will have been merged it is used
to instantiate these resources.
"""

import odin

from . import configs


class SourceAncestor(odin.Resource):
    """Indicates the fields included in an AS ancestor resource."""
    ref = odin.StringField()
    level = odin.StringField()


class SourceRef(odin.Resource):
    """Indicates the fields included in an AS ref resource."""
    ref = odin.StringField()


class SourceDate(odin.Resource):
    """Indicates the fields included in an AS date resource."""
    expression = odin.StringField(null=True)
    begin = odin.StringField(null=True)
    end = odin.StringField(null=True)
    date_type = odin.StringField(choices=configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=configs.DATE_LABEL_CHOICES)


class SourceExtent(odin.Resource):
    """Indicates the fields included in an AS extent resource."""
    number = odin.StringField()
    container_summary = odin.StringField(null=True)
    portion = odin.StringField(choices=(('whole', 'Whole'), ('part', 'Part'))),
    extent_type = odin.StringField(choices=configs.EXTENT_TYPE_CHOICES)


class SourceExternalId(odin.Resource):
    """Indicates the fields included in an AS external id resource."""
    external_id = odin.StringField()
    source = odin.StringField()


class SourceSubcontainer(odin.Resource):
    """Indicates the fields included in an AS sub container resource."""
    indicator_2 = odin.StringField()
    type_2 = odin.StringField(choices=configs.CONTAINER_TYPE_CHOICES)
    top_container = odin.DictAs(SourceRef)


class SourceInstance(odin.Resource):
    """Indicates the fields included in an AS instance resource."""
    instance_type = odin.StringField(choices=configs.INSTANCE_TYPE_CHOICES)
    is_representative = odin.BooleanField()
    sub_container = odin.DictAs(SourceSubcontainer)


class SourceLinkedAgent(odin.Resource):
    """Indicates the fields included in an AS linked agent resource."""
    role = odin.StringField(choices=configs.AGENT_ROLE_CHOICES)
    relator = odin.StringField(choices=configs.AGENT_RELATOR_CHOICES, null=True)
    ref = odin.StringField()


class SourceNameBase(odin.Resource):
    """Indicates the fields included in an AS name resource. Used in Family, Corporate Entity, and Personal name resources."""
    sort_name = odin.StringField()
    authorized = odin.BooleanField()
    is_display_name = odin.BooleanField()
    use_dates = odin.ArrayOf(SourceDate)
    rules = odin.StringField(choices=configs.NAME_RULES_CHOICES, null=True)
    source = odin.StringField(choices=configs.NAME_SOURCE_CHOICES, null=True)


class SourceNameCorporateEntity(SourceNameBase):
    """Indicates the fields included in an AS corporate entity name resource."""
    primary_name = odin.StringField()


class SourceNameFamily(SourceNameBase):
    """Indicates the fields included in an AS family name resource."""
    family_name = odin.StringField()


class SourceNamePerson(SourceNameBase):
    primary_name = odin.StringField()
    rest_of_name = odin.StringField(null=True)
    name_order = odin.StringField(choices=(('direct', 'Direct'), ('inverted', 'Inverted')))


class SourceSubnote(odin.Resource):
    """Indicates the fields included in an AS subnote resource."""
    jsonmodel_type = odin.StringField()
    content = odin.StringField(null=True)
    items = odin.StringField(null=True)


class SourceNote(odin.Resource):
    """Indicates the fields included in an AS note resource."""
    jsonmodel_type = odin.StringField()
    type = odin.StringField(null=True)
    label = odin.StringField(null=True)
    subnotes = odin.ArrayOf(SourceSubnote, null=True)
    content = odin.StringField(null=True)
    items = odin.StringField(null=True)


class SourceRightsStatementAct(odin.Resource):
    """Indicates the fields included in an AS rights statement act resource."""
    act_type = odin.StringField()
    start_date = odin.DateField()
    end_date = odin.DateField(null=True)
    restriction = odin.StringField()
    notes = odin.ArrayOf(SourceNote)


class SourceRightsStatement(odin.Resource):
    """Indicates the fields included in an AS rights statement resource."""
    determination_date = odin.DateField(null=True)
    rights_type = odin.StringField()
    start_date = odin.DateField()
    end_date = odin.DateField(null=True)
    status = odin.StringField(null=True)
    other_rights_basis = odin.StringField(null=True)
    jurisdiction = odin.StringField(null=True)
    notes = odin.ArrayOf(SourceNote)
    acts = odin.ArrayOf(SourceRightsStatementAct)


class SourceTerm(odin.Resource):
    """Indicates the fields included in an AS term resource."""
    term_type = odin.StringField(choices=configs.TERM_TYPE_CHOICES)


class SourceSubject(odin.Resource):
    """Indicates the fields included in an AS subject resource."""
    title = odin.StringField()
    terms = odin.ArrayOf(SourceTerm)
    uri = odin.StringField()


class SourceComponentBase(odin.Resource):
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
    level = odin.StringField()
    jsonmodel_type = odin.StringField(choices=COMPONENT_TYPES)
    external_ids = odin.ArrayOf(SourceExternalId)
    subjects = odin.ArrayOf(SourceRef)
    extents = odin.ArrayOf(SourceExtent)
    dates = odin.ArrayOf(SourceDate)
    rights_statements = odin.ArrayOf(SourceRightsStatement)
    linked_agents = odin.ArrayOf(SourceLinkedAgent)
    notes = odin.ArrayOf(SourceNote)
    uri = odin.StringField()


class SourceArchivalObject(SourceComponentBase):
    """Indicates the fields included in an AS archival object resource."""
    position = odin.IntegerField()
    ref_id = odin.StringField()
    component_id = odin.StringField(null=True)
    display_string = odin.StringField()
    language = odin.StringField(null=True)
    restrictions_apply = odin.BooleanField()
    ancestors = odin.ArrayOf(SourceAncestor)
    resource = odin.DictAs(SourceRef)
    parent = odin.DictAs(SourceRef, null=True)
    has_unpublished_ancestor = odin.BooleanField()
    children = odin.ArrayOf(SourceAncestor, null=True)
    instances = odin.ArrayOf(SourceInstance)


class SourceResource(SourceComponentBase):
    """Indicates the fields included in an AS resource resource."""
    restrictions = odin.BooleanField()
    ead_id = odin.StringField(null=True)
    finding_aid_title = odin.StringField(null=True)
    finding_aid_filing_title = odin.StringField(null=True)
    language = odin.StringField()
    id_0 = odin.StringField()
    id_1 = odin.StringField(null=True)
    id_0 = odin.StringField(null=True)
    children = odin.ArrayOf(SourceAncestor)
    tree = odin.DictAs(SourceRef)


class SourceSubject(odin.Resource):
    """Indicates the fields included in an AS subject resource."""
    title = odin.StringField()
    source = odin.StringField(choices=configs.SUBJECT_SOURCE_CHOICES)
    external_ids = odin.ArrayOf(SourceExternalId)
    publish = odin.BooleanField()
    terms = odin.ArrayOf(SourceSubject)
    uri = odin.StringField()


class SourceAgentBase(odin.Resource):
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
    notes = odin.ArrayOf(SourceNote)
    dates_of_existence = odin.ArrayOf(SourceDate)
    title = odin.StringField()
    uri = odin.StringField()


class SourceAgentCorporateEntity(SourceAgentBase):
    """Indicates the fields included in an AS agent corporate entity resource."""
    names = odin.ArrayOf(SourceNameCorporateEntity)
    display_name = odin.DictAs(SourceNameCorporateEntity)


class SourceAgentFamily(SourceAgentBase):
    """Indicates the fields included in an AS agent family resource."""
    names = odin.ArrayOf(SourceNameFamily)
    display_name = odin.DictAs(SourceNameFamily)


class SourceAgentPerson(SourceAgentBase):
    """Indicates the fields included in an AS agent person resource."""
    names = odin.ArrayOf(SourceNamePerson)
    display_name = odin.DictAs(SourceNamePerson)
