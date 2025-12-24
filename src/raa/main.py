import argparse
import raa.raa as rp

def main():
    parser = argparse.ArgumentParser(description="Collect GitHub activity and update README file.")
    parser.add_argument('--username', type=str, required=True, help='GitHub username to fetch activity for')
    parser.add_argument('--filename', type=str, default='README.md', help='README file to update')
    args = parser.parse_args()


    p = rp.UpdateReadme(args.username, args.filename)
    p.validate_filename()
    p.fetch_activity()
    p.construct_readme_section()
    for event in p.parsed_events:
        print(f"{event}")