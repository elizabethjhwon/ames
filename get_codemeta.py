from ames.harvesters import get_datacite_codemeta
import argparse,json

parser = argparse.ArgumentParser(description=\
        "Get Codemeta from existing source")
parser.add_argument('-doi', help=\
    'report name (options: doi_report,file_report,status_report,creator_report)')

args = parser.parse_args()

if args.doi:
    doi = args.doi
    codemeta = get_datacite_codemeta(doi)
    with open('new_codemeta.json','w') as outfile:
        json.dump(codemeta,outfile)
