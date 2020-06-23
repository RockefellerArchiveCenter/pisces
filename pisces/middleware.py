import cProfile
import os
import tempfile
import time

from pisces import settings

try:
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE
except BaseException:
    PROFILE_LOG_BASE = tempfile.gettempdir()


def profile(log_file):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the
    file name, such that 'my_view.prof' become 'my_view-20100211T170321.prof',
    where the time stamp is in UTC. This makes it easy to run and compare
    multiple trials.
    """

    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    if not os.path.isdir(PROFILE_LOG_BASE):
        os.makedirs(PROFILE_LOG_BASE)

    def _outer(f):
        def _inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            (base, ext) = os.path.splitext(log_file)
            base = base + "-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
            final_log_file = base + ext

            prof = cProfile.Profile()
            try:
                ret = prof.runcall(f, *args, **kwargs)
                prof.dump_stats(final_log_file)
            except Exception as e:
                print("Profiling error: {}".format(e))
            return ret

        return _inner
    return _outer
