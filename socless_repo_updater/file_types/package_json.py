import json, base64
from socless_repo_updater.constants import PACKAGE_JSON
from socless_repo_updater.exceptions import VersionUpdateException
from socless_repo_updater.gh_helpers import setup_for_file_update, update_file_and_pr
from socless_repo_updater.models import BumpDependencyResult
from github import Repository
from copy import deepcopy


def update_package_json_contents(
    package_json: dict,
    pj_deps: dict,
    pj_replace_only: bool = True,
) -> dict:
    new_package_json = deepcopy(package_json)
    for name, version in pj_deps.items():
        if name not in new_package_json["dependencies"] and pj_replace_only:
            print(f"Skipping {name}. {name} not in dependencies and replace_only=True")
        else:
            new_package_json["dependencies"][name] = version
    return new_package_json


def update_package_json(
    repo: str,
    updated_dependencies: dict,
    replace_only=True,
    org="twilio-labs",
    head_branch: str = "",
    main_branch: str = "master",
    ghe=False,
) -> BumpDependencyResult:
    setup_info = setup_for_file_update(
        repo=repo,
        org=org,
        file_path=PACKAGE_JSON,
        head_branch=head_branch,
        main_branch=main_branch,
        ghe=ghe,
    )

    gh_repo = setup_info.gh_repo
    pj_contentfile = setup_info.contentfile
    head_branch = setup_info.branch_name

    if not pj_contentfile.content:
        raise VersionUpdateException("File content is empty or doesnt exist")

    raw_pj = base64.b64decode(pj_contentfile.content)
    modified_package_json = json.loads(raw_pj)

    for name, version in updated_dependencies.items():
        if name not in modified_package_json["dependencies"] and replace_only:
            print(
                f"Skipping {name} for {repo}. {name} not in dependencies and replace_only=True"
            )
        else:
            modified_package_json["dependencies"][name] = version

    if modified_package_json == json.loads(raw_pj):
        result_msg = "No changes made, dependencies are current."
        result_updated = False
        pull_request = False
    else:
        commit_message = "updating versions for: " + "".join(
            updated_dependencies.keys()
        )
        raw_content = json.dumps(modified_package_json, indent=4)

        result = update_file_and_pr(
            file_path=pj_contentfile.path,
            commit_msg=commit_message,
            raw_content=raw_content,
            file_sha=pj_contentfile.sha,
            pr_title="CLI- dependency version bump",
            pr_body=f"updating versions for \n```{json.dumps(updated_dependencies)}```",
            head_branch=head_branch,
            main_branch=main_branch,
            gh_repo=gh_repo,
        )
        result_updated = True
        result_msg = result.result_msg
        pull_request = result.pr

    return BumpDependencyResult(
        file_updated=result_updated,
        message=result_msg,
        repo_name=repo,
        pull_request=pull_request,
        setup_info=setup_info,
    )
