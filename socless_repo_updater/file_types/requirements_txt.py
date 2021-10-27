import json, base64
from typing import Union
from src.constants import REQUIREMENTS_FULL_PATH, SOCLESS_PYTHON_PIP_PATTERN
from src.exceptions import VersionUpdateException
from src.gh_helpers import (
    init_github,
    setup_for_file_update,
    update_file_and_pr,
    dict_merge,
    check_release_exists,
)
from src.structs import BumpDependencyResult
import re


def build_replacement_pip_string(socless_python_release_tag: str) -> str:
    return f"git+https://github.com/twilio-labs/socless_python.git@{socless_python_release_tag}#egg=socless"


def validate_socless_python_release(release_tag_or_latest: str) -> str:
    if release_tag_or_latest == "latest":
        open_source_github = init_github(False)
        socless_python_repo = open_source_github.get_repo("twilio-labs/socless_python")
        release = socless_python_repo.get_latest_release().tag_name
        return release
    elif not check_release_exists(
        repo="socless_python",
        org="twilio-labs",
        release=release_tag_or_latest,
        ghe=False,
    ):
        raise VersionUpdateException(
            f"Release {release_tag_or_latest} not found for twilio-labs/socless_python"
        )

    return release_tag_or_latest


def update_socless_python_in_requirements_txt(
    requirements_txt: Union[str, bytes], release: str
) -> str:
    if isinstance(requirements_txt, bytes):
        requirements_txt = requirements_txt.decode("UTF-8")

    file_with_new_release = re.sub(
        SOCLESS_PYTHON_PIP_PATTERN,
        build_replacement_pip_string(release),
        requirements_txt,
    )
    return file_with_new_release


def requirements_txt_are_equal(first: Union[str, bytes], second: Union[str, bytes]):
    if isinstance(first, bytes):
        first = first.decode("UTF-8")
    if isinstance(second, bytes):
        second = second.decode("UTF-8")
    return first == second


def bump_socless_python(
    repo: str,
    release: str,
    org="twilio-labs",
    bypass_release_validation=False,
    head_branch: str = "",
    main_branch: str = "master",
    ghe: bool = False,
) -> BumpDependencyResult:
    if not release:
        raise VersionUpdateException(
            "No version specified for socless_python bump.\n (HINT: use 'latest' for a shortcut to the most recent release)"
        )

    if not bypass_release_validation:
        release = validate_socless_python_release(release)

    # get requirements.txt for this repo
    setup_info = setup_for_file_update(
        repo=repo,
        org=org,
        file_path=REQUIREMENTS_FULL_PATH,
        head_branch=head_branch,
        main_branch=main_branch,
        ghe=ghe,
    )
    gh_repo = setup_info.gh_repo
    contentfile = setup_info.contentfile
    head_branch = setup_info.branch_name

    if not contentfile.content:  # type: ignore
        raise VersionUpdateException("File content is empty or doesnt exist")

    raw_file = base64.b64decode(contentfile.content)  # type: ignore
    file_as_string = raw_file.decode("UTF-8")

    file_with_new_release = re.sub(
        SOCLESS_PYTHON_PIP_PATTERN,
        build_replacement_pip_string(release),
        file_as_string,
    )

    if file_as_string == file_with_new_release:
        result_msg = "No changes made, dependencies are current."
        result_updated = False
        pull_request = False
    else:
        commit_message = f"update socless_python to {release}"

        result = update_file_and_pr(
            file_path=contentfile.path,  # type: ignore
            commit_msg=commit_message,
            raw_content=file_with_new_release,
            file_sha=contentfile.sha,  # type: ignore
            pr_title="CLI- dependency version bump",
            pr_body=commit_message,
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
        pull_request=pull_request,  # type: ignore
        setup_info=setup_info,
    )
