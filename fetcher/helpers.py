import requests
from asnake.aspace import ASpace
from electronbonder.client import ElectronBond
from pisces import settings
from silk.profiling.profiler import silk_profile

from .models import FetchRun, FetchRunError


def last_run_time(source, object_status, object_type):
    """
    Returns the last time a successful fetch against a given data source
    for a particular object type was started. Allows incremental checking of
    updates.
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
def send_post_request(url, data, current_run=None):
    """Sends a POST request to a specified URL with a JSON payload.

    Args:
        url (str): the URL to which to send the POST request.
        data (dict): a data payload
        current_run (FetchRun): the current FetchRun instance.
    """
    try:
        resp = requests.post(url, json=data)
        resp.raise_for_status()
        return True
    except requests.exceptions.HTTPError:
        if current_run:
            FetchRunError.objects.create(
                run=current_run,
                message=resp.json()["detail"],
            )
        else:
            raise Exception(resp.json()["detail"])


def instantiate_aspace(self, config=None):
    """Instantiates and returns an ASpace object with a repository as an attribute.

    Args:
        config (dict): optional config dict

    An optional config object can be passed to this function, otherwise the
    default configs are targeted.
    """
    config = config if config else settings.ARCHIVESSPACE
    aspace = ASpace(baseurl=config['baseurl'],
                    username=config['username'],
                    password=config['password'])
    repo = aspace.repositories(config['repo'])
    setattr(aspace, 'repo', repo)  # TODO: I am unsure whether or not this is a good idea
    if isinstance(repo, dict) and 'error' in repo:
        raise Exception(self.repo['error'])
    return aspace


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
        if not resp.status_code:
            raise Exception(
                "Cartographer status endpoint is not available. Service may be down.")
        return client
    except Exception as e:
        raise Exception(
            "Cartographer is not available: {}".format(e))
