# just_tbp/constants.py
from typing import Dict, Literal, Union

# Numerical Category IDs
AUDIO_MUSIC = 101
AUDIO_BOOKS = 102
AUDIO_SOUND_CLIPS = 103
AUDIO_FLAC = 104
AUDIO_OTHER = 199

VIDEO_MOVIES = 201
VIDEO_MOVIES_DVDR = 202
VIDEO_MUSIC_VIDEOS = 203
VIDEO_MOVIE_CLIPS = 204
VIDEO_TV_SHOWS = 205
VIDEO_HANDHELD = 206
VIDEO_HD_MOVIES = 207
VIDEO_HD_TV_SHOWS = 208
VIDEO_3D = 209
VIDEO_OTHER = 299

APPLICATION_WINDOWS = 301
APPLICATION_MAC = 302
APPLICATION_UNIX = 303
APPLICATION_HANDHELD = 304
APPLICATION_IOS = 305
APPLICATION_ANDROID = 306
APPLICATION_OTHER = 399

GAMES_PC = 401
GAMES_MAC = 402
GAMES_PSX = 403
GAMES_XBOX360 = 404
GAMES_WII = 405
GAMES_HANDHELD = 406
GAMES_IOS = 407
GAMES_ANDROID = 408
GAMES_OTHER = 499

OTHER_EBOOKS = 601
OTHER_COMICS = 602
OTHER_PICTURES = 603
OTHER_COVERS = 604
OTHER_PHYSIBLES = 605
OTHER_OTHER = 699

# Type alias for all valid numerical category IDs
CategoryId = Literal[
    101, 102, 103, 104, 199,
    201, 202, 203, 204, 205, 206, 207, 208, 209, 299,
    301, 302, 303, 304, 305, 306, 399,
    401, 402, 403, 404, 405, 406, 407, 408, 499,
    601, 602, 603, 604, 605, 699
]

# Type alias for categories used in top100 endpoint
Top100Category = Union[CategoryId, Literal["all", "recent"]]


CATEGORIES: dict[str, dict[str, int]] = {
    "audio": {
        "music": AUDIO_MUSIC,
        "audio_books": AUDIO_BOOKS,
        "sound_clips": AUDIO_SOUND_CLIPS,
        "FLAC": AUDIO_FLAC,
        "other": AUDIO_OTHER
    },
    "video": {
        "movies": VIDEO_MOVIES,
        "movies_dvdr": VIDEO_MOVIES_DVDR,
        "hd_movies": VIDEO_HD_MOVIES,
        "music_videos": VIDEO_MUSIC_VIDEOS,
        "movie_clips": VIDEO_MOVIE_CLIPS,
        "tv_shows": VIDEO_TV_SHOWS,
        "hd_tv_shows": VIDEO_HD_TV_SHOWS,
        "handheld": VIDEO_HANDHELD,
        "3d": VIDEO_3D,
        "other": VIDEO_OTHER
    },
    "application": {
        "windows": APPLICATION_WINDOWS,
        "mac": APPLICATION_MAC,
        "UNIX": APPLICATION_UNIX,
        "handheld": APPLICATION_HANDHELD,
        "IOS": APPLICATION_IOS,
        "android": APPLICATION_ANDROID,
        "other": APPLICATION_OTHER
    },
    "games": {
        "PC": GAMES_PC,
        "mac": GAMES_MAC,
        "psx": GAMES_PSX,
        "xbox360": GAMES_XBOX360,
        "wii": GAMES_WII,
        "handheld": GAMES_HANDHELD,
        "IOS": GAMES_IOS,
        "android": GAMES_ANDROID,
        "other": GAMES_OTHER
    },
    "other": {
        "ebooks": OTHER_EBOOKS,
        "comics": OTHER_COMICS,
        "pictures": OTHER_PICTURES,
        "covers": OTHER_COVERS,
        "physibles": OTHER_PHYSIBLES,
        "other": OTHER_OTHER
    }
}

DEFAULT_BASE_URL = "https://apibay.org"