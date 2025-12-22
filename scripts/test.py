import raa.raa as rp

p = rp.UpdateReadme("WardDeb")
p.fetch_activity()
for _ in p.events:
    print(_)
    print(p.events[_])