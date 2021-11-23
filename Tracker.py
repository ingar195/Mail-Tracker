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
        try:
            eta = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["estimatedTimeOfArrival"]
        except:
            eta = ""

        combined = header + ", " + body + ", " + eta
        print(combined)
        return combined
    except:
        return "Tracking id invalid"


def track(jsonFile):
    logging.debug(f"track({jsonFile}):")
    currentState = readConfig(jsonFile)

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


def CheckStatus():
    pass

def ReadFile(fileName):
    logging.debug("ReadFile")
    with open(fileName) as f:
        fileLines = f.readline()
    logging.debug(f"Return: {fileLines}")
    return fileLines


def readConfig(jsonFile):
    logging.debug("readConfig()")
    with open(jsonFile, "r") as jf:
        return json.load(jf)


def writeconfig(jsonFile, data):
    with open(jsonFile, "w+") as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))


def Notify(Name, CurrentState):
    pb.push_note(Name, CurrentState)


def Menu():
    pass


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("Tracker.log"),
        logging.StreamHandler()
    ])

pb = Pushbullet(ReadFile("pushbulletapikey"))
print(os.path.isfile("packages.json"))
track("packages.json")
