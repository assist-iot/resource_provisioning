from flask import Flask, jsonify, request
import os
import re
import main

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    resp = jsonify(status="healthy")
    resp.status_code = 200
    return resp

@app.route('/train', methods=['GET'])
def train():
    history = int(os.environ['HISTORY_DATA'])
    future = int(os.environ['FUTURE_DATA'])
    return main.train(history,future)

@app.route('/train-values', methods=['GET', 'POST'])
def train_values():
    if request.method == 'GET':
        headers = ['History_data','Future_data']
        data = []
        data.append(os.environ['HISTORY_DATA'])
        data.append(os.environ['FUTURE_DATA'])
        return jsonify(dict(zip(headers,data)))
    else:
        content_type = request.headers.get('Content-Type')
        if not(content_type == 'application/json'):
            return 'Content-Type not supported!'
        data = dict(request.json)
        if not('History_data' in data and 'Future_data' in data):
            return 'Error in json body'
        if not(re.search('^[0-9]*$', data['History_data']) and re.search('^[0-9]*$', data['Future_data'])):
            return 'Values are not numbers'
        h = int(data['History_data'])
        f = int(data['Future_data'])
        if not(h > 0 and f > 0):
            return 'Values must be positive numbers'
        os.environ['HISTORY_DATA'] = str(h)
        os.environ['FUTURE_DATA'] = str(f)
        return 'Train values changed'
        
### MAIN ###

if __name__ == "__main__":
    port = int(os.environ.get('TM_PORT'))
    app.run(debug=True, host='0.0.0.0', port=port)