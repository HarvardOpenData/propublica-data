#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Creates a csv file with the financial data of orgs on Propublica.

Inputs:
listoforgs.csv (the list of propublica numbers)
manualdata.csv (any data that is only available via pdf should be filled
                into this file manually)

Output:
finaldata.csv

"""

import json
import urllib2
import csv
import time

def main():
    """Compiles data into csv file"""

    # keep track of start time
    overallstart = time.time()

    print "Starting script..."

    # collect list of orgs to analyze
    pronums = []
    with open("listoforgs.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for row in reader:
            pronums.append(row[0])

    # collect the manual data that was human-read from the pdfs
    # store the info in a dictionary format with the pdfurl as key
    manualdata = {}
    reader = csv.DictReader(open("manualdata.csv"))
    for row in reader:
        key = row.pop('PDF URL')
        manualdata[key] = row

    # write up all the data in a finaldata.csv
    with open("finaldata.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        header = ["Propublica Number", "Club Name", "Tax Year", "Data Source",
                  "PDF URL", "Total Revenue", "Total Functional Expenses",
                  "Net Income", "Total Assets", "Total Liabilities", "Net Assets"]
        writer.writerow(header)

        # for every propublica organization
        for pronum in pronums:

            # keep track of the time it takes to analyze each org
            start = time.time()
            url = "https://projects.propublica.org/nonprofits/api/v2/organizations/" + pronum + ".json"
            orgjson = json.loads(urllib2.urlopen(url).read())
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
                writer.writerow([pronum, officialname, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

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
                writer.writerow([pronum, officialname, year, datasrc, pdfurl, totrev, totexp, netinc, totass, totlia, netass])

            # end time
            end = time.time()

            # print time spent on this org
            print "Completed " + officialname + " in " + str(round((end - start), 2)) + "s"

    overallend = time.time()

    # print total time spent
    print "Total time: " + str(round((overallend - overallstart), 2)) + "s"

if __name__ == "__main__":
    main()
