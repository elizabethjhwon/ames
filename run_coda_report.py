import os, argparse, csv
from py_dataset import dataset
import random
from progressbar import progressbar
from ames.harvesters import get_caltechfeed, get_records
from ames.harvesters import get_eprint_keys, get_eprint


def is_in_range(year_arg, year):
    # Is a given year in the range of a year argument YEAR-YEAR or YEAR?
    if year_arg != None:
        split = year_arg.split("-")
        if len(split) == 2:
            if int(year) >= int(split[0]) and int(year) <= int(split[1]):
                return True
        else:
            if year == split[0]:
                return True
    else:
        return True
    return False


def keep_record(metadata, years, item_type=None, group=None):
    keep = True

    if years:
        # Not implemented for CaltechDATA
        if "date" in metadata:
            year = metadata["date"].split("-")[0]
            if is_in_range(years, year) == False:
                keep = False
        else:
            keep = False

    if item_type:
        # CaltechDATA item
        if "resourceTye" in metadata:
            if metadata["resourceType"]["resourceTypeGeneral"] not in item_type:
                keep = False
        # Eprints item
        elif "type" in metadata:
            if "monograph_type" in metadata:
                # There are records with monograph_type that arn't monographs
                if metadata["type"] == "monograph":
                    if (
                        metadata["monograph_type"] not in item_type
                        and metadata["type"] not in item_type
                    ):
                        keep = False
                else:
                    if metadata["type"] not in item_type:
                        keep = False
            else:
                if metadata["type"] not in item_type:
                    keep = False
        else:
            print("Item type not found in record")
            keep = False

    if group:
        # Not implemented for CaltechDATA
        if "local_group" in metadata:
            match = False
            if isinstance(metadata["local_group"]["items"], list) == False:
                # Deal with single item listings
                metadata["local_group"]["items"] = [metadata["local_group"]["items"]]
            for gname in metadata["local_group"]["items"]:
                if gname in group:
                    match = True
            if match == False:
                keep = False
        else:
            keep = False
    return keep


def break_up_group(metadata, field, val, row):
    """Break up a array in 'field' into a single element with number 'val'"""
    if field in metadata:
        if len(metadata[field]) > val:
            row.append(metadata[field][val])
        else:
            # This many values are not present, add blank cell
            row.append("")
    else:
        # Metadata not present, add blank cell
        row.append("")
    return row


def thesis_metadata(file_obj, keys, source, years=None):
    """Output a full metadata report of information about theses"""
    file_obj.writerow(
        [
            "Author-Family",
            "Author-Given",
            "Title",
            "Abstract",
            "Type",
            "Awards",
            "Degree-Date",
            "Institution",
            "Division",
            "Option-Major",
            "Option-Minor",
            "Keywords",
            "Advisor1-Family",
            "Advisor1-Given",
            "Advisor1-Role",
            "Advisor2-Family",
            "Advisor2-Given",
            "Advisor2-Role",
            "Advisor3-Family",
            "Advisor3-Given",
            "Advisor3-Role",
            "Advisor4-Family",
            "Advisor4-Given",
            "Advisor4-Role",
            "Persistent URL",
            "DOI",
        ]
    )
    all_metadata = []
    dot_paths = [
        ".creators.items[0].name.family",
        ".creators.items[0].name.given",
        ".title",
        ".abstract",
        ".thesis_type",
        ".thesis_awards",
        ".date",
        ".institution",
        ".divisions.items[0]",
        ".option_major.items",
        ".option_minor.items",
        ".keywords",
        ".thesis_advisor.items[:].name.family",
        ".thesis_advisor.items[:].name.given",
        ".thesis_advisor.items[:].role",
        ".official_url",
        ".doi",
    ]
    labels = [
        "creator_family",
        "creator_given",
        "title",
        "abstract",
        "thesis_type",
        "thesis_awards",
        "date",
        "institution",
        "division",
        "major",
        "minor",
        "keywords",
        "advisor_family",
        "advisor_given",
        "advisor_role",
        "official_url",
        "doi",
    ]
    if source.split(".")[-1] == "ds":
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))
    all_metadata.sort(key=lambda all_metadata: all_metadata["creator_family"])
    for metadata in all_metadata:
        # Determine if we want the record
        if keep_record(metadata, years):
            row = []
            if "creator_given" in metadata:
                row.append(metadata["creator_family"])
                row.append(metadata["creator_given"])
            else:
                row.append(metadata["creator_family"])
                row.append("")
            row.append(metadata["title"])
            row.append(metadata["abstract"])
            row.append(metadata["thesis_type"])
            if "thesis_awards" in metadata:
                award = metadata["thesis_awards"]
            else:
                award = ""
            row.append(award)
            row.append(metadata["date"])
            row.append(metadata["institution"])
            row.append(metadata["division"])
            major = ""
            for opt in metadata["major"]:
                if major == "":
                    major = opt
                else:
                    major += ", " + opt
            row.append(major)
            minor = ""
            if "minor" in metadata:
                for opt in metadata["minor"]:
                    if minor == "":
                        minor = opt
                    else:
                        minor += ", " + opt
            row.append(minor)
            row.append(metadata["keywords"])
            for i in range(4):
                record = break_up_group(metadata, "advisor_family", i, row)
                record = break_up_group(metadata, "advisor_given", i, row)
                record = break_up_group(metadata, "advisor_role", i, row)
            row.append(metadata["official_url"])
            if "doi" in metadata:
                doi = metadata["doi"]
            else:
                doi = ""
            row.append(doi)
            file_obj.writerow(row)


def thesis_report(file_obj, keys, source, years=None):
    """Output a report of information about theses"""
    file_obj.writerow(
        [
            "Year",
            "Author",
            "ORCID",
            "Title",
            "Advisor",
            "Type",
            "Option",
            "Persistent URL",
            "DOI",
        ]
    )
    all_metadata = []
    dot_paths = [
        ".date",
        ".creators.items[0].name.family",
        ".creators.items[0].name.given",
        ".creators.items[0].orcid",
        ".title",
        ".thesis_advisor.items[0].name.family",
        ".thesis_advisor.items[0].name.given",
        ".thesis_type",
        ".option_major.items",
        ".official_url",
        ".doi",
    ]
    labels = [
        "date",
        "creator_family",
        "creator_given",
        "creator_orcid",
        "title",
        "advisor_family",
        "advisor_given",
        "thesis_type",
        "option",
        "official_url",
        "doi",
    ]
    if source.split(".")[-1] == "ds":
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))
    all_metadata.sort(key=lambda all_metadata: all_metadata["creator_family"])
    for metadata in all_metadata:
        # Determine if we want the record
        if keep_record(metadata, years):
            if "creator_given" in metadata:
                creator = metadata["creator_family"] + ", " + metadata["creator_given"]
            else:
                creator = metadata["creator_family"]
            if "advisor_family" in metadata:
                advisor = metadata["advisor_family"] + ", " + metadata["advisor_given"]
            else:
                advisor = ""
            if "creator_orcid" in metadata:
                orcid = metadata["creator_orcid"]
            else:
                orcid = ""
            if "doi" in metadata:
                doi = metadata["doi"]
            else:
                doi = ""
            option = ""
            for opt in metadata["option"]:
                if option == "":
                    option = opt
                else:
                    option += ", " + opt
            file_obj.writerow(
                [
                    metadata["date"],
                    creator,
                    orcid,
                    metadata["title"],
                    advisor,
                    metadata["thesis_type"],
                    option,
                    metadata["official_url"],
                    doi,
                ]
            )


def doi_report(
    file_obj, keys, source, years=None, all_records=True, item_type=None, group=None
):
    """Output a report of DOIs """
    file_obj.writerow(
        [
            "Eprint ID",
            "DOI",
            "Year",
            "Author ID",
            "Title",
            "Resolver URL",
            "Series Information",
        ]
    )
    all_metadata = []
    if source.split(".")[-1] == "ds":
        dot_paths = [
            "._Key",
            ".doi",
            ".official_url",
            ".date",
            ".related_url",
            ".creators",
            ".title",
            ".local_group",
            ".type",
            ".monograph_type",
            ".other_numbering_system",
            ".series",
            ".number",
        ]
        labels = [
            "eprint_id",
            "doi",
            "official_url",
            "date",
            "related_url",
            "creators",
            "title",
            "local_group",
            "type",
            "monograph_type",
            "other_numbering_system",
            "series",
            "number",
        ]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        doi = ""

        # Determine if we want the record
        if keep_record(metadata, years, item_type, group):

            ep = metadata["eprint_id"]
            # Handle odd CaltechAUTHORS DOI setup
            if "doi" in metadata:
                doi = metadata["doi"].strip()
            elif "related_url" in metadata and "items" in metadata["related_url"]:
                items = metadata["related_url"]["items"]
                for item in items:
                    if "url" in item:
                        url = item["url"].strip()
                    if "type" in item:
                        itype = item["type"].strip().lower()
                    if "description" in item:
                        description = item["description"].strip().lower()
                    if itype == "doi" and description == "article":
                        doi = url
                        break
            else:
                doi = ""
            if "creators" in metadata:
                if "id" in metadata["creators"]["items"][0]:
                    author = metadata["creators"]["items"][0]["id"]
                else:
                    author = ""
                    print("Record " + ep + " is missing author id")

            if "title" not in metadata:
                print("Record " + ep + " is missing Title")
                exit()
            title = metadata["title"]
            url = metadata["official_url"]
            if "date" in metadata:
                year = metadata["date"].split("-")[0]
            else:
                year = ""
            # Series info
            series = ""
            if "other_numbering_system" in metadata:
                num = metadata["other_numbering_system"]
                series = "other numbering:"
                for item in num["items"]:
                    if "id" in item:
                        series += " " + item["name"] + " " + item["id"]
                    else:
                        series += " " + item["name"]
            if "series" in metadata:
                series += "series:"
                if "number" in metadata:
                    series += " " + metadata["series"] + " " + metadata["number"]
                else:
                    series += " " + metadata["series"]
            if all_records == False:
                if doi != "":
                    file_obj.writerow([ep, doi, year, author, title, url, series])
            else:
                file_obj.writerow([ep, doi, year, author, title, url, series])
    print("Report finished!")


def status_report(file_obj, keys, source):
    """Output a report of items that have a status other than archive
    or have metadata visability other than show.
    Under normal circumstances this should return no records when run on feeds"""
    file_obj.writerow(["Eprint ID", "Resolver URL", "Status"])

    all_metadata = []
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".eprint_status", ".official_url", ".metadata_visibility"]
        labels = ["eprint_id", "eprint_status", "official_url", "metadata_visibility"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        if metadata["eprint_status"] != "archive":
            ep = metadata["eprint_id"]
            status = metadata["eprint_status"]
            url = metadata["official_url"]
            print("Record matched: ", url)
            file_obj.writerow([ep, url, status])
        if metadata["metadata_visibility"] != "show":
            print(metadata["metadata_visibility"])
            ep = metadata["eprint_id"]
            status = metadata["metadata_visibility"]
            url = metadata["official_url"]
            print("Record matched: ", url)
            file_obj.writerow([ep, url, status])
    print("Report finished!")


def license_report(file_obj, keys, source, item_type=None, rtype="summary"):
    """Write report with license types"""
    if source.split(".")[0] != "CaltechDATA":
        print(source.split(".")[0] + " is not supported for license report")
        exit()
    else:
        all_metadata = []
        dot_paths = [
            "._Key",
            ".rightsList",
            ".resourceType",
            ".creators",
            ".fundingReferences",
        ]
        labels = ["id", "rightsList", "resourceType", "creators", "fundingReferences"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
        licenses = {}

        if rtype == "summary":

            file_obj.writerow(["License Name", "Number of Records", "IDs"])
            for metadata in all_metadata:
                if item_type != None:
                    # Restrict to a specific item type
                    if metadata["resourceType"]["resourceTypeGeneral"] in item_type:
                        lic = metadata["rightsList"][0]["rights"]
                    else:
                        lic = None
                # Otherwise we always save license
                else:
                    lic = metadata["rightsList"]["rights"]

                if lic != None:
                    if lic in licenses:
                        licenses[lic]["count"] += 1
                        licenses[lic]["ids"].append(metadata["id"])
                    else:
                        new = {}
                        new["count"] = 1
                        new["ids"] = [metadata["id"]]
                        licenses[lic] = new

            for lic in licenses:
                file_obj.writerow([lic, licenses[lic]["count"], licenses[lic]["ids"]])

        else:

            file_obj.writerow(["CaltechDATA ID", "Authors", "License", "Funders"])
            for metadata in all_metadata:
                write = False
                if item_type != None:
                    # Restrict to a specific item type
                    if metadata["resourceType"]["resourceTypeGeneral"] in item_type:
                        write = True
                # Otherwise we always save license
                else:
                    write = True

                if write == True:
                    creators = ""
                    for c in metadata["creators"]:
                        if creators != "":
                            creators += ";"
                        creators += c["creatorName"]
                    funders = ""
                    if "fundingReferences" in metadata:
                        for c in metadata["fundingReferences"]:
                            if funders != "":
                                funders += ";"
                            funders += c["funderName"]
                    if "rightsList" not in metadata:
                        print("record ", metadata["id"], " is missing license")
                        exit()
                    file_obj.writerow(
                        [
                            metadata["id"],
                            creators,
                            metadata["rightsList"][0]["rights"],
                            funders,
                        ]
                    )


def file_report(file_obj, keys, source, years=None):
    """Write out a report of files with potential issues"""
    file_obj.writerow(["Eprint ID", "Problem", "Impacted Files", "Resolver URL"])
    all_metadata = []
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".documents", ".date", ".official_url"]
        labels = ["eprint_id", "documents", "date", "official_url"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            all_metadata.append(get_eprint(source, eprint_id))

    for metadata in all_metadata:
        if "date" in metadata:
            year = metadata["date"].split("-")[0]
            if is_in_range(years, year):
                if "documents" in metadata:
                    for d in metadata["documents"]:
                        if "files" in d:
                            for f in d["files"]:
                                filename = f["filename"]
                                extension = filename.split(".")[-1]
                                if extension == "html":
                                    ep = metadata["eprint_id"]
                                    url = metadata["official_url"]
                                    print("HTML: ", url)
                                    file_obj.writerow([ep, "HTML File", filename, url])
                                if extension == "htm":
                                    ep = metadata["eprint_id"]
                                    url = metadata["official_url"]
                                    print("HTM: ", url)
                                    file_obj.writerow([ep, "HTML File", filename, url])
                                if len(filename) > 200:
                                    ep = metadata["eprint_id"]
                                    url = metadata["official_url"]
                                    print("Length: ", url)
                                    file_obj.writerow(
                                        [ep, "File Name Length", filename, url]
                                    )
    print("Report finished!")


def creator_report(file_obj, keys, source, update_only=False):
    creator_ids = []
    creators = {}
    print(f"Processing {len(keys)} eprint records for creators")
    if source.split(".")[-1] == "ds":
        dot_paths = ["._Key", ".creators.items"]
        labels = ["eprint_id", "items"]
        all_metadata = get_records(dot_paths, "dois", source, keys, labels)
        for metadata in progressbar(all_metadata, redirect_stdout=True):
            key = metadata["eprint_id"]
            if "items" in metadata:
                find_creators(metadata["items"], key, creators, creator_ids)
    else:
        for eprint_id in progressbar(keys, redirect_stdout=True):
            metadata = get_eprint(source, eprint_id)
            if metadata != None:
                if "creators" in metadata and "items" in metadata["creators"]:
                    items = metadata["creators"]["items"]
                    find_creators(items, eprint_id, creators, creator_ids)

    creator_ids.sort()
    file_obj.writerow(["creator_id", "orcid", "existing_ids", "update_ids"])
    for creator_id in creator_ids:
        creator = creators[creator_id]
        # print(creator)
        write = False
        if update_only:
            if creator["orcids"] and creator["update_ids"]:
                write = True
        else:
            write = True
        if write == True:
            orcid = "|".join(creator["orcids"])
            eprint_ids = "|".join(creator["eprint_ids"])
            update_ids = "|".join(creator["update_ids"])
            if len(creator["orcids"]) > 1:
                # All items will need to be updated if there are multiple orcids
                update_ids = update_ids + "|" + eprint_ids
                eprint_ids = ""
            file_obj.writerow([creator_id, orcid, eprint_ids, update_ids])
    print("Report finished!")


def find_creators(items, eprint_id, creators, creator_ids):
    """Take a item list and return creators"""
    for item in items:
        if "id" in item:
            creator_id = item["id"]
            orcid = ""
            if "orcid" in item:
                orcid = item["orcid"]
            if creator_id in creators:
                # Existing creator
                if orcid != "":
                    if creators[creator_id]["orcids"] == []:
                        # New ORCID
                        creators[creator_id]["orcids"].append(orcid)
                        creators[creator_id]["eprint_ids"].append(eprint_id)
                    elif orcid in creators[creator_id]["orcids"]:
                        # We already have ORCID
                        creators[creator_id]["eprint_ids"].append(eprint_id)
                    else:
                        # Creator has multiple orcids
                        creators[creator_id]["orcids"].append(orcid)
                        creators[creator_id]["update_ids"].append(eprint_id)
                else:
                    # We always want to (potentially) update blank orcids
                    creators[creator_id]["update_ids"].append(eprint_id)
            else:
                # We have a new creator
                creators[creator_id] = {}
                if orcid != "":
                    creators[creator_id]["orcids"] = [orcid]
                    creators[creator_id]["eprint_ids"] = [eprint_id]
                    creators[creator_id]["update_ids"] = []
                else:
                    creators[creator_id]["orcids"] = []
                    creators[creator_id]["eprint_ids"] = []
                    creators[creator_id]["update_ids"] = [eprint_id]
                creator_ids.append(creator_id)


if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")

    parser = argparse.ArgumentParser(description="Run a report on CODA repositories")
    parser.add_argument(
        "report_name",
        help="report name (options: doi_report,file_report,status_report,creator_report)",
    )
    parser.add_argument(
        "repository",
        help="options: thesis, authors, caltechdata, test (if using eprints source)",
    )
    parser.add_argument(
        "-source", default="feeds", help="options: feeds (default), eprints"
    )
    parser.add_argument("output", help="output tsv name")
    parser.add_argument("-years", help="format: 1939 or 1939-1940")
    parser.add_argument(
        "-item",
        nargs="+",
        help='Item type from repository (e.g. Dataset or "technical_report")',
    )
    parser.add_argument(
        "-group",
        nargs="+",
        help='Group from repository (e.g. "Keck Institute for Space Studies")',
    )
    parser.add_argument("-username", help="Eprints username")
    parser.add_argument("-password", help="Eprints password")
    parser.add_argument("-sample", help="Number of records if you want a random sample")

    args = parser.parse_args()

    if args.source == "feeds":
        source = get_caltechfeed(args.repository)
        keys = dataset.keys(source)
        keys.remove("captured")
    elif args.source == "eprints":
        if args.username:
            source = "https://" + args.username + ":" + args.password + "@"
        else:
            source = "https://"
        if args.repository == "authors":
            source += "authors.library.caltech.edu"
        elif args.repository == "thesis":
            source += "thesis.library.caltech.edu"
        elif args.repository == "test":
            if args.username:
                source = "http://" + args.username + ":" + args.password + "@"
            else:
                source = "http://"
            source += "authorstest.library.caltech.edu"
        else:
            print("Repository not known")
            exit()
        keys = get_eprint_keys(source)
    else:
        print("Source is not feeds or eprints, exiting")
        exit()

    if args.sample != None:
        keys = random.sample(keys, int(args.sample))
    keys.sort(key=int, reverse=True)

    print("Running report for ", args.repository)

    with open("../" + args.output, "w", newline="\n", encoding="utf-8") as fout:
        if args.output.split(".")[-1] == "tsv":
            file_out = csv.writer(fout, delimiter="\t")
        else:
            file_out = csv.writer(fout)
        if args.report_name == "file_report":
            file_report(file_out, keys, source, args.years)
        elif args.report_name == "creator_report":
            creator_report(file_out, keys, source, update_only=True)
        elif args.report_name == "status_report":
            status_report(file_out, keys, source)
        elif args.report_name == "doi_report":
            doi_report(
                file_out,
                keys,
                source,
                years=args.years,
                all_records=True,
                item_type=args.item,
                group=args.group,
            )
        elif args.report_name == "thesis_report":
            thesis_report(file_out, keys, source, args.years)
        elif args.report_name == "thesis_metadata":
            thesis_metadata(file_out, keys, source, args.years)
        elif args.report_name == "license_report":
            license_report(
                file_out, keys, source, item_type=args.item
            )  # ,rtype='full')
        else:
            print(args.report_name, " report type is not known")
