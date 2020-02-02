import requests

from .models import FetchRun


def last_run_time(source, object_type):
    """
    Returns the last time a successful fetch against a given data source
    for a particular object type was started. Allows incremental checking of
    updates.
    """
    return (int(
        FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type
        ).order_by("-start_time")[0].start_time.timestamp())
        if FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type
    ).exists()
        else 0)


def send_post_request(url, data):
    """
    Sends a POST request to a specified URL with a JSON payload.
    """
    assert(isinstance(data, dict))
    resp = requests.post(url, json=data)
    resp.raise_for_status()
