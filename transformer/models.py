from django.db import models
from django.contrib.postgres.fields import JSONField
from itertools import chain
from operator import attrgetter


class TransformRun(models.Model):
    STARTED = 0
    FINISHED = 1
    ERRORED = 2
    STATUS_CHOICES = (
        (STARTED, 'Started'),
        (FINISHED, 'Finished'),
        (ERRORED, 'Errored'),
    )
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    PISCES = 4
    CARTOGRAPHER = 5
    TREES = 6
    WIKIDATA = 7
    WIKIPEDIA = 8
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (PISCES, 'Pisces'),
        (CARTOGRAPHER, 'Cartographer'),
        (TREES, 'Trees'),
        (WIKIDATA, 'Wikidata'),
        (WIKIPEDIA, 'Wikipedia')
    )
    OBJECT_TYPE_CHOICES = (
        ('agents', 'Agents'),
        ('collections', 'Collections'),
        ('objects', 'Objects'),
        ('terms', 'Terms')
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPE_CHOICES, null=True, blank=True)


class TransformRunError(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    run = models.ForeignKey(TransformRun, on_delete=models.CASCADE)


class Language(models.Model):
    expression = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)

    def __str__(self): return self.expression


class Agent(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    wikipedia_url = models.URLField(null=True, blank=True)
    wikidata_id = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self): return self.title if self.title else "Agent ({})".format(self.pk)

    def collections(self):
        return set(chain(self.agent_collections.all(), self.creator_collections.all()))


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

    def __str__(self): return self.title if self.title else "Term ({})".format(self.pk)


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
    tree_order = models.IntegerField(null=True, blank=True)
    source_tree = JSONField()
    creators = models.ManyToManyField(Agent, related_name='creator_collections')
    languages = models.ManyToManyField(Language, related_name='language_collections')
    agents = models.ManyToManyField(Agent, related_name='agent_collections')
    terms = models.ManyToManyField(Term, related_name='term_collections')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self): return self.title if self.title else "Collection ({})".format(self.pk)

    def has_children(self):
        return bool([len(self.collection_set.all()), len(self.object_set.all())])

    def children(self):
        # This is probably not the most performant way to do this.
        return sorted(list(chain(self.collection_set.all(), self.object_set.all())), key=attrgetter('tree_order'))

    def ancestors(self):
        return self.get_ancestor(self.parent, [])

    def get_ancestor(self, ancestor, array):
        if ancestor:
            array.insert(0, ancestor)
            if ancestor.parent:
                self.get_ancestor(ancestor.parent, array)
        return array


class Object(models.Model):
    title = models.CharField(max_length=16384, null=True, blank=True)
    tree_order = models.IntegerField(null=True, blank=True)
    agents = models.ManyToManyField(Agent, related_name='agent_objects')
    terms = models.ManyToManyField(Term, related_name='term_objects')
    languages = models.ManyToManyField(Language, related_name='language_objects')
    parent = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self): return self.title if self.title else "Object ({})".format(self.pk)

    def ancestors(self):
        return self.get_ancestor(self.parent, [])

    def get_ancestor(self, ancestor, array):
        if ancestor:
            array.insert(0, ancestor)
            if ancestor.parent:
                self.get_ancestor(ancestor.parent, array)
        return array


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

    def __str__(self): return self.expression


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

    def __str__(self): return "{} {}".format(self.value, self.type)


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
    type = models.CharField(max_length=100, choices=NOTE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    rights_statement = models.ForeignKey(RightsStatement, on_delete=models.CASCADE, null=True, blank=True)
    rights_granted = models.ForeignKey(RightsGranted, on_delete=models.CASCADE, null=True, blank=True)


class Subnote(models.Model):
    SUBNOTE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('orderedlist', 'Ordered List'),
        ('definedlist', 'Defined List'),
    )
    type = models.CharField(max_length=100, choices=SUBNOTE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = JSONField()
    note = models.ForeignKey(Note, on_delete=models.CASCADE)


class Identifier(models.Model):
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    PISCES = 4
    CARTOGRAPHER = 5
    WIKIDATA = 6
    WIKIPEDIA = 7
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (PISCES, 'Pisces'),
        (CARTOGRAPHER, 'Cartographer'),
        (WIKIDATA, 'Wikidata'),
        (WIKIPEDIA, 'Wikipedia')
    )
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    identifier = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self): return "{}: {}".format(self.source, self.identifier)


class SourceData(models.Model):
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    CARTOGRAPHER = 4
    WIKIDATA = 5
    WIKIPEDIA = 6
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (CARTOGRAPHER, 'Cartographer'),
        (WIKIDATA, 'Wikidata'),
        (WIKIPEDIA, 'Wikipedia')
    )
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    data = JSONField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self): return "{} {}".format(self.source, self.created)
