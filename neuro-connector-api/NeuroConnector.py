import getopt
import re
import sys
import time
import traceback
import urllib3
import logging
from time import sleep as pause
import json
import requests
import datetime
import urllib.parse
from datetime import datetime as dt

logging.getLogger("neuro-api-client").propagate = False
logging.basicConfig(filename='neuro-api-client.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


class NeuroConnector:
    token = ''
    headers = ''
    url = ''
    requestWrapper = None
    connectionId = None
    organization = None
    jobName = None
    jobNumber = None
    projectName = None

    def __init__(self, appToken, url, connectionId, organizationId, jobName, jobNumber=None):
        self.jobNumber = jobNumber

        self.jobName = jobName
        assert self.jobName, "job name needed"

        if appToken:
            token = "Bearer " + appToken
        else:
            token = None

        self.requestWrapper = RequestWrapper(token=token,
                                             url=url)

        assert self.requestWrapper, "couldn't initiate request wrapper"

        self.connectionId = connectionId
        self.organizationId = organizationId
        assert self.organizationId, "organizationId missing"

    def delete_record(self, key):
        o = {}
        o['webhookEvent'] = 'jira:issue_deleted'
        o['issue'] = {'key': key, 'id': key}
        o['testId'] = key
        o['externalProject'] = "TEST"
        o['connectionId'] = self.connectionId
        o['organization'] = self.organizationId
        payload = o
        print(payload)
        endpoint = "/ms-provision-receptor/zfjcloud/v2/webhook/" + self.connectionId
        print(endpoint)

        self.send_webhook(endpoint, payload)

    def send_webhook(self, endpoint, payload):
        # endpoint = "/ms-provision-receptor/custom/zephyr/zephyr-f-cloud-controller"
        self.requestWrapper.make(endpoint=endpoint, payload=payload, types="POST")

    # Neuro needs updatedDate to be today's date and in isoformat and seconds to 3 decimal places,
    # e.g. 2021-08-19T13:06:23.123+0100
    def formatCurrentDateTime(self):
        currentDateTime = (dt.now(datetime.timezone.utc) - datetime.timedelta(hours=0,
                                                                              minutes=3)).astimezone().isoformat(
            timespec='milliseconds')

        # Removes the : symbol from timezone
        parsed = re.sub(r'([+-]\d+):(\d+)$', r'\1\2', currentDateTime)

        return parsed

    def getEpochTime(self):
        return str(int(time.time()))

    def deleteData(self):
        logging.info("deleting existing data")
        endpoint = '/ms-provision-receptor/custom/zephyr/remove-data/' + self.organizationId + '/' + self.connectionId

        response = self.requestWrapper.make(endpoint=endpoint, types="DELETE")
        logging.info(response[1]['status'] + " deleting data")

        return response

    def parseJSONfile(self, filepath):
        payload = ''
        with open(filepath, encoding='utf-8') as json_file:
            payload = json.load(json_file)
        return payload

    def buildTestResultWebhookPayload(self, results, jobName, jobNumber, path):
        duration = self.calculateDuration(results)

        timestamp = self.getEpochTime()
        if jobNumber is None:
            jobNumber = str(timestamp)
            id = str(jobName) + "_" + str(timestamp)
        else:
            id = str(jobName) + "_" + str(jobNumber) + "_" + str(timestamp)

        return {
            "actions": [
                {
                    "path": str(path),
                    "testResult": results
                }
            ],
            "displayName": "#" + jobNumber,
            "duration": 0,
            "estimatedDuration": duration,
            "fullDisplayName": str(jobName) + " #" + jobNumber,
            "id": id,
            "number": int(jobNumber),
            "organization": self.organizationId,
            "projectName": str(jobName),
            "result": self.getResult(results),
            "timestamp": timestamp,
            "url": "https://myneuro.ai"
        }

    def encodeStringForURL(self, string):
        return urllib.parse.quote(string)

    def sendCucumberTestResultsJson(self, filePath):
        assert filePath, "file path must not be null"
        results = self.parseJSONfile(filePath)

        payload = self.buildTestResultWebhookPayload(results=results, jobName=self.jobName, jobNumber=self.jobNumber,
                                                     path=filePath)
        endpoint = "/ms-source-mediator/cucumber/webhook/receive"
        self.send_webhook(endpoint=endpoint, payload=payload)

    def getResult(self, results):
        stepStatuses = []

        for scenario in results:
            if 'elements' in scenario:
                for element in scenario['elements']:
                    if 'steps' in element:
                        for step in element['steps']:
                            if 'result' in step:
                                if 'status' in step['result']:
                                    stepStatuses.append(step['result']['status'])

        if len(stepStatuses) > 0:
            overallResult = "SUCCESS"
            for status in stepStatuses:
                if status not in ["passed", "failed"]:
                    overallResult = "UNSTABLE"
        else:
            overallResult = "FAILURE"

        return overallResult

    def calculateDuration(self, results):
        duration = 0
        for scenario in results:
            if 'elements' in scenario:
                for element in scenario['elements']:
                    if 'steps' in element:
                        for step in element['steps']:
                            if 'result' in step:
                                if 'duration' in step['result']:
                                    duration = duration + int(step['result']['duration'])

        return duration

    # def removeEmbeddings(self, results):
    #     for scenario in results:
    #         if 'elements' in scenario:
    #             for element in scenario['elements']:
    #                 if 'steps' in element:
    #                     for step in element['steps']:
    #                         if 'result' in step:
    #                             if 'duration' in step['result']:
    #                                 duration = duration + int(step['result']['duration'])


class RequestWrapper():
    request = None
    logging.getLogger("neuro-api-client").propagate = False
    logging.basicConfig(filename='neuro-api-client.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def __init__(self, url,token=None):
        self.request = Request(token, url)
        # TO DO - implement certificate verification and remove the below
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        assert self.request

    def make(self, endpoint=None, types=None, payload=None):
        attempt = 0
        maxAttempts = 5
        errorMessage = ""
        waitInSeconds = 60

        assert endpoint
        assert types

        while attempt < maxAttempts:
            try:
                if payload:
                    response, data = self.request.make(endpoint=endpoint, types=types, payload=payload)
                else:
                    response, data = self.request.make(endpoint=endpoint, types=types)

                if response.status_code != 200:
                    if payload:
                        errorMessage = str(
                            response.status_code) + " " + response.reason + " @ endpoint " + types + " " + endpoint + "\nWith request Payload = " + json.dumps(
                            payload) + "\nResponse payload: " + json.dumps(data)
                    else:
                        errorMessage = str(
                            response.status_code) + " " + response.reason + " @ endpoint " + types + " " + endpoint + "\nWith response payload: " + json.dumps(
                            data)
                    logging.warning(errorMessage)
                    logging.warning("waiting " + str(waitInSeconds) + " seconds")

                    pause(waitInSeconds)
                    logging.warning(
                        "RETRYING " + str(attempt + 1) + " of " + str(maxAttempts) + " times")

                    attempt += 1
                else:
                    print("Response: " + str(response.json()))
                    return response, data

            except:
                if not payload:
                    payload = {}
                raise Exception(
                    "request @ endpoint " + types + " " + endpoint + " failed. reason unknown and purposefully unhandled - likely code error. \n Request Payload = " + json.dumps(
                        payload))

        logging.error("Failed attempt to get data from Test Rail, attempt: " + str(attempt) + " with " + str(
            waitInSeconds) + "s wait between each attempt")
        raise Exception(
            "More than " + str(maxAttempts) + " attempts to call Test Rail API failed. Last cause: " + errorMessage)


class Request:
    token = ""
    headers = {}
    type = ""
    url = ""
    params = ""

    # The constructor specifies the headers - none of the inputs are mandatory as defaults are provided
    def __init__(self, token, url):
        self.token = token
        if token is not None:
            self.headers = {"accept": 'application/json', "Authorization": self.token,
                            "content-type": "application/json"}
        else:
            self.headers = {"accept": 'application/json',
                            "content-type": "application/json"}
        self.url = url

    # Call this method to make the actual HTTP request
    def make(self, endpoint="", types="GET", params="", payload=None):
        if payload:
            payload = json.dumps(payload)
        target = self.url + endpoint
        print(types + " " + target + " \nPayload: " + payload[:200] + "... [truncated to 200 chars]")
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


if __name__ == "__main__":
    appToken = None
    organizationId = None
    baseUrl = None
    function = None
    filePath = None
    connectionId = None
    jobNumber = None
    jobName = None

    instructions = '\nNeuroConnector -f [function] -p [filePath] -u [baseUrl] -a [appToken optional] -o [organizationId] -c [connectonId optional] -n [jobName] -j [jobNumber optional]  \n\nFunctions [1=sendTestResultsJson]\n'

    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, "f:p:u:a:o:c:n:j:h")
    except getopt.GetoptError:
        print(instructions, file=sys.stderr)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c"):
            connectionId = arg
        elif opt in ("-o"):
            organizationId = arg
        elif opt in ("-u"):
            baseUrl = arg
        elif opt in ("-a"):
            appToken = arg
        elif opt in ("-f"):
            function = arg
        elif opt in ("-p"):
            filePath = arg
        elif opt in ("-n"):
            jobName = arg
        elif opt in ("-j"):
            jobNumber = arg
        elif opt in ("-h"):
            print("HELP " + instructions, file=sys.stderr)
            sys.exit()
        else:
            print(instructions, file=sys.stderr)
            sys.exit()

    assert baseUrl, "url must not be none\n" + instructions
    assert organizationId, "organizationId must not be none\n" + instructions
    assert function, "function must not be none\n" + instructions

    assert jobName, "jobName must not be none\n" + instructions

    try:
        nc = NeuroConnector(appToken=appToken, url=baseUrl, connectionId=connectionId, organizationId=organizationId,
                            jobName=jobName, jobNumber=jobNumber)
        if str(function) == '1':
            assert filePath, "filePath must not be none\n" + instructions
            nc.sendCucumberTestResultsJson(filePath=filePath)
        else:
            raise Exception("no function configured for " + str(function))
    except Exception as e:
        print("NeuroConnector failed for reason " + str(e), file=sys.stderr)
        logging.error(traceback.format_exc())
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(2)
