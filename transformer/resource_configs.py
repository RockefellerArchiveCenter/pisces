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
    ('single', 'Single'),
    ('inclusive', 'Inclusive'),
    ('bulk', 'Bulk')
)

DATE_LABEL_CHOICES = (
    ('agent_relation', 'Agent Relation'),
    ('broadcast', 'Broadcast'),
    ('copyright', 'Copyright'),
    ('creation', 'Creation'),
    ('deaccession', 'Deaccession'),
    ('digitized', 'Digitized'),
    ('event', 'Event'),
    ('existence', 'Existence'),
    ('issued', 'Issued'),
    ('modified', 'Modified'),
    ('publication', 'Publication'),
    ('record_keeping', 'Record Keeping'),
    ('usage', 'Usage'),
    ('other', 'Other'),
)

EXTENT_TYPE_CHOICES = ( # TODO: update from AS
    ('box(es)', 'Boxes'),
    ('cassettes', 'Cassettes'),
    ('cubic_feet', 'Cubic Feet'),
    ('Cubic Feet', 'Cubic Feet'),
    ('document box(es)', 'Document Boxes'),
    ('files', 'Files'),
    ('gigabytes', 'Gigabytes'),
    ('leaves', 'Leaves'),
    ('linear_feet', 'Linear Feet'),
    ('megabytes', 'Megabytes'),
    ('microform reels', 'Microform Reels'),
    ('photographic_prints', 'Photographic Prints'),
    ('photographic_slides', 'Photographic Slides'),
    ('record cartons', 'Record Cartons'),
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
    ('unspecified', 'Unspecified')
)

NAME_SOURCE_CHOICES = ( # TODO: get from AS
    ('local', 'Local sources'),
    ('naf', 'Library of Congress Name Authority File'),
    ('ingest', 'Ingested'),
)

NAME_RULES_CHOICES = ( # TODO: update from AS
    ('dacs', 'Describing Archives: a Content Standard'),
    ('local', 'Local Rules')
)

NOTE_TYPE_CHOICES = (
  ('abstract', 'Abstract'),
  ('accessrestrict', 'Conditions Governing Access'),
  ('accruals', 'Accruals'),
  ('acqinfo', 'Immediate Source of Acquisition'),
  ('additional_information', 'Additional Information'),
  ('altformavail', 'Existence and Location of Copies'),
  ('appraisal', 'Appraisal'),
  ('arrangement', 'Arrangement'),
  ('bibliography', 'Bibliography'),
  ('bioghist', 'Biographical / Historical'),
  ('custodhist', 'Custodial History'),
  ('dimensions', 'Dimensions'),
  ('edition', 'Edition'),
  ('expiration', 'Expiration'),
  ('extension', 'Extension'),
  ('extent', 'Extent'),
  ('fileplan', 'File Plan'),
  ('inscription', 'Inscription'),
  ('index', 'Index'),
  ('langmaterial', 'Language of Materials'),
  ('legalstatus', 'Legal Status'),
  ('materials', 'Materials'),
  ('materialspec', 'Materials Specific Details'),
  ('note', 'General Note'),
  ('odd', 'General'),
  ('otherfindaid', 'Other Finding Aids'),
  ('originalsloc', 'Existence and Location of Originals'),
  ('permissions', 'Permissions'),
  ('physdesc', 'Physical Description'),
  ('physfacet', 'Physical Facet'),
  ('physloc', 'Physical Location'),
  ('phystech', 'Physical Characteristics and Technical Requirements'),
  ('prefercite', 'Preferred Citation'),
  ('processinfo', 'Processing Information'),
  ('relatedmaterial', 'Related Archival Materials'),
  ('restrictions', 'Restrictions')
  ('rights_statement', 'Rights'),
  ('rights_statement_act', 'Acts'),
  ('scopecontent', 'Scope and Contents'),
  ('separatedmaterial', 'Separated Materials'),
  ('summary', 'Summary'),
  ('type_note', 'Type Note'),
  ('userestrict', 'Conditions Governing Use'),
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

SUBJECT_SOURCE_CHOICES = ( # TODO: add AS subject sources
    ('lcsh', 'Library of Congress Subject Headings'),
    ('local', 'Local sources')
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
