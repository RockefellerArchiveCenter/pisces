from django.db import models
from django.contrib.postgres.fields import JSONField


class TransformRun(models.Model):
    STARTED = 0
    FINISHED = 1
    ERRORED = 2
    STATUS_CHOICES = (
        (STARTED, 'Started'),
        (FINISHED, 'Finished'),
        (ERRORED, 'Errored'),
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)


class Language(models.Model):
    expression = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)


class Agent(models.Model):
    PERSON = 0
    ORGANIZATION = 1
    FAMILY = 2
    SOFTWARE = 3
    AGENT_TYPE_CHOICES = (
        (PERSON, 'Person'),
        (ORGANIZATION, 'Organization'),
        (FAMILY, 'Family'),
        (SOFTWARE, 'Software'),
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, choices=AGENT_TYPE_CHOICES, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Term(models.Model):
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
    title = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, choices=TERM_TYPE_CHOICES, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Collection(models.Model):
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
    title = models.CharField(max_length=255, null=True, blank=True)
    level = models.CharField(max_length=100, choices=LEVEL_CHOICES, null=True, blank=True)
    tree = JSONField()
    creators = models.ManyToManyField(Agent, related_name='creator_collections')
    languages = models.ManyToManyField(Language, related_name='language_collections')
    agents = models.ManyToManyField(Agent, related_name='agent_collections')
    terms = models.ManyToManyField(Term, related_name='term_collections')
    parents = models.ManyToManyField('self')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Object(models.Model):
    title = models.CharField(max_length=16384, null=True, blank=True)
    agents = models.ManyToManyField(Agent, related_name='agent_objects')
    terms = models.ManyToManyField(Term, related_name='term_objects')
    languages = models.ManyToManyField(Language, related_name='language_objects')
    parents = models.ManyToManyField(Collection)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class RightsStatement(models.Model):
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
    determinationDate = models.DateTimeField(null=True, blank=True)
    rightsType = models.CharField(max_length=255, choices=RIGHTS_TYPE_CHOICES)
    dateStart = models.DateTimeField(null=True, blank=True)
    dateEnd = models.DateTimeField(null=True, blank=True)
    copyrightStatus = models.CharField(max_length=255, choices=COPYRIGHT_STATUSES, blank=True, null=True)
    otherBasis = models.CharField(max_length=255, blank=True, null=True)
    jurisdiction = models.CharField(max_length=255, blank=True, null=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class RightsGranted(models.Model):
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
    rights_statement = models.ForeignKey(RightsStatement, on_delete=models.CASCADE)
    act = models.CharField(max_length=100, choices=ACT_CHOICES)
    dateStart = models.DateTimeField()
    dateEnd = models.DateTimeField(null=True, blank=True)
    restriction = models.CharField(max_length=100, choices=RESTRICTION_CHOICES)


class Date(models.Model):
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
    begin = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    expression = models.CharField(max_length=255)
    label = models.CharField(max_length=100, choices=DATE_TYPE_CHOICES)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)


class Extent(models.Model):
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
    value = models.FloatField()
    type = models.CharField(max_length=100, choices=EXTENT_TYPE_CHOICES)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)


class Note(models.Model):
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
      ('rights_statement', 'Rights')
    )
    type = models.CharField(max_length=100, choices=NOTE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    rights_statement = models.ForeignKey(RightsStatement, on_delete=models.CASCADE, null=True, blank=True)
    rights_granted = models.ForeignKey(RightsGranted, on_delete=models.CASCADE, null=True, blank=True)


class Identifier(models.Model):
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    PISCES = 4
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (PISCES, 'Pisces')
    )
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    identifier = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)


class SourceData(models.Model):
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace')
    )
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    data = JSONField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
