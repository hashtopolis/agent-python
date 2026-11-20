#/bin/python3
#https://pypi.org/project/setuppy-generator/ 
#https://pypi.org/project/setupcfg-generator/ 
from setuptools import setup

setup(
install_requires=['requirements.txt'],
    name='hashtopolis-agent-python',
     version='0.6.0',
    url='https://github.com/s3inlc/hashtopolis-agent-python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'requests',
        'psutil',
    ],
    packages=[
        'htpclient',
    ],
    py_modules=[
        '__main__',
    ],
)
