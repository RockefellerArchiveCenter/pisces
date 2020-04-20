import requests
from asnake.aspace import ASpace
from electronbonder.client import ElectronBond
from pisces import settings
from silk.profiling.profiler import silk_profile
from transformer.models import DataObject

from .models import FetchRun, FetchRunError


@silk_profile()
def last_run_time(source, object_status, object_type):
    """Returns a timestamp for a successful fetch.

    Args:
        source (int): a data source, see FetchRun.SOURCE_CHOICES
        object_status (int): the process status, see FetchRun.STATUS_CHOICES
        object_type (str): an object type that was fetched, see FetchRun.OBJECT_TYPE_CHOICES

    Returns:
        int: A UTC timestamp coerced to an integer.
    """
    return (int(
        FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type,
            object_status=object_status
        ).order_by("-start_time")[0].start_time.timestamp())
        if FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type,
            object_status=object_status
    ).exists()
        else 0)


@silk_profile()
def instantiate_aspace(self, config=None, repo=False):
    """Instantiates and returns an ASpace object with a repository as an attribute.

    Args:
        config (dict): optional config dict

    An optional config object can be passed to this function, otherwise the
    default configs are targeted.
    """
    config = config if config else settings.ARCHIVESSPACE
    aspace = ASpace(
        baseurl=config['baseurl'],
        username=config['username'],
        password=config['password'])
    if repo:
        repo = aspace.repositories(config['repo'])
        setattr(aspace, 'repo', repo)  # TODO: I am unsure whether or not this is a good idea
        if isinstance(repo, dict) and 'error' in repo:
            raise Exception(self.repo['error'])
    return aspace


@silk_profile()
def instantiate_electronbond(self, config=None):
    """Instantiates and returns an ElectronBond client.

    Args:
        config (dict): an optional config dict
    """
    config = config if config else settings.CARTOGRAPHER
    client = ElectronBond(
        baseurl=config['baseurl'],
        user=config['user'],
        password=config['password'])
    try:
        resp = client.get(config['health_check_path'])
        resp.raise_for_status()
        return client
    except Exception as e:
        raise Exception(
            "Cartographer is not available: {}".format(e))


@silk_profile()
def get_es_id(identifier, source, object_type):
    es_id = None
    matches = DataObject.find_matches(object_type, source, identifier)
    for match in matches:
        if match.indexed:
            es_id = match.es_id
    return es_id


@silk_profile()
def handle_deleted_uri(uri, source, object_type, current_run):
    updated = None
    es_id = get_es_id(uri, source, object_type)
    if es_id:
        try:
            resp = requests.post(settings.INDEX_DELETE_URL, json=es_id)
            resp.raise_for_status()
            updated = es_id
        except requests.exceptions.HTTPError:
            if current_run:
                FetchRunError.objects.create(
                    run=current_run,
                    message=resp.json()["detail"],
                )
        else:
            raise Exception(resp.json()["detail"])
    return updated
