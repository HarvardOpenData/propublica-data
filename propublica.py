#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Creates a csv file with the financial data of orgs on Propublica.

Inputs:
listoforgs.csv (the list of propublica numbers)
manualdata.csv (any data that is only available via pdf should be filled
                into this file manually)

Output:
finaldata.csv (data autograbbed from the API merged with manual data)
"""

import csv
import json
import time
import urllib2

def get_list_of_orgs(list_of_orgs_file):
    """Gets list of organizations. Assumes first column has the organization
numbers."""
    org_nums = []
    with open(list_of_orgs_file, "r") as csv_file:
        reader = csv.reader(csv_file)
        # Avoid header row
        next(reader)
        for row in reader:
            org_nums.append(row[0])
    return org_nums

def get_manual_data(manual_data_file):
    """Stores data from a csv into a dictionary format with the pdfurl as the
key """
    manual_data = {}
    reader = csv.DictReader(open(manual_data_file))
    for row in reader:
        key = row.pop('PDF URL')
        manual_data[key] = row
    return manual_data

def lookup_org(org_num):
    """Looks up org by orgnum. Returns corresponding json from ProPublica"""
    url = "https://projects.propublica.org/nonprofits/api/v2/organizations/"+org_num+".json"
    org_json = json.loads(urllib2.urlopen(url).read())
    return org_json

def parse_org_filings(org_json):
    """Turns json w/org data to dict for csv"""
    org_data = {}
    org_data["official_name"] = org_json["organization"]["name"]
    org_data["pronum"] = org_json["organization"]["id"]
    org_filings = {}
    org_data["filings"] = org_filings
    for filing in org_json["filings_with_data"]:
        filing_data = {}
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
    return org_data

def write_org_filings(org_data, write_function):
    """Takes a dict of org filings and writes it to csv"""
    official_name = org_data["official_name"]
    org_num = org_data["pronum"]
    for filing_year in org_data["filings"]:
        filing_data = org_data["filings"][filing_year]
        datasrc = filing_data["source"]
        year = filing_data["year"]
        pdfurl = filing_data["pdfurl"]
        totrev = filing_data["totrev"]
        totexp = filing_data["totexp"]
        netinc = filing_data["netinc"]
        totass = filing_data["totass"]
        totlia = filing_data["totlia"]
        netass = filing_data["netass"]
        write_function([org_num, official_name, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

def main():
    """Compiles data into csv file"""
    overall_start_time = time.time()

    print "Starting script..."

    org_nums = get_list_of_orgs("listoforgs.csv")
    manual_data = get_manual_data("manualdata.csv")

    # write up all the data in a finaldata.csv
    with open("finaldata.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        header = ["Propublica Number", "Club Name", "Tax Year", "Data Source",
                  "PDF URL", "Total Revenue", "Total Functional Expenses",
                  "Net Income", "Total Assets", "Total Liabilities", "Net Assets"]
        writer.writerow(header)

        # for every propublica organization
        for org_num in org_nums:
            start_time = time.time()

            org_json = lookup_org(org_num)
            org_filings = parse_org_filings(org_json)
            write_org_filings(org_filings, writer.writerow)

            official_name = org_json["organization"]["name"]

            # for all the years without direct data, check if we have it in our manual data
            for filing in org_json["filings_without_data"]:
                datasrc = "Manual"
                year = filing["tax_prd_yr"]
                pdfurl = filing["pdf_url"]
                try:
                    pdfdata = manualdata[pdfurl]
                except:
                    pdfdata = {}
                totrev = pdfdata.get("Total Revenue", "NA")
                totexp = pdfdata.get("Total Expenses", "NA")
                netinc = pdfdata.get("Net Income", "NA")
                totass = pdfdata.get("Total Assets", "NA")
                totlia = pdfdata.get("Total Liabilities", "NA")
                netass = pdfdata.get("Net Assets", "NA")
                writer.writerow([org_num, official_name, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

            end_time = time.time()
            print "Completed " + official_name + " in " + str(round((end_time -
                                                                    start_time), 2)) + "s"

    overall_end_time = time.time()
    print "Total time: " + str(round((overall_end_time - overall_start_time), 2)) + "s"

if __name__ == "__main__":
    main()

    # For debugging
    # org_json = lookup_org("43078945")
    # org_data = parse_org_filings(org_json)
    # write_org_filings(org_data)
