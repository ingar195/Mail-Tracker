import requests
from pushbullet import Pushbullet
import logging
import json
import os


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
    data = GetData(f"https://sporing.posten.no/tracking/api/fetch/{trackingNumber}")
    try:
        currentEvent = data["consignmentSet"][0]["packageSet"][0]["eventSet"][0]["description"]
        eta = ""
        return currentEvent, eta
    except:
        return "Tracking id invalid"


def Postnord(trackingNumber):
    logging.debug("Postnord")
    postnordAPIKey = ReadFile("postnordapikey")
    data = GetData(f"https://api2.postnord.com/rest/shipment/v5/trackandtrace/findByIdentifier.json?apikey={postnordAPIKey}&id={trackingNumber}&locale=no")
    try:
        header = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["header"]
        body = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["body"]
        try:
            eta = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["estimatedTimeOfArrival"]
        except:
            eta = ""

        combined = header + ", " + body
        logging.debug(combined)
        return combined, eta
    except:
        return "Tracking id invalid"


def track():
    logging.debug(f"track():")
    currentState = readConfig()

    for package in currentState:
        logging.debug(package)
        transporter = currentState[package]["Transporter"].lower()
        trackingNumber = currentState[package]["TrackingNumber"]

        if transporter == "posten":
            CheckStatus(currentState, package, Posten(trackingNumber))
        elif transporter == "postnord":
            CheckStatus(currentState, package, Postnord(trackingNumber))
        else:
            logging.error(f"{transporter} not supported")


def CheckStatus(currentState, package, trackingData):
    logging.debug(f"CheckStatus({currentState}, {package}, {trackingData}):")

    if trackingData != "Tracking id invalid":
        checkedState = trackingData[0]
        checkedEta = trackingData[1]
        lastUpdate = currentState[package]["LastUpdate"]
        eta = currentState[package]["ETA"]
        
        logging.info(f"{package}: last state: {checkedState}")

        if eta != checkedEta:
            Notify(package, f"ETA changed form {eta} to {checkedEta}")
            currentState[package]["ETA"] = checkedEta
        if lastUpdate != checkedState:
            Notify(package, f"Last update changed form {lastUpdate} to {checkedState}")
            currentState[package]["LastUpdate"] = checkedState
        writeconfig(currentState)
    else:
        logging.error("No data from provider")


def ReadFile(fileName):
    logging.debug("ReadFile")
    with open(fileName) as f:
        fileLines = f.readline()
    logging.debug(f"Return: {fileLines}")
    return fileLines


def readConfig():
    logging.debug("readConfig()")
    with open(jsonFile, "r") as jf:
        return json.load(jf)


def writeconfig(data):
    with open(jsonFile, "w+") as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))


def Notify(Name, CurrentState):
    pb.push_note(Name, CurrentState)


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("Tracker.log"),
        logging.StreamHandler()
    ])


jsonFile = "packages.json"
pb = Pushbullet(ReadFile("pushbulletapikey"))
if os.path.isfile(jsonFile):
    track()
else:
    logging.error(f"Could not find: {jsonFile}")
