import raa.raa as rp

p = rp.UpdateReadme("WardDeb")
p.fetch_activity()
p.construct_readme_section()
for event in p.parsed_events:
    print(f"{event}")