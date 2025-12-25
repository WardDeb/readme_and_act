import argparse
import os
import raa.raa as rp

def main():
    parser = argparse.ArgumentParser(description="Collect GitHub activity and update README file.")
    
    default_username = os.getenv('INPUT_GH_USERNAME') or os.getenv('GH_USERNAME')
    default_filename = os.getenv('INPUT_TARGET_FILE', 'README.md')
    default_max_lines = int(os.getenv('INPUT_MAX_LINES', '5'))
    
    parser.add_argument('--username', type=str, default=default_username, help='GitHub username to fetch activity for')
    parser.add_argument('--filename', type=str, default=default_filename, help='README file to update')
    parser.add_argument('--max-lines', type=int, default=default_max_lines, help='Maximum number of activity lines to show')
    args = parser.parse_args()

    if not args.username:
        raise ValueError("GitHub username is required. Set INPUT_GH_USERNAME environment variable or use --username argument.")

    p = rp.UpdateReadme(args.username, args.filename)
    p.validate_filename()
    p.fetch_activity()
    p.construct_readme_section(num_events=args.max_lines)
    for event in p.parsed_events:
        print(f"{event}")