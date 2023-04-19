# neuro-connector-api
## About
This is for connecting to neuro and pushing data such as test results, and triggers for releases and deployments
## Implementation
```
pip install neuro-connector-api
python3 neuro-connector-api.NeuroConnector -h
```

## Params
```
-h, --help : Help

Function 1 (sendTestResultsJson) 
NeuroConnector --func 1 --org [organizationId] --path [filePath] --jobName [jobName] --jobNum [jobNumber (optional)]
        --url [baseUrl (optional)]

Function 2 (releaseTrigger)
NeuroConnector --func 2 --org [organizationId] --projKey [projectKey, e.g jira/management] --vcsProj [vcsProject]
        --branch [branchName] --commitId [commitId] --label [type label, e.g ms/client] --url [baseUrl (optional)]
 
Function 3 (deploymentTrigger)
NeuroConnector --func 3 --org [organizationId] --projKey [projectKey, e.g jira/management] --vcsProj [vcsProject]
        --branch [branchName] --commitId [commitId] --label [type label, e.g ms/client] --url [baseUrl (optional)] 
