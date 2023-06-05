import requests
from pushbullet import Pushbullet
import logging
import json
import os


def get_data(url):
    logging.debug("get_data")
    try:
        response = requests.get(url)
        data = response.json()
        return data

    except Exception as e:
        print("No connection to server {}".format(url))
        return None


def posten(tracking_number):
    logging.debug("Posten")
    data = get_data(f"https://sporing.posten.no/tracking/api/fetch/{tracking_number}")
    try:
        current_event = data["consignmentSet"][0]["packageSet"][0]["eventSet"][0]["description"]
        eta = ""
        return current_event, eta
    except:
        return "Tracking id invalid"


def postnord(tracking_number):
    logging.debug("postnord")
    postnord_api_key = read_file("postnordapikey")
    data = get_data(f"https://api2.postnord.com/rest/shipment/v5/trackandtrace/findByIdentifier.json?apikey={postnord_api_key}&id={tracking_number}&locale=no")
    try:
        header = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["header"]
        try:
            eta = data["TrackingInformationResponse"]["shipments"][0]["statusText"]["estimatedTimeOfArrival"]
        except:
            eta = ""

        logging.debug(header)
        return header, eta
    except:
        return "Tracking id invalid"


def track():
    logging.debug(f"track():")
    current_state = read_config()

    for package in current_state:
        logging.debug(package)
        transporter = current_state[package]["Transporter"].lower()
        tracking_number = current_state[package]["TrackingNumber"]

        if transporter == "posten":
            check_status(current_state, package, posten(tracking_number))
        elif transporter == "postnord":
            check_status(current_state, package, postnord(tracking_number))
        else:
            logging.error(f"{transporter} not supported")


def check_status(current_state, package, tracking_data):
    logging.debug(f"Check status(c{current_state}, p{package}, data{tracking_data}):")

    if tracking_data != "Tracking id invalid":
        checked_state = tracking_data[0]
        checked_eta = tracking_data[1]
        last_update = current_state[package]["LastUpdate"]
        eta = current_state[package]["ETA"]
        
        logging.info(f"{package}: last state: {checked_state}")

        if eta != checked_eta:
            notify(package, f"ETA changed form {eta} to {checked_eta}")
            current_state[package]["ETA"] = checked_eta
        if last_update != checked_state:
            notify(package, f"Last update changed form {last_update} to {checked_state}")
            current_state[package]["LastUpdate"] = checked_state
        write_config(current_state)
    else:
        logging.error("No data from provider")


def read_file(file_name):
    logging.debug("ReadFile")
    with open(file_name) as f:
        file_lines = f.readline()
    logging.debug(f"Return: {file_lines}")
    return file_lines


def read_config():
    logging.debug("readConfig()")
    with open(json_file, "r") as jf:
        return json.load(jf)


def write_config(data):
    logging.debug(f"writeconfig({data}):")
    with open(json_file, "w+") as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))


def notify(name, current_state):
    logging.debug(f"Notify({name}, {current_state}):")
    # logging.INFO(f"Allert {Name}: {CurrentState}")
    pb.push_note(name, current_state)


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("Tracker.log"),
        logging.StreamHandler()
    ])


json_file = "packages.json"
pb = Pushbullet(read_file("pushbulletapikey"))
if os.path.isfile(json_file):
    track()
else:
    logging.error(f"Could not find: {json_file}")
