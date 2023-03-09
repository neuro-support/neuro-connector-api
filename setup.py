from setuptools import setup

setup(
   name='neuro-connector-api',
   version='v1.0.1-alpha',
   description='Connects to app.myneuro.ai',
   author='Ben Hesketh',
   author_email='bhesketh@wearedragonfly.co',
   packages=['neuro-connector-api'],  #same as name
   install_requires=['wheel', 'bar', 'greek','urllib3','requests'], #external packages as dependencies
)