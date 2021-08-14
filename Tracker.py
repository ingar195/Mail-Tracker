import requests
from pushbullet import Pushbullet
import sqlite3
import logging
import time


def SqlCommand(sql_command):
    logging.debug("SqlCommand")
    try:
        logging.debug(f"Sql command = {sql_command}")
        (cursor.execute(sql_command))
        returnVar = cursor.fetchall()

    except:
        logging.error(f"sqlCommand failed to execute: {sql_command}")
        returnVar = "none"
    connection.commit()
    return returnVar


def InitDB():
    logging.debug("InitDB")
    # Check if table exists
    SqlCommand("""
    CREATE TABLE IF NOT EXISTS Mail ( 
    itemnumber INTEGER PRIMARY KEY,
    Name text,
    Provider text, 
    TrackingNumber text NOT NULL,
    CurrentState text);""")


def AppendDB(Name, Provider, TrackingNumber, CurrentState):
    logging.debug("AppendDB")
    serachReturn = SearchAndCheck(TrackingNumber, False)
    if TrackingNumber != serachReturn[3]:
        SqlCommand("""INSERT INTO Mail 
        (itemnumber, Name, Provider, 
        TrackingNumber, CurrentState) 
        VALUES (null,"{}","{}","{}","{}");""".format(Name, Provider, TrackingNumber, CurrentState))
    else:
        logging.error(f"Tracking number {TrackingNumber} already in list")


def Update(TrackingNumber, CurrentState):
    logging.debug("update")
    SqlCommand("UPDATE Mail SET CurrentState = '{}' WHERE TrackingNumber = '{}';".format(
        CurrentState, TrackingNumber))


def SearchAndCheck(query, check):
    logging.debug("SearchAndCheck")
    if check == True:
        logging.debug("True")
    else:
        logging.debug("False")

    rows = SqlCommand("SELECT * FROM Mail")
    # TODO use sql search for trackingnumber
    #
    logging.debug("len = {}".format(len(rows)))
    row = None
    for row in rows:
        itemnumber = row[0]
        Name = row[1]
        Provider = row[2]
        TrackingNumber = row[3]
        CurrentState = row[4]
        if check == True:
            logging.debug("Check = {}".format(check))
            Trace(Name, Provider, TrackingNumber, CurrentState)
        if TrackingNumber == query:
            logging.debug(f"Itemnumber: {itemnumber}, Name: {Name}, Provider: {Provider}, Tracking number: {TrackingNumber}, Current state: {CurrentState}")
    logging.debug("Search return = {}".format(row))
    return row


def Trace(Name, Provider, TrackingNumber, CurrentState):
    logging.debug("Trace")
    logging.debug(
        f"Name {Name}, Provider {Provider}, TrackingNumber {TrackingNumber}, CurrentState {CurrentState}")

    if Provider.lower() == "posten":
        logging.debug(f"Provider = {Provider}")
        checkedState = Posten(TrackingNumber)
    elif Provider.lower() == "postnord":
        logging.debug(f"Provider = {Provider}")
        checkedState = Postnord(TrackingNumber)
    else:
        checkedState = "not supported provider"
        logging.error(f"Provider not supported: {Provider}")

    logging.debug(f"checkedState = {checkedState}")
    if checkedState != "not supported provider":
        logging.debug("checkedState != not supported provider")
        if checkedState != CurrentState:
            Notify(Name, checkedState)
            Update(TrackingNumber, checkedState)
        pass


def Delete(TrackingNumber):
    logging.debug("Delete")
    SqlCommand(
        "DELETE FROM Mail WHERE TrackingNumber = {};".format(TrackingNumber))


def GetData(url):
    logging.debug("GetData")
    try:
        response = requests.get(url)
        data = response.json()
        return data

    except Exception as e:
        print("No connection to server {}".format(url))
        return None


def Posten(trackingNumber):
    logging.debug("Posten")
    data = GetData(
        f"https://sporing.posten.no/tracking/api/fetch/{trackingNumber}")
    try:
        currentEvent = data["consignmentSet"][0]["packageSet"][0]["eventSet"][0]["description"]
        print(currentEvent)
        return currentEvent
    except:
        return "Tracking id invalid"


def Postnord(trackingNumber):
    logging.debug("Postnord")
    postnordAPIKey = ReadFile("postnordapikey")
    data = GetData(
        f"https://api2.postnord.com/rest/shipment/v5/trackandtrace/findByIdentifier.json?apikey={postnordAPIKey}&id={trackingNumber}&locale=no")
    try:
        header = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["header"]
        body = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["body"]
        combined = header + ", " + body
        print(combined)
        return combined
    except:
        return "Tracking id invalid"


def ReadFile(fileName):
    logging.debug("ReadFile")
    with open(fileName) as f:
        fileLines = f.readline()
    logging.debug(f"Return: {fileLines}")
    return fileLines


def Notify(Name, CurrentState):
    pb.push_note(Name, CurrentState)


def Menu():
    pass


logging.basicConfig(level=logging.DEBUG)

pb = Pushbullet(ReadFile("pushbulletapikey"))
DBFile = "Mail.db"
connection = sqlite3.connect(DBFile)
cursor = connection.cursor()
InitDB()
while True:
    SearchAndCheck("", True)
    time.sleep(5*60)
