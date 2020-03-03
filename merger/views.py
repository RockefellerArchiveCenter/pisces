from asterism.views import BaseServiceView

from .mergers import (AgentMerger, ArchivalObjectMerger, ArrangementMapMerger,
                      ResourceMerger, SubjectMerger)

MERGERS = {
    "resource": ResourceMerger,
    "archival_object": ArchivalObjectMerger,
    "subject": SubjectMerger,
    "person": AgentMerger,
    "organization": AgentMerger,
    "family": AgentMerger,
    "arrangement_map": ArrangementMapMerger,
}


class MergeView(BaseServiceView):
    """Merges transformed data objects."""

    def get_service_response(self, request):
        if not request.data:
            raise Exception("No data submitted to merge")
        merger = MERGERS[request.data.get("object_type")]
        return merger().merge(request.data.get("object_type"), request.data.get("object"))
