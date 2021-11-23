import requests
from pushbullet import Pushbullet
import logging
import time




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
        try:
            eta = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["estimatedTimeOfArrival"]
        except:
            eta = ""

        combined = header + ", " + body + ", " + eta
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


while True:
    time.sleep(5*60)
