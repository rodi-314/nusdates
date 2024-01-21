import time
import flask
import csv
import json
import threading

JSON_API_NAME = "jsonapiserver"
current_data = {}

app = flask.Flask(JSON_API_NAME)


@app.route("/")
def test_connection():
    return 'hello world'
    #return flask.Response("{}", status=200, mimetype='application/json')


@app.route("/query", methods=['GET', 'POST'])
def return_query():
    # print(flask.request.data)
    return json.dumps(current_data)


# threading.Thread(target=app.run, kwargs={'host': 'localhost', 'port': 8080}, daemon=True).start()

app.run('localhost', 1111)

# with open('GASP_data.csv', 'r') as data_file:
#     csv_reader = csv.reader(data_file)
#     headers = next(csv_reader)
#     for row in csv_reader:
#         for index, value in enumerate(row):
#             try:
#                 current_data[headers[index]] = float(value)
#             except ValueError:
#                 current_data[headers[index]] = value
#         print(current_data['c_Demand'])
#         time.sleep(1)
