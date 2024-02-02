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
import argparse


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
    custom = {}

    def __init__(self, url, organizationId, appToken=None):

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

    def parseJSONfile(self, filepath):
        assert filepath is not None, "filepath required"
        payload = ''
        with open(filepath, 'rb') as json_file:
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
    
    def buildPytestResultWebhookPayload(self, results, jobName, jobNumber):
        if results['duration']:
            duration = results['duration']
        else:
            duration=0
        
        timestamp = self.getEpochTime()
        
        date_time=self.formatCurrentDateTime()
        print(date_time)


        tests=self.getPytestResults(results)

        if jobNumber is None:
            jobNumber = str(timestamp[:-3])
            id = str(jobName) + "_" + str(timestamp)
        else:
            id = str(jobName) + "_" + str(jobNumber) + "_" + str(timestamp)
        
        if results['created']:
            created_timestamp=results['created']
        else:
            created_timestamp=0

        return {
            "organization": self.organizationId,
            "displayName": "#"+str(jobName),
            "number": int(jobNumber),
            "duration": duration,
            "dateCreated": date_time,
            "timestamp": created_timestamp,
            "projectName": str(jobName),
            "tests": tests
            }
    
    def buildMochaResultWebhookPayload(self, results, jobName, jobNumber):
        if results['stats']['duration']:
            duration = results['stats']['duration']
        else:
            duration=0
        
        timestamp = self.getEpochTime()
        
        date_time=self.formatCurrentDateTime()
        print(date_time)


        tests=self.getMochaResults(results)

        if jobNumber is None:
            jobNumber = str(timestamp[:-3])
            id = str(jobName) + "_" + str(timestamp)
        else:
            id = str(jobName) + "_" + str(jobNumber) + "_" + str(timestamp)
        
        if results['stats']['start']:
            created_timestamp=dt.strptime(results['stats']['start'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()*1000
        else:
            created_timestamp=0

        return {
            "organization": self.organizationId,
            "displayName": "#"+str(jobName),
            "number": int(jobNumber),
            "duration": duration,
            "dateCreated": date_time,
            "timestamp": str(int(created_timestamp)),
            "projectName": str(jobName),
            "tests": tests
            }
    
    def getPytestResults(self,results):
        tests=[]
        

        for test in results['tests']:
            tests_temp={
            "title": "",
            "duration": 0,
            "result": "",
            "custom": {}
                }
            tests_temp['title']=test['nodeid'].split('::')[-1]
            tests_temp['duration']=test['setup']['duration']+test['call']['duration']+test['teardown']['duration']
            tests_temp['result']=test['outcome']
            tests_temp['custom']['keywords']=test['keywords']
            tests.append(tests_temp)
        
        return tests
    
    def getMochaResults(self,results):
        tests=[]

        if results.get('results'):
            for result in results['results']:
                if result['suites']:
                    for s in result['suites']:
                        tests_temp={
                                "title": "",
                                "duration": 0,
                                "result": "",
                                "custom":{}
                                    }
                        tests_temp['custom']['suite_title']=s['title']
                        tests_temp['duration']=s['duration']
                        if s['tests']:
                            for test in s['tests']:
                                tests_temp['title']=test['title']
                                tests_temp['result'] =test['state']
                                if test['err']:
                                    tests_temp['custom']['error']=test['err']
                                tests.append(tests_temp)
        if results.get('tests'):
                if results['failures']:
                    for failed_case in results['failures']:
                        tests_temp={
                            "title": "",
                            "duration": 0,
                            "result": "",
                            "custom":{}
                                }
                        tests_temp['title']=failed_case['title']
                        tests_temp['duration']=failed_case['duration']
                        tests_temp['result']='failed'
                        if failed_case['err']:
                            tests_temp['custom']['error']=failed_case['err']
                        tests_temp['custom']['fulltitle']=failed_case['fullTitle']
                        tests.append(tests_temp)
                if results['passes']:
                    for passed_case in results['passes']:
                        tests_temp={
                            "title": "",
                            "duration": 0,
                            "result": "",
                            "custom":{}
                                }
                        tests_temp['title']=passed_case['title']
                        tests_temp['duration']=passed_case['duration']
                        tests_temp['result']='passed'
                        tests_temp['custom']['fulltitle']=passed_case['fullTitle']
                        tests.append(tests_temp)
                if results['pending']:
                    for pending_case in results['pending']:
                        tests_temp={
                            "title": "",
                            "duration": 0,
                            "result": "",
                            "custom":{}
                                }
                        tests_temp['title']=pending_case['title']
                        tests_temp['duration']=pending_case['duration']
                        tests_temp['result']='pending'
                        tests_temp['custom']['fulltitle']=pending_case['fullTitle']
                        tests.append(tests_temp)
        
        return tests


    def sendCucumberTestResultsJson(self, filePath,
                                    jobName, jobNumber=None):
        print("Sending webhook for cucumber test results to " + self.url)

        results = self.parseJSONfile(filePath)

        payload = self.buildTestResultWebhookPayload(results=results, jobName=jobName, jobNumber=jobNumber)
        endpoint = "/ms-source-mediator/cucumber/webhook/receive"
        self.send_webhook(endpoint=endpoint, payload=payload)

    def sendPytestTestResultsJson(self, filePath,
                                    jobName, jobNumber=None):
        print("Sending webhook for pytest test results to " + self.url)

        results = self.parseJSONfile(filePath)

        payload = self.buildPytestResultWebhookPayload(results=results, jobName=jobName, jobNumber=jobNumber)

        #remove below block writing payload to a file. only for testing. 
        print('$$$$$$$$$$$$$$$$$$$$')
        print(payload)
        with open('sample_test_reports\payload_pytest.json', 'w') as f:
            json.dump(payload,f, indent=4)


        endpoint = "/ms-source-mediator/cucumber/webhook/receive"
        #uncomment the below line once the endpoint is ready for testing
        #self.send_webhook(endpoint=endpoint, payload=payload)

    def sendMochaTestResultsJson(self, filePath,
                                    jobName, jobNumber=None):
        print("Sending webhook for Mocha test results to " + self.url)

        results = self.parseJSONfile(filePath)

        payload = self.buildMochaResultWebhookPayload(results=results, jobName=jobName, jobNumber=jobNumber)

        #remove below block writing payload to a file. only for testing. 
        print('$$$$$$$$$$$$$$$$$$$$')
        print(payload)
        with open('sample_test_reports\payload_mocha_suits.json', 'w') as f:
            json.dump(payload,f, indent=4)


        endpoint = "/ms-source-mediator/cucumber/webhook/receive"
        #uncomment the below line once the endpoint is ready for testing
        #self.send_webhook(endpoint=endpoint, payload=payload)

    def sendTriggerWebhook(self, payload):
        endpoint = "/ms-source-mediator/custom/release_and_deployment/webhook/receive"
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
    def releaseTrigger(self, issueKey, projectName, branch, repositoryName, label, environmentName, environmentType):
        payload = self.buildGenericTriggerPayload(issueKey, projectName, branch, repositoryName, label, environmentName,
                                                  environmentType)
        payload["triggerType"] = "release"
        print("Sending webhook for release trigger to " + self.url)
        self.sendTriggerWebhook(payload)

    def deploymentTrigger(self, projectName, branch, repositoryName, label, environmentName, environmentType):
        payload = self.buildGenericTriggerPayload(projectName, branch, repositoryName, label, environmentName,
                                                  environmentType)

        payload["triggerType"] = "deployment"
        print("Sending webhook for deployment trigger to " + self.url)
        self.sendTriggerWebhook(payload)

    def buildGenericTriggerPayload(self, issueKey, projectName, branch, repositoryName, label, environmentName,
                                   environmentType):

        assert issueKey is not None, "issueKey needed"
        assert projectName is not None, "projectName needed"
        assert branch is not None, "branch needed"
        assert repositoryName is not None, "repositoryName needed"
        assert label is not None, "label needed"
        assert environmentName is not None, "environmentName needed"
        assert environmentType is not None, "environmentType needed"

        return {
            'branchId': branch,
            'custom': self.custom,
            "dateCreated": self.formatCurrentDateTime(),
            'environmentName': environmentName,
            'environmentType': environmentType,
            "issueKey": issueKey,
            'label': label,
            'organization': self.organizationId,
            'projectName': projectName,
            'repositoryName': repositoryName
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

    opts = []

    # common
    organizationId = None
    baseUrl = None

    # Function 1 (sendTestResultsJson)
    function = None
    filePath = None
    jobNumber = None
    jobName = None

    # Function 2 (releaseTrigger) & Function 3 (deploymentTrigger)
    issueKey = None
    projectName = None
    branch = None
    repositoryName = None
    label = None
    environmentName = None
    environmentType = None
    triggerType = None
    
    def __init__(self):
        self.parse_arguments()
    
    def parse_arguments(self):

        parser = argparse.ArgumentParser(
                    prog='python3 -m neuro-connector-api.NeuroConnector',
                    description='A CLI to push release metrics by connecting to Neuro')
        parser.add_argument('functions', type=str, help='function to be performed. ex, sendCucumberResults, releaseTrigger or deploymentTrigger')
        parser.add_argument('org', type=str, help='organization id of Neuro')
        parser.add_argument('jobname', type=str, help='jobname')
        parser.add_argument('path', type=str, help='path of test report file')
        parser.add_argument('--jobNum', type=str, help='Job Number')
        
        args = parser.parse_args()

        self.function=args.functions
        self.organizationId=args.org
        self.jobName=args.jobname
        self.filePath=args.path
        self.jobName=args.jobname

    def orchestrate(self):
    
        try:
            nc = NeuroConnector(url=self.baseUrl, organizationId=self.organizationId)
            
            match(str(self.function)):
                    case 'sendCucumberResults':
                        nc.sendCucumberTestResultsJson(self.filePath, self.jobName, self.jobNumber)

                    case 'sendPytestResults':
                        nc.sendPytestTestResultsJson(self.filePath, self.jobName, self.jobNumber)
                    
                    case 'sendMochaResults':
                        nc.sendMochaTestResultsJson(self.filePath, self.jobName, self.jobNumber)

                    case 'releaseTrigger':
                        nc.releaseTrigger(self.issueKey, self.projectName, self.branch, self.repositoryName, self.label,
                                    self.environmentName, self.environmentType)
                        
                    case 'deploymentTrigger':
                        nc.deploymentTrigger(self.projectName, self.branch, self.repositoryName, self.label,
                                        self.environmentName, self.environmentType)
                    #case 'sendTestNGResults':
                    #case 'sendJunitResults':
                    
                    case _:
                        raise Exception(self.function + " function not defined")
    
        except Exception as e:
            print("NeuroConnector failed for reason " + str(e), file=sys.stderr)
            logging.error(traceback.format_exc())
            print(traceback.format_exc(), file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    #Orchestrator(args=sys.argv[1:]).orchestrate()
    Orchestrator().orchestrate()