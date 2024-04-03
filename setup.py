from setuptools import setup

setup(
   name='neuro-connector-api',
   version='v3.0.1',
   description='Pushes data to https://${env}.myneuro.ai',
   long_description='Intended to be used in the command line: python3 -m neuro-connector-api.NeuroConnector --help \n',
   author='Ben Hesketh',
   author_email='support@myneuro.ai',
   packages=['neuro-connector-api'],  #same as name
   install_requires=['wheel', 'bar', 'greek','urllib3','requests', 'xmltodict'], #external packages as dependencies
)
