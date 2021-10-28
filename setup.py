from setuptools import setup, find_packages


setup(
    name="socless_repo_updater",
    version="0.1.0",
    description="A example Python package",
    url="https://github.com/noxasaxon/socless_repo_updater",
    author="Saxon Hunt",
    author_email="saxon.h@outlook.com",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "socless_repo_parser @ git+https://github.com/twilio-labs/socless_repo_parser.git#egg=socless_repo_parser",
        "ruamel.yaml==0.17.4",
        "pygithub==1.55",
    ],
)
