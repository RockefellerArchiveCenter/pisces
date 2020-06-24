"""Source resources and their fields.

The resources in this file come from RAC data sources, including ArchivesSpace
and Cartographer, as well as external sources such as Wikipedia and Wikidata.
It is assumed that data from multiple sources will have been merged it is used
to instantiate these resources.
"""

import odin

from . import configs


class SourceAncestor(odin.Resource):
    """A related SourceResource or SourceArchivalObject.

    SourceAncestors are parents of the current data object. Order is significant; they
    are listed from closest to furthest away (in other words the last ancestor
    will always be the top level of a collection).
    """
    ref = odin.StringField()
    level = odin.StringField()
    order = odin.StringField(null=True)
    title = odin.StringField(null=True)
    type = odin.StringField(null=True)


class SourceRef(odin.Resource):
    """A reference to a related object."""
    ref = odin.StringField()


class SourceDate(odin.Resource):
    """Records the dates associated with an aggregation of archival records."""
    expression = odin.StringField(null=True)
    begin = odin.StringField(null=True)
    end = odin.StringField(null=True)
    date_type = odin.StringField(choices=configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=configs.DATE_LABEL_CHOICES)


class SourceExtent(odin.Resource):
    """Records the size of an aggregation of archival records."""
    number = odin.StringField()
    container_summary = odin.StringField(null=True)
    portion = odin.StringField(choices=(('whole', 'Whole'), ('part', 'Part'))),
    extent_type = odin.StringField()


class SourceExternalId(odin.Resource):
    """Uniquely identifies a data object."""
    external_id = odin.StringField()
    source = odin.StringField()


class SourceLanguageAndScript(odin.Resource):
    """Records the language and scripts of archival records.

    Applies to resources post-ArchivesSpace v2.7 only.
    """
    language = odin.StringField(null=True)


class SourceLangMaterial(odin.Resource):
    """Records information about the languages of archival records.

    Applies to resources post-ArchivesSpace v2.7 only.
    """
    language_and_script = odin.DictAs(SourceLanguageAndScript, null=True)


class SourceSubcontainer(odin.Resource):
    """Provides detailed container information."""
    indicator_2 = odin.StringField(null=True)
    type_2 = odin.StringField(choices=configs.CONTAINER_TYPE_CHOICES, null=True)
    top_container = odin.DictAs(SourceRef)


class SourceInstance(odin.Resource):
    """The physical or digital instantiation of a group of records."""
    instance_type = odin.StringField(choices=configs.INSTANCE_TYPE_CHOICES)
    is_representative = odin.BooleanField()
    sub_container = odin.DictAs(SourceSubcontainer, null=True)
    digital_object = odin.DictAs(SourceRef, null=True)


class SourceLinkedAgent(odin.Resource):
    """A reference to a SourceAgentFamily, SourceAgentPerson or SourceAgentCorporateEntity."""
    role = odin.StringField(choices=configs.AGENT_ROLE_CHOICES)
    relator = odin.StringField(choices=configs.AGENT_RELATOR_CHOICES, null=True)
    ref = odin.StringField()


class SourceNameBase(odin.Resource):
    """Base class for structured representations of names.

    Subclassed by more specific representations SourceNameCorporateEntity,
    SourceNamePerson and SourceNameFamily.
    """
    sort_name = odin.StringField()
    authorized = odin.BooleanField()
    is_display_name = odin.BooleanField()
    use_dates = odin.ArrayOf(SourceDate)
    rules = odin.StringField(choices=configs.NAME_RULES_CHOICES, null=True)
    source = odin.StringField(choices=configs.NAME_SOURCE_CHOICES, null=True)


class SourceNameCorporateEntity(SourceNameBase):
    """A structured representation of an SourceAgentCorporateEntity's name."""
    primary_name = odin.StringField()


class SourceNameFamily(SourceNameBase):
    """A structured representation of a SourceAgentFamily's name."""
    family_name = odin.StringField()


class SourceNamePerson(SourceNameBase):
    """A structured representation of a SourceAgentPerson's name."""
    primary_name = odin.StringField()
    rest_of_name = odin.StringField(null=True)
    name_order = odin.StringField(choices=(('direct', 'Direct'), ('inverted', 'Inverted')))


class SourceSubnote(odin.Resource):
    """Contains note content."""
    jsonmodel_type = odin.StringField()
    content = odin.StringField(null=True)
    items = odin.ArrayField(null=True)


class SourceNote(odin.Resource):
    """Human-readable note.

    SourceNotes contain one or more SourceSubnotes.
    """
    jsonmodel_type = odin.StringField()
    type = odin.StringField(null=True)
    label = odin.StringField(null=True)
    subnotes = odin.ArrayOf(SourceSubnote, null=True)
    content = odin.StringField(null=True)
    items = odin.StringField(null=True)


class SourceRightsStatementAct(odin.Resource):
    """A representation of permissions or restrictions for an aggregation of records."""
    act_type = odin.StringField()
    start_date = odin.DateField()
    end_date = odin.DateField(null=True)
    restriction = odin.StringField()
    notes = odin.ArrayOf(SourceNote)


class SourceRightsStatement(odin.Resource):
    """A PREMIS-compliant rights statement.

    SourceRightsStatements contain once or more SourceRightsStatementActs, which
    document permissions or restrictions on archival records."""
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
    """A controlled term."""
    term_type = odin.StringField(choices=configs.TERM_TYPE_CHOICES)


class SourceSubject(odin.Resource):
    """A topical term."""
    title = odin.StringField()
    source = odin.StringField(choices=configs.SUBJECT_SOURCE_CHOICES)
    external_ids = odin.ArrayOf(SourceExternalId)
    publish = odin.BooleanField()
    terms = odin.ArrayOf(SourceTerm)
    uri = odin.StringField()


class SourceComponentBase(odin.Resource):
    """Base class for archival components.

    Subclassed by SourceArchivalObject and SourceResource.

    Both language and lang_material need to exist in order to accomodate
    ArchivesSpace API changes between v2.6 and v2.7.
    """
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
    language = odin.StringField(null=True)
    lang_materials = odin.ArrayOf(SourceLangMaterial, null=True)
    rights_statements = odin.ArrayOf(SourceRightsStatement)
    linked_agents = odin.ArrayOf(SourceLinkedAgent)
    notes = odin.ArrayOf(SourceNote)
    uri = odin.StringField()


class SourceArchivalObject(SourceComponentBase):
    """A component of a SourceResource."""
    position = odin.IntegerField()
    ref_id = odin.StringField()
    component_id = odin.StringField(null=True)
    display_string = odin.StringField()
    restrictions_apply = odin.BooleanField()
    ancestors = odin.ArrayOf(SourceAncestor)
    resource = odin.DictAs(SourceRef)
    parent = odin.DictAs(SourceRef, null=True)
    has_unpublished_ancestor = odin.BooleanField()
    children = odin.ArrayOf(SourceAncestor, null=True)
    instances = odin.ArrayOf(SourceInstance)


class SourceResource(SourceComponentBase):
    """An aggregation of records.

    SourceResources generally contain SourceArchivalObjects as children.
    """
    restrictions = odin.BooleanField()
    ead_id = odin.StringField(null=True)
    finding_aid_title = odin.StringField(null=True)
    finding_aid_filing_title = odin.StringField(null=True)
    id_0 = odin.StringField()
    id_1 = odin.StringField(null=True)
    id_0 = odin.StringField(null=True)
    children = odin.ArrayOf(SourceAncestor)
    tree = odin.DictAs(SourceRef)


class SourceAgentBase(odin.Resource):
    """A base class for agents.

    Subclassed by SourceAgentFamily, SourceAgentPerson and
    SourceAgentCorporateEntity.
    """
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
    """An organization."""
    names = odin.ArrayOf(SourceNameCorporateEntity)
    display_name = odin.DictAs(SourceNameCorporateEntity)


class SourceAgentFamily(SourceAgentBase):
    """A family."""
    names = odin.ArrayOf(SourceNameFamily)
    display_name = odin.DictAs(SourceNameFamily)


class SourceAgentPerson(SourceAgentBase):
    """A person."""
    names = odin.ArrayOf(SourceNamePerson)
    display_name = odin.DictAs(SourceNamePerson)
