from webcutter.dplex import PlexInterface
from webcutter.dcut import CutterInterface

from simplemenu.menu import Menu
from pprint import pprint as pp
import time
import sys

clear = lambda: print("\033[H\033[J", end="")

fileserver = '192.168.15.10'
baseurl = 'http://192.168.15.10:32400'
token = '7YgcyPLqGVM-PVxq2QVo'

plex = PlexInterface(baseurl,token)
cutter = CutterInterface(fileserver)

clear()
print('WebCutter Frame Demo')
print("="*20)

movie = plex._plex.library.section('Plex Recordings').get('Monty Pythons wunderbare Welt der Schwerkraft')
pp(plex.movie_rec(movie))

try:
    print(f"\n---- '{movie.title}' ---")
    cutter.frame(movie, '00:15:19')
except Exception as err:
    print()
    print(str(err))
