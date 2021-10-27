import uuid
from typing import List, Optional, Union
from github.PullRequest import PullRequest
from github.Repository import Repository
from github import GithubException
from github.ContentFile import ContentFile
from dataclasses import dataclass

from socless_repo_updater.exceptions import UpdaterError


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
) -> Union[bool, PullRequest]:
    for pull in gh_repo.get_pulls(state="open", sort="created", base=base_branch):
        if (
            pull.raw_data["base"]["ref"] == base_branch
            and pull.raw_data["head"]["ref"] == head_branch
        ):
            return pull
    return False
