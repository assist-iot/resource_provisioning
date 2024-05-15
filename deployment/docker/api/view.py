from flask import Flask, flash, redirect, render_template, jsonify, request
import os
import main
import re

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

### Common Endpoints ###

@app.route('/version', methods=['GET'])
def version():
    resp = jsonify(main.version())
    resp.status_code = 200
    return resp

@app.route('/v1/health', methods=['GET'])
def health():
    health_status = main.health()
    if health_status:
        resp = jsonify(status="healthy")
        resp.status_code = 200
    else:
        resp = jsonify(status="unhealthy")
        resp.status_code = 503
    return resp

@app.route('/v1/api-export', methods=['GET'])
def apiexport():
    resp = jsonify(main.apiexport())
    resp.status_code = 200
    return resp

### API ###
    
@app.route('/v1/enablers', methods=['GET', 'POST'])
def enablers():
    if request.method == 'GET':
        resp = jsonify(main.enablers())
        resp.status_code = 200
        return resp
    elif request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if not(content_type == 'application/json'):
            resp = jsonify('Content-Type not supported!')
            resp.status_code = 406
            return resp
        string = main.enablerspost(request.json)
        resp = jsonify(string)
        if string == "Enablers managed updates sucessfully": resp.status_code = 200
        else: resp.status_code = 400
        return resp

@app.route('/v1/addEnablers', methods=['GET'])
def addEnablers():
    return jsonify(main.addEnablers())

@app.route('/v1/deleteData', methods=['POST'])
def deleteData():
    return jsonify(main.deleteData())

### TM ###

@app.route('/v1/train', methods=['GET'])
def train():
    resp = jsonify(main.train())
    resp.status_code = 200
    return resp

@app.route('/v1/train-values', methods=['GET', 'POST'])
def train_values():
    if request.method == 'GET':
        resp = jsonify(main.trainvalues())
        resp.status_code = 200
        return resp
    else:
        content_type = request.headers.get('Content-Type')
        if not(content_type == 'application/json'):
            resp = jsonify('Content-Type not supported!')
            resp.status_code = 406
            return resp
        string = main.trainvaluespost(request.json)
        resp = jsonify(string)
        if string == "Train values changed": resp.status_code = 200
        else: resp.status_code = 400
        return resp

### IM ###

@app.route('/v1/inference', methods=['GET'])
def inference():
    resp = jsonify(main.inference())
    resp.status_code = 200 
    return resp

### MAIN ###

if __name__ == "__main__":
    main.createTables()
    main.addEnablers()
    port = int(os.environ.get('API_PORT'))
    app.run(debug=True, host='0.0.0.0', port=port)