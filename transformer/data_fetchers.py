import json

from wikipediaapi import Wikipedia
from wikidata.client import Client as wd_client

from .models import Agent, Identifier, SourceData


class WikidataDataFetcher:
    def __init__(self):
        self.client = wd_client()

    def run(self):
        for agent in Agent.objects.filter(wikidata_id__isnull=False):
            print(agent)
            agent_data = self.client.get(agent.wikidata_id, load=True).data
            if SourceData.objects.filter(source=SourceData.WIKIDATA, agent=agent).exists():
                source_data = SourceData.objects.get(source=SourceData.WIKIDATA, agent=agent)
                # Could insert a check here to see if data has been updated since last save.
                source_data.data = agent_data
                source_data.save()
            else:
                SourceData.objects.create(source=SourceData.WIKIDATA, data=agent_data, agent=agent)
            if not Identifier.objects.filter(source=Identifier.WIKIDATA, agent=agent).exists():
                Identifier.objects.create(source=Identifier.WIKIDATA, identifier=agent.wikidata_id, agent=agent)


class WikipediaDataFetcher:
    def __init__(self):
        self.client = Wikipedia('en')

    def run(self):
        for agent in Agent.objects.filter(wikipedia_url__isnull=False):
            agent_name = agent.wikipedia_url.split('/')[-1]
            print(agent)
            agent_page = self.client.page(agent_name)
            if SourceData.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                source_data = SourceData.objects.get(source=SourceData.WIKIPEDIA, agent=agent)
                source_data.data = agent_page.summary
                source_data.save()
            else:
                SourceData.objects.create(source=SourceData.WIKIPEDIA, data=agent_page.summary, agent=agent)
            if not Identifier.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                # TODO: Something is happening to agent_name in the save that is stripping spaces and truncating, etc.
                # Maybe get a better identifier?
                Identifier.objects.create(source=Identifier.WIKIPEDIA, identifier=agent_name, agent=agent)
