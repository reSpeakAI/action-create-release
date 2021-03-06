from typing import List
from github import Repository, GitRelease
from github.WorkflowRun import WorkflowRun
import re
from functools import cmp_to_key


def get_running_workflows(repo: Repository,
                          shas: List[str] = [],
                          workflow_ids: List[int] = [],
                          branches: List[str] = []
                          ) -> List[WorkflowRun]:
    running_workflows = []

    # Filter by status
    running_workflows.extend([x for x in repo.get_workflow_runs() if x.status in ['queued', 'in_progress']])

    # Filter by branches
    if branches:
        running_workflows = [x for x in running_workflows if x.head_branch in branches]

    # Filter by specific workflow ids instead of all
    if workflow_ids:
        running_workflows = [x for x in running_workflows if x.workflow_id in workflow_ids]

    # Filter by specific shas
    if shas:
        running_workflows = [x for x in running_workflows if x.head_sha in shas]

    return running_workflows


def get_previous_version(repo: Repository) -> str | None:
    """Return the most recent version tag found"""
    # Look at releases to find the previous version
    releases = [r.tag_name for r in list(repo.get_releases())]

    def sort_semver(r1, r2):
        """
        Sorts in descending semver order, so highet version first.
        Example Ordering:
            v2.0.0
            v1.9.10-build.20
            v1.9.10-build.19
            v1.9.10-build.0
            v1.9.10
            v1.9.9-build.4
            v1.9.9
        Return negative value for r1 before r2, postive for r1 after r2, 0 for equal
        Example Input/Output:
            r1=v1.0.0, r2=v2.0.0, result should return positive
            r1=v2.0.0-build.0, r2=v2.0.0, result should return negative
            r1=v2.0.0-build.0, r2=v2.0.1, result should return positive
        """

        # Official semantic version regex from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
        reg = re.compile(
            r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')

        # Strip out the v in the version number and match it to the regex
        match1 = reg.match(r1.replace('v', ''))
        match2 = reg.match(r2.replace('v', ''))

        # If one of these releases is not a semver release then just skip comparing
        if not r2:
            return -1

        if not r1:
            return 1

        # Compare the semver versions and find the highest version
        cmp_major = int(match2['major']) - int(match1['major'])
        if cmp_major != 0:
            return cmp_major

        cmp_minor = int(match2['minor']) - int(match1['minor'])
        if cmp_minor != 0:
            return cmp_minor

        cmp_patch = int(match2['patch']) - int(match1['patch'])
        if cmp_patch != 0:
            return cmp_patch

        cmp_build = int((match2['prerelease'] or '.-1').split('.')[1]) - int((match1['prerelease'] or '.-1').split('.')[1])
        if cmp_build == 0:
            print(f'Warning: found equal release versions:\n\tr1:{r1}\n\tr2:{r2}')

        return cmp_build

    # Sort releases by created date, most recent first
    releases.sort(key=cmp_to_key(sort_semver))

    return releases[0] if releases else None


def bump_version(previous_version: str, bump_type: str, build_name: str) -> str:
    default = 'v0.0.1'

    # Return the default if no previous version found
    if not previous_version:
        if bump_type == 'build':
            return f'{default}-{build_name}.0'
        else:
            return default

    # Official semantic version regex from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    reg = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')
    # Strip out the v in the version number and match it to the regex
    match = reg.match(previous_version.replace('v', ''))
    assert match

    if bump_type == 'build':
        build_meta = match['prerelease']
        build_count = (build_meta or '.-1').split('.')[1]
        increment_bc = int(build_count) + 1
        current_version = f'{match["major"]}.{match["minor"]}.{match["patch"]}-{build_name}.{increment_bc}'
    elif bump_type == 'patch':
        patch = int(match['patch']) + 1
        current_version = f'{match["major"]}.{match["minor"]}.{patch}'
    elif bump_type == 'minor':
        minor = int(match['minor']) + 1
        current_version = f'{match["major"]}.{minor}.0'
    elif bump_type == 'major':
        major = int(match['major']) + 1
        current_version = f'{major}.0.0'

    return f'v{current_version}'


def create_release(repo: Repository, version: str, sha: str, bump_type: str) -> GitRelease:
    # Get changelog
    # TODO
    change_log = ''

    # Create the tag and release
    if bump_type == 'build':
        return repo.create_git_tag_and_release(
            version,
            version,
            version,
            change_log,
            sha,
            'commit',
            prerelease=True,
        )
    else:
        return repo.create_git_tag_and_release(
            version,
            version,
            version,
            change_log,
            sha,
            'commit',
        )
