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



By the Harvard Open Data Project, copyright (c) 2017

"""

import json
import urllib2
import csv
import time

def get_list_of_orgs(file_loc):
    """
    Get the list of organizations to analyze. Assumes
    the first column of the CSV has the organization numbers.
    """
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
    """
    Store the human-read data from the pdfs into
    a dictionary format with the pdfurl as the key
    """
    manualdata = {}
    reader = csv.DictReader(open(file_loc))
    for row in reader:
        key = row.pop('PDF URL')
        manualdata[key] = row
    return manualdata


def lookup_org(orgnum):
    url = "https://projects.propublica.org/nonprofits/api/v2/organizations/" + orgnum + ".json"
    orgjson = json.loads(urllib2.urlopen(url).read())
    return orgjson


def main():
    """Compiles data into csv file"""

    # keep track of start time
    overallstart = time.time()

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

            # keep track of the time it takes to analyze each org
            start = time.time()

            # grab all the data on this org
            orgjson = lookup_org(orgnum)

            # grab the name
            officialname = orgjson["organization"]["name"]

            # for all the years that have direct data in the API, grab the data
            for filing in orgjson["filings_with_data"]:
                datasrc = "Auto"
                year = filing["tax_prd_yr"]
                pdfurl = filing["pdf_url"]
                totrev = filing["totrevenue"]
                totexp = filing["totfuncexpns"]
                netinc = int(totrev) - int(totexp)
                totass = filing["totassetsend"]
                totlia = filing["totliabend"]
                netass = int(totass) - int(totlia)
                writer.writerow([orgnum, officialname, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

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

            # end time
            end = time.time()

            # print time spent on this org
            print "Completed " + officialname + " in " + str(round((end - start), 2)) + "s"

    overallend = time.time()

    # print total time spent
    print "Total time: " + str(round((overallend - overallstart), 2)) + "s"


if __name__ == "__main__":
    main()
