import os
from datetime import date
from py_dataset import dataset
from ames.harvesters import get_caltechdata
from ames.matchers import update_datacite_media

password = os.environ["DATACITE"]
prefix = "10.14291"
user = "CALTECH.LIBRARY"

os.chdir("data")

collection = "caltechdata.ds"

get_caltechdata(collection)
update_datacite_media(user, password, collection, prefix)

password = os.environ["TIND_DATACITE"]
prefix = "10.22002"
user = "TIND.CALTECH"

update_datacite_media(user, password, collection, prefix)

# Save date in collection
today = date.today().isoformat()
dataset.update(collection, "mediaupdate", {"mediaupdate": today})
