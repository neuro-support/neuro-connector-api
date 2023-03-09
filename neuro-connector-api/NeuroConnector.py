import getopt
import json
from RequestWrapper import RequestWrapper
import sys
import logging
import traceback

logging.getLogger("neuro-api-client").propagate = False
logging.basicConfig(filename='neuro-api-client.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class NeuroConnector:
    token = ''
    headers = ''
    url = ''
    requestWrapper = None
    connectionId=None
    organization=None

    def __init__(self, appToken,url,connectionId,organizationId):
        self.requestWrapper = RequestWrapper(token="Bearer " + appToken,
                                             url=url)
        assert self.requestWrapper, "couldn't initiate request wrapper"

        self.connectionId=connectionId
        assert self.connectionId, "connectionId missing"
        self.organizationId=organizationId
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

    def deleteData(self):
        logging.info("deleting existing data")
        endpoint = '/ms-provision-receptor/custom/zephyr/remove-data/' + self.organizationId + '/' + self.connectionId

        response = self.requestWrapper.make(endpoint=endpoint, types="DELETE")
        logging.info(response[1]['status'] + " deleting data")


        return response

    def parseJSONfile(self, filepath):
        payload = ''
        with open(filepath) as json_file:
            payload = json.load(json_file)
        return payload

    def sendTestResultsJson(self, filePath):
        assert filePath,"file path must not be null"
        j=self.parseJSONfile(filePath)
        endpoint="999999"
        self.send_webhook(endpoint=endpoint,payload=j)

if __name__ == "__main__":
    organizationId=None
    baseUrl=None
    appToken=None
    function=None
    filePath=None

    instructions = 'NeuroConnector.py -c [connectonId] -o [organizationId] -u [baseUrl] -a [appToken] -f [function] -p [filePath]\nFunctions [1=sendTestResultsJson]\n'
    connectionId = "637f77dcb688b65de6436769"

    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args,"c:o:u:a:f:p:h")
    except getopt.GetoptError:
        print (instructions, file=sys.stderr)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c"):
            connectionId = arg
        elif opt in ("-o"):
           organizationId = arg
        elif opt in ("-u"):
            baseUrl=arg
        elif opt in ("-a"):
            appToken = arg
        elif opt in ("-f"):
            function=arg
        elif opt in ("-p"):
            filePath = arg
        elif opt in ("-h"):
            print(instructions)
        else:
            print(instructions, file=sys.stderr)
            sys.exit()
    try:
        nc = NeuroConnector(appToken=appToken,url=baseUrl,connectionId=connectionId,organizationId=organizationId)
        if str(function)=='1':
            nc.sendTestResultsJson(filePath=filePath)
        else:
            raise Exception("no function configured for "+ str(function))
    except Exception as e:
        print("NeuroConnector failed for reason " + str(e), file=sys.stderr)
        logging.error(traceback.format_exc())
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(2)
