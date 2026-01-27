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
    "IssuesEvent": "🐞 made/updated issue(s) in",
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