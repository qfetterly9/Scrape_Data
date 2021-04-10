#
#
#  This version requests all the detail pages every time. 
# 
#
# largely from https://www.analyticsvidhya.com/blog/2015/10/beginner-guide-web-scraping-beautiful-soup-python/
# see docs at https://www.crummy.com/software/BeautifulSoup/bs4/doc/#get-text
#
# for requests library http://docs.python-requests.org/en/master/user/quickstart/#make-a-request
# import the library used to query a website
#
# /Users/eric/anaconda3/bin/python3
# find place to change this in edit -> Configure Pyhon
# 
#
# for the sqlite database
# https://docs.python.org/3.5/library/sqlite3.html?highlight=sqlite3#module-sqlite3
#
#To get javascript support for the downloads
# 
# used Selenium
# https://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python#26440563
# and also
# https://stackoverflow.com/questions/26393231/using-python-requests-with-javascript-pages
# chromium
# https://www.raspberrypi.org/forums/viewtopic.php?p=1172541
#
#
#2020-07-05 put into service at 4pm central time.
#
#2020-09-12 corrrect to local time. 




import sys, os, string, re, time, copy, datetime, dateutil, dateutil.tz, csv
import sqlite3
from sqlite3 import Error

import requests, re
from bs4 import BeautifulSoup
import argparse


def fix_charges(name_id, charges): #post process charges, list of list of charges

    #########################
    ## now get arrests and charges in arrests
    #########################

    outcharges = []
    ##tmp1 = datetime.datetime.strptime(head1.td.string, "%m/%d/%Y %I:%M %p")
    headers = ['Name Number','Date', 'Agency', 'Arrest Number', 'Agency Case Number', 'Offense', 'Date/Time', 'Disposition Date', 'Court Case Number', 'Entry Code']
    for arrest in charges: #these are the tables
        if arrest[0] != headers: #check for header so safe to remove
            if args.verbose >= 2:print("Error Header changed")
            if args.verbose >= 2:print("expected headers",headers)
            if args.verbose >= 2:print("arrest   headers",arrest[0])
            
            
        for charge in arrest[1:]: #i strip heading row, fix dates individual charges
            for pos in [1, 6]:
                tmp1 = datetime.datetime.strptime(charge[pos], "%m/%d/%Y %I:%M %p")
                charge[pos] = tmp1.isoformat()
            # different format for disposition date
            try:
                if charge[7] != 'N/A':
                    tmp1 = datetime.datetime.strptime(charge[7], "%m/%d/%Y")
                    charge[7] = tmp1.isoformat()
            except:
                #if not leave alone
                print("ERROR!: tried to convert time, failed with", charge[6])
            
            outcharges.append(charge) #charges from different arrests all included. 
            
    
    return outcharges   



def table_to_csv(tbl):
    output=[] #going to turn these into list of lists (rows) with td elements in rows
    if args.verbose >= 3: print(tbl)

    thead_tag = tbl.find("thead")
    
    if not thead_tag:  #Simple table no thead and no tbody
        for tr in tbl.find_all("tr"):
            line = []
            for td in tr.find_all("td"):
                line.append(td.get_text().strip())
                # not append sub_csv since these do not have subtables
            output.append(line) 
        if args.verbose >= 3:print("========")
        if args.verbose >= 3:print(output)
        return output
    
    # We do have a thead so more complicated 
    # this should never now get a nested table. 
    if thead_tag:
        ###head = thead_tag.find_all("th")
        heads = tbl.find_all("th")
        headers = []
        for h in heads:
            headers.append(h.get_text().strip())
        output.append(headers)
    #now do the body
    tbody = tbl.find("tbody")  
    for tr_tag in tbody.find_all("tr"):
        line = []
        for td_tag in tr_tag.find_all("td"): # return link if exists
            if td_tag.a: 
                if args.verbose >= 3:print("----")
                if args.verbose >= 3:print(td_tag)
                line.append(td_tag.a.get('href').strip())
            else:
                line.append(td_tag.get_text().strip())
        output.append(line)  
    if args.verbose >= 3:print("========")
    if args.verbose >= 3:print(output)
    
    return output
    
def convert2iso(indate):
    #print(indate)
    if re.search(r"(?i)/\d+/\d+ .*(AM|PM)", indate):
        tmp1 = datetime.datetime.strptime(indate, "%m/%d/%Y %I:%M %p")
        return tmp1.isoformat(sep=' ')
    elif re.search(r"(?i)/\d+/\d+", indate):
        tmp1 = datetime.datetime.strptime(indate, "%m/%d/%Y")
        return tmp1.isoformat(sep=' ')
    else:
        return indate

def mk_dictionary(list_of_lists):
    global date_string_today, date_string_file_today
    html2desc = {
        "Name Number":"Name_Number", 
        "Name":"Name", 
        "Status":"Status", 
        "Booking Date":"Booking_Date",
        "Booking Number":"Booking_Number",
        "Building":"Building", 
        "Area":"Area", 
        "Scheduled Release":"Scheduled_Release"
        }    
    if args.verbose >= 2: print(list_of_lists)
    output={}
    for pairs in list_of_lists:
        key = html2desc[pairs[0]]
        output[key] = pairs[1]
        if key in ["Booking_Date", "Scheduled_Release"]:
            output[key] = convert2iso(output[key])
    output["First_Seen"] = date_string_today
    output["Last_Seen"]  = date_string_today
    return output

"""    
def get_race_ccap(ccap_link):
    ccap_object = requests.get(ccap_link)
    if (int(ccap_object.status_code) == 200):  #we have the page 
        ccap_page = ccap_object.text
        print(ccap_page)
        soup = BeautifulSoup(ccap_page, 'html.parser')
        d_detail =     soup.find("div", class_="defendantDetail")
        race_node = d_detail.find("dl", class_="cell-3 s-cell-6 field").dd
        print(race_node)
        #race =     soup.select('div[class="defendantDetail"]').select('dl[class="cell-3 s-cell-6 field"').dd.get_text()
        birthday = soup.select('div[class="defendantDetail"]').select('dl[class="cell-3 s-cell-12 field"').dd.get_text()
    else: 
        race = "no_ccap"
    
    return race
"""

def get_booking_and_charges(name_id, page):
    name_list = [name_id,]
    soup = BeautifulSoup(page, 'html.parser')
    #print(soup.prettify())

    count = 0
    
    # because of nested tables look for tables with subtables and process both 
    # tables separately
    
    all_tables = soup.find_all("table")
    list_tables = []
    
    booking_info = []    
    for a_table in all_tables:
        csv_out = []

        if args.verbose >= 3:print("table numbers", len(all_tables))
        subtable = a_table.find("table")
        parent_names = [x.name for x in a_table.parents]
        if args.verbose >= 3:print("============")
        if args.verbose >= 3:print(parent_names)
        if args.verbose >= 3:print(a_table)
        
        if len(parent_names) == 0:  #subtable was extracted now has no parents
                                    #so ignore this version 
            continue
        elif subtable: #this has a subtable - extract both and combine
            subtable_node = a_table.table.extract()
            csv_parent = table_to_csv( a_table)
            csv_child = table_to_csv(subtable_node)
            #add table to subtable - 1 header and then data for the rest
            csv_out.append(["Name Number"]+csv_parent[0]+csv_child[0])  #this is a header - will be removed
            for i in range(1,len(csv_child)):
                csv_out.append([name_id]+csv_parent[1]+csv_child[i])
        else:  #this is a plain old table
            if count == 0:  # The table with the booking info
                if len(booking_info): 
                    print("ERROR: Dup Booking info one detail page", booking_info)
                    sys.exit("ERROR: Dup Booking info one detail page")
                booking_info = table_to_csv( a_table) 
            else:  # some other table don't lose it
                csv_out = table_to_csv( a_table)
                
        if csv_out: list_tables.append(csv_out)
        count += 1
        
    #turn key, value lists into dictionary enries and fix key names
    booking_meta_dict = mk_dictionary(booking_info)
    return booking_meta_dict, list_tables    



def add_person2db(db_cur, person_meta):
    person_meta[-2] = person_meta[-1]  # since this is a new listing set the first_seen date as current
                                       # This can be a first visit or a new update e.g. new status, new housing
    db_cur.execute('''INSERT INTO bookings  
                      ("Name_Number", "Name", "Status", "Booking_Date", "Booking_Number",
                       "Building", "Area", "Scheduled_Release", "First_Seen", "Last_Seen") 
                       VALUES (?,?,?,?,?,?,?,?,?,?)''', person_meta)
    return(db_cur)

def update_last_seen_db(db_cur, rowid, date_string_today):
    db_cur.execute('''UPDATE bookings SET Last_Seen = ? WHERE `rowid` = ?  ''',(date_string_today, rowid,))
    return(db_cur)

def save_page(filename, page):
    global date_string_file_today
    
    filename = "individuals/"+name_id+"_"+date_string_file_today+".html"
    with open(filename, "w") as fl:
        fl.write(page)
        
    
def merge_db_or_index_w_detail(base_row, detail_info):
    #this is called with either the index data or with db data as base
    #works on data from one person. 
    #base_row is a list and detail_info is a dictionary. 
    fields = ["Name_Number", "Name", "Status", "Booking_Date", "Booking_Number","Building", "Area", "Scheduled_Release", "First_Seen", "Last_Seen" ]
   
    output = []      #this is the best data we have
    if args.verbose >= 2: 
        print("Merging    base_row:", base_row)
        print("with detail_info:", detail_info)

    base_row_l = list(base_row)  # force it to list a db record would not be a list

    
    for i, field_nm in enumerate(fields):
        # if detail_info is present it is default.  
        # If not then uses base record (either dbase or minimal record)
        if detail_info and detail_info.get(field_nm):  #returns None if there is no such key
            output.append(detail_info[field_nm])  # so the default is to use the page info 
        else:
            output.append(base_row_l[i])  #if we cannot get it from the detail page use Database

    # check stuff from row 
        if (field_nm == "Name Number") and (base_row_l[i] != detail_info["Name Number"]):
            print("get_person_dict: Error! Person Number not match between detail page and database")
            output[i] = detail["Name_Number"]+" "+str(base_row_l)+"Person ERROR!!"
            
        elif (field_nm == "Name"): # do not want the "firstname lastname" Name from detail page, want "lastname, firstname" from index or database
            output[i] = base_row[i]  
            
        elif (field_nm == "First_Seen"):  #Always use database value of "First_Seen"
            output[i] = base_row_l[i]
        

    return  output

junk2 = """def get_status_from_secondary_page(p_page):
    html2desc = {
        "Name Number":"Name_Number", 
        "Name":"Name", 
        "Status":"Status", 
        "Booking Date":"Booking_Date",
        "Booking Number":"Booking_Number",
        "Building":"Building", 
        "Area":"Area", 
        "Scheduled Release":"Scheduled_Release"
        }

    detail = {}

    #now if we got the page from the web site,  parse the page returned 
    pt = BeautifulSoup(p_page, 'html.parser') # parse to get person tree
    s_div = pt.find("div", class_="col-lg-10 col-md-10 col-sm-12 col-xs-12")
    s_table = s_div.table
    for row in s_table.find_all("tr"):
        field1 = row.td
        field2 = field1.find_next_sibling("td")   
        
        descriptor_html = field1.get_text(" ", strip=True)
        descriptor = html2desc[descriptor_html] #change headings into what we want for database field names
        value = field2.get_text(" ", strip=True) 
        
        detail[descriptor] = value
    
    #Convert booking data to iso - this is coming from page so is never going to be iso 
    tmp1 = datetime.datetime.strptime(detail["Booking_Date"], "%m/%d/%Y %I:%M %p")
    detail["Booking_Date"] = tmp1.isoformat()
    
    if detail["Scheduled_Release"].count(r"/") == 2:
        tmp1 = datetime.datetime.strptime(detail["Scheduled_Release"], "%m/%d/%Y")
        detail["Scheduled_Release"] = tmp1.isoformat()
    
    return detail
"""

def get_person_dict(index_listing, db_cur):
#start with single listing and expand it by going to the details page
    global date_string_today, date_string_file_today
    if args.verbose >= 3: print(index_listing)
    index_info = {}
    link = index_listing[0]
    index_info["link"] = link
    name_id = link.split(r"/")[-1].strip()
    index_info["Name_Number"] = name_id
    index_info["Name"] = index_listing[1].strip()
    index_info["Status"] = index_listing[2].strip()
    index_info["Last_Seen"] = index_listing[3].strip()
    index_info["First_Seen"] = index_listing[3].strip() #Same
    minimal_row = [index_info["Name_Number"],index_info["Name"],index_info["Status"],"","","","","", index_info["First_Seen"],index_info["Last_Seen"]]
    detail_info = 0
    all_charges = []
    
    
    ###  Get the accumulating data for this person from Database
    try:
        db_cur.execute('''SELECT *, rowid FROM bookings WHERE `Name_Number` = ? ORDER BY `Last_Seen` DESC''',(name_id,))
        dbrow = db_cur.fetchone()  #this should be the most recent record from the database

    except:
        if args.verbose >=2: print(index_listing, "Unable to get expanded data from DB for this person")
        dbrow=False  #not in database
        rowid = 0

    if dbrow:
        rowid = dbrow[-1]    #capture the rowid and then strip it off 
        dbrow = dbrow[:-1]


#now grab the expansion page. Now doing for every page used to do it only if status changed
    p_page = ""
    person_page_object = False  #if there is a requests error the person_page_object will have a value
    try:
        person_page_object = requests.get("https://danesheriff.com"+link)
    except:
        print("in get_person_dict problem getting detail page:", link)
        time.sleep(20)
        try:  # give it one more shot
            person_page_object = requests.get("https://danesheriff.com"+link)
        except:
            print("ERRORx2 in get_person_dict bailing on: ", link)
 
    if person_page_object and (int(person_page_object.status_code) == 200):  #we have the page 
        p_page = person_page_object.text
        detail_info, charges = get_booking_and_charges(name_id, p_page)
        all_charges = fix_charges(name_id, charges) # 
        #detail_info = get_status_from_secondary_page(p_page)

###############################################
#       
# OK now we have three pieces or at least tried to get them. 
#       (Default line from index page, details page, database)
# dbrow is the record from the database 
# detail_info comes from the detail page 
#
####################################################


###################################################
#
#first get the data for the daily version with nothing from database. 2020-05-04
#
###################################################
    
    #in any case get the combination base and detail_info 
    web_data = merge_db_or_index_w_detail(minimal_row, detail_info)  
    

########################################################
#
#Now go through the effort to try to match with database 
#
########################################################


    if not dbrow  and not detail_info: #no db entry and nothing from detail page => add mostly empty record to database. 
        print("request for person from detail page did not succeed:", link,":", index_info["Name"])
        db_cur = add_person2db(db_cur, minimal_row)
        save_page("individuals/no_parse_"+name_id+"_"+date_string_file_today+".html", p_page)
        return db_cur, "No Database No detail page", minimal_row, [],[]
    #return "db and detail match, update db", best_data, all_charges, web_data

    elif dbrow and not detail_info: # if cannot parse the detail page -- at least update database Last_Seen 
        save_page("individuals/no_parse_"+name_id+"_"+date_string_file_today+".html", p_page)
        db_cur = update_last_seen_db(db_cur,rowid, date_string_today)
        return db_cur, "Has DB entry, no detail page", dbrow, [], minimal_row
    
    elif detail_info:  #either a new person to us or a person with db record and potentially new information from web page
        #in any case get the combination base and detail_info
        base_detail = (index_info, detail_info)
        if dbrow:  #check the database
            temp_db_row = list(dbrow)
            temp_db_row[-1] = date_string_today  #make so the lists can be compared update_last_seen
        else:  
            temp_db_row = minimal_row
            #print(
            rowid = 0
            
        best_data = merge_db_or_index_w_detail(temp_db_row, detail_info)
        #detail_info is dictionary
             #temp_db_row was just created from index page info i.e. minimal_row
        
        ##########
        #  if there is info from detail page figure out if anything is new
        #  if new info write a new record 
        ##########
        
        #print("comparing merged", best_data)
        #print("with db     row ", temp_db_row)
        if best_data == temp_db_row and rowid: #nothing new so just update db record if there is a db record i.e. rowid
            db_cur = update_last_seen_db(db_cur,rowid, date_string_today)
            #print("return from best_data == temp_db_row", best_data, all_charges)
            return db_cur, "db and detail match, update db", best_data, all_charges, web_data
        
        else:
            db_cur = add_person2db(db_cur, best_data)  #add new record to database
            save_page("individuals/"+name_id+"_"+date_string_file_today+".html", p_page) #add to our collection detail pages
            #print("return from else", best_data, all_charges)
            return db_cur, "person has changes", best_data, all_charges, web_data


def get_people(soup, date_string_today): #go through the index page and pull out the individuals
    global args
    isodatetime = date_string_today
    inmate_table1 = soup.find(id="tblInmates")
    inmate_table = inmate_table1.find("tbody")
    ###print(inmate_table)
    people = []
    for row in inmate_table.find_all("tr"):
        url_str = row.a['href']
     
        row_list=[]
        for field in row.find_all("td"):
            #print(type(field), field)
            row_list.append(field.get_text(" ", strip=True))
        
        row_list[0] = url_str
        row_list.append(isodatetime)
        people.append(row_list)
        if args.verbose >= 3: print("row_list", row_list)
        if args.verbose >= 3: print("now people", people)
    return people

  

#
def write_people_meta(people):
    with open(args.outfile, 'w', newline='') as csvfile:
        output_writer = csv.writer(csvfile, delimiter='\t',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if args.verbose >= 3: print(people)
        count = 0
        for person in people:
            if args.verbose >= 3: print("write_people", person)
            output_writer.writerow(person)
            count +=1
        print("wrote",count,"records to", args.outfile)
 
def write_new_charges(db_cur, charges):
###  Writes out the charges to a file, and put the new ones in 
    
    with open(args.outcharges, 'w', newline='') as csvfile:
        output_writer = csv.writer(csvfile, delimiter='\t',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if args.verbose >= 3: print(charges)
        count = 0

        for charge in charges:
            
            try:
                db_cur.execute('''SELECT *, rowid FROM charges 
                                        WHERE `Name_Number` = ?
                                        AND `Date` = ?
                                        AND `Agency` = ?
                                        AND `Arrest_Number` = ?
                                        AND `Agency_Case_Number` = ?
                                        AND `Offense` = ?
                                        AND `DateTime` = ?
                                        AND `Disposition_Date` = ?
                                        AND `Court_Case_Number` = ?
                                        AND `Entry_Code` = ?''', tuple(charge))
                                                                  
                dbrow = db_cur.fetchone()
                                                
            except Exception as e:
                if args.verbose >= 3:  
                    print(e)
                    print("Error in searching for ",charge)
                sys.exit("Lost Connection to database")
                
                
            if dbrow:
                #on the first of the month print out everything
                date, time = args.outcharges.split("T")
                year, month, day = date.split("-")
                if day == "01":
                    output_writer.writerow(charge)
                    count +=1                    
                continue
            else: #not in database so add new info to both csv file and database
                
                #first write to the csv file
                if args.verbose >= 3: print("write_csv_charge", charge)
                output_writer.writerow(charge)
                count +=1                
                
                #now add to database
                #print(dbrow)
                #print(charge)
                db_cur.execute('''INSERT INTO charges(`Name_Number`, `Date`, `Agency`, `Arrest_Number`, `Agency_Case_Number`, `Offense`, `DateTime`, `Disposition_Date`, `Court_Case_Number`, `Entry_Code`) 
                                      VALUES (?,?,?,?,?,?,?,?,?,?)''', tuple(charge)) 
                
    print("wrote",count,"new counts to", args.outcharges)
        

    return(db_cur)


def get_db_cursor():
    dbase = sqlite3.connect('all_jail.db')
    dbcur = dbase.cursor()
    #    if not(databases.find("bookings")):
    
    b_db_exists =0
    c_db_exists =0
    for row in dbcur.execute("SELECT name FROM sqlite_master WHERE type='table'; "):
        if args.verbose >=3: print(row)
        if row[0] == "bookings" : b_db_exists = 1
        if row[0] == "charges" : c_db_exists = 1
            
    if not(b_db_exists):
        dbcur.execute('''CREATE TABLE bookings
                             ("Name_Number" text, "Name" text, "Status" text, "Booking_Date" text, "Booking_Number" text,
                              "Building" text, "Area" text, "Scheduled_Release" text, "First_Seen" text, "Last_Seen" text)''')
        #"Name_Number", "Name", "Status", "Booking_Date", "Booking_Number","Building", "Area", "Scheduled_Release", "First_Seen", "Last_Seen"        
        dbase.commit()
        
    if not(c_db_exists):
        dbcur.execute('''CREATE TABLE charges
                             ("Name_Number" text, "Date" text,"Agency" text,"Arrest_Number" text,"Agency_Case_Number" text,
                              "Offense" text,"DateTime" text,"Disposition_Date" text,"Court_Case_Number" text,"Entry_Code" text)''')
        # headers = ['Name Number','Date', 'Agency', 'Arrest Number', 'Agency Case Number', 'Offense', 'Date/Time', 'Disposition Date', 'Court Case Number', 'Entry Code']
        dbase.commit()

    return dbase, dbcur

################################################################################
################################################################################
##                                   Main
################################################################################
################################################################################


#################################
## Start by parsing the options
###############################
starttime = datetime.datetime.today()

parser = argparse.ArgumentParser(description='scrape the jail data')

parser.add_argument('-i','--inurl', dest='inurl', default="https://danesheriff.com/inmates",
#                   required=True,
                   help='Input file - should be a CSV file with arguments in first row')

parser.add_argument('-o','--outfile', dest='outfile', type=str, default='placeholder_file',
                   help='Location and name of outfile')

parser.add_argument("-v", "--verbosity", dest='verbose', type=int, default=1,
                    help="increase output verbosity")

args = parser.parse_args()
if args.verbose >= 3: print("Initial args:",args)

server_now = datetime.server_now = datetime.datetime.now(tz=dateutil.tz.tzlocal())
mad_now = server_now.astimezone(dateutil.tz.gettz("America/Chicago"))

date_string_file_today = mad_now.strftime("%Y-%m-%dT%H-%M")
date_string_today = mad_now.strftime("%Y-%m-%d %H:%M") # we want these the same time but here there is a : and no T in it for excel


if args.outfile == "placeholder_file":
    args.outfile = os.path.join("daily","all_in_jail"+date_string_file_today+".csv")
    args.index_fname = os.path.join("daily","index"+date_string_file_today+".html")
    
    args.outcharges = os.path.join("daily","charges"+date_string_file_today+".csv")
    #args.outfile=os.path.join('processed',"people_in_jail"+"date")
print(sys.argv[0], "Reworked args:",args)

### other setup


#print  'options', options


#########################################
## done args.  now for processing
#########################################33

page_object = False
try:
    page_object = requests.get(args.inurl)  # get the page with all the people - the index page
except:
    time.sleep(20)
    try:
        page_object = requests.get(args.inurl)  # if at first you don't succeed, try one time more
    except:    
        print("ERROR: Request did not succeed from index page URL:", args.inurl, "page_object:", page_object)


    
if page_object and page_object.status_code == 200:
    page = page_object.text
    with open(args.index_fname, "w") as fl_index:
        fl_index.write(page)
else:
    print("Request did not succeed from URL:", args.inurl)
#print(page)



dbase, db_cur = get_db_cursor() #this database holds the data of previous runs

#Parse the html in the 'page' variable, and store it in Beautiful Soup format
soup = BeautifulSoup(page, 'html.parser')

people = get_people(soup, date_string_today)  # this is the listing of people from index not individual pages
if args.verbose >= 1: print("len of people",len(people))


people_meta = []
all_charges=[]
web_info = []
count = 0
### for person in people[0:5]:  #test with fewer people
for person in people:
    name_url = person[0]
    name_id = name_url.split("/")[-1]
    
    #main call to all the rest. get_person_dict does the database updates NOW (2020-05-04) write the daily census
    db_cur, action, best_data, new_charges, web_data = get_person_dict(person, db_cur) #this compares db and detail page and does updates
#    if new_charges: 
#        ccap_link = new_charges[-1][-2] 
#        race = get_race_ccap(ccap_link)
    race = "?"
    all_charges = all_charges + new_charges
    people_meta.append(best_data) 
    web_info.append(web_data)
    #all_charges_dict[name_id]=bookings[name_id]  # want to transfer over the date and everthing else
    count += 1
    if count%50 == 0: 
        #dbase.commit()
        nowtime = datetime.datetime.today()
        sofar = nowtime - starttime
        if args.verbose >= 1: print("just expanded data:", "{:30}".format(person[1]), "record #: ", count, "\t", round(sofar.total_seconds()/60.0, 1), " min") 
    dbase.commit()     
    
if args.verbose >= 2: print("len of people_meta",len(people_meta))    
write_people_meta(web_info)
#write_people_meta(people_meta)
if args.verbose >= 1: 
    print("number of new charges:", len(all_charges))
write_new_charges(db_cur, all_charges)
dbase.commit()

endtime = datetime.datetime.today()

timedif = endtime - starttime
difmin = (timedif.total_seconds())/60.0
if args.verbose >= 1: 
    print("Started:",starttime.isoformat(), "\nfinished:", endtime.isoformat(), "\ntook:",difmin, "min" )
