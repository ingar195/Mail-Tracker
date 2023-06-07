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
        shipment_state = event["status"]
        last_update = event["description"]
        date = event["displayDate"]
        time = event["displayTime"]

        if not eta:
            eta = "Unknown"

        logging.debug(eta)
        logging.debug(sender)
        logging.debug(shipment_state)
        logging.debug(last_update)
        logging.debug(date)
        logging.debug(time)

        return {"tracking_number": tracking_number, "eta": eta, "shipment_state": shipment_state, "last_update": last_update, "date": date, "time": time}
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


def track(tracking_number, carrier=None):
    logging.debug("track")

    if  carrier != None or carrier == "sample":
        carrier = get_provider(tracking_number)
        logging.debug(carrier)
    else:
        logging.error("Carrier not found")
        return False

    if carrier == "posten":
        tmp_json = posten(tracking_number)
    elif carrier == "postnord":
        tmp_json = postnord(tracking_number)
    else:
        return False
    
    return tmp_json

def update_all(parcel_file="packages.json", config_file="config.json"):

    packages = read_config(parcel_file)

    ret_data = {}

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

        else:
            return False

        logging.debug(tracking_data)
        if tracking_data["shipment_state"] != packages[package]["shipment_state"]:
            logging.info(f"Package {package} has changed status from {packages[package]['shipment_state']} to {tracking_data['shipment_state']}")
            ret_data[package] = tracking_data
            # Update package state
            tracking_data["carrier"] = carrier
            packages[package] = tracking_data
            logging.debug(json.dumps(packages, indent=4))   
            write_config(packages, "packages.json")

        else:
            logging.info(f"Package {package} has not changed status")

    return ret_data


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
    pb = Pushbullet(read_config("pushbulletapikey"))

    # logging.INFO(f"Alert {Name}: {CurrentState}")
    pb.push_note(name, current_state)


def get_all_parcels():
    logging.debug("get_all_parcels()")
    update_all()
    parcels = read_config("packages.json")
    logging.debug(parcels)
    return parcels


app = Flask(__name__)


@app.route('/api/tracking/<tracking_number>', methods=['GET'])
def api_track(tracking_number):
    return jsonify(["a", "b", "c"])


@app.route('/api/parcels/<filter_var>', methods=['GET'])
def parcels_filter(filter_var):
    if filter_var == "all":
        ret = get_all_parcels()

    return jsonify(ret)


@app.route('/api/carrier', methods=['GET'])
def get_carrier():
    return jsonify(["posten"])


@app.route('/api/<add_rm>/<name>', methods=['POST', 'GET'])
def add(name, add_rm):
    logging.debug(f"add({name}, {add_rm}):")
    if add_rm == "add":
        data = request.get_json()
        carrier = data["carrier"]
        parcels = get_all_parcels()
        tmp_json = track(data["tracking_number"], carrier)
        logging.debug(tmp_json)

        if tmp_json:
            logging.debug("Package tracked")
            tmp_json["carrier"] = carrier
            parcels[name] = tmp_json
            logging.debug(json.dumps(parcels, indent=4))   
            write_config(parcels, "packages.json")
            return jsonify({"status": "ok", "message": "Package added"})
        
        else:
            logging.error("Could not track package")
            return jsonify({"status": "error", "message": "Could not track package"})

    
    elif add_rm == "rm":
        parcels = get_all_parcels()
        parcels.pop(name)
        write_config(parcels, "packages.json")
        return jsonify({"status": "ok", "message": "Package removed"})


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

    app.run(host='0.0.0.0', port=web_port, debug=True)

    # track(parcel_file, config_file)
