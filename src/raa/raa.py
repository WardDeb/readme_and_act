from github import Github, InputGitAuthor
from pydantic import BaseModel, field_validator
from typing import Optional, Any
from datetime import datetime
from pathlib import Path
import re
import os
import logging
from raa.defaults import ALLOWED_EVENT_TYPES as DEFAULT_ALLOWED_EVENT_TYPES, \
                        WANTED_EVENT_TYPES as DEFAULT_WANTED_EVENT_TYPES, \
                        FILE_MARKERS as DEFAULT_FILE_MARKERS

ALLOWED_EVENT_TYPES = DEFAULT_ALLOWED_EVENT_TYPES
WANTED_EVENT_TYPES = DEFAULT_WANTED_EVENT_TYPES
FILE_MARKERS = DEFAULT_FILE_MARKERS

class GithubEvent(BaseModel):
    type: str
    actor: Optional[str] = None
    repo: Optional[str] = None
    created_at: datetime
    payload: Any
    
    @field_validator('type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Event type '{v}' is not in allowed types: {ALLOWED_EVENT_TYPES}")
        return v

class UpdateReadme:
    '''
    General class for an UpdateReadme instance.
    '''

    def __init__(self, username=None, filename="README.md", github_token=None, test=False, num_events=5, gh_repo=None, cfg=None):
        # Initialize logging first so methods called during __init__ can use self.logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing UpdateReadme instance")
        global ALLOWED_EVENT_TYPES, WANTED_EVENT_TYPES, FILE_MARKERS

        if github_token:
            self.logger.info("Using authenticated GitHub client")
            self.g = Github(github_token)
        else:
            self.logger.warning("No GitHub token provided - using unauthenticated client (limited API access)")
            self.g = Github()
        self.user = self.g.get_user(username)
        self.username = username
        self.filename = Path(filename)
        self.test = test
        self.num_events = num_events
        self.gh_repo = gh_repo
        self.validate_filename()
        self.logger.info("Initialized UpdateReadme instance")
        self.ignore_repos = []

        if cfg:
            import tomllib
            self.logger.info(f"Loading configuration from {cfg}")
            with open(cfg, "rb") as f:
                config_data = tomllib.load(f)

            _allowed = config_data.get("ALLOWED_EVENT_TYPES")
            if _allowed is not None:
                ALLOWED_EVENT_TYPES = _allowed
                self.logger.info(f"Overridden ALLOWED_EVENT_TYPES with {ALLOWED_EVENT_TYPES}")

            _wanted = config_data.get("WANTED_EVENT_TYPES")
            if _wanted is not None:
                WANTED_EVENT_TYPES = _wanted
                self.logger.info(f"Overridden WANTED_EVENT_TYPES with {WANTED_EVENT_TYPES}")

            _markers = config_data.get("FILE_MARKERS")
            if _markers is not None:
                FILE_MARKERS = _markers
                self.logger.info(f"Overridden FILE_MARKERS with {FILE_MARKERS}")
            
            _ignore = config_data.get("IGNORE_REPOS")
            if _ignore is not None:
                self.ignore_repos = _ignore
                self.logger.info(f"Loaded IGNORE_REPOS: {self.ignore_repos}")

        else:
            self.logger.info("Using default configuration")

    def validate_filename(self):
        '''
        Validate that the filename is a markdown file.
        '''
        self.logger.info(f"Validating filename: {self.filename}")
        if not self.filename.exists():
            self.logger.error(f"The file {self.filename} does not exist.")
            raise FileNotFoundError(f"The file {self.filename} does not exist.")
        replace_start = False
        replace_end = False
        with self.filename.open('r') as f:
            for line in f:
                if FILE_MARKERS["start_marker"] in line:
                    replace_start = True
                if FILE_MARKERS["end_marker"] in line:
                    replace_end = True
                if replace_start and replace_end:
                    break
        if not (replace_start and replace_end):
            self.logger.error(f"The README file must contain a start pattern {FILE_MARKERS['start_marker']} and end pattern {FILE_MARKERS['end_marker']} to identify where to insert activity.")
            raise ValueError(f"The README file must contain a start pattern {FILE_MARKERS['start_marker']} and end pattern {FILE_MARKERS['end_marker']} to identify where to insert activity.")

    def fetch_activity(self):
        '''
        Fetch recent Github activity
        '''
        self.logger.info(f"Fetching recent activity for user: {self.username}")
        events = self.user.get_events()
        edict = {}

        for event in events:
            if event.type in WANTED_EVENT_TYPES:
                event_data = GithubEvent(
                    type=event.type,
                    actor=event.actor.login if event.actor else None,
                    repo=event.repo.name if event.repo else None,
                    created_at=event.created_at,
                    payload=event.payload
                )
                if event_data.repo in self.ignore_repos:
                    self.logger.info(f"Ignoring event from repo: {event_data.repo}")
                    continue
                edict[event.id] = event_data
        self.events = edict
        self.logger.info(f"Fetched {len(self.events)} (whitelisted) events")
    
    def construct_readme_section(self):
        '''
        Parse through the selected events, collate where needed, and collect them.
        '''
        self.logger.info(f"Constructing README section with top {self.num_events} events")
        parsed_events = {}
        for event_id, event in self.events.items():
            # Get repo and construct URL
            repo_url = f"https://github.com/{event.repo}"
            repo_name = event.repo
            if event.repo not in parsed_events:
                parsed_events[repo_name] = f"{WANTED_EVENT_TYPES[event.type]}|[{repo_name}]({repo_url})"
            else:
                if WANTED_EVENT_TYPES[event.type] not in parsed_events[repo_name]:
                    eventstr, repostr = parsed_events[repo_name].split("|")
                    eventstr += f", {WANTED_EVENT_TYPES[event.type]}"
                    parsed_events[repo_name] = f"{eventstr}|{repostr}"
            if len(parsed_events) == self.num_events:
               break
        self.parsed_events = []
        for ix, (_, event) in enumerate(parsed_events.items()):
            self.parsed_events.append(f"{ix+1}. " + event.replace("|", " "))
        self.logger.info(f"README section constructed, {len(self.parsed_events)} events after collation.")

    def update_file(self):
        '''
        Update the target file with the parsed events between the pattern markers,
        then commit and push the changes
        '''
        commit_email = "41898282+github-actions[bot]@users.noreply.github.com"
        commit_name = "github-actions[bot]"
        commit_msg = "More work found!"
        repo_name = self.gh_repo
        if not repo_name:
            self.logger.error("No repo_name provided.")
            raise ValueError("No repo_name provided.")
        self.logger.info(
            f"github info provided: commit_email={commit_email}, commit_name={commit_name}, commit_msg={commit_msg}, repo_name={repo_name}"
        )

        # Read the file content from GitHub
        repo = self.g.get_repo(repo_name)
        file_path = str(self.filename)
        
        try:
            contents = repo.get_contents(file_path)
            current_content = contents.decoded_content.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Could not fetch {file_path} from {repo_name}: {e}")
            raise FileNotFoundError(f"Could not fetch {file_path} from {repo_name}: {e}")
        
        # Create the new section content
        new_section = "\n".join(self.parsed_events)
        
        # Replace content between markers
        pattern = f"{re.escape(FILE_MARKERS["start_marker"])}.*?{re.escape(FILE_MARKERS["end_marker"])}"
        replacement = f"{FILE_MARKERS["start_marker"]}\n{new_section}\n{FILE_MARKERS["end_marker"]}"
        updated_content = re.sub(pattern, replacement, current_content, flags=re.DOTALL)

        self.logger.info(f"Replaced content is: {replacement}")

        if updated_content == current_content:
            self.logger.info("No changes detected in the README section. Not committing.")
            return
        
        if not self.test:
            try:
                committer = InputGitAuthor(commit_name, commit_email)
                repo.update_file(
                    path=file_path,
                    message=commit_msg,
                    content=updated_content,
                    sha=contents.sha,
                    committer=committer
                )
                self.logger.info(f"Updated {file_path} in {repo_name} successfully.")
            except Exception as e:
                self.logger.error(f"Failed to update file on GitHub: {e}")
                raise RuntimeError(f"Failed to update file on GitHub: {e}")
