#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Creates a csv file containing the financial data of specified organizations
using ProPublica.

Inputs:
LIST_OF_ORGS_FILE (the list of propublica numbers)
MANUAL_DATA_FILE (any data that is only available via pdf should be filled into
this file manually)

Output:
finaldata.csv (data autograbbed from the API merged with manual data)
"""

from __future__ import print_function
import csv
import json
import time
import urllib2

LIST_OF_ORGS_FILE = "listoforgs.csv"
MANUAL_DATA_FILE = "manualdata.csv"

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

def get_manual_data(manual_data_file):
    """Stores data from a csv into a dict format with the pdfurl as the key."""
    manual_data = {}
    reader = csv.DictReader(open(manual_data_file))
    for row in reader:
        key = row.pop('PDF URL')
        manual_data[key] = row
    return manual_data

def lookup_org(org_num):
    """Looks up org by ProPublica num. Returns json from ProPublica"""
    url = "https://projects.propublica.org/nonprofits/api/v2/organizations/"+org_num+".json"
    org_json = json.loads(urllib2.urlopen(url).read())
    return org_json

def parse_org_data(org_json, manual_data):
    """Turns json w/org data into dict for csv"""
    org_data = {}
    org_data["official_name"] = org_json["organization"]["name"]
    org_data["pronum"] = org_json["organization"]["id"]
    org_data["filings"] = {}

    incomplete_filings = []

    for filing in org_json["filings_with_data"]:
        filing_data = {}
        # TODO: Somehow factor out the fields
        filing_data["source"] = "Auto"
        filing_data["year"] = filing["tax_prd_yr"]
        filing_data["pdfurl"] = filing["pdf_url"]
        filing_data["totrev"] = filing["totrevenue"]
        filing_data["totexp"] = filing["totfuncexpns"]
        filing_data["netinc"] = filing["totrevenue"] - filing["totfuncexpns"]
        filing_data["totass"] = filing["totassetsend"]
        filing_data["totlia"] = filing["totliabend"]
        filing_data["netass"] = filing["totassetsend"] - filing["totliabend"]
        org_data["filings"][filing_data["year"]] = filing_data
    for filing in org_json["filings_without_data"]:
        #TODO: Add other formats that need to be skipped. 
        if filing["formtype_str"] == "990T": 
            print("Skipping Manual 990T Form for " + str(org_data["official_name"]) + " " + str(filing_data["year"]))
        else:
            filing_data = {}
            filing_data["source"] = "Manual"
            filing_data["year"] = filing["tax_prd_yr"]
            filing_data["pdfurl"] = filing["pdf_url"]
            try:
                pdfdata = manual_data[filing_data["pdfurl"]]
            except KeyError:
                print("Missing/Misspelled manual data for "+
                      org_data["official_name"]+" "+ str(filing_data["year"]))
                incomplete_filings.append(str(org_data["official_name"])+" "+
                                          str(filing_data["year"]))
                pdfdata = {}
            # TODO: Make error handling more specific if necessary.
            except Exception as err:
                print("Unexpected Error Occured: "+str(err))
            filing_data["totrev"] = pdfdata.get("Total Revenue", "NA")
            filing_data["totexp"] = pdfdata.get("Total Functional Expenses", "NA")
            filing_data["netinc"] = pdfdata.get("Net Income", "NA")
            filing_data["totass"] = pdfdata.get("Total Assets", "NA")
            filing_data["totlia"] = pdfdata.get("Total Liabilities", "NA")
            filing_data["netass"] = pdfdata.get("Net Assets", "NA")
            org_data["filings"][filing_data["year"]] = filing_data
    return (org_data, incomplete_filings)

def write_org_data(org_data, write_function):
    """Takes a dict of org filings and writes it to csv"""
    for filing_year in org_data["filings"]:
        filing_data = org_data["filings"][filing_year]
        write_function([org_data["pronum"], org_data["official_name"],
                        filing_data["year"], filing_data["source"],
                        filing_data["pdfurl"], filing_data["totrev"],
                        filing_data["totexp"], filing_data["netinc"],
                        filing_data["totass"], filing_data["totlia"],
                        filing_data["netass"]])

def main():
    """Compiles data into csv file"""
    overall_start_time = time.time()
    print("Starting script...")

    org_nums = get_list_of_orgs(LIST_OF_ORGS_FILE)
    manual_data = get_manual_data(MANUAL_DATA_FILE)

    incomplete_data = []

    with open("finaldata.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        # TODO: Factor out the header
        # TODO: Find a way to better ensure header is synced with manualdata.csv
        header = ["Propublica Number", "Club Name", "Tax Year", "Data Source",
                  "PDF URL", "Total Revenue", "Total Functional Expenses",
                  "Net Income", "Total Assets", "Total Liabilities",
                  "Net Assets"]
        writer.writerow(header)

        for org_num in org_nums:
            start_time = time.time()
            org_json = lookup_org(org_num)
            org_data, incomplete_filings = parse_org_data(org_json, manual_data)
            write_org_data(org_data, writer.writerow)
            if incomplete_filings:
                incomplete_data.append(incomplete_filings)
            end_time = time.time()
            print("Completed "+org_data["official_name"]+" in "+
                  str(round((end_time - start_time), 2))+"s")

    overall_end_time = time.time()
    # TODO: Improve formatting of incomplete entries
    print("Incomplete entries:")
    for filing in incomplete_data:
        if filing:
            print(filing)
    print ("Total time: "+str(round((overall_end_time - overall_start_time),
                                    2)) + "s")

if __name__ == "__main__":
    main()
