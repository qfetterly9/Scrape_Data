#!/usr/bin/env python3
# Encoding: UTF-8

#
# reads in a mhtml file and extracts the html
# then uses beautiful soup to parse and report out.
#

import sys
import os, glob
import string
import re
import time
import copy
import datetime
import dateutil
import dateutil.tz
import pprint
import csv
import base64
import re
import email
import email.message
import mimetypes
import os
import sys
import argparse

from bs4 import BeautifulSoup


def table_to_csv(tbl):
    output = []  # going to turn these into list of lists (rows) with td elements in rows
    if args.verbose >= 3:
        print(tbl)

    thead_tag = tbl.find("thead")

    if not thead_tag:  # Simple table no thead and no tbody
        for tr in tbl.find_all("tr"):
            line = []
            for td in tr.find_all("td"):
                line.append(td.get_text(strip = True))
                # not append sub_csv since these do not have subtables
            output.append(line)
        if args.verbose >= 3:
            print("========")
        if args.verbose >= 3:
            print(output)
        return output

    # We do have a thead so more complicated
    # this should never now get a nested table.
    if thead_tag:
        # head = thead_tag.find_all("th")
        heads = tbl.find_all("th")
        headers = []
        for h in heads:
            headers.append(h.get_text(strip = True))
        output.append(headers)
    # now do the body
    for tbody in tbl.find_all("tbody"):  # each row has its own table body (to get outline formating??)
        last_line = []
        for tr_tag in tbody.find_all("tr"):
            line = []
            for td_tag in tr_tag.find_all("td"):  # return link if exists
                if td_tag.a:
                    if args.verbose >= 3:
                        print("----")
                    if args.verbose >= 3:
                        print(td_tag)
                    line.append(td_tag.a.get('href').strip())
                #elif (td_tag["colspan"="4"] and td_tag.dl):
                elif (td_tag.dl):
                    line= ["",[td_tag.dl.dt.get_text(strip = True),td_tag.dl.dd.get_text(strip = True)], "","","" ]
                    
                else:
                    line.append(td_tag.get_text(strip = True))
            if line and line[0] == "Modifier:": 
                line[0] = last_line[0]+"-"+"Modifier"
                #do not update last_line if this is a modifier line
            else:
                last_line = line
            output.append(line)
    if args.verbose >= 3:
        print("========")
    if args.verbose >= 3:
        print(output)

    return output


def table_court_record_to_csv_unused(tbl):
    output = []  # going to turn these into list of lists (rows) with td elements in rows
    if args.verbose >= 3:
        print(tbl)

    thead_tag = tbl.find("thead")

    # We do have a thead so more complicated
    # this should never now get a nested table.
    if thead_tag:
        # head = thead_tag.find_all("th")
        heads = tbl.find_all("th")
        headers = []
        for h in heads:
            headers.append(h.get_text(strip = True))
        headers.append("Addtional Text")
        output.append(headers)
    # now do the body
    for tbody in tbl.find_all("tbody"):  # each row has its own table body (to get outline formating??)
        last_line = []
        for tr_tag in tbody.find_all("tr"):
            line = []
            for td_tag in tr_tag.find_all("td"):  # Modified text
                if (td_tag.dl):
                    line= ["",[td_tag.dl.dt.get_text(strip = True),td_tag.dl.dd.get_text(strip = True)], "","","" ]
                    
                else:
                    line.append(td_tag.get_text(strip = True))
            if line and line[0] == "Modifier:": 
                line[0] = last_line[0]+"-"+"Modifier"
                #do not update last_line if this is a modifier line
            else:
                last_line = line
            output.append(line)
    if args.verbose >= 3:
        print("========")
    if args.verbose >= 3:
        print(output)

    return output



def decode_mhtml2html(filename):

    mht = open(filename, "rb")

    # Read entire MHT archive -- it's a multipart(/related) message.
    a = email.message_from_bytes(mht.read())  # Parser is "conducive to incremental parsing of email messages, such as would be necessary when reading the text of an email message from a source that can block", so I guess it's more efficient to have it read stdin directly, rather than buffering.

    parts = a.get_payload()  # Multiple parts, usually?
    if not type(parts) is list:
        parts = [a]  # Single 'str' part, so convert to list.

    # Save all parts to files.
    partn = 0
    for p in parts:  # Look for the part with the html
        partn += 1
        if args.verbose > 1: print("in parts", partn, len(p), p.get("content-location"))
        # ??? cs = p.get_charset() # Expecting "utf-8" for root HTML, None for all other parts.
        ct = p.get_content_type()  # String coerced to lower case of the form maintype/subtype, else get_default_type().
        fp = p.get("content-location") or "index.html"  # File path. Expecting root HTML is only part with no location.

        if args.verbose > 3: print("partn, ct, fp:", partn, ct, fp)

        if ct == "text/html" and (re.search("wcca.wicourts.gov/caseDetail", fp) or fp == "index.html"):
            html_bytes = p.get_payload(decode=True)
            html = html_bytes.decode('utf-8')
            # print("Length:", len(html))
            # print(html)
            if re.search("<!DOCTYPE html><html", html):
                return(html)

def decode64_mhtml2html(text):
    output = ""
    p_list = text.split("------=_NextPart")  #get all the parts
    partn = 0
    for p in p_list:  # go through the list and find the ones that could be the payload html
        partn += 1
        if p.find("Content-Type: text/html") >=0 and p.find("Content-Transfer-Encoding: base64") >=0:
            print("part_num:",partn,"=========================================================")
            print("header:", p[:250])
            match = re.search(r'(?ms)unicode"[ \n]*(.*)', p)
            if match:
                encoded_text = match.group(1).strip()
                #print("the encoded text:  ", len(encoded_text), len(encoded_text)%4)
                #print("the encoded text2:\n|"+encoded_text[:200])
                #base64_bytes = encoded_text.encode('ascii')
                output = base64.b64decode(encoded_text).decode('utf-16')
                #print(bytes_str[:64])
                #output = str(bytes_str, )
                #print(output[:200])
                #output = message_bytes.b64decode('ascii')
                
                #print("base64:\n", output)
                if output.find("id=reactContent"): #There are two sections get the first, correct one
                    return output
                else: 
                    return ""
                        

def parse_arguments_fix():
    global args

    parser = argparse.ArgumentParser(description='Parse the ccap records')

    parser.add_argument('-i', '--infile', dest='infile', default="Metcalf/State of Wisconsin vs. Wilbert Gordy.mht",
                        #                   required=True,
                        help='Input file - should be a CSV file with arguments in first row')

    #parser.add_argument('-d', '--indir', dest='indir', default="Donaldson/Jan 29 2019/",
    parser.add_argument('-d', '--indir', dest='indir', default=".",
    #parser.add_argument('-d', '--indir', dest='indir', default="",
                        #                   required=True,
                        help='Input file - should be a CSV file with arguments in first row')

    parser.add_argument('-o', '--outdir', dest='outdir', type=str, default='output',
                        help='Location of outfile')

    parser.add_argument('-r', '--report', dest='report', type=str, default='ext_charges',
                        help='Location and name of outfile')

    parser.add_argument("-v", "--verbosity", dest='verbose', type=int, default=1,
                        help="increase output verbosity")

    args = parser.parse_args()
    if args.verbose >= 3:
        print("Initial args:", args)


        # args.outfile=os.path.join('processed',"people_in_jail"+"date")
    print(sys.argv[0], "Reworked args:", args)

    # other setup


def extract_summary(s):
    global case_id
    if case_id == "2019CM002802":
        xxx = 1   # can set breakpoint here 
        print("in summary",s.prettify())
    output = {}
    cases_soup = None
    for link in s.find_all('dl'):  # get all the dt dd pairs and stuff in dictionary
        #print("in summary",link.prettify())
        output[link.dt.string] = link.dd.get_text(strip = True)
        if link.dt.string == "Case(s) cross-referenced with this case":
            cases_soup = link

    other_cases = []
      # get the div containing the cross references
    if cases_soup:
        for lnk in cases_soup.find_all("a"):
            #repr(lnk["href"]) gets you the whole link
            cross_case = lnk.get_text(strip = True)
            other_cases.append(cross_case)
    output["Cross references"] = other_cases
    return output


def extract_charges(s):
    global case_id
    if case_id == "2019CF000256":
        xxx = 1   # can set breakpoint here
    output = {}
    #print(s.prettify())
    general_row = s.find('div', class_="flex")  # get the first info
    general_info ={}
    for dl in general_row.find_all("dl"): #get the stuff in top row
        general_info[dl.dt.text.strip()] = dl.dd.text.strip()
    output["general"] = general_info
    
    
    for chrg in s.find_all('div', class_="charge"):  # do this charge by charge
        flex_row = chrg.find('div', class_="flex")
        chg_info ={}
        for dl in flex_row.find_all("dl"): #get the stuff in top row
            chg_info[dl.dt.text.strip()] = dl.dd.text.strip()
        output[chg_info["Count"]] = general_info
        
        
    #print("inside extract_charges:", s.find("div", class_="row").get_text())
    #print("inside extract_charges:", s.find("div", class_="row").find("span", class_="money").get_text())
    
    output["owes_court"] = s.find("span", class_="money").get_text(strip = True)

    charge_sum_table = s.find("table", class_="charge-summary")
    output["charge_summary"] = table_to_csv(charge_sum_table)

    return output

def extract_judgement_table(sentence): #This is if the sentences in a table. 
    global case_id
    output = {}
    header_cnt = 0
    
    #we think there is a table, go find it.
    table_bs = sentence.find("table")
    tbl = table_to_csv(table_bs)
    for index in range(len(tbl)): #expand tables with 1 more column to match older format
        if tbl[index][0]=="Condition": 
            tbl[index].insert(2, "Begin Date")
        else:
            tbl[index].insert(2, "")
    output["penalties_table"] = tbl
    table_bs.extract() #delete from sentence
    
    #put everything else in top
    """for row in sentence.find_all("div", class_="row"):
    #    for h5 in row.find_all("h5"):
    #        header_cnt += 1
    #        h_name = "header_"+str(header_cnt)
    #        output["h_name"] = h5.get_text()
    #    for dl in row.find_all("dl"):  
    #        output[dl.dt.get_text()] = dl.dd.get_text()
    """
            

    output["penalties_top"] = {}
    for dl in sentence.find_all("dl"):
        output["penalties_top"][dl.dt.get_text(strip = True)] = dl.dd.get_text(strip = True)
    return output

def extract_judgement_divs(sentence): #this is if the sentences are in rows for the table
    global case_id
    output = {}
    header_cnt = 0
    
    ######
    # First get the sentencing data and delete from sentence
    # Then get the top stuff which will then not be contaminated by punishment data
    ######
    output["penalties_table"] = [] #this is going to be a list of lists to mimic table_to_csv
    sentence_head = ["Sentence","Time","Begin date","Notes"]
    output["penalties_table"].append(sentence_head)
    for row in sentence.find_all("div", class_="supervision"):
        #print("row_div_judgement", row.prettify())
        row_dict ={}  #but first we make a dictionary
        row_list = []
        for dl in row.find_all("dl"):
            row_dict[dl.dt.get_text(strip = True)] = dl.dd.get_text(strip = True)
            
        for label in sentence_head:
            row_list.append(row_dict[label])  #turn into list
        output["penalties_table"].append(row_list)
        
        row.extract() #here is where the data is deleted from the tree
        
    #now get remaining dl, dt, dd info
    output["penalties_top"] = {}
    
    for dl in sentence.find_all("dl"):
        output["penalties_top"][dl.dt.get_text(strip = True)] = dl.dd.get_text(strip = True)
    
    
    return output

def extract_fullcharges(s):
    global case_id
    if case_id == "2019CF000256":
        xxx = 1   # can set breakpoint here
    
    output = {}
    output_rows = []
    output2 = []
    
    #######
    # first do the charge details and table with modifiers and then do the charge history table (a real table)
    ######
    for chrg in s.find_all('div', class_="chargeDetail"): 
        #print(chrg.prettify())  #pretty print
        chrg_dict = {}
        chrg_line = []
        modifiers = []
        for item in chrg.find_all('dl'): #put them into a dictionary
            tbl = item.find('table')
            if tbl:
                #This will be the table of modifiers
                chrg_dict[item.dt.get_text(strip = True)] = table_to_csv(tbl)     
            else: 
                chrg_dict[item.dt.get_text(strip = True)] = item.dd.get_text(strip = True)
        output_rows.append(chrg_dict)
        #move this to the report
        #for name in headers[:-2]:   # force items into order we want
                                    # but don't do modifiers they are on a table below this line
        #    if chrg_dict[name] == '\xa0':
        #        chrg_line.append("")
        #    else:
        #        chrg_line.append(chrg_dict[name])

        jdgmt = chrg.find("div", class_="jdgmtWrapper")
        if jdgmt:
            if jdgmt.find("table"): # Has table based sanctions
                chrg_dict["sentence"] = extract_judgement_table(jdgmt)
            elif len(jdgmt.find_all("div", class_="supervision")) >= 3: # has rows of dl sanctions
                chrg_dict["sentence"] = extract_judgement_divs(jdgmt) 
            #print(output["sentence"])
            
            
    #now go for charge history. 
    charge_history = s.find("div", class_="chargeHist")
    if charge_history:
        chg_h_table = charge_history.find("table")
        output["chargeHist"] = table_to_csv(chg_h_table)
        #print(output["chargeHist"])
    output["chargeDetail"] = output_rows
    
    return output


def extract_defendant(s):
    output = {}
    for link in s.find_all('dl'):  # get all the dt dd pairs and stuff in dictionary
        if link.dd.table: # not really text in dd, really a table 
            dd_table = table_to_csv(link.dd.table)
            output[link.dt.get_text(strip = True)] = dd_table

        else:
            output[link.dt.get_text(strip = True)] = link.dd.get_text(strip = True)

    if not output.setdefault("Address", ""): #Sometimes Address has a update date appended
                                                #Add a blank value and then fill it
        for key in output.keys():
            if len(key) > 7 and key.find("Address")>=0:
                output["Address"] = output[key]

    return output


def extract_activities(s):
    output = {}
    activities_table = s.find("table")
    output["court_activities"] = table_to_csv(activities_table)
    
    return output


def extract_ct_records(s):
    output = {}
    records_table = s.find("table")
    output["court_records"] = table_to_csv(records_table)
    
    return output

def extract_civilJdgmts(sect):
    output = {}
    for link in sect.find_all('dl'):  # get all the dt dd pairs and stuff in dictionary
        output[link.dt.string] = link.dd.string
    return output

def extract_receivables(sect):
    output = {}
    records_table = sect.find("table")
    output["receivables"] = table_to_csv(records_table)
    
    return output

def extract_citations(sect):
    output = {}
    for ctn in sect.find_all("div", class_="citation"):
        citation_node = ctn.find("h5", class_="detailHeader")
        citation_n = citation_node.text
        label, citation_n = citation_n.split()
        output[citation_n] = {}
        for dl in ctn.find_all("dl"):
            output[citation_n][dl.dt.text] = dl.dd.text.strip()
    
    return output

def report_race_gender(extracted_data, header):
    race2letter = {"African American": "B", "American Indian or Alaskan Native":"N",
"Asian or Pacific Islander":"A", "Caucasian":"W", "Hispanic":"L", "Unknown":"U"}
    gender2letter = {"Male":"M","Female":"F",}
    output=[]
    defendant_dict = extracted_data["defendant"]
    defendant_dict["Case Number"] = extracted_data["case_number"]
    defendant_dict["Name_Number"] = ""
    #print(defendant_dict)
    for key in header:
        if key == "Sex":
            if not(defendant_dict.get(key, "U")):
                dat = "U"
            else:
                dat = gender2letter[defendant_dict.get(key, "U")]  #convert from .eg Caucasian to W by lookup in dictionary
        elif key == "Race":
            #print("race is:", key, defendant_dict.get(key, "U"))
            if not(defendant_dict.get(key, "U")):
                dat = "U"
            else:
                dat = race2letter[defendant_dict.get(key, "U")]
        elif key == "Filing date":
            #print("race is:", key, defendant_dict.get(key, "U"))
            dat = extracted_data["summary"]["Filing date"]

        elif key == "Address":
            #print("race is:", key, defendant_dict.get(key, "U"))
            dat = extracted_data["summary"]["Address"]
            
        elif key == "Cross references":
            #print("race is:", key, defendant_dict.get(key, "U"))
            dat = extracted_data["summary"]["Cross references"]
            dat = "|".join(dat)

        else:
            dat = defendant_dict.get(key, "")
        output.append(dat)
    
    return output


def linearize_sentence(sentence_dat): # called by report_ext_charges
    # 1.makes rows of sentence fit into one field 2. tries to extract money and time
    # This works on only a single sentence
    # Action, Court offical, Sentence(location), Time, probation, Fees
    """ possible parts of charge (in a table)
    penalty Alcohol assessment
    penalty Alcohol treatment
    penalty Community service
    penalty Condition
    penalty Costs
    penalty DOT License Revoked
    penalty Drug treatment
    penalty Employment / School
    penalty Expunction
    penalty Fine
    penalty Firearms/Weapons Restriction
    penalty Forfeiture / Fine
    penalty House of Correction
    penalty Ignition interlock
    penalty Jail time
    penalty Local Jail
    penalty Other
    penalty Other Sentence
    penalty Prohibitions
    penalty Psych treatment
    penalty Restitution
    penalty Sentence
    """
    
    #print(sentence_dat)
    output = {}
    time_sentc = ""
    money_sentc = ""
    sentence_location = ""
    probation = ""
    all_sentc = ""
    penalties_top = sentence_dat["penalties_top"]
    if sentence_dat.get("penalties_table"): 
        for row in sentence_dat["penalties_table"]: #Penalties table should be the same regardless if the sentence is in a table or a series of rows. 
            # not sure this loop is needed maybe there is only one row with money or time
            if args.verbose >= 3: print("penalty", row[0])
            
            all_sentc += "|" + ":".join(row) 
            if row[0] == "Sentence" or row[0] == "Condition" : continue  #header row
            if row[0] in ["Local Jail", "Jail time", "House of Correction"] : 
                time_sentc += row[1]+" - "+row[3]+" | "
            if row[3].find("$") >=0: 
                money_sentc += row[3]+" | "
            if row[0] and (row[0] not in ["Costs", "Other Sentence", "Prohibitions", "Other", "Restitution"]) : 
                sentence_location += row[0] + " | "
            
    
    output["sentence_location"] =  sentence_location[1:] # strip off initial | char 
    output["Time"] = time_sentc
    output["Probation"] = probation
    output["Fine"] = money_sentc
    output["All Sentence"] = all_sentc
   
    return output


def report_court_records(extracted_data, race_gender_line):
    prosecutor = extracted_data["charges"]["general"]["Prosecuting agency attorney"]
    output = []
    for x in range(1,len(extracted_data["court_records"]["court_records"])):
        if extracted_data["court_records"]["court_records"][x][0]:        #only if there is a date showing up in first column i.e. first row of table
            records_outlist = []
            row_data = extracted_data["court_records"]["court_records"][x]
            records_outlist.extend(race_gender_line + [prosecutor] + row_data) 

                    
        #if in range and if the first column is empty, then its additional text and we want that in same line     
            if x+1 < len(extracted_data["court_records"]["court_records"]) and not extracted_data["court_records"]["court_records"][x+1][0]:
                records_outlist.append(extracted_data["court_records"]["court_records"][x+1][1][1])
            else: #no additional text but add blank to make all lines have same # elements 
                records_outlist.append("")
            #courtRecordWriter.writerow(records_outlist)
            output.append(records_outlist)
        
    return output


def report_ext_charges(extracted_data, charges_header):
    
    """
    Called by main 
    Returns a list of lists of lines
    
 
    """
    if extracted_data["case_number"] == "2019CM001585":
        xxx = 1
    
    output= []
    charge_line_list = []
    
    extended_charges = extracted_data.get("full_charges")
    
    for chrg_dict in extended_charges["chargeDetail"]: # each charge
    
#        charge_line_list += race_list    
        line_dict = {}  # clear
        line_dict.update(chrg_dict)
        for head in charges_header:   # fill everything we can 
            line_dict[head] = chrg_dict.get(head, "")  
            
            #always need this 
            line_dict["Prosecutor"] = extracted_data["charges"]["general"]["Prosecuting agency attorney"]    
            #sometimes need this, but will be overwritten if not needed
            line_dict["Court official"] = extracted_data["charges"]["general"]["Responsible official"]    
        
        ##### Add modifiers
        modifier_table = chrg_dict.get("Charge modifier(s)")
        if modifier_table:
            mod_citation = []
            mod_desc = []

            tbl_header = modifier_table[1]
            for row in modifier_table[1:]: # skip header and then grab any data and concat
                mod_citation.append(row[0])
                mod_desc.append(row[1])
            
            line_dict["Modifier Citation"]= " | ".join(mod_citation) #add in modifiers
            line_dict["Modifier Desc"]= " | ".join(mod_desc)        

            
        sentence_dat = chrg_dict.get("sentence")
        if sentence_dat:
            #prosecutor = extracted_data["charges"]["general"]["Prosecuting agency attorney"]
            line_dict.update(linearize_sentence(sentence_dat))

        
        charge_line_list = []                
        for name in charges_header:   # force items into order we want
            charge_line_list.append(line_dict.get(name))    


        output.append(charge_line_list) 
    chg_hist = extracted_data["full_charges"].get("chargeHist")
    if chg_hist:  #if there is any history, make new lines for that history
        for amend in chg_hist:
            if amend[0] == "Count": continue  #don't do the header
            line_dict = {}  # clear
            for head in charges_header:   # fill empty 
                line_dict[head] = ""  
            line_dict['Count'] = amend[0]
            line_dict['Statute cite'] = amend[1]
            line_dict['Description'] = amend[2]
            line_dict['Action'] = amend[3]
            
            
            
        charge_line_list = []                
        for name in charges_header:   # force items into order we want
            charge_line_list.append(line_dict.get(name))    


        output.append(charge_line_list)       
    return output
    

def extract_data(soup):
    # partition the HTMTL into sections and extract data from each section
    global case_id 
    case_id = ""
    data = {}

    case_id_bs = soup.find("div", id="case-header-info").find("span", class_="caseNo")
    case_id = case_id_bs.get_text(strip = True)
    data["case_number"] = case_id
    for sect in soup.find_all('section'):
        #print(sect["id"])
        if sect["id"] == "summary":
            # print(sect.prettify())
            data["summary"] = extract_summary(sect)
        elif sect["id"] == "charges":  # get the court officials
            #print(sect.prettify())
            data["charges"] = extract_charges(sect)
        elif sect["id"] == "fullCharges":  # get expanded charges
            #print(sect.prettify())
            data["full_charges"] = extract_fullcharges(sect)
        elif sect["id"] == "defendant":
            #print(sect.prettify())
            data["defendant"] = extract_defendant(sect)
        elif sect["id"] == "activities":
            #print(sect.prettify())
            data["court_activities"] = extract_activities(sect)
        elif sect["id"] == "records":
            #print(sect.prettify())
            data["court_records"] = extract_ct_records(sect)
        elif sect["id"] == "civilJdgmts":
            #print(sect.prettify())
            data["civilJdgmts"] = extract_civilJdgmts(sect)
        elif sect["id"] == "receivables":
            #print(sect.prettify())
            data["receivables"] = extract_receivables(sect)
        elif sect["id"] == "citations":
            #print(sect.prettify())
            data["citations"] = extract_citations(sect)
            #print("casenum:",case_id.text)
        else:
            print("ERROR: Here is a section we are not handling", sect.prettify()) 

    return data


def run_one_file(file_nm): 
    output_race_gender = {}
    #print("opening filename", file_nm)

    text = open(file_nm, "r").read()
    
    if text.find("------MultipartBoundary") >= 0: #not found = -1
        html_page = decode_mhtml2html(file_nm) # pass the filename because it is not easy to pass a string
    elif text.find("<body") >= 0:
        html_page = text
    elif text.find("------=_NextPart") >= 0:
        print("ERROR This is probably encoded", file_nm, file=sys.stderr)
        # html_page = decode64_mhtml2html(text)
        return "ERROR"  #this is temporary for 
    else:
        print("ERROR Cannot figure out what kind of file we have with", file_nm, file=sys.stderr)
        return "ERROR"
    #print("len:", len(html_page))

    # Parse the html in the 'page' variable, and store it in Beautiful Soup format
    if len(html_page) < 2500:
        print("ERROR: file too short at",len(html_page), "char",  file_nm, file=sys.stderr)
        return "ERROR"
    else:
        soup = BeautifulSoup(html_page, 'html.parser')

    extracted_data = extract_data(soup)


    # might as well look at the data we have collected in a pleasing way
    pp = pprint.PrettyPrinter(indent=2, width=100)  # make a pprint object for debugging
    for top_keys in extracted_data.keys():
        if args.verbose > 1: print("Data from Section", top_keys)
        if args.verbose > 3: pp.pprint(extracted_data[top_keys])  # use python builtin pp to pretty print the complex data we have created
        
    out_fn = os.path.join(args.outdir, args.report+".csv")
        
    if not(extracted_data.get("full_charges")):
        print("ERROR: no expanded charges in:", file_nm, file=sys.stderr)
    return extracted_data


################################################################################
################################################################################
# Main
################################################################################
################################################################################



def main():
    global case_id
    starttime = datetime.datetime.today()
    output_race_gender = []
    r_s_header = ["Name_Number", "Defendant name", "Date of birth", "DOC_ID", "Race", "Sex", "Case Number", "Filing date"]
    r_s_a_header = r_s_header+ ["Address", "Cross references"]
    #output_race_gender.append(r_s_header) # set this so each input file (person) adds one line to a CSV file
      
    output_ext_charges = []
    ext_charges_header = ["Count","Statute cite","Description","Severity","Offense date","Plea","Modifier Citation", "Modifier Desc", "Action", "Court official", "Prosecutor", "Sentence", "Time", "Probation", "Fine", "All Sentence"]
    #output_ext_charges.append(r_s_header+ext_charges_header)
    
    output_ct_record = []
    court_records_header = ['Date', 'Event', 'Court official', 'Court reporter','Amount', "Additional text"]  
    #output_ct_record.append(r_s_header+court_records_header)

  
    
    parse_arguments_fix()  # get the arguments and set the output file
    
    if args.indir:  #do a directory of files and subdirectories. 
        d = os.path.dirname(os.path.abspath(__file__))
        path_to_files = os.path.join(d,args.indir,"**")

        count = 0
        charges_lines = []
        ct_record_lines = []
        for file_nm in glob.glob(path_to_files, recursive=True ):
            filename, file_ext = os.path.splitext(file_nm)
            #print("file ext", filename, file_ext)
            if not(file_ext == ".html" or file_ext == ".mhtml" 
                   or file_ext == ".mht" or file_ext == ".mht"):
                print("WARNING: not able to process", file_nm)
                continue
            count += 1
            if args.verbose >= 1: print("about to process", file_nm)
            extracted_data  = run_one_file(file_nm)
            if extracted_data == "ERROR": 
                continue # maybe got a webarchive as a .mht file
            else:
                if args.verbose >= 1: print("SUCCESS:", file_nm, file=sys.stderr)
            
            if extracted_data.get("defendant"):    
                race_gender_addr_line = report_race_gender(extracted_data, r_s_a_header) # format data for this file
                output_race_gender.append(race_gender_addr_line) # save it for the whole thing
                trim_point = len(r_s_header)
                race_gender_line = race_gender_addr_line[:trim_point]
            else:
                race_gender_line = [""]*len(r_s_header)
                print("ERROR No defendent so no case # or Race_Gender")
                
            if extracted_data.get("full_charges"):    
                charges_lines = report_ext_charges(extracted_data, ext_charges_header) # format data for this file
                for charge in charges_lines:    
                    junk = race_gender_line+charge
                    output_ext_charges.append(race_gender_line+charge) # save it for the whole thing
                
            if extracted_data.get("court_records"):  
                prosecutor = extracted_data["charges"]["general"]['Prosecuting agency attorney']
                ct_records_lines = report_court_records(extracted_data, race_gender_line) # format data for this file
                output_ct_record.extend(ct_records_lines) # save it for the whole thing

    elif args.indir == "":  #Do a single file
        extracted_data  = run_one_file(args.infile)
        if args.report == "race_sex": 
            race_gender_line = report_race_gender(extracted_data, r_s_header) # format data for this file
            output_race_gender.append(race_gender_line) # save it for the whole thing
        
 
 #######################
 #
 # now write out reports
 #
 #######################
    #First find the earliest and latest dates in Filing Date
    last_date = "1111" # set low and work up
    first_date = "9999"# set high and work down
    for line in output_race_gender:
        month, day, year = line[7].split("-")  # 
        isodate = "-".join([year, month, day])
        if isodate > last_date: last_date = isodate
        if isodate < first_date: first_date = isodate
    file_dates = "_to_".join([first_date, last_date])
 
    out_fn = os.path.join(args.outdir, "race_sex"+file_dates+".csv")

    with open(out_fn, "w") as outfile1:
        writer = csv.writer(outfile1, delimiter="\t")
        writer.writerow(r_s_a_header)
        writer.writerows(output_race_gender) # give a list of lists. 1 list each row

   
    out_fn = os.path.join(args.outdir, "ext_charges"+file_dates+".csv")

    with open(out_fn, "w") as outfile2:
        writer = csv.writer(outfile2, delimiter="\t")
        writer.writerow(r_s_header+ext_charges_header)
        junk = output_ext_charges[:5]
        writer.writerows(output_ext_charges) # give a list of lists. 1 list each row
        
    out_fn = os.path.join(args.outdir, "court_records"+file_dates+".csv")

    with open(out_fn, "w") as outfile2:
        writer = csv.writer(outfile2, delimiter="\t")
        writer.writerow(r_s_header+["Prosecutor"]+court_records_header)
        writer.writerows(output_ct_record) # give a list of lists. 1 list each row



    print("Extracted from %d files with correct file extension"%count)
    endtime = datetime.datetime.today()
    
    timedif = endtime - starttime
    difmin = (timedif.total_seconds()) / 60.0
    if args.verbose >= 1:
        print("Started:", starttime.isoformat(), "\nfinished:", endtime.isoformat(), "\ntook:", difmin, "min")


if __name__ == "__main__":
    # execute only if run as a script
    main()
