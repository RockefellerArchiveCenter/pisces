AGENT_RELATOR_CHOICES = (
    ()
)

AGENT_ROLE_CHOICES = (
    ()
)

CONTAINER_TYPE_CHOICES = ( # TODO: add from AS
    ()
)

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

INSTANCE_TYPE_CHOICES = ( # TODO: add from AS
    ()
)

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

NAME_SOURCE_CHOICES = (
    ()
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

RIGHTS_ACT_CHOICES = (
    ('publish', 'Publish'),
    ('disseminate', 'Disseminate'),
    ('replicate', 'Replicate'),
    ('migrate', 'Migrate'),
    ('modify', 'Modify'),
    ('use', 'Use'),
    ('delete', 'Delete'),
)

RIGHTS_COPYRIGHT_STATUSES = (
    ('copyrighted', 'copyrighted'),
    ('public domain', 'public domain'),
    ('unknown', 'unknown'),
)

RIGHTS_RESTRICTION_CHOICES = (
    ('allow', 'Allow'),
    ('disallow', 'Disallow'),
    ('conditional', 'Conditional'),
)

RIGHTS_TYPE_CHOICES = (
    ('copyright', 'Copyright'),
    ('statute', 'Statute'),
    ('license', 'License'),
    ('other', 'Other')
)

SOURCE_CHOICES = (
    ('archivesspace', 'ArchivesSpace'),
    ('cartographer', 'Cartographer'),
    ('wikidata', 'Wikidata'),
    ('wikipedia', 'Wikipedia')
)

SUBNOTE_TYPE_CHOICES = (
    ('text', 'Text'),
    ('orderedlist', 'Ordered List'),
    ('definedlist', 'Defined List'),
)

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
