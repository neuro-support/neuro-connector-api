import json
import logging
from RequestWrapper import RequestWrapper

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
