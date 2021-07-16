from setuptools import setup, find_packages

setup(
    name='SportyDataGen',
    version='1.0',
    long_description=__doc__,
    packages=find_packages(include=['sport-activities-features']),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)