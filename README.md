# ames

[![DOI](https://data.caltech.edu/badge/110025475.svg)](https://data.caltech.edu/badge/latestdoi/110025475)

Automated Metadata Service

Manage metadata from different sources.  The examples in the package are
specific to Caltech repositories, but could be generalized.  This package 
is currently in development and will have additional sources and matchers 
added over time.

## Install:

If you just need functions (like codemeta_to_datacite): `pip install ames`
If you want to run operations, download the whole repo to get examples

## Requirements: 

Python 3.7 (Recommended via [Anaconda](https://www.anaconda.com/download)) 

You should have requests and datacite: `pip install requests datacite`

Harvesting requires [Dataset](https://github.com/caltechlibrary/dataset).

CaltechDATA integration requires [caltechdata_api](https://github.com/caltechlibrary/caltechdata_api)

## Organization

### Harvesters

- crossref_refs - Harvest references in datacite metadata from crossref event data
- caltechdata - Harvest metadata from CaltechDATA
- cd_github - Harvest GitHub repos and codemeta files from CaltechDATA
- matomo - Harvest web statistics from matomo
- caltechfeeds - Harvest Caltech Library metadata from feeds.library.caltech.edu

### Matchers

- caltechdata - Match content in CaltechDATA
- update_datacite - Match content in DataCite

## Example Operations

The run scripts show examples of using ames to perform a specific update
operation.

### CodeMeta management

In the test directory these is an example of using the codemeta_to_datacite
function to convert a codemeta file to DataCite standard metdata

### CodeMeta Updating

Collect GitHub records in CaltechDATA, search for a codemeta.json file, and
update CaltechDATA with new metadata.

#### Setup
You need to set an environmental variable with your token to access
CaltechDATA `export TINDTOK=`

#### Usage
Type `python run_codemeta.py`. 

### CaltechDATA Citation Alerts

Harvest citation data from the Crossref Event Data API, records in
CaltechDATA, match records, update metadata in CaltechDATA, and send email to
user.

#### Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=` and Mailgun `export MAILTOK=`.

#### Usage

Type `python run_event_data.py`. You'll be prompted for confirmation if any 
new citations are found.  

### Media Updates

Update media records in DataCite that indicate the files associated with a DOI.

#### Setup
You need to set an environmental variable with your password for your DataCite
account using `export DATACITE=`

#### Usage
Type `python run_media_update.py`.  

### CaltechDATA metadata updates

This will run checks on the quality of metadata in CaltechDATA.  Currently this
verifies whether redundent links are present in the related identifier section.  

#### Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=`

#### Usage
Type `python run_caltechdata_updates.py`. 

### Matomo downloads

This will harvest download information from matomo.  Very experimental.  

#### Setup
You need to set environmental variables with your token to access
Matomo `export MATTOK=`

#### Usage
Type `python run_downloads.py`. 

### CODA Reports (Feeds)

Harvest metadata from Caltech Library repositories and run reports.  Current
report lists records (optionally filtered by year) and their DOIs.

#### Usage
Type something like `python run_coda_report.py doi_report thesis report.tsv -year 1977-1978`

- The first option is the report type.
- The next option is the repository (thesis or authors)
- The next option is the output file name
- You can include a -year to return records from a specific year (1977) or a
range (1977-1978)

