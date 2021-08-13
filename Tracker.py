import requests
from colorama import Fore, init
from pushbullet import Pushbullet
import time
from datetime import datetime


def getData(url):
    try:
        response = requests.get(url)
        data = response.json()
        return data

    except Exception as e:
        print("No connection to server {}".format(url))
        return None


def posten(url):
    data = getData(url)
    if data is not None:
        lastEvent = data["consignmentSet"][0]["packageSet"][0]["eventSet"][0]["description"]
        print(Fore.GREEN + lastEvent)
        return lastEvent
    else:
        return "Error"


def ReadFile(fileName, lines):
    with open(fileName) as f:
        if lines == True:
            fileLines = f.readlines()
        else:
            fileLines = f.readline()
    return fileLines


init(autoreset=True)

pb = Pushbullet(ReadFile("pushbulletapikey", False))

while True:
    lastEvent = posten("https://sporing.posten.no/tracking/api/fetch/")

    now = datetime.now()
    currentTime = now.strftime("%H:%M:%S")
    print(currentTime)

    if lastEvent != "Sendingen er lastet opp for utkjøring.":
        pb.push_note("Package update", lastEvent)

    time.sleep(60)
