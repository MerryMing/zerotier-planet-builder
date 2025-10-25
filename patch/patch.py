import os
import json
import glob
from re import M


def get_moon():
    with open("/var/lib/zerotier-one/moon.json", "r") as f:
        moon = json.load(f)
        return moon


def get_patch():
    with open("/app/patch/patch.json", "r") as f:
        return json.load(f)


def patch():
    moon = get_moon()
    patch = get_patch()

    identity = moon["roots"][0]["identity"]
    moon["roots"][0]["stableEndpoints"] = patch["stableEndpoints"]

    # 修改moon  
    with open("/var/lib/zerotier-one/moon.json", "w") as f:
        f.write(json.dumps(moon,sort_keys=True, indent=2))

    #print("修改后的moon")
    #print(moon)

    # 修改world
    moon["roots"][0]["stableEndpoints"] = get_patch()["stableEndpoints"]
    text = f"""// Los Angeles
	roots.push_back(World::Root());
	roots.back().identity = Identity("{identity}");
"""

    for i in get_patch()["stableEndpoints"]:
        text += f'\n        roots.back().stableEndpoints.push_back(InetAddress("{i}"));'

    # 生成文件
    with open("/app/patch/mkworld.cpp", "r") as cpp:
        world = "".join(cpp.readlines())
        world = world.replace("//__PATCH_REPLACE__", text)

    # Try to find where the ZeroTier source places mkworld.cpp. Historically
    # it was under /opt/ZeroTierOne/attic/world/, but newer versions may use
    # /opt/ZeroTierOne/world/ or another location. Search the repo first and
    # fall back to the historical path (creating directories if needed).
    candidates = glob.glob('/opt/ZeroTierOne/**/mkworld.cpp', recursive=True)
    if candidates:
        target = candidates[0]
        target_dir = os.path.dirname(target)
    else:
        target_dir = '/opt/ZeroTierOne/attic/world'
        target = os.path.join(target_dir, 'mkworld.cpp')
        # ensure directory exists so open(..., 'w') won't fail
        os.makedirs(target_dir, exist_ok=True)

    with open(target, "w") as cpp:
        cpp.write(world)


if __name__ == '__main__':
    patch()
