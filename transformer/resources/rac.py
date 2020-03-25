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
    """A short reference to a first-class entity (Agent, Collection, Object or Term).

    Field-specific notes:
        order: applies only to children and parent Objects and Collections References.
        type: indicates what type of linked object the Reference points to.
        uri: applies only to Terms; a URI for the Term in an external vocabulary.
        relator: applies only to References for Agent objects.
        level: applies only to Collection and Object References.
        identifier: applies only to Terms; an identifier for a Term in an external vocabulary.
    """
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
    order = odin.StringField(null=True)
    title = odin.StringField(null=True)
    type = odin.StringField(choices=configs.REFERENCE_TYPE_CHOICES, null=True)
    uri = odin.StringField(null=True)
    relator = odin.StringField(null=True)
    role = odin.StringField(null=True)
    level = odin.StringField(null=True)
    identifier = odin.StringField(null=True)


class Date(odin.Resource):
    """Records the dates associated with an aggregation of archival records."""
    # TODO REMOVE DEFAULT WHEN DATE PARSING IS ADDED
    begin = odin.DateTimeField(default="2019")
    end = odin.DateTimeField()
    expression = odin.StringField()
    type = odin.StringField(choices=configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=configs.DATE_LABEL_CHOICES)
    source = odin.StringField(null=True, default='archivesspace', choices=configs.SOURCE_CHOICES)


class Extent(odin.Resource):
    """Records the size of an aggregation of archival records."""
    value = odin.StringField()
    type = odin.StringField(choices=configs.EXTENT_TYPE_CHOICES)


class Language(odin.Resource):
    """A human language."""
    expression = odin.StringField()
    identifier = odin.StringField()


class Term(odin.Resource):
    """A controlled term.

    Term is a first-class entity in the RAC data model.
    """
    title = odin.StringField()
    type = odin.StringField(default="term")
    term_type = odin.StringField(choices=configs.TERM_TYPE_CHOICES)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


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


class Collection(odin.Resource):
    """An aggregation of archival records.

    Collections contain other aggregations of records (either Objects or
    Collections), and may themselves be contained within another Collection.
    Collection is a first-class entity in the RAC data model.
    """
    title = odin.StringField()
    type = odin.StringField(default="collection")
    level = odin.StringField()
    dates = odin.ArrayOf(Date)
    creators = odin.ArrayOf(Reference)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    agents = odin.ArrayOf(Reference)
    terms = odin.ArrayOf(Reference)
    children = odin.ArrayOf(Reference, null=True)
    ancestors = odin.ArrayOf(Reference, null=True)
    rights = odin.ArrayOf(RightsStatement)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


class Object(odin.Resource):
    """An aggregation of archival records.

    Objects may be contained within Collections, but do not contain other
    Objects or Collections. Object is a first-class entity in the RAC data model.
    """
    title = odin.StringField()
    type = odin.StringField(default="object")
    dates = odin.ArrayOf(Date)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    agents = odin.ArrayOf(Reference)
    terms = odin.ArrayOf(Reference)
    ancestors = odin.ArrayOf(Reference, null=True)
    rights = odin.ArrayOf(RightsStatement)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
    tree_position = odin.IntegerField()


class Agent(odin.Resource):
    """A person, family or organization who acts on or is represented in records.

    Agent is a first-class entity in the RAC data model.
    """
    title = odin.StringField()
    type = odin.StringField(default="agent")
    agent_type = odin.StringField()
    description = odin.StringField(null=True)
    dates = odin.ArrayOf(Date)
    collections = odin.ArrayOf(Reference, null=True)
    objects = odin.ArrayOf(Reference, null=True)
    notes = odin.ArrayOf(Note)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
