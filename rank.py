import guessit
import re
from math import log, exp

average = lambda v: sum(v)/len(v)

VIDEO_SCORE = {
    'language' : {
        "$weight" : 3,
        "$missing" : 0.9,
        "$other" : 0.1,

        "$reduce" : max,

        "en"  : 10,
    },
    'other' : {
        "$weight" : 3,
        "$missing" : 0.6,
        "$other" : 0.6,
        "$reduce" : average,

        "Fix" : 1.0,
        "Proper" : 1.0,
        "Audio Fixed" : 1.0,
        "Sync Fixed" : 1.0,
        "Reencoded" : 0.8,
        "Remux" : 0.8,
        "Retail" : 0.8,
        "Dual Audio" : 0.6,
        "XXX" : 0.0,
        "NTSC" : 0.2,
        "SECAM" : 0.0,
        "PAL" : 0.2,
        "Screener" : 0.0,
        "Line Dubbed" : 0.4,
        "Mic Dubbed" : 0.2,
        "Micro HD" : 0.2,
        "Low Definition" : 0.1,
        "HD": 0.6,
        "Full HD" : 0.6,
        "Ultra HD" : 0.6,
        "Trailer" : 0.0,
        "Line Audio" : 0.4,
        "Converted" : 0.3,
        "Mux" : 0.5,
    },
    'format' : {
        "$weight"  : 2,
        "$missing" : 0.8,
        "$other" : 0.6,

        "VHS": 0.1,
        "Camera": 0.0, 
        "HD Camera": 0.0,
        "Telesync" : 0.0,
        "HD Telesync": 0.0,
        "Workprint" : 0.0,
        "Telecine" : 0.0,
        "HD Telecine" : 0.0,
        "Digital TV" : 0.8,
        "DVD" : 0.7,
        "Video on Demand": 0.7,
        "Web" : 0.8,
        "Blu-ray" : 1.0,
        "Ultra HDTV" : 1.0,

    },
    'container' : {
        "$weight"  : 1,
        "$missing" : 0.6,
        "$other"   : 0.5,

        "mp4"      : 1,
        "avi"      : 0.3,
        "mkv"      : 0.8,
    },
    'screen_size': {
        '$weight'  : 2,
        "$missing" : 0.5,
        "$other"   : 0.4,

        "720p"     : 1.0,
        "1080p"    : 0.9,
        "4K"       : 0.7,
    },
    'video_codec' : {
        '$weight'  : 3,
        '$missing' : 0.2,
        '$other'   : 0.3,

        'H.264'    : 1.0,
        'H.265'    : 1.0,
        "RealVideo" : 0.1,
        "MPEG-2" : 0.2,
        "DivX" : 0.1,
        "Xvid" : 0.1,
        "VC-1" : 0.1,
        "VP7" : 0.2,
        "VP8" : 0.3,
        "VP9" : 0.4,
        "H.263" : 0.3,
    },
    'audio_codec' : {
        "$weight" : 1,
        "$missing" : 0.8,
        "$other" : 0.8,
        "$reduce": max,

        'AC3' : 1.0,
        "MP3" : 0.9,
        "MP2" : 0.7,
        "Dolby Digital" : 1.0,
        "Dolby Atmos" : 1.0,
        "AAC" : 1.0,
        "DTS" : 1.0,
        "Opus" : 0.7,
        "Vorbis" : 0.6,
        "PCM" : 0.1,
        "LPCM" : 0.1
    },
    "edition" : {
        "$weight" : 1,
        "$missing" : 1,
        "$other" : 1,
        "$reduce" : average,

        "Director's Definitive Cut" : 0.8,
        "Director's Cut" : 0.8,
        "IMAX" : 0.7,        
    },
    "release_group" : {
        "$weight" : 1,
        "$missing" : 0.1,
        "$other" : 0.8,
        "IMMERSE" : 0.9,
    },
    'subtitle_language' : {
        '$weight' : 1,
        '$missing' : 0.9,
        "$other" : 0,
        "$reduce" : max,

        "en" : 1.0,
    }
}

sum_weights = sum([VIDEO_SCORE[x]['$weight'] for x in VIDEO_SCORE])

release_group_re = re.compile(r"(.*) *\[.*\]")

def score(record) -> float:
    def score_helper(v, data):
        x = str(v)
        return data[x] if x in data else data['$other']
    info = record['extra']

    sum_log = 0
    for attr, data in VIDEO_SCORE.items():
        weight = data['$weight']
        if attr not in info:
            score = data['$missing']
        else:
            val = info[attr]

            if attr == "release_group":
                m = release_group_re.match(val)
                if m:
                    val = m.group(1)

            if isinstance(val, list):
                avg_func = data['$reduce']
                s = []
                for v in val:
                    s.append(score_helper(v, data))

                score = avg_func(s)
            else:
                score = score_helper(val, data)
        if score <= 0.0: # XXX comparing floats... should be OK in this instance
            return 0.0   # if any score is 0 - we want to reject this file
        sum_log += log(score)*weight
    return exp(sum_log/sum_weights)

