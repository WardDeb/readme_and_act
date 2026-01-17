from github import Github
from pydantic import BaseModel, field_validator
from typing import Optional, Any
from datetime import datetime
from pathlib import Path
import re
import os
import logging

# All possible event types from github
ALLOWED_EVENT_TYPES = [
    "CreateEvent",
    "DeleteEvent",
    "DiscussionEvent",
    "ForkEvent",
    "GollumEvent",
    "IssueCommentEvent",
    "IssuesEvent",
    "MemberEvent",
    "PublicEvent",
    "PullRequestEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
    "PushEvent",
    "ReleaseEvent",
    "WatchEvent",
]

# Wanted event types to display
WANTED_EVENT_TYPES = {
    "DiscussionEvent": "📣 contributed to discussion in",
    "ForkEvent": "🥄 forked",
    "IssuesEvent": "🐞 made/updated issue in",
    "PublicEvent": "🎉 released",
    "PullRequestEvent": "🪢 PR'ed to",
    "PushEvent": "🫸 pushed commit(s) to" ,
    "ReleaseEvent": "🎉 released",
}

# file markers
FILE_MARKERS = {
    "start_marker": "<!--START_SECTION:raa-->",
    "end_marker": "<!--END_SECTION:raa-->"
}

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

    def __init__(self, username=None, filename="README.md", github_token=None, test=False, num_events=5, gh_repo=None):
        # Initialize logging first so methods called during __init__ can use self.logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing UpdateReadme instance")

        self.g = Github(github_token) if github_token else Github()
        self.user = self.g.get_user(username)
        self.username = username
        self.filename = Path(filename)
        self.test = test
        self.num_events = num_events
        self.gh_repo = gh_repo
        self.validate_filename()
        self.logger.info("Initialized UpdateReadme instance")


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
        # Update the file on GitHub
        if self.test:
            self.logger.info("Testing mode. Not committing.")
            return

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
        
        try:
            repo.update_file(
                path=file_path,
                message=commit_msg,
                content=updated_content,
                sha=contents.sha,
                committer={"name": commit_name, "email": commit_email}
            )
            self.logger.info(f"Updated {file_path} in {repo_name} successfully.")
        except Exception as e:
            self.logger.error(f"Failed to update file on GitHub: {e}")
            raise RuntimeError(f"Failed to update file on GitHub: {e}")
