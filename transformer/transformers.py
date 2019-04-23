from dateutil import parser
import json
import os
from pycountry import languages

from django.utils import timezone

from .models import *


class ArchivesSpaceTransformError(Exception): pass
class ArrangementMapTransformError(Exception): pass


class ArrangementMapDataTransformer:
    def __init__(self):
        self.last_run = (TransformRun.objects.filter(status=TransformRun.FINISHED, source=TransformRun.CARTOGRAPHER).order_by('-start_time')[0].start_time
                         if TransformRun.objects.filter(status=TransformRun.FINISHED, source=TransformRun.CARTOGRAPHER).exists() else None)
        self.current_run = TransformRun.objects.create(status=TransformRun.STARTED, source=TransformRun.CARTOGRAPHER)

    def run(self):
        for collection in (Collection.objects.filter(modified__gte=self.last_run, identifier__source=Identifier.CARTOGRAPHER)
                           if self.last_run else Collection.objects.filter(identifier__source=Identifier.CARTOGRAPHER)):
            self.obj = collection
            self.source_data = SourceData.objects.get(collection=self.obj, source=SourceData.CARTOGRAPHER).data
            self.obj.title = self.source_data.get('title')
            if self.source_data.get('arrangement'):
                try:
                    Note.objects.filter(collection=self.obj).delete()
                    note = Note.objects.create(type='arrangement', title="Arrangement", collection=self.obj)
                    Subnote.objects.create(type='text', content=self.source_data.get('arrangement'), note=note)
                except Exception as e:
                    raise ArrangementMapTransformError('Error transforming notes: {}'.format(e))
            if self.source_data.get('parent'):
                self.parent(self.source_data.get('parent'))
            if self.source_data.get('children'):
                self.children(self.source_data.get('children'))
                if not self.obj.parent:
                    self.process_tree(self.source_data.get('children'), 0)
            self.obj.save()
        self.current_run.status = TransformRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def children(self, children):
        for child in children:
            if not child.get('children'):
                c = Collection.objects.get(identifier__source=Identifier.ARCHIVESSPACE,
                                           identifier__identifier=child.get('ref', child.get('id')))
                c.parent = self.obj
                c.save()

    def parent(self, parent):
        try:
            if Identifier.objects.filter(source=Identifier.CARTOGRAPHER, identifier=parent).exists():
                self.obj.parent = Collection.objects.get(identifier__source=Identifier.CARTOGRAPHER,
                                                         identifier__identifier=parent)
            else:
                raise ArrangementMapTransformError('Missing parent data {}'.format(parent.get('ref')))
        except Exception as e:
            raise ArrangementMapTransformError('Error transforming parent: {}'.format(e))

    def process_tree(self, tree, idx):
        try:
            for tree_item in tree:
                obj = Collection.objects.get(identifier__identifier=tree_item.get('ref'))
                obj.tree_order = idx
                obj.save()
                if len(tree_item.get('children', '')) > 0:
                    self.process_tree(tree_item.get('children'), 0)
                idx += 1
        except Exception as e:
            raise ArrangementMapTransformError('Error processing tree: {}'.format(e))


class ArchivesSpaceDataTransformer:
    def __init__(self):
        self.last_run = (TransformRun.objects.filter(status=TransformRun.FINISHED, source=TransformRun.ARCHIVESSPACE).order_by('-start_time')[0].start_time
                         if TransformRun.objects.filter(status=TransformRun.FINISHED, source=TransformRun.ARCHIVESSPACE).exists() else None)
        self.current_run = TransformRun.objects.create(status=TransformRun.STARTED, source=TransformRun.ARCHIVESSPACE)

    def run(self):
        for cls in [(Agent, 'agent'), (Collection, 'collection'), (Object, 'object'), (Term, 'term')]:
            for obj in (cls[0].objects.filter(modified__gte=self.last_run, identifier__source=Identifier.ARCHIVESSPACE)
                        if self.last_run else cls[0].objects.filter(identifier__source=Identifier.ARCHIVESSPACE)):
                self.obj = obj
                self.source_data = SourceData.objects.get(**{cls[1]: self.obj, "source": SourceData.ARCHIVESSPACE}).data
                getattr(self, "transform_to_{}".format(cls[1]))()
        self.current_run.status = TransformRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def datetime_from_string(self, date_string):
        if date_string:
            try:
                return timezone.make_aware(parser.parse(date_string))
            except Exception:
                return None
        return None

    def num_from_string(self, string):
        try:
            return int(string)
        except ValueError:
            try:
                return float(string)
            except ValueError:
                return False

    def parse_date(self, date):
        begin = self.datetime_from_string(date.get('begin'))
        end = self.datetime_from_string(date.get('end'))
        expression = date.get('expression')
        if not expression:
            expression = date.get('begin')
            if date.get('end'):
                expression = "{}-{}".format(date.get('begin'), date.get('end'))
        return (begin, end, expression)

    def parse_note_content(self, note, content=None):
        try:
            content = content if content else []
            if note.get('jsonmodel_type') in ['note_bioghist', 'note_multipart']:
                for n in note.get('subnotes'):
                    content.append(self.parse_note_content(n)[0])
            else:
                if note.get('jsonmodel_type') in ['note_orderedlist', 'note_definedlist']:
                    content.append((note.get('jsonmodel_type').split('note_')[1], note.get('items')))
                elif note.get('jsonmodel_type') == 'note_bibliography':
                    content.append(('text', note.get('content')))
                    content.append(('orderedlist', note.get('items')))
                elif note.get('jsonmodel_type') == 'note_index':
                    l = [{'label': i.get('type'), 'value': i.get('value')} for i in note.get('items')]
                    content.append(('text', note.get('content')))
                    content.append(('definedlist', l))
                elif note.get('jsonmodel_type') == 'note_chronology':
                    m = [{'label': i.get('event_date'), 'value': ', '.join(i.get('events'))} for i in note.get('items')]
                    content.append(('definedlist', m))
                else:
                    content.append(('text', (note.get('content')
                                    if isinstance(note.get('content'), list) else [note.get('content')])))
            return content
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming note content {}'.format(e))

    def parse_note(self, note):
        type = note.get('type', note.get('jsonmodel_type').split('note_',1)[1])
        title = note.get('label', [t[1] for t in Note.NOTE_TYPE_CHOICES if t[0] == type][0])
        content = self.parse_note_content(note)
        return (type, title, content)

    def agents(self, agents):
        try:
            agent_list = [a for a in agents if a['role'] != 'creator']
            creator_list = [a for a in agents if a['role'] == 'creator']
            agent_set = []
            creator_set = []
            for list in [(agent_list, agent_set), (creator_list, creator_set)]:
                for agent in list[0]:
                    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).exists():
                        list[1].append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=agent.get('ref')).agent)
                    else:
                        raise ArchivesSpaceTransformError('Missing data for agent {}'.format(agent.get('ref')))
            self.obj.agents.clear()
            self.obj.agents.set(agent_set)
            if type(self.obj) == Collection:
                self.obj.creators.clear()
                self.obj.creators.set(creator_set)
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming agent: {}'.format(e))

    def dates(self, dates, relation_key):
        try:
            Date.objects.filter(**{relation_key: self.obj}).delete()
            for date in dates:
                parsed = self.parse_date(date)
                Date.objects.create(**{"begin": parsed[0],
                                       "end": parsed[1],
                                       "expression": parsed[2],
                                       "label": date.get('label'),
                                       relation_key: self.obj})
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming dates: {}'.format(e))

    def extents(self, extents, relation_key):
        try:
            Extent.objects.filter(**{relation_key: self.obj}).delete()
            for extent in extents:
                if self.num_from_string(extent.get('number')):
                    Extent.objects.create(**{"value": self.num_from_string(extent.get('number')),
                                             "type": extent.get('extent_type'),
                                             relation_key: self.obj})
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming extents: {}'.format(e))

    def languages(self, lang):
        try:
            lang_data = languages.get(alpha_3=lang)
            new_lang = (Language.objects.get(identifier=lang)
                        if Language.objects.filter(identifier=lang, expression=lang_data.name).exists()
                        else Language.objects.create(expression=lang_data.name, identifier=lang))
            self.obj.languages.clear()
            self.obj.languages.set([new_lang])
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming languages: {}'.format(e))

    def notes(self, notes, relation_key, object=None):
        try:
            object = object if object else self.obj
            Note.objects.filter(**{relation_key: object}).delete()
            for note in notes:
                parsed = self.parse_note(note)
                note = Note.objects.create(**{"type": parsed[0],
                                              "title": parsed[1],
                                              relation_key: object})
                for subnote in parsed[2]:
                    Subnote.objects.create(type=subnote[0],
                                           content=subnote[1],
                                           note=note)
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming notes: {}'.format(e))

    def parent(self, parent):
        try:
            if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=parent.get('ref')).exists():
                self.obj.parent = Collection.objects.get(identifier__source=Identifier.ARCHIVESSPACE,
                                                         identifier__identifier=parent.get('ref'))
            else:
                raise ArchivesSpaceTransformError('Missing parent data {}'.format(parent.get('ref')))
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming parent: {}'.format(e))

    def process_tree(self, tree, idx):
        try:
            for tree_item in tree:
                obj = (Collection.objects.get(identifier__source=Identifier.ARCHIVESSPACE,identifier__identifier=tree_item.get('record_uri'))
                       if tree_item.get('has_children') else
                       Object.objects.get(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=tree_item.get('record_uri')))
                obj.tree_order = idx
                obj.save()
                if tree_item.get('has_children'):
                    self.process_tree(tree_item.get('children'), 0)
                idx += 1
        except Exception as e:
            raise ArchivesSpaceTransformError('Error processing tree: {}'.format(e))

    def rights_statements(self, rights_statements, relation_key):
        try:
            RightsStatement.objects.filter(**{relation_key: self.obj}).delete()
            for statement in rights_statements:
                new_rights = RightsStatement.objects.create(**{
                    "determinationDate": statement.get('determination_date'),
                    "rightsType": statement.get('rights_type'),
                    "dateStart": self.datetime_from_string(statement.get('start_date')),
                    "dateEnd": self.datetime_from_string(statement.get('end_date')),
                    "copyrightStatus": statement.get('status'),
                    "otherBasis": statement.get('other_rights_basis'),
                    "jurisdiction": statement.get('jurisdiction'),
                    relation_key: self.obj})
                self.notes(statement.get('notes'), 'rights_statement', new_rights)
                for rights_granted in statement.get('acts'):
                    new_grant = RightsGranted.objects.create(
                        rights_statement=new_rights,
                        act=rights_granted.get('act_type'),
                        dateStart=self.datetime_from_string(rights_granted.get('start_date')),
                        dateEnd=self.datetime_from_string(rights_granted.get('end_date')),
                        restriction=rights_granted.get('restriction'))
                    self.notes(rights_granted.get('notes'), 'rights_granted', new_grant)
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming rights: {}'.format(e))

    def terms(self, terms):
        try:
            term_set = []
            for term in terms:
                if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=term.get('ref')).exists():
                    term_set.append(Identifier.objects.get(source=Identifier.ARCHIVESSPACE, identifier=term.get('ref')).term)
                else:
                    self.missing.append(term.get('ref'))
            self.obj.terms.clear()  # This could be problematic
            self.obj.terms.set(term_set)
        except Exception as e:
            raise ArchivesSpaceTransformError('Error transforming terms: {}'.format(e))

    def transform_to_agent(self):
        self.obj.title = self.source_data.get('display_name').get('sort_name')
        self.obj.type = self.source_data.get('jsonmodel_type')
        try:
            self.notes(self.source_data.get('notes'), 'agent')
            self.obj.save()
        except Exception as e:
            print(e)
            TransformRunError.objects.create(message=str(e), run=self.current_run)

    def transform_to_collection(self):
        self.obj.title = self.source_data.get('title')
        self.obj.level = self.source_data.get('level')
        try:
            self.dates(self.source_data.get('dates'), 'collection')
            self.extents(self.source_data.get('extents'), 'collection')
            self.notes(self.source_data.get('notes'), 'collection')
            self.rights_statements(self.source_data.get('rights_statements'), 'collection')
            if self.source_data.get('language'):
                self.languages(self.source_data.get('language'))
            self.terms(self.source_data.get('subjects'))
            self.agents(self.source_data.get('linked_agents'))
            if (self.source_data.get('jsonmodel_type') == 'archival_object') and self.source_data.get('ancestors'):
                self.parent(self.source_data.get('ancestors')[0])
            if self.source_data.get('jsonmodel_type') == 'resource':
                self.process_tree(self.obj.source_tree.get('children'), 0)
            self.obj.save()
        except Exception as e:
            print(e)
            TransformRunError.objects.create(message=str(e), run=self.current_run)

    def transform_to_object(self):
        self.obj.title = self.source_data.get('title', self.source_data.get('display_string'))
        try:
            self.dates(self.source_data.get('dates'), 'object')
            self.extents(self.source_data.get('extents'), 'object')
            self.notes(self.source_data.get('notes'), 'object')
            self.rights_statements(self.source_data.get('rights_statements'), 'object')
            if self.source_data.get('language'):
                self.languages(self.source_data.get('language'))
            self.terms(self.source_data.get('subjects'))
            self.agents(self.source_data.get('linked_agents'))
            if self.source_data.get('ancestors'):
                self.parent(self.source_data.get('ancestors')[0])
            self.obj.save()
        except Exception as e:
            print(e)
            TransformRunError.objects.create(message=str(e), run=self.current_run)

    def transform_to_term(self):
        self.obj.title = self.source_data.get('title')
        try:
            self.obj.save()
        except Exception as e:
            print(e)
            TransformRunError.objects.create(message=str(e), run=self.current_run)
