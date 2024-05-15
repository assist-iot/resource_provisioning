from flask import Flask, jsonify, request
import os
import re
import main

app = Flask(__name__)

@app.route('/inference', methods=['GET'])
def inference():
    return main.inference()

@app.route('/health', methods=['GET'])
def health():
    resp = jsonify(status="healthy")
    resp.status_code = 200
    return resp
        
### MAIN ###

if __name__ == "__main__":
    port = int(os.environ.get('IM_PORT'))
    app.run(debug=True, host='0.0.0.0', port=port)