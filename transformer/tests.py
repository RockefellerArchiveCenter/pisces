import random
import vcr

from django.test import Client, TestCase
from django.urls import reverse

from .test_library import import_fixture_data, add_wikidata_ids, add_wikipedia_ids, get_random_string
from .models import *
from .fetchers import *
from .transformers import *

fetch_vcr = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)
