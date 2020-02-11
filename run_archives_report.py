import getpass
import os, argparse, csv, json
from py_dataset import dataset
from progressbar import progressbar
from asnake.client import ASnakeClient
from asnake.aspace import ASpace
from ames.harvesters import get_records, get_caltechfeed


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


def get_subjects(aspace):
    """Return dictionary to go from subject name to uri"""
    subjects = {}
    print(f"Requesting subject")
    for sbj in progressbar(aspace.subjects):
        subjects[sbj.title] = sbj.uri
    return subjects


def get_agents(aspace):
    """returns a dictionary of people to go from uri to name"""
    agents = {}
    for agent in progressbar(aspace.agents):
        agents[agent.uri] = agent.title
    return agents


def make_line(json, fields):
    """Return specific fields from a json object"""
    row = []
    for field in fields:
        if field in json:
            row.append(json[field])
        else:
            row.append("")
    return row


def add_blocks(json):
    """Return content from within blocks in json accession record"""
    row = []
    if len(json["dates"]) > 0:
        if len(json["dates"]) > 1:
            print("Multiple dates")
            exit()
        else:
            date = json["dates"][0]
            fields = ["expression", "begin", "end", "date_type", "label"]
            row = make_line(date, fields)
    else:
        row = ["", "", "", "", ""]
    if "extents" in json:
        if len(json["extents"]) > 1:
            print("Multiple extents")
            exit()
        else:
            date = json["extents"][0]
            fields = ["number", "physical_details"]
            row = row + make_line(date, fields)
    else:
        row = row + ["", ""]
    if "linked_agents" in json:
        agent_str = ""
        for agent in json["linked_agents"]:
            if agent_str == "":
                agent_str = agent["ref"]
            else:
                agent_str = agent_str + ";" + agent["ref"]
        row.append(agent_str)
    else:
        row.append("")
    if "subjects" in json:
        subj_str = ""
        for subj in json["subjects"]:
            if subj_str == "":
                subj_str = subj["ref"]
            else:
                subj_str = subj_str + ";" + subj["ref"]
        row.append(subj_str)
    else:
        row.append("")
    if "user_defined" in json:
        user = json["user_defined"]
        fields = ["text_2", "text_3", "text_4"]
        row = row + make_line(user, fields)
    else:
        row = row + ["", "", ""]
    return row


def accession_format_report(file_obj, repo, aspace, subject=None, years=None):
    fields = [
        "title",
        "id_0",
        "id_1",
        "accession_date",
        "content_description",
        "provenance",
        "general_note",
        "restrictions_apply",
        "publish",
        "access_restrictions",
        "access_restrictions_note",
        "use_restrictions",
    ]
    extras = [
        "expression",
        "begin",
        "end",
        "date_type",
        "label",
        "number",
        "physical_details",
        "agents",
        "subjects",
        "text_2",
        "text_3",
        "text_4",
    ]
    file_obj.writerow(fields + extras)
    for acc in progressbar(repo.accessions):
        if acc.extents:
            for ext in acc.extents:
                ext = ext.json()
                if "physical_details" in ext:
                    physical = ext["physical_details"]
                    if "FORMAT" in physical:
                        types = ["Cassette", "DAT", "CD", "CDR"]
                        formt = physical.split("FORMAT: ")[1].split(";")[0]
                        if formt in types:
                            json = acc.json()
                            row = make_line(json, fields)
                            row = row + add_blocks(json)
                            file_obj.writerow(row)


def accession_report(file_obj, repo, aspace, subject=None, years=None):
    print(f"Requesting agents")
    agents = get_agents(aspace)
    print(f"Requesting subjects")
    subjects = get_subjects(aspace)
    if subject in subjects:
        search_uri = subjects[subject]
    else:
        print(f"subject {subject} not found")
        exit()
    print(f"Requesting accessions")
    for acc in repo.accessions:
        for uri in acc.subjects:
            if search_uri == uri.ref:
                agent = ""
                if len(acc.linked_agents) > 0:
                    # print(agents['/agents/people/102'])
                    agent = agents[acc.linked_agents[0].ref]
                try:
                    idv = acc.id_0 + "-" + acc.id_1
                except AttributeError:
                    idv = acc.id_0
                file_obj.writerow([acc.title, idv, acc.accession_date, agent])


def agent_report(file_obj, repo, aspace):
    dot_paths = [
        "._Key",
        ".directory_info",
        ".ORCID",
        ".sort_name",
        ".ArchivesSpace_ID",
        ".family",
        ".given",
    ]
    labels = ["id", "directory_info", "orcid", "name", "as", "family", "given"]
    source = get_caltechfeed("people")
    keys = dataset.keys(source)
    keys.remove("captured")

    all_metadata = get_records(dot_paths, "p_list", source, keys, labels)

    all_metadata.sort(key=lambda all_metadata: all_metadata["id"])

    to_match = {}
    already_matched = []

    for metadata in all_metadata:
        if "as" in metadata:
            if metadata["as"] != "":
                file_obj.writerow([metadata["as"], metadata["id"], metadata["name"]])
                already_matched.append(metadata["as"])
            else:
                to_match[metadata["name"]] = metadata

    print(f"Requesting agents")
    for agent in progressbar(aspace.agents):
        if agent.agent_type == "agent_person":
            name = agent.display_name.sort_name
            uid = int(agent.uri.split("/")[-1])
            if uid not in already_matched:
                if name in to_match:
                    person = to_match[name]
                    file_obj.writerow(
                        [
                            uid,
                            person["id"],
                            person["name"],
                            "ADD ASPACE ID TO CaltechPEOPLE",
                        ]
                    )
                    to_match.pop(name)
                else:
                    file_obj.writerow([uid, "", name, "Not in CaltechPEOPLE"])

    for name in to_match:
        file_obj.writerow(["", to_match[name]["id"], name, "ADD to Aspace"])


if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")

    parser = argparse.ArgumentParser(description="Run a report on ArchiveSpace")
    parser.add_argument("report_name", help="report name (options: accession_report)")
    parser.add_argument("output", help="output file name")
    parser.add_argument("-years", help="format: 1939 or 1939-1940")
    parser.add_argument("-subject", help="Return items that match subject")

    args = parser.parse_args()

    # Initialize the ASnake client
    baseurl = "https://collections.archives.caltech.edu/staff/api/"

    username = input("Username: ")
    password = getpass.getpass(f"Password for {username}: ")

    aspace = ASpace(baseurl=baseurl, username=username, password=password)

    repo = aspace.repositories(2)
    if repo.repo_code != "Caltech Archives":
        print("Incorrect REPO")
        print(repo)
        exit()

    with open("../" + args.output, "w", newline="\n", encoding="utf-8") as fout:
        if args.output.split(".")[-1] == "tsv":
            file_out = csv.writer(fout, delimiter="\t")
        else:
            file_out = csv.writer(fout)
        if args.report_name == "accession_report":
            accession_report(file_out, repo, aspace, args.subject, args.years)
        if args.report_name == "format_report":
            accession_format_report(file_out, repo, aspace, args.subject, args.years)
        if args.report_name == "agent_report":
            agent_report(file_out, repo, aspace)
        else:
            print(args.report_name, " report type is not known")