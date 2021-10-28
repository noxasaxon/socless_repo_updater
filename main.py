import sys
from socless_repo_updater.updater import SoclessUpdater


if __name__ == "__main__":
    repo_urls = sys.argv[1:]

    # dict of package.json dependencies to update
    # pj_deps = {"serverless": "9.9.9", "sls_apb" : "git+https://github.com/twilio-labs/sls-apb.git#1.3.0"}
    pj_deps = {}

    # the socless_python release tag to update in requirements.txt
    # socless_python_version = "9.9.9"
    socless_python_version = ""

    # IF you have an existing branch you'd like to update the PR for, supply branch name here
    head_branch = ""

    # TODO: make a real cli if necessary
    if not pj_deps and not socless_python_version:
        raise Exception(
            "Please edit `main.py` and supply the requested dependencies to update"
        )

    updater = SoclessUpdater().update_with_regular_github(
        repo_urls,
        pj_deps=pj_deps,
        socless_python_version=socless_python_version,
        head_branch=head_branch,
    )
