from typing import Union, List
from dataclasses import dataclass
from github.Repository import Repository
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest


@dataclass
class FileExistence:
    gh_repo: Repository
    file_path: str
    branch_exists: bool = False
    file_exists: bool = False
    file_contents: Union[bool, ContentFile, List[ContentFile]] = False


@dataclass
class UpdateFileResults:
    gh_repo: Repository
    repo_name: str
    file_path: str
    branch_name: str
    file_updated: bool
    file_contents: bool = False


@dataclass
class UpdatePRResult:
    pr: Union[bool, PullRequest]
    result_msg: str


@dataclass
class FileUpdateSetupInfo:
    contentfile: Union[bool, ContentFile, List[ContentFile]]
    file_path: str
    branch_name: str
    main_branch: str
    gh_repo: Repository


@dataclass
class BumpDependencyResult:
    file_updated: bool
    message: str
    repo_name: str
    pull_request: Union[str, bool]
    setup_info: FileUpdateSetupInfo