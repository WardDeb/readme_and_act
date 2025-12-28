import argparse
import os
import raa.raa as rp

def main():
    parser = argparse.ArgumentParser(description="Collect GitHub activity and update README file.")
    
    default_username = os.getenv('INPUT_GH_USERNAME') or os.getenv('GH_USERNAME')
    default_filename = os.getenv('INPUT_TARGET_FILE', 'README.md')
    default_max_lines = int(os.getenv('INPUT_MAX_LINES', '5'))
    default_commit_name = os.getenv('INPUT_COMMIT_NAME', 'github-actions[bot]')
    default_commit_email = os.getenv('INPUT_COMMIT_EMAIL', '41898282+github-actions[bot]@users.noreply.github.com')
    default_commit_msg = os.getenv('INPUT_COMMIT_MSG', 'More work found!')
    default_repo = os.getenv('GITHUB_REPOSITORY')  # Automatically set by GitHub Actions
    github_token = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')  # For authentication
    
    parser.add_argument('--username', type=str, default=default_username, help='GitHub username to fetch activity for')
    parser.add_argument('--filename', type=str, default=default_filename, help='README file to update')
    parser.add_argument('--max-lines', type=int, default=default_max_lines, help='Maximum number of activity lines to show')
    parser.add_argument('--commit-name', type=str, default=default_commit_name, help='Name of the committer')
    parser.add_argument('--commit-email', type=str, default=default_commit_email, help='Email of the committer')
    parser.add_argument('--commit-msg', type=str, default=default_commit_msg, help='Commit message')
    parser.add_argument('--repo', type=str, default=default_repo, help='Repository name in format owner/repo')
    args = parser.parse_args()

    if not args.username:
        raise ValueError("GitHub username is required. Set INPUT_GH_USERNAME environment variable or use --username argument.")
    
    if not args.repo:
        raise ValueError("Repository name is required. Set GITHUB_REPOSITORY environment variable or use --repo argument.")

    p = rp.UpdateReadme(args.username, args.filename, github_token=github_token)
    p.validate_filename()
    p.fetch_activity()
    p.construct_readme_section(num_events=args.max_lines)
    
    # Display the parsed events
    for event in p.parsed_events:
        print(f"{event}")
    
    # Update file and commit/push changes
    p.update_file(
        commit_email=args.commit_email,
        commit_msg=args.commit_msg,
        commit_name=args.commit_name,
        repo_name=args.repo
    )