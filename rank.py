import PTN
import os.path


QUALITY_SCORE = {
        "web-dl": 10,
        "webdl" : 10,
        "hdtv"  : 6,
        "webrip": 6,
        }

RESOLUTION_SCORE = {
        "2160p" : 5,
        "1080p" : 8,
        "480p" : 7,
        "720p" : 10, # prefer 720p
        }

GROUP_SCORE = {
        "ntb" : 10,
        "kompost" : 9
        }

CODEC_SCORE = {
        "h.264" : 10,
        "h264" : 10,
        "h265" : 10,
        "h.265":10,
        "x264" : 9,
        "x265" : 9,
        "xvid" : 0, # we don't want xvid
        }


QUALITY_WEIGHT = 0.3
RESOLUTION_WEIGHT = 0.3
GROUP_WEIGHT = 0.1
CODEC_WEIGHT = 0.3

episodes = {}


import re
RE_VOL = re.compile("(.*)\.vol0.*") # XXX onlh needed to cleanup binsearch. Not needed in general
with open("binsearch.txt", "r") as f:
    for l in f.readlines():
        n = os.path.splitext(l.strip())[0]
        m = RE_VOL.match(n)
        if m:
            n = m.group(1)

        p = PTN.parse(n)
        if 'episode' not in p or 'season' not in p:
            continue
        title =  p['title'].lower()
        ep_num = p['episode']
        season_num = p['season']
        k = f"{title}/{season_num}x{ep_num}"
        if k not in episodes:
            episodes[k] = []

        episodes[k].append(p)

for k, ep in episodes.items():
    best = (-1,-1)
    for i,t in enumerate(ep):
        score = 0

        if 'codec' in t:
            codec = t['codec'].lower()
            score += CODEC_WEIGHT*CODEC_SCORE[codec]

        if 'group' in t:
            group = t['group'].lower()
            if group in GROUP_SCORE:
                score += GROUP_WEIGHT*GROUP_SCORE[group]

        if 'quality' in t:
           quality = t['quality'].lower()
           score += QUALITY_WEIGHT * QUALITY_SCORE[quality]

        if 'resolution' in t:
            resolution = t['resolution']
            score += RESOLUTION_WEIGHT * RESOLUTION_SCORE[resolution]

        if score > best[1]:
            best = i,score
    best_ep = ep[best[0]]
    best_score = best[1]
    print (k,score)

