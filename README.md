# pisces
A service for fetching and transforming data for discovery.

pisces is part of [Project Electron](https://github.com/RockefellerArchiveCenter/project_electron), an initiative to build sustainable, open and user-centered infrastructure for the archival management of digital records at the [Rockefeller Archive Center](http://rockarch.org/).

[![Build Status](https://travis-ci.org/RockefellerArchiveCenter/pisces.svg?branch=master)](https://travis-ci.org/RockefellerArchiveCenter/pisces)

## Setup

Install [git](https://git-scm.com/) and clone the repository

    $ git clone https://github.com/RockefellerArchiveCenter/pisces.git

Install [Docker](https://store.docker.com/search?type=edition&offering=community) and run docker-compose from the root directory

    $ cd pisces
    $ docker-compose up

Once the application starts successfully, you should be able to access the application in your browser at `http://localhost:8000`

When you're done, shut down docker-compose

    $ docker-compose down

Or, if you want to remove all data

    $ docker-compose down -v


## Services

pisces has two main services, both of which are exposed via HTTP endpoints (see [Routes](#routes) section below):

* Create, get, update and delete identifiers - basic operations to manage identifiers.
* Get or create identifiers - a single endpoint which returns an identifier if a match is found, or creates a new one if none exists.

![Pisces diagram](pisces-services.png)


### Routes

| Method | URL | Parameters | Response  | Behavior  |
|--------|-----|---|---|---|
|GET, PUT, POST, DELETE|/api/agents||200|Returns data about Agents|
|GET, PUT, POST, DELETE|/api/collections||200|Returns data about Collections|
|GET, PUT, POST, DELETE|/api/objects||200|Returns data about Objects|
|GET, PUT, POST, DELETE|/api/terms||200|Returns data about Terms|
|GET, PUT, POST, DELETE|/api/identifiers||200|Returns data about Identifiers|
|GET, PUT, POST, DELETE|/api/transforms||200|Returns data about TransformRun routines|
|GET|/api/find-by-id|`source` - target data source, one of `archivesspace`, `cartographer`, `wikidata` or `wikipedia` <br/> `identifier` - target identifier|200|Returns data about Agents|
|POST|/api/import||200|Imports sample data, will be replaced by fetchers|
|POST|/api/transform|`source` - target data source, one of `archivesspace`, `cartographer`, `wikidata` or `wikipedia` <br/> `object_type` - target object type, one of `collections`, `objects`, `agents`, `terms` (only relevant for ArchivesSpace data)|200|Transforms data|
|GET|/status||200|Return the status of the service|
|GET|/schema.json||200|Returns the OpenAPI schema for this service|

## License

This code is released under an [MIT License](LICENSE).
