from github import Github
from pydantic import BaseModel, field_validator
from typing import Optional, Any
from datetime import datetime
from pathlib import Path

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

    def __init__(self, username=None, filename="README.md"):
        self.g = Github()
        self.user = self.g.get_user(username)
        self.filename = Path(filename)
        self.validate_filename()

    def validate_filename(self):
        '''
        Validate that the filename is a markdown file.
        '''
        if not self.filename.exists():
            raise FileNotFoundError(f"The file {self.filename} does not exist.")
        replace_pattern = False
        with self.filename.open('r') as f:
            for line in f:
                if "<!--START_SECTION:raa-->" in line:
                    replace_pattern = True
                    break
        if not replace_pattern:
            raise ValueError("The README file must contain the pattern '<!--START_SECTION:raa-->' to identify where to insert activity.")

    def fetch_activity(self):
        '''
        Fetch recent Github activity
        '''
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
    
    def construct_readme_section(self, num_events=5):
        '''
        Parse through the selected events, collate where needed, and collect them.
        '''
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

