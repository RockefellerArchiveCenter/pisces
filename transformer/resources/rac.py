"""RAC Model resources and their fields."""

import odin

from . import configs


class Subnote(odin.Resource):
    """Sets the fields in the RAC subnote resource."""
    type = odin.StringField(choices=configs.SUBNOTE_TYPE_CHOICES)
    content = odin.StringField()


class Note(odin.Resource):
    """Sets the fields in the RAC note resource."""
    type = odin.StringField(choices=configs.NOTE_TYPE_CHOICES)
    title = odin.StringField(null=True)
    source = odin.StringField(null=True, default='archivesspace', choices=configs.SOURCE_CHOICES)
    subnotes = odin.ArrayOf(Subnote)


class ExternalIdentifier(odin.Resource):
    """Sets the fields in the RAC external identifer resource."""
    identifier = odin.StringField()
    source = odin.StringField(default='archivesspace', choices=configs.SOURCE_CHOICES)


class Reference(odin.Resource):
    """Sets the fields in the RAC reference resource."""
    external_identifiers = odin.ArrayOf(ExternalIdentifier)
    order = odin.StringField(null=True)
    title = odin.StringField(null=True)
    type = odin.StringField(choices=configs.REFERENCE_TYPE_CHOICES, null=True)
    uri = odin.StringField(null=True)
    relator = odin.StringField(null=True)
    role = odin.StringField(null=True)
    level = odin.StringField(null=True)
    expression = odin.StringField(null=True)
    identifier = odin.StringField(null=True)


class Date(odin.Resource):
    """Sets the fields in the RAC date resource."""
    # TODO REMOVE DEFAULT WHEN DATE PARSING IS ADDED
    begin = odin.DateTimeField(default="2019")
    end = odin.DateTimeField()
    expression = odin.StringField()
    type = odin.StringField(choices=configs.DATE_TYPE_CHOICES)
    label = odin.StringField(choices=configs.DATE_LABEL_CHOICES)
    source = odin.StringField(null=True, default='archivesspace', choices=configs.SOURCE_CHOICES)


class Extent(odin.Resource):
    """Sets the fields in the RAC extent resource."""
    value = odin.StringField()
    type = odin.StringField(choices=configs.EXTENT_TYPE_CHOICES)


class Language(odin.Resource):
    """Sets the fields in the RAC language resource."""
    expression = odin.StringField()
    identifier = odin.StringField()


class Term(odin.Resource):
    """Sets the fields in the RAC term resource."""
    title = odin.StringField()
    type = odin.StringField(default="term")
    term_type = odin.StringField(choices=configs.TERM_TYPE_CHOICES)
    external_identifiers = odin.ArrayOf(ExternalIdentifier)


class RightsGranted(odin.Resource):
    """Sets the fields in the RAC rights granted resource."""
    act = odin.StringField(choices=configs.RIGHTS_ACT_CHOICES)
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    restriction = odin.StringField(choices=configs.RIGHTS_RESTRICTION_CHOICES)
    notes = odin.ArrayOf(Note)


class RightsStatement(odin.Resource):
    """Sets the fields in the RAC rights statement resource."""
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
    """Sets the fields in the RAC collection resource."""
    title = odin.StringField()
    type = odin.StringField(default="collection")
    level = odin.StringField(choices=configs.LEVEL_CHOICES)
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
    rights = odin.ArrayOf(RightsStatement)
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
