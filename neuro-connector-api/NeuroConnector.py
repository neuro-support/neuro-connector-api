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

class NeuroConnector:
    logging.getLogger("neuro-connector-api").propagate = False
    logging.basicConfig(filename='neuro-connector-api.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    token = ''
    headers = ''
    url = ''
    requestWrapper = None
    connectionId = None
    organization = None
    jobName = None
    jobNumber = None
    projectName = None

    def __init__(self,url, organizationId, appToken=None):

        if url is None:
            self.url = "https://app.myneuro.ai"
        else:
            self.url = url

        if appToken:
            token = "Bearer " + appToken
        else:
            token = None

        self.requestWrapper = RequestWrapper(token=token,
                                             url=self.url)

        assert self.requestWrapper, "couldn't initiate request wrapper"

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
        return str(int(time.time() * 1000))

    def deleteData(self):
        logging.info("deleting existing data")
        endpoint = '/ms-provision-receptor/custom/zephyr/remove-data/' + self.organizationId + '/' + self.connectionId

        response = self.requestWrapper.make(endpoint=endpoint, types="DELETE")
        logging.info(response[1]['status'] + " deleting data")

        return response

    def parseJSONfile(self, filepath):
        assert filepath is not None, "filepath required"
        payload = ''
        with open(filepath, encoding='utf-8') as json_file:
            payload = json.load(json_file)
        return payload

    def buildTestResultWebhookPayload(self, results, jobName, jobNumber):
        duration = self.calculateDuration(results)

        timestamp = self.getEpochTime()

        if jobNumber is None:
            jobNumber = str(timestamp[:-3])
            id = str(jobName) + "_" + str(timestamp)
        else:
            id = str(jobName) + "_" + str(jobNumber) + "_" + str(timestamp)

        return {

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
            "url": self.url,
            "actions": [
                {
                    "testResult": results
                }
            ]
        }

    def encodeStringForURL(self, string):
        return urllib.parse.quote(string)

    def sendCucumberTestResultsJson(self, filePath,
                                    jobName, jobNumber=None):
        print("Sending webhook for cucumber test results to " + self.url)

        results = self.parseJSONfile(filePath)

        payload = self.buildTestResultWebhookPayload(results=results, jobName=jobName, jobNumber=jobNumber)
        endpoint = "/ms-source-mediator/cucumber/webhook/receive"
        self.send_webhook(endpoint=endpoint, payload=payload)

    def sendTriggerWebhook(self, payload):
        endpoint = "/???"
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
    def releaseTrigger(self, projectKey, branch, commitId, label, environmentName, environmentType, vcsProject):
        payload = self.buildGenericTriggerPayload(projectKey, branch, commitId, label, environmentName, environmentType,
                                                  vcsProject)
        payload["triggerType"] = "release"
        print("Sending webhook for release trigger to " + self.url)
        self.sendTriggerWebhook(payload)

    def deploymentTrigger(self, projectKey, branch, commitId, label, environmentName, environmentType, vcsProject):
        payload = self.buildGenericTriggerPayload(projectKey, branch, commitId, label, environmentName, environmentType,
                                                  vcsProject)
        payload["triggerType"] = "deployment"
        print("Sending webhook for deployment trigger to " + self.url)
        self.sendTriggerWebhook(payload)

    def buildGenericTriggerPayload(self, projectKey, branch, commitId, label, environmentName, environmentType,
                                   vcsProject):

        assert projectKey is not None, "projectKey needed"
        assert branch is not None, "branch needed"
        assert commitId is not None, "commitId needed"
        assert label is not None, "label needed"
        assert environmentName is not None, "environmentName needed"
        assert environmentType is not None, "environmentType needed"
        assert vcsProject is not None, "vcsProject needed"

        return {
            "organization": self.organizationId,
            "url": self.url,
            "timestamp": self.getEpochTime(),
            'projectKey': projectKey,
            'branch': branch,
            'commitId': commitId,
            'label': label,
            'environmentName': environmentName,
            'environmentType': environmentType,
            'vcsProject': vcsProject
        }


class RequestWrapper():
    request = None
    logging.getLogger("neuro-api-client").propagate = False
    logging.basicConfig(filename='neuro-api-client.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def __init__(self, url, token=None):
        self.request = Request(token, url)
        # TO DO - implement certificate verification and remove the below
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        assert self.request

    def make(self, endpoint=None, types=None, payload=None):
        attempt = 0
        maxAttempts = 5
        errorMessage = ""
        waitInSeconds = 10

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


class Orchestrator:
    logging.getLogger("neuro-connector-api").propagate = False
    logging.basicConfig(filename='neuro-connector-api.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    opts=[]

    # common
    organizationId = None
    baseUrl = None

    # Function 1 (sendTestResultsJson)
    function = None
    filePath = None
    jobNumber = None
    jobName = None

    # Function 2 (releaseTrigger) & Function 3 (deploymentTrigger)
    projectKey = None
    branch = None
    commitId = None
    label = None
    environmentName = None
    environmentType = None
    vcsProject = None

    def __init__(self, args):

        self.args = args
        self.opts = ["-h", "--func=", "--path=", "--url=", "--org=", "--jobName=", "--jobNum=", "--projKey=", "--vcsProj=",
                "--branch=", "--commitId=", "--label=", "--env=", "--envType=", "--help"]

        self.instructions= '\n-h, --help : Help\n'
        self.instructions = self.instructions + '\nFunction 1 (sendTestResultsJson)\nNeuroConnector --func 1 --org [organizationId] --path [filePath] --jobName [jobName] --jobNum [jobNumber (optional)] --url [baseUrl (optional)]\n'
        self.instructions = self.instructions + '\nFunction 2 (releaseTrigger)\nNeuroConnector --func 2 --org [organizationId] --projKey [projectKey, e.g jira/management] --vcsProj [vcsProject] --branch [branchName] --commitId [commitId] --label [type label, e.g ms/client] --url [baseUrl (optional)]\n'
        self.instructions = self.instructions + '\nFunction 3 (deploymentTrigger)\nNeuroConnector --func 2 --org [organizationId] --projKey [projectKey, e.g jira/management] --vcsProj [vcsProject] --branch [branchName] --commitId [commitId] --label [type label, e.g ms/client] --url [baseUrl (optional)]\n'

    def getParameterPairsForArgs(self):
        parameterPairs = {}
        for i, arg in enumerate(self.args):
            for opt in self.opts:
                if opt[-1] == "=" and opt[:-1] == arg:
                    try:
                        value = self.args[i + 1]
                        assert value is not None and not value.startswith("-")
                    except:
                        raise Exception("no value for key " + arg)

                    parameterPairs.update({arg: value})
                elif arg == opt and opt[-1] != "=":
                    parameterPairs.update({arg: None})

        return parameterPairs


    def orchestrate(self):
        parameterPairs=self.getParameterPairsForArgs()

        assert "-h" not in parameterPairs and "--help" not in parameterPairs and len(parameterPairs.keys()) >= 3, "\n\nSee instructions\n"+self.instructions
        assert "--func" in parameterPairs, "function param needed --func\n" + self.instructions

        function = parameterPairs["--func"]

        if str(function) == '1':
            for key in parameterPairs.keys():
                if key == "--org":
                    self.organizationId = parameterPairs[key]
                elif key == "--url":
                    self.baseUrl = parameterPairs[key]
                elif key == "--path":
                    self.filePath = parameterPairs[key]
                elif key == "--jobName":
                    self.jobName = parameterPairs[key]
                elif key == "--jobNum":
                    self.jobNumber = parameterPairs[key]

        elif str(function) in ['2', '3']:
            for key in parameterPairs.keys():
                if key == "--org":
                    self.organizationId = parameterPairs[key]
                elif key == "--url":
                    self.baseUrl = parameterPairs[key]
                elif key == "--projKey":
                    self.projectKey = parameterPairs[key]
                elif key == "--branch":
                    self.branch = parameterPairs[key]
                elif key == "--commitId":
                    self.commitId = parameterPairs[key]
                elif key == "--label":
                    self.label = parameterPairs[key]
                elif key == "--env":
                    self.environmentName = parameterPairs[key]
                elif key == "--envType":
                    self.environmentType = parameterPairs[key]
                elif key == "--vcsProj":
                    self.vcsProject = parameterPairs[key]

        try:
            nc = NeuroConnector(url=self.baseUrl, organizationId=self.organizationId)
            if str(function) == '1':
                nc.sendCucumberTestResultsJson(self.filePath, self.jobName, self.jobNumber)
            elif str(function) == '2':
                nc.releaseTrigger(self.projectKey, self.branch, self.commitId, self.label, self.environmentName, self.environmentType, self.vcsProject)
            elif str(function) == '3':
                nc.deploymentTrigger(self.projectKey, self.branch, self.commitId, self.label, self.environmentName, self.environmentType, self.vcsProject)
            else:
                print(self.instructions, file=sys.stderr)
                raise Exception("function not defined")

        except Exception as e:
            print("NeuroConnector failed for reason " + str(e), file=sys.stderr)
            logging.error(traceback.format_exc())
            print(traceback.format_exc(), file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    Orchestrator(args=sys.argv[1:]).orchestrate()
