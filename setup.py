from setuptools import setup

setup(
   name='neuro-connector-api',
   version='v2.0.3-beta',
   description='Pushes data to https://${env}.myneuro.ai',
   long_description='Intended to be used in the command line: python3 -m neuro-connector-api.NeuroConnector --help \n',
   author='Ben Hesketh',
   author_email='support@myneuro.ai',
   packages=['neuro-connector-api'],  #same as name
   install_requires=['wheel', 'bar', 'greek','urllib3','requests'], #external packages as dependencies
)
