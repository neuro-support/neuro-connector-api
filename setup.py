from setuptools import setup

setup(
   name='neuro-connector-api',
   version='v1.2.0-beta',
   description='Connects to app.myneuro.ai',
   long_description='Intended to be used in the command line. NeuroConnector.py -c [connectonId] -o [organizationId] -u [baseUrl] -a [appToken] -f [function] -p [filePath]\nFunctions [1=sendTestResultsJson]\n',
   author='Ben Hesketh',
   author_email='bhesketh@wearedragonfly.co',
   packages=['neuro-connector-api'],  #same as name
   install_requires=['wheel', 'bar', 'greek','urllib3','requests'], #external packages as dependencies
)