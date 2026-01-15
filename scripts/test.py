import raa.raa as rp

p = rp.UpdateReadme(
    username = "WardDeb",
    filename = "README.md",
    github_token = None,
    test = True,
    num_events = 5,
    gh_dict = {
        "commit_email": "",
        "commit_name": "",
        "commit_msg": "chore: update README with recent activity",
        "repo_name": "WardDeb/README_and_Act"
    }
)
p.fetch_activity()
p.construct_readme_section()
for event in p.parsed_events:
    print(f"{event}")
p.update_file()