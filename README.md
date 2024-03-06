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
```
## Function Overview
This connector has 7 functions that can be added to pipelines or run locally to send data to neuro. Data from the following can be sent to neuro using this connector:

1. Cucumber
2. Pytest
3. Mocha
4. TestNG
5. Junit
6. Release Metrics
7. Deployment Metrics

Functions 1-5 require organisation ID (request ID from neuro customer success at support@myneuro.ai), file path and a name for the job (this must match each time or else a new project is created in neuro during module creation)

Functions 6 & 7 require organisation ID (request ID from neuro customer success at support@myneuro.ai), JIRA issueKey, the name of the neuro module, the branch name, the repository name, a free text field called label, the environment name i.e. stage and the environment type i.e. test.

## Examples of each function:
```
1. sendCucumberResults
python3 NeuroConnector.py --func sendCucumberResults --org 1233211233211233211233 --path cucumber.json --jobname jobNameExample --url https://app.myneuro.ai

2. sendPytestResults
python3 NeuroConnector.py --func sendPytestResults --org 1233211233211233211233 --path pytest.json --jobname jobNameExample --url https://app.myneuro.ai

3. sendMochaResults
python3 NeuroConnector.py --func sendMochaResults --org 1233211233211233211233 --path mocha.json --jobname jobNameExample --url https://app.myneuro.ai

4. sendTestNGResults
python3 NeuroConnector.py --func sendTestNGResults --org 1233211233211233211233 --path testng.json --jobname jobNameExample --url https://app.myneuro.ai

5. sendJunitResults
python3 NeuroConnector.py --func sendJunitResults --org 1233211233211233211233 --path junit.json --jobname jobNameExample --url https://app.myneuro.ai

6. releaseTrigger
python3 NeuroConnector.py --func releaseTrigger --org 123321123321123321 --issueKey NC-123421 --projectName neuroModuleName --branch branchName --repositoryName repoName --label myCustomLabel --environmentName Stage --environmentType Test

7. deploymentTrigger
python3 NeuroConnector.py --func deploymentTrigger --org 123321123321123321 --projectName neuroModuleName --branch branchName --repositoryName repoName --label myCustomLabel --environmentName Stage --environmentType Test

   

```

# IGNORE THESE FUNCTIONS

Function 1 (sendTestResultsJson) 
NeuroConnector --func 1 --org [organizationId] --path [filePath] --jobName [jobName] --jobNum [jobNumber (optional)]
        --url [baseUrl (optional)]

Function 2 (releaseTrigger)
NeuroConnector --func 2 --url [baseUrl (optional)] --org [organizationId] --branch [branchName] --env [environment i.e. stage]
        --envType [env type i.e. test] --issueKey [JIRA Key] --label [Free text field] --projName [The name of the neuro module] --repositoryName [repo name]
        
 
Function 3 (deploymentTrigger)
NeuroConnector --func 3 --org [organizationId] --projKey [projectKey, e.g jira/management] --vcsProj [vcsProject]
        --branch [branchName] --commitId [commitId] --label [type label, e.g ms/client] --url [baseUrl (optional)] 
