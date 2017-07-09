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

def get_list_of_orgs(file_loc):
    """Get the list of organizations to analyze. Assumes the first column of
the CSV has the organization numbers."""
    orgnums = []
    with open(file_loc, "r") as csv_file:
        reader = csv.reader(csv_file)
        # avoid header row
        next(reader)
        # extract organization number
        for row in reader:
            orgnums.append(row[0])
    return orgnums

def get_manual_data(file_loc):
    """Store the human-read data from the pdfs into a dictionary format with
the pdfurl as the key """
    manualdata = {}
    reader = csv.DictReader(open(file_loc))
    for row in reader:
        key = row.pop('PDF URL')
        manualdata[key] = row
    return manualdata

def lookup_org(orgnum):
    """Looks up org by orgnum. Returns json"""
    url = "https://projects.propublica.org/nonprofits/api/v2/organizations/" + orgnum + ".json"
    orgjson = json.loads(urllib2.urlopen(url).read())
    return orgjson

def parse_org_filings(orgjson):
    """Turns json w/org data to dict for csv"""
    org_data = {}
    org_data["official_name"] = orgjson["organization"]["name"]
    org_data["pronum"] = orgjson["organization"]["id"]
    org_filings = {}
    org_data["filings"] = org_filings
    for filing in orgjson["filings_with_data"]:
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
    officialname = org_data["official_name"]
    orgnum = org_data["pronum"]
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
        write_function([orgnum, officialname, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

def write_to_csv():
    """Writes a dict with multiple filling years to csv"""
    pass

def main():
    """Compiles data into csv file"""
    overall_start_time = time.time()

    print "Starting script..."

    orgnums = get_list_of_orgs("listoforgs.csv")
    manualdata = get_manual_data("manualdata.csv")

    # write up all the data in a finaldata.csv
    with open("finaldata.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        header = ["Propublica Number", "Club Name", "Tax Year", "Data Source",
                  "PDF URL", "Total Revenue", "Total Functional Expenses",
                  "Net Income", "Total Assets", "Total Liabilities", "Net Assets"]
        writer.writerow(header)

        # for every propublica organization
        for orgnum in orgnums:
            start_time = time.time()

            #-----
            orgjson = lookup_org(orgnum)
            org_filings = parse_org_filings(orgjson)
            write_org_filings(org_filings, writer.writerow)

            #-----
            # grab all the data on this org
            # orgjson = lookup_org(orgnum)

            # grab the name
            officialname = orgjson["organization"]["name"]

            # for all the years that have direct data in the API, grab the data
            # for filing in orgjson["filings_with_data"]:
                # datasrc = "Auto"
                # year = filing["tax_prd_yr"]
                # pdfurl = filing["pdf_url"]
                # totrev = filing["totrevenue"]
                # totexp = filing["totfuncexpns"]
                # netinc = int(totrev) - int(totexp)
                # totass = filing["totassetsend"]
                # totlia = filing["totliabend"]
                # netass = int(totass) - int(totlia)
                # writer.writerow([orgnum, officialname, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

            # for all the years without direct data, check if we have it in our manual data
            for filing in orgjson["filings_without_data"]:
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
                writer.writerow([orgnum, officialname, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

            end_time = time.time()
            print "Completed " + officialname + " in " + str(round((end_time -
                                                                    start_time), 2)) + "s"

    overall_end_time = time.time()
    print "Total time: " + str(round((overall_end_time - overall_start_time), 2)) + "s"

if __name__ == "__main__":
    main()
    # org_json = lookup_org("43078945")
    # org_data = parse_org_filings(org_json)
    # write_org_filings(org_data)
