import json
import requests

class Request:
    token = ""
    headers = {}
    type = ""
    url = ""
    params = ""

    # The constructor specifies the headers - none of the inputs are mandatory as defaults are provided
    def __init__(self, token, url):
        self.token = token
        self.headers = {"accept": 'application/json', "Authorization": self.token, "content-type": "application/json"}
        self.url = url


    # Call this method to make the actual HTTP request
    def make(self, endpoint="", types="GET", params="", payload=None):
        if payload:
            payload = json.dumps(payload)
        target = self.url + endpoint
        response = None
        session = requests.Session()
        session.verify = False  # This is for DB connection

        if types == "GET":
            response = session.get(target, headers=self.headers, params=params)
        if types == "POST":
            response = session.post(target, headers=self.headers, data=payload)
        if types == "PUT":
            response = session.put(target, headers=self.headers, data=payload)
        if types == "DELETE":
            response = session.delete(target, headers=self.headers)

        try:
            # handling empty responses
            jsonResponse = response.json()
        except:
            jsonResponse = {}

        return response, jsonResponse
