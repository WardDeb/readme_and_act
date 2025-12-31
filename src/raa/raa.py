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

    def __init__(self, username=None, filename="README.md", github_token=None):
        # Initialize logging first so methods called during __init__ can use self.logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing UpdateReadme instance")

        self.g = Github(github_token) if github_token else Github()
        self.user = self.g.get_user(username)
        self.username = username
        self.filename = Path(filename)
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
        replace_pattern = False
        with self.filename.open('r') as f:
            for line in f:
                if "<!--START_SECTION:raa-->" in line:
                    replace_pattern = True
                    break
        if not replace_pattern:
            self.logger.error("The README file must contain the pattern '<!--START_SECTION:raa-->' to identify where to insert activity.")
            raise ValueError("The README file must contain the pattern '<!--START_SECTION:raa-->' to identify where to insert activity.")

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
    
    def construct_readme_section(self, num_events=5):
        '''
        Parse through the selected events, collate where needed, and collect them.
        '''
        self.logger.info(f"Constructing README section with top {num_events} events")
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
            if len(parsed_events) == num_events:
               break
        self.parsed_events = []
        for ix, (_, event) in enumerate(parsed_events.items()):
            self.parsed_events.append(f"{ix+1}. " + event.replace("|", " "))
        self.logger.info(f"README section constructed, {len(self.parsed_events)} events after collation.")

    def update_file(self, commit_email, commit_msg, commit_name, repo_name):
        '''
        Update the target file with the parsed events between the pattern markers,
        then commit and push the changes
        '''
        # Read the file content from GitHub
        repo = self.g.get_repo(repo_name)
        file_path = str(self.filename)
        
        try:
            contents = repo.get_contents(file_path)
            current_content = contents.decoded_content.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Could not fetch {file_path} from {repo_name}: {e}")
            raise FileNotFoundError(f"Could not fetch {file_path} from {repo_name}: {e}")
        
        # Define the pattern markers
        start_marker = "<!--START_SECTION:raa-->"
        end_marker = "<!--END_SECTION:raa-->"
        
        # Create the new section content
        new_section = "\n".join(self.parsed_events)
        
        # Replace content between markers
        pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        replacement = f"{start_marker}\n{new_section}\n{end_marker}"
        updated_content = re.sub(pattern, replacement, current_content, flags=re.DOTALL)
        
        # Update the file on GitHub
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



