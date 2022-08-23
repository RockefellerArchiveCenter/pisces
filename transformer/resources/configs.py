from ..models import ConfigurationChoice

NOTE_TRANSFORM_TYPES = [
    'abstract', 'accessrestrict', 'acqinfo', 'altformavail', 'bioghist',
    'custodhist', 'materialspec', 'odd', 'physdesc', 'phystech', 'processinfo',
    'relatedmaterial', 'scopecontent', 'userestrict']


def config_list(list_name):
    """Returns a list of formatted configuration choices."""
    choices = ConfigurationChoice.objects.filter(list__name=list_name)
    return [(c.value, c.display_name) for c in choices]
