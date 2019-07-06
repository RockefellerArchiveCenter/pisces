import odin


class Agent(odin.Resource):
    title = odin.StringField()
    type = odin.StringField()
    description = odin.StringField(null=True)
    dates = odin.ArrayOf(Date)
    collections = odin.ArrayOf(Collection)
    objects = odin.ArrayOf(Object)
    notes = odin.ArrayOf(Note)


class Collection(odin.Resource):
    LEVEL_CHOICES = (
        ('class', 'Class'),
        ('collection', 'Collection'),
        ('file', 'File'),
        ('fonds', 'Fonds'),
        ('item', 'Item'),
        ('otherlevel', 'Other Level'),
        ('recordgrp', 'Record Group'),
        ('series', 'Series'),
        ('subfonds', 'Sub-Fonds'),
        ('subgrp', 'Sub-Group'),
        ('subseries', 'Sub-Series'),
    )
    title = odin.StringField()
    level = odin.StringField(choices=LEVEL_CHOICES)
    dates = odin.ArrayOf(Date)
    creators = odin.ArrayOf(Agent)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    agents = odin.ArrayOf(Agent)
    terms = odin.ArrayOf(Term)
    parent = odin.DictOf(Collection)
    children = odin.ArrayOf(Collection)
    ancestors = odin.ArrayOf(Collection)
    rights_statements = odin.ArrayOf(RightsStatement)


class Object(odin.Resource):
    title = odin.StringField()
    dates = odin.ArrayOf(Date)
    languages = odin.ArrayOf(Language)
    extents = odin.ArrayOf(Extent)
    notes = odin.ArrayOf(Note)
    agents = odin.ArrayOf(Agent)
    terms = odin.ArrayOf(Term)
    parent = odin.DictOf(Collection)
    ancestors = odin.ArrayOf(Collection)
    rights_statements = odin.ArrayOf(RightsStatement)


class Term(odin.Resource):
    TERM_TYPE_CHOICES = (
        ('cultural_context', 'Cultural context'),
        ('function', 'Function'),
        ('geographic', 'Geographic'),
        ('genre_form', 'Genre / Form'),
        ('occupation', 'Occupation'),
        ('style_period', 'Style / Period'),
        ('technique', 'Technique'),
        ('temporal', 'Temporal'),
        ('topical', 'Topical'),
    )
    title = odin.StringField()
    type = odin.StringField(choices=TERM_TYPE_CHOICES)
    notes = odin.ArrayOf(Note)


class RightsStatement(odin.Resource):
    RIGHTS_TYPE_CHOICES = (
        ('copyright', 'Copyright'),
        ('statute', 'Statute'),
        ('license', 'License'),
        ('other', 'Other')
    )
    COPYRIGHT_STATUSES = (
        ('copyrighted', 'copyrighted'),
        ('public domain', 'public domain'),
        ('unknown', 'unknown'),
    )
    determinationDate = odin.DateTimeField()
    rightsType = odin.StringField(choices=RIGHTS_TYPE_CHOICES)
    dateStart = odin.DateTimeField()
    dateEnd = odin.DateTimeField()
    copyrightStatus = odin.StringField(choices=COPYRIGHT_STATUSES, null=True)
    otherBasis = odin.StringField(null=True)
    jurisdiction = odin.StringField(null=True)
    notes = odin.ArrayOf(Note)
    rights_granted = odin.ArrayOf(RightsGranted)


class RightsGranted(odin.Resource):
    ACT_CHOICES = (
        ('publish', 'Publish'),
        ('disseminate', 'Disseminate'),
        ('replicate', 'Replicate'),
        ('migrate', 'Migrate'),
        ('modify', 'Modify'),
        ('use', 'Use'),
        ('delete', 'Delete'),
    )
    RESTRICTION_CHOICES = (
        ('allow', 'Allow'),
        ('disallow', 'Disallow'),
        ('conditional', 'Conditional'),
    )
    act = odin.StringField(choices=ACT_CHOICES)
    dateStart = odin.DateTimeField()
    dateEnd = odin.DateTimeField()
    restriction = odin.StringField(choices=RESTRICTION_CHOICES)
    note = odin.DictOf(Note)


class Date(odin.Resource):
    DATE_TYPE_CHOICES = (
        ('record_keeping', 'Record Keeping'),
        ('broadcast', 'Broadcast'),
        ('copyright', 'Copyright'),
        ('creation', 'Creation'),
        ('deaccession', 'Deaccession'),
        ('agent_relation', 'Agent Relation'),
        ('digitized', 'Digitized'),
        ('existence', 'Existence'),
        ('event', 'Event'),
        ('issued', 'Issued'),
        ('modified', 'Modified'),
        ('publication', 'Publication'),
        ('usage', 'Usage'),
        ('other', 'Other'),
    )
    begin = odin.DateTimeField()
    end = odin.DateTimeField()
    expression = odin.StringField()
    label = odin.StringField(choices=DATE_TYPE_CHOICES)


class Extent(odin.Resource):
    EXTENT_TYPE_CHOICES = (
        ('cassettes', 'Cassettes'),
        ('cubic_feet', 'Cubic Feet'),
        ('files', 'Files'),
        ('gigabytes', 'Gigabytes'),
        ('leaves', 'Leaves'),
        ('linear_feet', 'Linear Feet'),
        ('megabytes', 'Megabytes'),
        ('photographic_prints', 'Photographic Prints'),
        ('photographic_slides', 'Photographic Slides'),
        ('reels', 'Reels'),
        ('sheets', 'Sheets'),
        ('terabytes', 'Terabytes'),
        ('volumes', 'Volumes'),
    )
    value = odin.FloatField()
    type = odin.StringField(choices=EXTENT_TYPE_CHOICES)


class Note(odin.Resource):
    SOURCE_CHOICES = (
        ('archivesspace', 'ArchivesSpace'),
        ('cartographer', 'Cartographer'),
        ('wikidata', 'Wikidata'),
        ('wikipedia', 'Wikipedia')
    )
    NOTE_TYPE_CHOICES = (
      ('accessrestrict', 'Conditions Governing Access'),
      ('accruals', 'Accruals'),
      ('acqinfo', 'Immediate Source of Acquisition'),
      ('altformavail', 'Existence and Location of Copies'),
      ('appraisal', 'Appraisal'),
      ('arrangement', 'Arrangement'),
      ('bibliography', 'Bibliography'),
      ('bioghist', 'Biographical / Historical'),
      ('custodhist', 'Custodial History'),
      ('fileplan', 'File Plan'),
      ('index', 'Index'),
      ('odd', 'General'),
      ('otherfindaid', 'Other Finding Aids'),
      ('originalsloc', 'Existence and Location of Originals'),
      ('phystech', 'Physical Characteristics and Technical Requirements'),
      ('prefercite', 'Preferred Citation'),
      ('processinfo', 'Processing Information'),
      ('relatedmaterial', 'Related Archival Materials'),
      ('scopecontent', 'Scope and Contents'),
      ('separatedmaterial', 'Separated Materials'),
      ('userestrict', 'Conditions Governing Use'),
      ('dimensions', 'Dimensions'),
      ('legalstatus', 'Legal Status'),
      ('summary', 'Summary'),
      ('edition', 'Edition'),
      ('extent', 'Extent'),
      ('note', 'General Note'),
      ('inscription', 'Inscription'),
      ('langmaterial', 'Language of Materials'),
      ('physdesc', 'Physical Description'),
      ('relatedmaterial', 'Related Materials'),
      ('abstract', 'Abstract'),
      ('physloc', 'Physical Location'),
      ('materialspec', 'Materials Specific Details'),
      ('physfacet', 'Physical Facet'),
      ('rights_statement', 'Rights'),
      ('rights_statement_act', 'Acts'),
      ('materials', 'Materials'),
      ('type_note', 'Type Note'),
      ('additional_information', 'Additional Information'),
      ('expiration', 'Expiration'),
      ('extension', 'Extension'),
      ('permissions', 'Permissions'),
      ('restrictions', 'Restrictions')
    )
    type = odin.StringField(choices=NOTE_TYPE_CHOICES)
    title = odin.StringField()
    source = odin.StringField(choices=SOURCE_CHOICES)
    subnotes = odin.ArrayOf(Subnote)


class Subnote(odin.Resource):
    SUBNOTE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('orderedlist', 'Ordered List'),
        ('definedlist', 'Defined List'),
    )
    type = odin.StringField(choices=SUBNOTE_TYPE_CHOICES)
    title = odin.StringField()


class Language(odin.Resource):
    expression = odin.StringField()
    identifier = odin.StringField()


####################################
# ArchivesSpace Resources
####################################

class ArchivesSpaceComponentBase(odin.Resource):
    class Meta:
        abstract = True

    COMPONENT_TYPES = (
        ('archival_object', 'Archival Object'),
        ('resource', 'Resource')
    )

    LEVEL_TYPES = ( # ArchivesSpace levels
        ()
    )

    publish = odin.BooleanField()
    title = odin.StringField()
    suppressed = odin.StringField()
    level = odin.StringField(choices=LEVEL_TYPES)
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
    position = odin.IntegerField()
    ref_id = odin.StringField()
    component_id = odin.StringField()
    display_string = odin.StringField()
    restrictions_apply = odin.BooleanField()
    ancestors = odin.ArrayOf(ArchivesSpaceAncestor)
    resource = odin.DictOf(ArchivesSpaceRef)
    parent = odin.DictOf(ArchivesSpaceRef)
    has_unpublished_ancestor = odin.BooleanField()


class ArchivesSpaceResource(ArchivesSpaceComponentBase):
    restrictions = odin.BooleanField()
    ead_id = odin.StringField()
    finding_aid_title = odin.StringField()
    finding_aid_filing_title = odin.StringField()
    finding_aid_date = odin.DateField()
    id_0 = odin.StringField()
    language = odin.StringField()
    tree = odin.DictOf(ArchivesSpaceRef)


class ArchivesSpaceSubject(odin.Resource):
    SUBJECT_SOURCE_CHOICES = ( # TODO: add AS subject sources
        ()
    )
    SUBJECT_TYPE_CHOICES = (
        ('subject', 'Subject')
    )

    title = odin.StringField()
    source = odin.StringField(choices=SUBJECT_SOURCE_CHOICES)
    jsonmodel_type = odin.StringField(choices=SUBJECT_TYPE_CHOICES)
    external_ids = odin.ArrayOf(ArchivesSpaceExternalId)
    publish = odin.BooleanField()
    terms = odin.ArrayOf(ArchivesSpaceTerm)
    uri = odin.StringField()


class ArchivesSpaceAgentBase(odin.Resource):
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
    names = odin.ArrayOf(ArchivesSpaceName)
    # related_agents = odin.ArrayOf()
    uri = odin.StringField()
    display_name = odin.DictOf(ArchivesSpaceName)
    title = odin.StringField()


class ArchivesSpaceAgentCorporateEntity(ArchivesSpaceAgentBase): pass


class ArchivesSpaceAgentFamily(ArchivesSpaceAgentBase): pass


class ArchivesSpaceAgentPerson(ArchivesSpaceAgentBase): pass


class ArchivesSpaceAncestor(odin.Resource): pass


class ArchivesSpaceDate(odin.Resource): pass


class ArchivesSpaceExtent(odin.Resource): pass


class ArchivesSpaceExternalId(odin.Resource): pass


class ArchivesSpaceInstance(odin.Resource): pass


class ArchivesSpaceLinkedAgent(odin.Resource): pass


class ArchivesSpaceName(odin.Resource): pass


class ArchivesSpaceNote(odin.Resource): pass


class ArchivesSpaceRef(odin.Resource): pass


class ArchivesSpaceRightsStatement(odin.Resource): pass


class ArchivesSpaceTerm(odin.Resource): pass
