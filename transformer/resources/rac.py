"""RAC data model resources and their fields."""

import odin

from . import configs


class Subnote(odin.Resource):
    """Contains note content."""
    type = odin.StringField(choices=configs.SUBNOTE_TYPE_CHOICES)
    content = odin.StringField(null=True, default=[])
    items = odin.StringField(null=True, default=[])


class Note(odin.Resource):
    """A human-readable note.

    Notes contain one or more Subnotes.
    """
    type = odin.StringField(choices=configs.NOTE_TYPE_CHOICES)
    title = odin.StringField(null=True)
    source = odin.StringField(null=True, default='archivesspace', choices=configs.SOURCE_CHOICES)
    subnotes = odin.ArrayOf(Subnote)


class ExternalIdentifier(odin.Resource):
    """Uniquely identifies a first-class entity."""
    identifier = odin.StringField()
    source = odin.StringField(default='archivesspace', choices=configs.SOURCE_CHOICES)


class Reference(odin.Resource):
    """Base class for short references to a first-class entity (Agent, Collection, Object or Term)."""
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
    title = odin.StringField()
    type = odin.StringField(choices=configs.REFERENCE_TYPE_CHOICES)
    identifier = odin.StringField()


class RecordReference(Reference):
    """Short reference to Collections or Objects."""
    order = odin.StringField()
    level = odin.StringField()
    dates = odin.StringField()
    description = odin.StringField()


class AgentReference(Reference):
    """Short reference to Agents."""
    relator = odin.StringField()
    role = odin.StringField()


class TermReference(Reference):
    """Short reference to Terms."""
    pass


class Date(odin.Resource):
    """Records the dates associated with an aggregation of archival records."""
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    expression = odin.StringField()
    type = odin.StringField(choices=configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=configs.DATE_LABEL_CHOICES)
    source = odin.StringField(null=True, default='archivesspace', choices=configs.SOURCE_CHOICES)


class Extent(odin.Resource):
    """Records the size of an aggregation of archival records."""
    value = odin.StringField()
    type = odin.StringField()


class Group(odin.Resource):
    """Information about the highest-level collection containing the data object."""
    category = odin.StringField()
    creators = odin.ArrayOf(AgentReference, null=True)
    dates = odin.ArrayOf(Date, null=True)
    identifier = odin.StringField()
    title = odin.StringField()


class Language(odin.Resource):
    """A human language."""
    expression = odin.StringField()
    identifier = odin.StringField()


class RightsGranted(odin.Resource):
    """Documents specific permissions or restrictions."""
    act = odin.StringField(choices=configs.RIGHTS_ACT_CHOICES)
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    restriction = odin.StringField(choices=configs.RIGHTS_RESTRICTION_CHOICES)
    notes = odin.ArrayOf(Note)


class RightsStatement(odin.Resource):
    """A PREMIS-compliant rights statement.

    RightsStatements contain once or more RightsGranted, which document
    permissions or restrictions on archival records.
    """
    determination_date = odin.DateTimeField()
    type = odin.StringField(default="rights_statement")
    rights_type = odin.StringField(choices=configs.RIGHTS_TYPE_CHOICES)
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    copyright_status = odin.StringField(choices=configs.RIGHTS_COPYRIGHT_STATUSES, null=True)
    other_basis = odin.StringField(null=True)
    jurisdiction = odin.StringField(null=True)
    rights_notes = odin.ArrayOf(Note)
    rights_granted = odin.ArrayOf(RightsGranted)


class BaseResource(odin.Resource):
    """Base class for all first-class entities in the RAC data model."""
    title = odin.StringField()
    uri = odin.StringField()
    group = odin.DictOf(Group)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


class Term(BaseResource):
    """A controlled term.

    Term is a first-class entity in the RAC data model.
    """
    category = odin.StringField(default="subject")
    type = odin.StringField(default="term")
    term_type = odin.StringField(choices=configs.TERM_TYPE_CHOICES)


class Collection(BaseResource):
    """An aggregation of archival records.

    Collections contain other aggregations of records (either Objects or
    Collections), and may themselves be contained within another Collection.
    Collection is a first-class entity in the RAC data model.
    """
    type = odin.StringField(default="collection")
    category = odin.StringField(default="collection")
    level = odin.StringField()
    dates = odin.ArrayOf(Date)
    creators = odin.ArrayOf(AgentReference)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    people = odin.ArrayOf(AgentReference)
    organizations = odin.ArrayOf(AgentReference)
    families = odin.ArrayOf(AgentReference)
    terms = odin.ArrayOf(TermReference)
    children = odin.ArrayOf(RecordReference, null=True)
    ancestors = odin.ArrayOf(RecordReference, null=True)
    rights = odin.ArrayOf(RightsStatement)
    formats = odin.ArrayField()
    online = odin.BooleanField(default=False)


class Object(BaseResource):
    """An aggregation of archival records.

    Objects may be contained within Collections, but do not contain other
    Objects or Collections. Object is a first-class entity in the RAC data model.
    """
    type = odin.StringField(default="object")
    category = odin.StringField(default="collection")
    dates = odin.ArrayOf(Date)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    people = odin.ArrayOf(AgentReference)
    organizations = odin.ArrayOf(AgentReference)
    families = odin.ArrayOf(AgentReference)
    terms = odin.ArrayOf(TermReference)
    ancestors = odin.ArrayOf(RecordReference, null=True)
    rights = odin.ArrayOf(RightsStatement)
    tree_position = odin.IntegerField()
    formats = odin.ArrayField()
    online = odin.BooleanField(default=False)


class Agent(BaseResource):
    """A person, family or organization who acts on or is represented in records.

    Agent is a first-class entity in the RAC data model.
    """
    type = odin.StringField(default="agent")
    category = odin.StringField()
    agent_type = odin.StringField()
    description = odin.StringField(null=True)
    dates = odin.ArrayOf(Date)
    notes = odin.ArrayOf(Note)
    people = odin.ArrayOf(AgentReference)
    organizations = odin.ArrayOf(AgentReference)
    families = odin.ArrayOf(AgentReference)
