import os, uuid
import collections.abc
from typing import Union
from github import Github, GithubException, UnknownObjectException
from socless_repo_updater.exceptions import VersionUpdateException
from github.Repository import Repository
from github.PullRequest import PullRequest
from socless_repo_updater.models import (
    FileUpdateSetupInfo,
    FileExistence,
    UpdatePRResult,
)


def init_github(ghe=False) -> Github:
    if ghe:
        domain = os.getenv("GHE_DOMAIN", "api.github.com")
        base_url = f"https://{domain}/api/v3"
        g = Github(base_url=base_url, login_or_token=os.getenv("GHE_TOKEN"))
    else:
        g = Github()
        # raise NotImplementedError()

    return g


def make_branch_name(name=""):
    branch_id = str(uuid.uuid4())
    name = f"{name}-" if name else ""
    branch_name = f"cli-{name}{branch_id}"[:39]
    return branch_name


def make_full_repo_name(repo, org="") -> str:
    if len(repo.split("/")) > 1:
        return repo
    elif not org:
        raise Exception("No org provided via separate arg OR via repo name")
    else:
        return f"{org}/{repo}"


def check_file_exists(gh_repo: Repository, file_path, branch_name) -> FileExistence:
    try:
        file_contents = gh_repo.get_contents(path=file_path, ref=branch_name)
        return FileExistence(
            gh_repo=gh_repo,
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
            elif "No commit found for the ref" in e.data["message"]:
                branch_exists = False
            else:
                print("404 uncaught")
                raise GithubException(e.status, e.data)

            return FileExistence(
                gh_repo=gh_repo,
                file_path=file_path,
                branch_exists=branch_exists,
                file_exists=False,
                file_contents=False,
            )
        else:
            raise GithubException(e.status, e.data)


def check_pr_exists(
    gh_repo: Repository,
    base_branch: str,
    head_branch: str,
) -> Union[bool, PullRequest]:
    for pull in gh_repo.get_pulls(state="open", sort="created", base=base_branch):
        if (
            pull.raw_data["base"]["ref"] == base_branch
            and pull.raw_data["head"]["ref"] == head_branch
        ):
            return pull
    return False


def setup_for_file_update(repo, org, file_path, head_branch, main_branch, ghe):
    g = init_github(ghe)
    repo_name = make_full_repo_name(repo, org)

    try:
        gh_repo = g.get_repo(repo_name)
    except UnknownObjectException as e:
        print(f"Unable to find repo {repo} in org {org}. {e}")
        raise Exception("No repo found")

    if not head_branch:
        head_branch = make_branch_name()
        print(f"new branch name: {head_branch}")
        file_existence_check = FileExistence(
            gh_repo,
            file_path,
            branch_exists=False,
            file_exists=False,
            file_contents=False,
        )
    else:
        # get file content from supplied branch
        file_existence_check = check_file_exists(
            gh_repo, file_path=file_path, branch_name=head_branch
        )

    if file_existence_check.file_exists:
        contentfile = file_existence_check.file_contents
    elif file_existence_check.branch_exists:
        # file doesn't exist, branch does
        raise FileNotFoundError(
            f"File {file_path} does not exist in branch {head_branch} for repo {repo}"
        )
    else:
        # branch does not exist, check if file exists on main, then create new branch from main
        file_query_main_branch = check_file_exists(
            gh_repo, file_path=file_path, branch_name=main_branch
        )
        if not file_query_main_branch.file_exists:
            raise VersionUpdateException(
                f"File {file_path} does not exist in branch {main_branch} for repo {repo}"
            )

        gh_source = gh_repo.get_branch(main_branch)
        gh_repo.create_git_ref(
            ref="refs/heads/" + head_branch, sha=gh_source.commit.sha
        )
        file_query = check_file_exists(
            gh_repo, file_path=file_path, branch_name=head_branch
        )
        contentfile = file_query.file_contents

    return FileUpdateSetupInfo(
        contentfile=contentfile,
        file_path=file_path,
        branch_name=head_branch,
        main_branch=main_branch,
        gh_repo=gh_repo,
    )


def update_file_and_pr(
    file_path: str,
    commit_msg: str,
    raw_content: str,
    file_sha: str,
    pr_title: str,
    pr_body: str,
    head_branch: str,
    main_branch: str,
    gh_repo: Repository,
) -> UpdatePRResult:
    gh_repo.update_file(
        file_path,
        message=commit_msg,
        content=raw_content,
        sha=file_sha,
        branch=head_branch,
    )

    pr = check_pr_exists(
        gh_repo=gh_repo, base_branch=main_branch, head_branch=head_branch
    )

    if isinstance(pr, PullRequest):
        result_msg = f"PR already exists: {pr.number}"
    else:
        pr = gh_repo.create_pull(
            title=pr_title,
            body=pr_body,
            base=main_branch,
            head=head_branch,
        )
        result_msg = f"New PR created: {pr.number}"

    return UpdatePRResult(pr=pr, result_msg=result_msg)


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
            elif k in rtn_dct and type(v) != type(rtn_dct[k]):
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


def check_release_exists(repo: str, org: str, release: str, ghe=False):
    g = init_github(ghe=ghe)
    gh_repo = g.get_repo(full_name_or_id=f"{org}/{repo}")

    try:
        release_query = gh_repo.get_release(release)
        # release_query.tag_name is 1.1.0
        return release_query
    except GithubException as e:
        print(f"Release {release} not found for {org}/{repo}")
        print(e)
        return False
