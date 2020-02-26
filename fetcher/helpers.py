import requests
from asnake.aspace import ASpace
from pisces import settings

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


def send_post_request(url, data, current_run=None):
    """
    Sends a POST request to a specified URL with a JSON payload.
    """
    try:
        assert(isinstance(data, dict))
        resp = requests.post(url, json=data)
        resp.raise_for_status()
    except Exception as e:
        print(e)
        if current_run:
            FetchRunError.objects.create(
                run=current_run,
                message=str(e),
            )


def instantiate_aspace(self, config=None):
    """
    Instantiates and returns an ASpace object with a repository as an attribute.
    An optional config object can be passed to this function,
    otherwise the default configs are targeted.
    """
    config = config if config else settings.ARCHIVESSPACE
    aspace = ASpace(baseurl=config['baseurl'],
                    username=config['username'],
                    password=config['password'])
    repo = aspace.repositories(config['repo'])
    setattr(aspace, 'repo', repo)  # TODO: I am unsure whether or not this is a good idea
    if isinstance(repo, dict) and 'error' in repo:
        raise Exception(self.repo['error'])  # TODO: This should probably target a more specific exception
    return aspace
