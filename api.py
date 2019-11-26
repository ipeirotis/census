import json
import os

from flask import Flask, Response, jsonify, request

from census import GeoLocator, Census

config = {
    "CENSUS_KEY": os.environ['CENSUS_KEY'],
    "GOOGLE_MAPS_KEY": os.environ['GOOGLE_MAPS_KEY'],
}

geolocator = GeoLocator(config["GOOGLE_MAPS_KEY"])
census = Census(config["CENSUS_KEY"], config["GOOGLE_MAPS_KEY"])

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/census_block/", methods=["GET"])
def get_census_block():
    query_parameters = request.args
    try:
        address = query_parameters.get('address')
        service = query_parameters.get('service')
    except:
        return jsonify({"status": "error"})


    if service:
        response = geolocator.get_census_block(address, service=service)
    else:
        response = geolocator.get_census_block(address)

    return jsonify(response)


@app.route("/details_block_level/", methods=["GET"])
def details_block_level():
    query_parameters = request.args
    try:
        address = query_parameters.get('address')
    except:
        return jsonify({"status": "error"})
    
    response = census.details_block_level(address)
    return jsonify(response)    
    


@app.route("/details_tract_level/", methods=["GET"])
def details_tract_level():
    query_parameters = request.args
    try:
        address = query_parameters.get('address')
    except:
        return jsonify({"status": "error"})
    
    response = census.details_tract_level(address)
    return jsonify(response)    
        


if __name__ == '__main__':
    print("Starting")
    app.run(host='0.0.0.0', port=5000, debug=True)
    print("Ended")
