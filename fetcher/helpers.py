from datetime import datetime

import requests
import shortuuid
from asnake.aspace import ASpace
from django.core.mail import send_mail
from electronbonder.client import ElectronBond
from pisces import settings

from .models import FetchRun, FetchRunError


def to_timestamp(datetime_obj):
    """Converts a datetime object into an integer timestamp representation."""
    return int(datetime_obj.timestamp())


def to_isoformat(datetime_obj):
    return datetime_obj.isoformat().replace('+00:00', 'Z')


def list_chunks(lst, n):
    """Yield successive n-sized chunks from list.

    Args:
        lst (list): list to chunkify
        n (integer): size of chunk to produce
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def last_run_time(source, object_status, object_type):
    """Returns a date object for a successful fetch.

    Args:
        source (int): a data source, see FetchRun.SOURCE_CHOICES
        object_status (int): the process status, see FetchRun.STATUS_CHOICES
        object_type (str): an object type that was fetched, see FetchRun.OBJECT_TYPE_CHOICES

    Returns:
        int: A UTC timestamp coerced to an integer.
    """
    if FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type,
            object_status=object_status).exists():
        return FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type,
            object_status=object_status
        ).order_by("-start_time")[0].start_time
    else:
        return datetime.fromtimestamp(0)


def instantiate_aspace(self, config=None):
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
    return aspace


def instantiate_electronbond(self, config=None):
    """Instantiates and returns an ElectronBond client.

    Args:
        config (dict): an optional config dict
    """
    config = config if config else settings.CARTOGRAPHER
    client = ElectronBond(baseurl=config['baseurl'])
    try:
        resp = client.get(config['health_check_path'])
        resp.raise_for_status()
        return client
    except Exception as e:
        raise Exception(
            "Cartographer is not available: {}".format(e))


def identifier_from_uri(uri):
    """Creates a short UUID.

    Uses `shortuuid`, which first creates a v5 UUID using an object's AS URI as
    a name, and then converts them to base57 using lowercase and uppercase
    letters and digits, and removing similar-looking characters such as
    l, 1, I, O and 0.

    This is a one-way process; while it is possible to consistently generate a
    given UUID given an AS URI, it is not possible to decode the URI from the
    UUID.
    """
    return shortuuid.uuid(name=uri)


async def handle_deleted_uris(uri_list, source, object_type, current_run):
    """Delivers POST request to indexing service with list of ids to be deleted."""
    updated = None
    es_ids = [identifier_from_uri(uri) for uri in list(set(uri_list))]
    if es_ids:
        try:
            resp = requests.post(settings.INDEX_DELETE_URL, json={"identifiers": es_ids})
            resp.raise_for_status()
            updated = es_ids
        except requests.exceptions.HTTPError:
            if current_run:
                FetchRunError.objects.create(
                    run=current_run,
                    message=resp.json()["detail"])
        except Exception as e:
            raise Exception("Error sending delete request: {}".format(e))
    return updated


def send_error_notification(fetch_run):
    """Send email with errors encountered during a fetch run."""
    try:
        errors = ""
        err_str = "errors" if fetch_run.error_count > 1 else "error"
        object_type = fetch_run.get_object_type_display()
        source = [s[1] for s in FetchRun.SOURCE_CHOICES if s[0] == int(fetch_run.source)][0]
        for err in fetch_run.errors:
            errors += "{}\n".format(err.message)
        send_mail(
            "{} {} exporting {} objects from {}".format(
                fetch_run.error_count, err_str, object_type, source),
            "The following errors were encountered while exporting {} objects from {}:\n\n{}".format(
                object_type, source, errors),
            "alerts@rockarch.org",
            settings.EMAIL_TO_ADDRESSES,
            fail_silently=False,)
    except Exception as e:
        print("Unable to send error notification email: {}".format(e))
