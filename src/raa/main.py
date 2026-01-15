import argparse
import raa.raa as rp
import os

def main():
    parser = argparse.ArgumentParser(description="Collect GitHub activity and update README file.")

    parser.add_argument('--username', type=str, required=False, help='GitHub username to fetch activity for')
    parser.add_argument('--filename', type=str, required=False, help='file to update')
    parser.add_argument('--max_lines', type=int, default=5, help='Maximum number of activity lines to show')
    parser.add_argument('--repo', default=None, required=False, help='Repository name to commit changes to. Defaults to github.com/username/username')
    parser.add_argument('--test', action='store_true', help='Run in test mode without committing changes')
    args = parser.parse_args()

    if not args.username:
        args.username = os.getenv('GH_USERNAME')
    if not args.filename:
        args.filename = os.getenv('FILE_NAME', 'README.md')
    if os.getenv('MAX_LINES'):
        args.max_lines = int(os.getenv('MAX_LINES'))
    if not args.repo:
        args.repo = os.getenv('REPO_NAME')
    
    p = rp.UpdateReadme(
        username = args.username,
        filename = args.filename,
        test = args.test,
        num_events = args.max_lines,
        gh_repo = args.repo
    )
    p.fetch_activity()
    p.construct_readme_section()
    p.update_file()
