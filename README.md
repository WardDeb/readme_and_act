# readme_and_act
an action to display recent activity on your profile, python-based as I don't know javascript.
Setup is inspired by both [recent-activity](https://github.com/Readme-Workflows/recent-activity/blob/main/action.yml) and [github activity readme](https://github.com/jamesgeorge007/github-activity-readme).

Note that this is work in progress, prone to changes.

## Setup

The action runs on a github repository, and will update a file (specified as 'FILE_NAME', see below) in that repository. The file needs to contain the following markers:
```
    <!--START_SECTION:raa-->
    <!--END_SECTION:raa-->
```

The action will replace the content between those markers with the inferred recent activity.

## Action template

This can be used as a template (will run every 30 minutes):

```yaml
name: Activity
on:
  schedule:
    - cron: "*/30 * * * *"
  workflow_dispatch:
jobs:
  build:
    name: Fetch latest activity
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: WardDeb/readme_and_act@main
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

The only required env variable is the GH_TOKEN, which is needed to commit the changes back to the repository.
Other (optional) variables are:

  - GH_USERNAME*: github username 
  - MAX_LINES: maximum number of lines to add in the readme (defaults to 5)
  - FILE_NAME: the actual file to be updated (has to contain the markers), defaults to README.md
  - REPO_NAME*: the repository to update. Defaults to <GH_USERNAME>/<GH_USERNAME>

Note that * marked variables are only relevant for testing, and are not relevant when running the action in a github workflow.

## Testing locally
To test locally, you can use [pixi](https://pixi.prefix.dev/latest/) and run:

```bash
pixi run test
```
