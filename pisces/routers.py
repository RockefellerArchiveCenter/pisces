from rest_framework.routers import APIRootView, DefaultRouter


class PiscesAPIRootView(APIRootView):
    """Root of the Pisces API. This router adds additional routes to the API Root."""
    name = "Pisces API"

    def get(self, request, *args, **kwargs):
        self.api_root_dict.update([('schema', 'schema')])
        return super(PiscesAPIRootView, self).get(request, *args, **kwargs)


class PiscesRouter(DefaultRouter):
    APIRootView = PiscesAPIRootView
