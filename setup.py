from setuptools import setup, find_packages

setup(
    name='my_fastapi_app',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'fastapi-app=app.main:app',
        ],
    },
)