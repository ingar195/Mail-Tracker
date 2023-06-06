from flask import Flask, request, jsonify, render_template
from pushbullet import Pushbullet
import requests
import argparse
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


def posten(tracking_number="70730259304981356", lang="en"):
    lang_list = ["en", "no"]
    if lang not in lang_list:
        logging.error(f"Language {lang} not supported, default to en")
        lang = "en"

    try:
        data = get_data(f"https://sporing.bring.no/tracking/api/fetch?query={tracking_number}&lang={lang}")

        package_set = data["consignmentSet"][0]["packageSet"][0]
        eta = package_set["dateOfEstimatedDelivery"]
        sender = package_set["senderName"]

        event = data["consignmentSet"][0]["packageSet"][0]["eventSet"][0]
        status = event["status"]
        last_event = event["description"]
        date = event["displayDate"]
        time = event["displayTime"]
        logging.debug(eta)
        logging.debug(sender)
        logging.debug(status)
        logging.debug(last_event)
        logging.debug(date)
        logging.debug(time)

        return {"eta", eta, "status", status, "last_event", last_event, "date", date, "time", time}
    except Exception as e:
        logging.error(e)
        return False



def postnord(tracking_number):
    return
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
        return False


def get_provider(tracking_number):
    function_list = [posten, postnord]
    for function in function_list:
        ret = function(tracking_number)
        if ret:
            return function.__name__
    logging.error("No provider found")


def track(parcel_file, config_file):

    packages = read_config(parcel_file)
    
    for package in packages:

        tracking_number = packages[package]["tracking_number"]
        logging.debug(tracking_number)

        if packages[package].get("carrier"):
            carrier = packages[package]["carrier"]
            logging.debug(carrier)
        else:
            carrier = get_provider(tracking_number)
            if carrier:
                packages[package]["carrier"] = carrier
                write_config(packages, parcel_file)
            logging.debug(carrier)
            input("Press enter to continue")

        if carrier == "posten":
            tracking_data = posten(tracking_number)

        elif carrier == "postnord":
            tracking_data = postnord(tracking_number)
        logging.debug(tracking_data)


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


def read_config(file_name):
    logging.debug("readConfig()")
    with open(file_name, "r") as jf:
        data = json.load(jf)
    # logging.debug(f"Return: {data}")
    return data


def write_config(data, json_file):
    logging.debug(f"write config({data}):")
    with open(json_file, "w+") as f:
        f.write(json.dumps(data, indent=4))


def notify(name, current_state):
    logging.debug(f"Notify({name}, {current_state}):")
    # logging.INFO(f"Alert {Name}: {CurrentState}")
    pb.push_note(name, current_state)


def get_all_parcels():
    logging.debug("get_all_parcels()")
    parcels = read_config("packages.json")
    parcel_list = []
    for parcel in parcels:
        parcel_list.append(parcel)
    return parcel_list


app = Flask(__name__)
@app.route('/api/tracking/<tracking_number>', methods=['GET'])
def api_track(tracking_number):
    return jsonify(["a", "b", "c"])


@app.route('/api/parcels/<filter_var>', methods=['GET'])
def parcels_filter(filter_var):
    if filter_var == "all":
        ret = get_all_parcels()
        ret = {
            "Zalando": {
                "tracking_number": "1234567890",
                "carrier": "posten",
                "ETA": "2020-01-02",
                "shipment_state": "In transit",
                "last_update": "2020-01-02"
            },
            "DHL": {
                "tracking_number": "asdfi",
                "carrier": "DHL",
                "ETA": "2020-01-0",
                "shipment_state": "In transit",
                "last_update": "2020-01-01"
            },
        }
        
    return jsonify(ret)

@app.route('/api/carrier', methods=['GET'])
def carrier():
    return jsonify(["DHL", "Posten", "Postnord"])

@app.route('/api/add', methods=['POST'])
def add():
    return jsonify(["a", "b", "c"])



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def pages():
    return render_template('test.html')


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Track packages")
    parser.add_argument("-c", "--config", help="config file", default="config.json", required=False)
    parser.add_argument("-pa", "--parcel", help="parcel file", default="packages.json", required=False)
    parser.add_argument("-l", "--log", help="log file", default="Tracker.log", required=False)
    parser.add_argument("-p", "--port", help="port", default="1234", required=False)
    args = parser.parse_args()

    log_file = args.log
    parcel_file = args.parcel
    config_file = args.config
    web_port = args.port


    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%d-%m-%Y:%H:%M:%S',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ])

    # pb = Pushbullet(read_file("pushbulletapikey"))
    app.run(host='0.0.0.0', port=web_port, debug=True)
    
    # track(parcel_file, config_file)





