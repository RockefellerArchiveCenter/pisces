import json
import re
import xml.etree.ElementTree as ET

import odin
import requests
from iso639 import languages

from fetcher.helpers import identifier_from_uri
from pisces import settings

from .resources.configs import NOTE_TRANSFORM_TYPES, config_list
from .resources.rac import (Agent, AgentReference, Collection, Date, Extent,
                            ExternalIdentifier, Group, Language, Note, Object,
                            RecordReference, Subnote, Term, TermReference)
from .resources.source import (SourceAgentCorporateEntity, SourceAgentFamily,
                               SourceAgentPerson, SourceAncestor,
                               SourceArchivalObject, SourceDate, SourceExtent,
                               SourceGroup, SourceLinkedAgent, SourceNote,
                               SourceRef, SourceResource, SourceStructuredDate,
                               SourceSubject)


def convert_dates(value):
    """Converts agent dates.

    Allows agent dates to be either SourceDate or SourceStructuredDate to
    accommodate AS API 3.0 changes. This logic could be simplified once we have
    migrated to AS 3.0."""
    if len(value) and value[0]["jsonmodel_type"] == "structured_date_label":
        return SourceStructuredDateToDate.apply(
            [odin.codecs.json_codec.loads(json.dumps(v), resource=SourceStructuredDate) for v in value]
        )
    else:
        return SourceDateToDate.apply(
            [odin.codecs.json_codec.loads(json.dumps(v), resource=SourceDate) for v in value]
        )


def has_online_asset(identifier):
    req = requests.head("{}/pdfs/{}".format(settings.ASSET_BASEURL.rstrip("/"), identifier))
    return True if req.status_code == 200 else False


def has_online_instance(instances, uri):
    try:
        digital_instances = [v for v in instances if v.instance_type == "digital_object"]
    except AttributeError:
        digital_instances = [v for v in instances if v["instance_type"] == "digital_object"]
    if len(digital_instances):
        if has_online_asset(identifier_from_uri(uri)):
            return True
    return False


def strip_tags(user_string):
    """Strips XML and HTML tags from a string."""
    try:
        xmldoc = ET.fromstring(f'<xml>{user_string}</xml>')
        textcontent = ''.join(xmldoc.itertext())
    except ET.ParseError:
        tagregxp = re.compile(r'<[/\w][^>]+>')
        textcontent = tagregxp.sub('', user_string)
    return textcontent


def transform_language(value, lang_materials):
    langz = []
    if value:
        lang_data = languages.get(part2b=value)
        langz.append(Language(expression=lang_data.name, identifier=value))
    elif lang_materials:
        for lang in [lng for lng in lang_materials if lng.language_and_script]:
            langz += transform_language(lang.language_and_script.language, None)
    return langz if len(langz) else [Language(expression="English", identifier="eng")]


def transform_formats(instances, subjects, ancestors):
    ancestor_subjects = []
    for a in ancestors:
        if a.subjects:
            ancestor_subjects += a.subjects
    combined_subjects = subjects + ancestor_subjects
    formats = ["documents"]
    for refs, format in [
            (settings.MOVING_IMAGE_REFS, "moving image"),
            (settings.AUDIO_REFS, "audio"),
            (settings.PHOTOGRAPH_REFS, "photographs")]:
        if len([s for s in combined_subjects if s.ref in refs]):
            formats.append(format)
    return formats


def transform_group(value, prefix):
    group = SourceGroupToGroup.apply(value)
    group.identifier = "/{}/{}".format(prefix, identifier_from_uri(value.identifier))
    return group


class SourceRefToTermReference(odin.Mapping):
    """Maps SourceRef to TermReference object."""
    from_obj = SourceRef
    to_obj = TermReference

    mappings = (
        ("type", None, "type"),
    )

    @odin.map_field(from_field="title", to_field="title")
    def title(self, value):
        return value.strip()

    @odin.map_list_field(from_field="ref", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="ref", to_field="identifier")
    def identifier(self, value):
        return identifier_from_uri(value)


class SourceAncestorToRecordReference(odin.Mapping):
    """Maps SourceAncestor to RecordReference object."""
    from_obj = SourceAncestor
    to_obj = RecordReference

    mappings = (
        ("type", None, "type"),
        ("dates", None, "dates"),
    )

    @odin.map_field(from_field="title", to_field="title")
    def title(self, value):
        return strip_tags(value.strip())

    @odin.map_field(from_field="order", to_field="order")
    def order(self, value):
        return int(value) if value else None

    @odin.map_field(from_field="ref", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="ref", to_field="identifier")
    def identifier(self, value):
        return identifier_from_uri(value)


class SourceLinkedAgentToAgentReference(odin.Mapping):
    """Maps SourceLinkedAgent to AgentReference object."""
    from_obj = SourceLinkedAgent
    to_obj = AgentReference

    mappings = (
        ("relator", None, "relator"),
        ("role", None, "role")
    )

    @odin.map_field(from_field="type", to_field="type")
    def type(self, value):
        AGENT_MAP = {
            "agent_corporate_entity": "organization",
            "agent_person": "person",
            "agent_family": "family"
        }
        return AGENT_MAP[value]

    @odin.map_field(from_field="title", to_field="title")
    def title(self, value):
        return strip_tags(value.strip())

    @odin.map_list_field(from_field="ref", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="ref", to_field="identifier")
    def identifier(self, value):
        return identifier_from_uri(value)


class SourceStructuredDateToDate(odin.Mapping):
    """Maps SourceStructuredDate to Date object."""
    from_obj = SourceStructuredDate
    to_obj = Date

    mappings = (
        odin.define(from_field="date_type_structured", to_field="type"),
        odin.define(from_field="date_label", to_field="label")
    )

    @odin.map_field(from_field="date_type_structured", to_field="begin")
    def begin(self, value):
        if value == "single":
            return self.source.structured_date_single.date_standardized
        else:
            return self.source.structured_date_range.begin_date_standardized

    @odin.map_field(from_field="date_type_structured", to_field="end")
    def end(self, value):
        if value == "single":
            return self.source.structured_date_single.date_standardized
        else:
            return self.source.structured_date_range.end_date_standardized

    @odin.map_field(from_field="date_type_structured", to_field="expression")
    def expression(self, value):
        if value == "single":
            date_obj = self.source.structured_date_single
            return date_obj.date_expression if date_obj.date_expression else date_obj.date_standardized
        else:
            date_obj = self.source.structured_date_range
            begin = date_obj.begin_date_expression if date_obj.begin_date_expression else date_obj.begin_date_standardized
            end = date_obj.end_date_expression if date_obj.end_date_expression else date_obj.end_date_standardized
            return "{}-{}".format(begin, end)


class SourceDateToDate(odin.Mapping):
    """Maps SourceDate to Date object."""
    from_obj = SourceDate
    to_obj = Date

    mappings = (
        odin.define(from_field="date_type", to_field="type"),
    )

    @odin.map_field(from_field="end", to_field="end")
    def end(self, value):
        return self.source.begin if self.source.date_type == "single" else value

    @odin.map_field(from_field="expression", to_field="expression")
    def expression(self, value):
        if not value:
            value = "{}-{}".format(self.source.begin, self.source.end) if self.source.end else "{}-".format(self.source.begin)
        return value


class SourceExtentToExtent(odin.Mapping):
    """Maps SourceExtent to Extent object."""
    from_obj = SourceExtent
    to_obj = Extent

    mappings = (
        ("extent_type", None, "type"),
        ("number", None, "value")
    )


class SourceGroupToGroup(odin.Mapping):
    """Maps SourceGroup to Group.

    Since the structure of these object is exactly the same, all field mappings
    can be assumed. Identifier is overwritten via customized mappings in each
    object type.
    """
    from_obj = SourceGroup
    to_obj = Group

    @odin.assign_field(to_field="category")
    def category(self):
        category = "collection"
        if "corporate_entities" in self.source.identifier:
            category = "organization"
        elif "subjects" in self.source.identifier:
            category = "subject"
        elif any(t in self.source.identifier for t in ["families", "people"]):
            category = "person"
        return category

    @odin.map_list_field(from_field="dates", to_field="dates")
    def dates(self, value):
        return convert_dates(value)


class SourceNoteToNote(odin.Mapping):
    """Maps SourceNote to Note object."""
    from_obj = SourceNote
    to_obj = Note

    @odin.map_field(from_field="type", to_field="title")
    def title(self, value):
        if self.source.label:
            title = self.source.label
        elif value:
            title = [v[1] for v in config_list('note_types') if v[0] == value][0]
        else:
            title = [v[1] for v in config_list('note_types') if v[0] == self.source.jsonmodel_type.split("note_")[1]][0]
        return title

    @odin.map_field(from_field="type", to_field="type")
    def type(self, value):
        return value if value else self.source.jsonmodel_type.split("note_", 1)[1]

    def map_subnotes(self, value):
        """Maps Subnotes to values based on the note type."""
        if value.jsonmodel_type == "note_definedlist":
            subnote = Subnote(type="definedlist", items=value.items)
        elif value.jsonmodel_type == "note_orderedlist":
            items_list = [{idx: item} for idx, item in enumerate(value.items)]
            subnote = Subnote(type="orderedlist", items=items_list)
        elif value == "note_bibliography":
            subnote = self.bibliograpy_subnotes(value.content, value.items)
        elif value.jsonmodel_type == "note_index":
            subnote = self.index_subnotes(value.content, value.items)
        elif value.jsonmodel_type == "note_chronology":
            subnote = self.chronology_subnotes(value.items)
        else:
            subnote = Subnote(
                type="text", content=[strip_tags(c) for c in value.content]
                if isinstance(value.content, list) else [strip_tags(value.content)])
        return subnote

    @odin.map_list_field(from_field="subnotes", to_field="subnotes", to_list=True)
    def subnotes(self, value):
        """Handles different note types."""
        if self.source.jsonmodel_type in ["note_multipart", "note_bioghist"]:
            subnotes = (self.map_subnotes(v) for v in value)
        elif self.source.jsonmodel_type in ["note_singlepart"]:
            # Here content is a list passed as a string, so we have to reconvert.
            content = [self.source.content.strip("][\"\'")]
            subnotes = [Subnote(type="text", content=[strip_tags(c) for c in content])]
        elif self.source.jsonmodel_type == "note_index":
            subnotes = self.index_subnotes(self.source.content, self.source.items)
        elif self.source.jsonmodel_type == "note_bibliography":
            subnotes = self.bibliograpy_subnotes(self.source.content, self.source.items)
        elif self.source.jsonmodel_type == "note_chronology":
            subnotes = self.chronology_subnotes(self.source.items)
        return subnotes

    def bibliograpy_subnotes(self, raw_content, items):
        data = []
        # Here content is a list passed as a string, so we have to reconvert.
        content = [raw_content.strip("][\'")]
        data.append(Subnote(type="text", content=[strip_tags(c) for c in content]))
        data.append(Subnote(type="orderedlist", content=items))
        return data

    def index_subnotes(self, content, items):
        data = []
        items_list = [{"label": i.get("type"), "value": i.get("value")} for i in items]
        data.append(Subnote(type="text", content=json.loads(content)))
        data.append(Subnote(type="definedlist", items=items_list))
        return data

    def chronology_subnotes(self, items):
        items_list = [{"label": i.get("event_date"), "value": i.get("events")} for i in items]
        return Subnote(type="definedlist", items=items_list)


class SourceResourceToCollection(odin.Mapping):
    """Maps SourceResource to Collection object."""
    from_obj = SourceResource
    to_obj = Collection

    @odin.map_field(from_field="title", to_field="title")
    def title(self, value):
        return strip_tags(value)

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def notes(self, value):
        return SourceNoteToNote.apply([v for v in value if (v.publish and v.type in NOTE_TRANSFORM_TYPES)])

    @odin.map_list_field(from_field="dates", to_field="dates")
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field(from_field="language", to_field="languages", to_list=True)
    def languages(self, value):
        return transform_language(value, self.source.lang_materials)

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/collections/{}".format(identifier_from_uri(value))

    @odin.map_list_field(from_field="subjects", to_field="terms")
    def terms(self, value):
        return SourceRefToTermReference.apply(value)

    @odin.map_list_field(from_field="linked_agents", to_field="creators")
    def creators(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.role == "creator"]

    @odin.map_list_field(from_field="linked_agents", to_field="people")
    def people(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_person"]

    @odin.map_list_field(from_field="linked_agents", to_field="organizations")
    def organizations(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_corporate_entity"]

    @odin.map_list_field(from_field="linked_agents", to_field="families")
    def families(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_family"]

    @odin.map_list_field(from_field="instances", to_field="formats")
    def formats(self, value):
        return transform_formats(value, self.source.subjects, self.source.ancestors)

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        return transform_group(value, "collections")

    @odin.map_field(from_field="ancestors", to_field="parent")
    def parent(self, value):
        return identifier_from_uri(value[0].ref) if value else None


class SourceArchivalObjectToCollection(odin.Mapping):
    """Maps SourceArchivalObject to Collection object."""
    from_obj = SourceArchivalObject
    to_obj = Collection

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def notes(self, value):
        return SourceNoteToNote.apply([v for v in value if (v.publish and v.type in NOTE_TRANSFORM_TYPES)])

    @odin.map_field
    def title(self, value):
        title = value.strip() if value else self.source.display_string.strip()
        if getattr(self.source, "component_id", None):
            title = "{}, {} {}".format(title, self.source.level.capitalize(), self.source.component_id)
        return strip_tags(title)

    @odin.map_field(from_field="language", to_field="languages", to_list=True)
    def languages(self, value):
        return transform_language(value, self.source.lang_materials)

    @odin.map_list_field(from_field="subjects", to_field="terms")
    def terms(self, value):
        return SourceRefToTermReference.apply(value)

    @odin.map_list_field(from_field="linked_agents", to_field="creators")
    def creators(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.role == "creator"]

    @odin.map_list_field(from_field="linked_agents", to_field="people")
    def people(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_person"]

    @odin.map_list_field(from_field="linked_agents", to_field="organizations")
    def organizations(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_corporate_entity"]

    @odin.map_list_field(from_field="linked_agents", to_field="families")
    def families(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_family"]

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/collections/{}".format(identifier_from_uri(value))

    @odin.map_list_field(from_field="instances", to_field="formats")
    def formats(self, value):
        return transform_formats(value, self.source.subjects, self.source.ancestors)

    @odin.map_field(from_field="instances", to_field="online")
    def online(self, value):
        return has_online_instance(value, self.source.uri)

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        return transform_group(value, "collections")

    @odin.map_field(from_field="ancestors", to_field="parent")
    def parent(self, value):
        return identifier_from_uri(value[0].ref)


class SourceArchivalObjectToObject(odin.Mapping):
    """Maps SourceArchivalObject to Objects object."""
    from_obj = SourceArchivalObject
    to_obj = Object

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def notes(self, value):
        return SourceNoteToNote.apply([v for v in value if (v.publish and v.type in NOTE_TRANSFORM_TYPES)])

    @odin.map_list_field(from_field="dates", to_field="dates")
    def dates(self, value):
        return SourceDateToDate.apply(value)

    @odin.map_field
    def title(self, value):
        title = value.strip() if value else self.source.display_string.strip()
        return strip_tags(title)

    @odin.map_field(from_field="language", to_field="languages", to_list=True)
    def languages(self, value):
        return transform_language(value, self.source.lang_materials)

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/objects/{}".format(identifier_from_uri(value))

    @odin.map_list_field(from_field="subjects", to_field="terms")
    def terms(self, value):
        return SourceRefToTermReference.apply(value)

    @odin.map_list_field(from_field="linked_agents", to_field="people")
    def people(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_person"]

    @odin.map_list_field(from_field="linked_agents", to_field="organizations")
    def organizations(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_corporate_entity"]

    @odin.map_list_field(from_field="linked_agents", to_field="families")
    def families(self, value):
        return [SourceLinkedAgentToAgentReference.apply(v) for v in value if v.type == "agent_family"]

    @odin.map_list_field(from_field="instances", to_field="formats")
    def formats(self, value):
        return transform_formats(value, self.source.subjects, self.source.ancestors)

    @odin.map_field(from_field="instances", to_field="online")
    def online(self, value):
        return has_online_instance(value, self.source.uri)

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        return transform_group(value, "collections")

    @odin.map_field(from_field="ancestors", to_field="parent")
    def parent(self, value):
        return identifier_from_uri(value[0].ref)


class SourceSubjectToTerm(odin.Mapping):
    """Maps SourceSubject to Term object."""
    from_obj = SourceSubject
    to_obj = Term

    @odin.map_field(from_field="terms", to_field="term_type")
    def type(self, value):
        return next(iter(value), None).term_type

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/terms/{}".format(identifier_from_uri(value))

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        return transform_group(value, "terms")


class SourceAgentCorporateEntityToAgentReference(odin.Mapping):
    """Maps SourceAgentCorporateEntity to an AgentReference object."""
    from_obj = SourceAgentCorporateEntity
    to_obj = AgentReference

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.assign_field(to_field="type")
    def reference_type(self):
        return "organization"

    @odin.map_field(from_field="uri", to_field="identifier")
    def identifier(self, value):
        return identifier_from_uri(value)

    @odin.assign_field(to_field="role")
    def role(self):
        return "creator"


class SourceAgentCorporateEntityToAgent(odin.Mapping):
    """Maps SourceAgentCorporateEntity to Agent object."""
    from_obj = SourceAgentCorporateEntity
    to_obj = Agent

    mappings = (
        odin.define(from_field="title", to_field="authorized_name"),
    )

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def notes(self, value):
        return SourceNoteToNote.apply([v for v in value if (v.publish and v.jsonmodel_type.split("_")[-1] in NOTE_TRANSFORM_TYPES)])

    @odin.map_list_field(from_field="dates_of_existence", to_field="dates")
    def dates(self, value):
        return convert_dates(value)

    @odin.map_field(from_field="agent_record_identifiers", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        external_ids = [ExternalIdentifier(identifier=v.record_identifier, source=v.source) for v in value] if value else []
        return external_ids + [ExternalIdentifier(identifier=self.source.uri, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/agents/{}".format(identifier_from_uri(value))

    @odin.assign_field(to_field="agent_type")
    def agent_types(self):
        return "organization"

    @odin.assign_field(to_field="category")
    def category(self):
        return "organization"

    @odin.map_list_field(from_field="jsonmodel_type", to_field="organizations")
    def organizations(self, value):
        return [SourceAgentCorporateEntityToAgentReference.apply(self.source)]

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        return transform_group(value, "agents")


class SourceAgentFamilyToAgentReference(odin.Mapping):
    """Maps SourceAgentCorporateEntity to an AgentReference object."""
    from_obj = SourceAgentFamily
    to_obj = AgentReference

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.assign_field(to_field="type")
    def reference_type(self):
        return "family"

    @odin.map_field(from_field="uri", to_field="identifier")
    def identifier(self, value):
        return identifier_from_uri(value)

    @odin.assign_field(to_field="role")
    def role(self):
        return "creator"


class SourceAgentFamilyToAgent(odin.Mapping):
    """Maps SourceAgentFamily to Agent object."""
    from_obj = SourceAgentFamily
    to_obj = Agent

    mappings = (
        odin.define(from_field="title", to_field="authorized_name"),
    )

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def notes(self, value):
        return SourceNoteToNote.apply([v for v in value if (v.publish and v.jsonmodel_type.split("_")[-1] in NOTE_TRANSFORM_TYPES)])

    @odin.map_list_field(from_field="dates_of_existence", to_field="dates")
    def dates(self, value):
        return convert_dates(value)

    @odin.map_field(from_field="agent_record_identifiers", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        external_ids = [ExternalIdentifier(identifier=v.record_identifier, source=v.source) for v in value] if value else []
        return external_ids + [ExternalIdentifier(identifier=self.source.uri, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/agents/{}".format(identifier_from_uri(value))

    @odin.assign_field(to_field="agent_type")
    def agent_types(self):
        return "family"

    @odin.assign_field(to_field="category")
    def category(self):
        return "person"

    @odin.map_list_field(from_field="jsonmodel_type", to_field="families")
    def families(self, value):
        return [SourceAgentFamilyToAgentReference.apply(self.source)]

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        return transform_group(value, "agents")


class SourceAgentPersonToAgentReference(odin.Mapping):
    """Maps SourceAgentCorporateEntity to an AgentReference object."""
    from_obj = SourceAgentPerson
    to_obj = AgentReference

    @odin.map_field(from_field="uri", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        return [ExternalIdentifier(identifier=value, source="archivesspace")]

    @odin.assign_field(to_field="type")
    def reference_type(self):
        return "person"

    @odin.map_field(from_field="uri", to_field="identifier")
    def identifier(self, value):
        return identifier_from_uri(value)

    @odin.assign_field(to_field="role")
    def role(self):
        return "creator"


class SourceAgentPersonToAgent(odin.Mapping):
    """Maps SourceAgentPerson to Agent object."""
    from_obj = SourceAgentPerson
    to_obj = Agent

    mappings = (
        odin.define(from_field="title", to_field="authorized_name"),
    )

    def parse_name(self, value):
        """Parses names of people agents."""
        first_name = value.rest_of_name if value.rest_of_name else ""
        last_name = value.primary_name if value.primary_name else ""
        return f'{first_name} {last_name}'.strip()

    @odin.map_field(from_field="display_name", to_field="title")
    def title(self, value):
        return self.parse_name(value)

    @odin.map_list_field(from_field="notes", to_field="notes", to_list=True)
    def notes(self, value):
        return SourceNoteToNote.apply([v for v in value if (v.publish and v.jsonmodel_type.split("_")[-1] in NOTE_TRANSFORM_TYPES)])

    @odin.map_list_field(from_field="dates_of_existence", to_field="dates")
    def dates(self, value):
        return convert_dates(value)

    @odin.map_field(from_field="agent_record_identifiers", to_field="external_identifiers", to_list=True)
    def external_identifiers(self, value):
        external_ids = [ExternalIdentifier(identifier=v.record_identifier, source=v.source) for v in value] if value else []
        return external_ids + [ExternalIdentifier(identifier=self.source.uri, source="archivesspace")]

    @odin.map_field(from_field="uri", to_field="uri")
    def uri(self, value):
        return "/agents/{}".format(identifier_from_uri(value))

    @odin.assign_field(to_field="agent_type")
    def agent_types(self):
        return "person"

    @odin.assign_field(to_field="category")
    def category(self):
        return "person"

    @odin.map_list_field(from_field="jsonmodel_type", to_field="people")
    def people(self, value):
        return [SourceAgentPersonToAgentReference.apply(self.source)]

    @odin.map_field(from_field="group", to_field="group")
    def group(self, value):
        value.title = self.parse_name(self.source.display_name)
        return transform_group(value, "agents")
