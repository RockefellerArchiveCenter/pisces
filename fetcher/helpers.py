from .models import FetchRun


def last_run_time(source, object_type=None):
    return int(
        FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=source,
            object_type=object_type
        ).order_by('-start_time')[0].start_time.timestamp())
    if FetchRun.objects.filter(
        status=FetchRun.FINISHED,
        source=source,
        object_type=object_type
        ).exists()
    else 0
