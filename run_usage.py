import os
import dataset
from ames.harvesters import file_mapping, get_usage, build_usage
from ames.harvesters import build_aggregate, aggregate_usage
from ames.harvesters import get_caltechdata, get_history
from ames.matchers import add_usage, submit_report

if os.path.isdir("data") == False:
    os.mkdir("data")
os.chdir("data")

production = True
collection = "caltechdata.ds"

get_caltechdata(collection, production)

mapping_file = "tindfile_mapping.csv"

mapping = file_mapping(collection, mapping_file)

history = False

if history == True:
    keys = dataset.keys(collection)
    h_collection = "caltechdata_history.ds"
    get_history(h_collection, keys)
    mapping = file_mapping(h_collection, mapping_file)

update = False

usage_collection = "caltechdata_usage.ds"
if update == True:
    token = os.environ["MATTOK"]
    build_usage(collection, usage_collection)
    get_usage(usage_collection, mapping, token)
    token = os.environ["TINDTOK"]
    add_usage(collection, token, usage_collection, production=True)

#Aggregrate usage into month buckets
month_collection = "caltechdata_aggregate.ds"
build_aggregate(month_collection)
aggregate_usage(usage_collection, month_collection)

submit_report(usage_collection, start_date, end_date, production=False)
