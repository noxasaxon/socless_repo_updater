import uuid
import collections.abc
from dataclasses import dataclass
from typing import List, Optional, Union
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.ContentFile import ContentFile

from socless_repo_updater.exceptions import UpdaterError, VersionUpdateException


def make_branch_name(name=""):
    branch_id = str(uuid.uuid4())
    name = f"{name}-" if name else ""
    branch_name = f"cli-{name}{branch_id}"[:39]
    return branch_name


@dataclass
class FileExistenceCheck:
    file_path: str
    branch_exists: bool = False
    file_exists: bool = False
    file_contents: Optional[Union[ContentFile, List[ContentFile]]] = None


def check_github_file_exists(
    gh_repo: Repository, file_path, branch_name
) -> FileExistenceCheck:
    try:
        file_contents = gh_repo.get_contents(path=file_path, ref=branch_name)
        if isinstance(file_contents, list):
            raise UpdaterError(
                f"File path {file_path} branch: {branch_name} points to a directory"
            )

        return FileExistenceCheck(
            file_path=file_path,
            branch_exists=True,
            file_exists=True,
            file_contents=file_contents,
        )
    except GithubException as e:
        # Error getting file, either file or branch does not exist
        if e.status == 404:
            # either branch or file not found
            if e.data["message"] == "Not Found":
                # branch exists, but file does not
                branch_exists = True

                # NOTE: short circuting this here to simplify usage
                raise UpdaterError(
                    f"{file_path} not found on existing branch {branch_name}"
                ) from e
            elif "No commit found for the ref" in e.data["message"]:
                branch_exists = False
            else:
                raise UpdaterError("404 uncaught") from e

            # NOTE: For now, if file DOES NOT exist but branch DOES exist this will raise an error
            return FileExistenceCheck(
                file_path=file_path,
                branch_exists=branch_exists,
                file_exists=False,
                file_contents=None,
            )
        else:
            raise UpdaterError("Unhandled Error") from e


def check_pr_exists(
    gh_repo: Repository,
    base_branch: str,
    head_branch: str,
) -> Optional[PullRequest]:
    for pull in gh_repo.get_pulls(state="open", sort="created", base=base_branch):
        if (
            pull.raw_data["base"]["ref"] == base_branch
            and pull.raw_data["head"]["ref"] == head_branch
        ):
            return pull
    return None


def commit_file_with_pr(
    gh_repo: Repository,
    gh_file_object: ContentFile,
    new_content: str,
    file_path: str,
    head_branch: str,
    default_branch: str,
    commit_message: str,
) -> PullRequest:
    _ = gh_repo.update_file(
        path=file_path,
        message=commit_message,
        content=new_content,
        sha=gh_file_object.sha,
        branch=head_branch,
    )

    existing_pr = check_pr_exists(
        gh_repo=gh_repo, base_branch=default_branch, head_branch=head_branch
    )
    if existing_pr:
        print(f"PR already exists: {existing_pr.number}")
        return existing_pr
    else:
        new_pr = gh_repo.create_pull(
            title="CLI- dependency version bump",
            body="updating dependencies, please check changed files",
            base=default_branch,
            head=head_branch,
        )
        return new_pr


def dict_merge(*args, add_keys=True):
    assert len(args) >= 2, "dict_merge requires at least two dicts to merge"
    rtn_dct = args[0].copy()
    merge_dicts = args[1:]
    for merge_dct in merge_dicts:
        if add_keys is False:
            merge_dct = {
                key: merge_dct[key] for key in set(rtn_dct).intersection(set(merge_dct))
            }
        for k, v in merge_dct.items():
            if not rtn_dct.get(k):
                rtn_dct[k] = v
            elif k in rtn_dct and type(v) != type(rtn_dct[k]):  # noqa
                raise TypeError(
                    f"Overlapping keys exist with different types: original is {type(rtn_dct[k])}, new value is {type(v)}"
                )
            elif isinstance(rtn_dct[k], dict) and isinstance(
                merge_dct[k], collections.abc.Mapping
            ):
                rtn_dct[k] = dict_merge(rtn_dct[k], merge_dct[k], add_keys=add_keys)
            elif isinstance(v, list):
                for list_value in v:
                    if list_value not in rtn_dct[k]:
                        rtn_dct[k].append(list_value)
            else:
                rtn_dct[k] = v
    return rtn_dct


def validate_socless_python_release(
    public_gh: Github, release_tag_or_latest: str
) -> str:
    if release_tag_or_latest == "latest":
        socless_python_repo = public_gh.get_repo("twilio-labs/socless_python")
        release = socless_python_repo.get_latest_release().tag_name
        return release
    elif not release_tag_or_latest:
        raise VersionUpdateException(
            "No version tag or 'latest' specified for socless_python"
        )
    # elif not check_release_exists(
    #     repo="socless_python",
    #     org="twilio-labs",
    #     release=release_tag_or_latest,
    #     ghe=False,
    # ):
    #     raise VersionUpdateException(
    #         f"Release {release_tag_or_latest} not found for twilio-labs/socless_python"
    #     )

    return release_tag_or_latest


# def check_release_exists(repo: str, org: str, release: str, ghe=False):
#     g = init_github(ghe=ghe)
#     gh_repo = g.get_repo(full_name_or_id=f"{org}/{repo}")

#     try:
#         release_query = gh_repo.get_release(release)
#         # release_query.tag_name is 1.1.0
#         return release_query
#     except GithubException as e:
#         print(f"Release {release} not found for {org}/{repo}")
#         print(e)
#         return False
