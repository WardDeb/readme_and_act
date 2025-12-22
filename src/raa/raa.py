from github import Github
from pydantic import BaseModel, field_validator
from typing import Optional, Any
from datetime import datetime

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
WANTED_EVENT_TYPES = [
    "DiscussionEvent",
    "ForkEvent",
    "IssuesEvent",
    "PublicEvent",
    "PullRequestEvent",
    "PushEvent",
    "ReleaseEvent"
]

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

    def __init__(self, username=None):
        self.g = Github()
        self.user = self.g.get_user(username)

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
    
    def construct_readme_section(self):
        '''
        Parse through the selected events, collate where needed, and collect them.
        '''

