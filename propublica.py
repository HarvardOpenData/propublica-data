#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Creates a csv file containing the financial data of specified organizations
using ProPublica.

Inputs:
LIST_OF_ORGS_FILE (the list of propublica numbers)
EXISTING_DATA_FILE (any data that is already compiled, including manual data)

Output:
finaldata.csv (data autograbbed from the API merged with existing data)
"""

from __future__ import print_function
import csv
import json
import time
import urllib2

LIST_OF_ORGS_FILE = "listoforgs.csv"
EXISTING_DATA_FILE = "existingdata.csv"

def get_list_of_orgs(list_of_orgs_file):
    """Returns list of orgs. Assumes first column is the ProPublica numbers."""
    org_nums = []
    with open(list_of_orgs_file, "r") as csv_file:
        reader = csv.reader(csv_file)
        # Avoid header row
        next(reader)
        for row in reader:
            org_nums.append(row[0])
    return org_nums

def get_existing_data(existing_data_file):
    """
    Stores data from a csv into a dict format with the pdfurl as the key.
    Only looks at data that is manual, as anything that is auto will be
    re-grabbed from the API.
    """
    existing_data = {}
    reader = csv.DictReader(open(existing_data_file))
    for row in reader:
        data_src = row.pop('Data Source')
        if data_src == 'Manual':
            pdfurl = row.pop('PDF URL')
            existing_data[pdfurl] = row
    return existing_data

def lookup_org(org_num):
    """Looks up org by ProPublica num. Returns json from ProPublica"""
    url = "https://projects.propublica.org/nonprofits/api/v2/organizations/"+org_num+".json"
    org_json = json.loads(urllib2.urlopen(url).read())
    return org_json

def parse_org_data(org_json, existing_data):
    """Turns json w/org data into dict for csv"""
    org_data = {}
    org_data["official_name"] = org_json["organization"]["name"]
    org_data["pronum"] = org_json["organization"]["id"]
    org_data["filings"] = {}

    incomplete_filings = []

    # TODO: Change parsing order so entries in finaldata.csv are in sensible order.
    for filing in org_json["filings_with_data"]:
        filing_data = {}
        # TODO: Somehow factor out the fields
        filing_data["source"] = "Auto"
        filing_data["year"] = filing["tax_prd_yr"]
        try: 
            filing_data["type"] = filing["formtype"]
        except Exception:
            filing_data["type"] = "NA"
        filing_data["pdfurl"] = filing["pdf_url"]
        filing_data["totrev"] = filing["totrevenue"]
        filing_data["totexp"] = filing["totfuncexpns"]
        filing_data["netinc"] = filing["totrevenue"] - filing["totfuncexpns"]
        filing_data["totass"] = filing["totassetsend"]
        filing_data["totlia"] = filing["totliabend"]
        filing_data["netass"] = filing["totassetsend"] - filing["totliabend"]
        
        org_data["filings"][filing_data["pdfurl"]] = filing_data
    for filing in org_json["filings_without_data"]:

        # TODO: we need to decide what to do when there are multiple forms for
        # same year. Currently, our script uses the year as a key for
        # org_data["filings"] so when there are multiple forms, the last one
        # just overrides everything. are we okay with just having any form on there?
        # if so, we don't need to do anything
        filing_data = {}
        filing_data["source"] = "Manual"
        filing_data["year"] = filing["tax_prd_yr"]
        filing_data["pdfurl"] = filing["pdf_url"]
        try:
            # see if we already have the data given this pdf, remove if we do
            # now, only the outdated pdf urls will remain in existing_data
            pdfdata = existing_data.pop(filing_data["pdfurl"])
        except KeyError:
            org_and_year = org_data["official_name"]+" "+ str(filing_data["year"])
            print("Missing data or extra pdf for " + org_and_year)
            incomplete_filings.append(org_and_year)
            pdfdata = {}
        # TODO: Make error handling more specific if necessary.
        except Exception as err:
            print("Unexpected Error Occured: "+str(err))
        filing_data["type"] = pdfdata.get("Form Type", "NA")
        filing_data["totrev"] = pdfdata.get("Total Revenue", "NA")
        filing_data["totexp"] = pdfdata.get("Total Functional Expenses", "NA")
        filing_data["netinc"] = pdfdata.get("Net Income", "NA")
        filing_data["totass"] = pdfdata.get("Total Assets", "NA")
        filing_data["totlia"] = pdfdata.get("Total Liabilities", "NA")
        filing_data["netass"] = pdfdata.get("Net Assets", "NA")

        # TODO: decide here whether we're okay with using the year as key
        # it's fine if we decide we only need one form.
        org_data["filings"][filing_data["pdfurl"]] = filing_data
    return (org_data, incomplete_filings)

def write_org_data(org_data, write_function):
    """Takes a dict of org filings and writes it to csv in year order"""
    pdfurls = org_data["filings"].keys()
    pdfurls.sort()
    for pdfurl in pdfurls:
        filing_data = org_data["filings"][pdfurl]
        write_function([org_data["pronum"], org_data["official_name"],
                        filing_data["year"], filing_data["type"], filing_data["source"],
                        filing_data["pdfurl"], filing_data["totrev"],
                        filing_data["totexp"], filing_data["netinc"],
                        filing_data["totass"], filing_data["totlia"],
                        filing_data["netass"]])

def main():
    """Compiles data into csv file"""
    overall_start_time = time.time()
    print("Starting script...")

    org_nums = get_list_of_orgs(LIST_OF_ORGS_FILE)
    existing_data = get_existing_data(EXISTING_DATA_FILE)

    incomplete_data = []

    with open("finaldata.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        # TODO: Factor out the header
        # TODO: Find a way to better ensure header is synced with existingdata.csv
        header = ["Propublica Number", "Club Name", "Tax Year", "Form Type", "Data Source",
                  "PDF URL", "Total Revenue", "Total Functional Expenses",
                  "Net Income", "Total Assets", "Total Liabilities",
                  "Net Assets"]
        writer.writerow(header)

        for org_num in org_nums:
            start_time = time.time()
            org_json = lookup_org(org_num)
            org_data, incomplete_filings = parse_org_data(org_json, existing_data)
            write_org_data(org_data, writer.writerow)
            if incomplete_filings:
                incomplete_data.append(incomplete_filings)
            end_time = time.time()
            print("Completed "+org_data["official_name"]+" in "+
                  str(round((end_time - start_time), 2))+"s")

        if existing_data == {}:
            print("All your existing data was used!")
        else:
            print("The following pdf links are outdated and are not included in the final data.")
            for oldlink in existing_data:
                print(oldlink)

    overall_end_time = time.time()

    if incomplete_data:
        print("Incomplete entries:")
    for filing in incomplete_data:
        if filing:
            print(filing)
    print ("Total time: "+str(round((overall_end_time - overall_start_time),
                                    2)) + "s")

if __name__ == "__main__":
    main()
