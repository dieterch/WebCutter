from flask import Flask, request, redirect, url_for, render_template, send_file
from webcutter.dplex import PlexInterface
from webcutter.dcut import CutterInterface
import os
import time
import subprocess
from pprint import pprint as pp
from pprint import pformat as pf

fileserver = '192.168.15.10'
baseurl = 'http://192.168.15.10:32400'
token = '7YgcyPLqGVM-PVxq2QVo'

plex = PlexInterface(baseurl,token)
cutter = CutterInterface(fileserver)

app= Flask(__name__)

initial_section = plex.sections[0]
initial_movie_key = 5
initial_movie = initial_section.recentlyAdded()[initial_movie_key]

global selection
selection = { 
    'sections' : [s for s in plex.sections if s.type == 'movie'],
    'section' : initial_section,
    'movies' : initial_section.recentlyAdded(),
    'movie' : initial_movie,
    'pos_time' : '00:00:00',
    'frame'  : 'frame.jpg',
    'eta' : 0 
    }

# section related stuff
def _update_section(section_name, force=False):
    global selection
    #print(f"\n{selection['section'].title} != {section_name}, {(selection['section'].title != section_name)}") # beim ersten Aufruf kommt der Funktionsname zurück, nicht das Ergebnis => if clause ...
    if ((selection['section'].title != section_name) or force): 
        sec = plex.server.library.section(section_name)
        mvs = sec.recentlyAdded()
        default_movie = mvs[initial_movie_key]
        selection.update({ 'section' : sec, 'movies' : mvs, 'movie' : default_movie })
        #print(f"_update_selection if clause:\n{pf({k:v for k,v in selection.items() if k in ['section','movie','pos','frame']})}\n")
    else:
        pass
        #print(f"_update_selection else clause:\n{pf({k:v for k,v in selection.items() if k in ['section','movie','pos','frame']})}\n")
    return selection['section']    

@app.route("/update_section", methods=['POST'])
def update_section():
    global selection
    if request.method == 'POST':
        section_name = request.json['section']
        _update_section(section_name)        
        print(f"update_section: {pf(request.json)}")
        return redirect(url_for('index'))

@app.route("/force_update_section")
def force_update_section():
    global selection
    _update_section(selection['section'].title, force=True)        
    print(f"force_update_section.")
    return 'force update section'

@app.route("/sections")
def get_sections():
    global selection
    return { 'sections': [s.title for s in selection['sections']], 'section': selection['section'].title }

# movie related stuff
def _update_movie(movie_name):
    global selection
    sel_movie = selection['movies'][initial_movie_key]
    if movie_name != '':
        lmovie = [m for m in selection['movies'] if m.title == movie_name]
        if lmovie:
            sel_movie = lmovie[0]
    #print(sel_movie)
    selection['movie'] = sel_movie
    return selection['movie']

@app.route("/movies")
def get_movies():
    global selection
    return { 'movies': [m.title for m in selection['movies']], 'movie': selection['movie'].title }

@app.route("/movie_info", methods=['POST'])
def set_movie_get_info():
    global selection
    if request.method == 'POST':
        section_name = request.json['section']
        movie_name = request.json['movie']
        if movie_name != '':
            s = _update_section(section_name)
            m = _update_movie(movie_name)
            m_info = { 'movie_info': plex.movie_rec(m) }
        else:
            if section_name == '':
                s = _update_section('Plex Recordings')
            m = _update_movie('')
            m_info = { 'movie_info': plex.movie_rec(m) }
            #m_info = { 'movie_info': { 'duration': 0 } }
        print(f"\nmovie_info: {request.json} -> \n{pf(m_info)}")
        return m_info       

@app.route("/frame", methods=['POST'])
def get_frame():
    global selection
    if request.method == 'POST':
        pos_time = request.json['pos_time']
        movie_name = request.json['movie_name']
        m = _update_movie(movie_name)
        try:
            pic_name = cutter.frame(m ,pos_time ,os.path.dirname(__file__) + "/static/")
            ret = { 'frame': url_for('static', filename=pic_name) }
        except subprocess.CalledProcessError as e:
            print(f"\nframe throws error:\n{str(e)}\n") 
            ret = { 'frame': url_for('static', filename='error.jpg') }
        finally:
            print(f"frame: {request.json} -> {ret}")
            return ret

@app.route("/pos")
def get_pos():
    global selection
    return { 'pos': selection['pos_time'] }

@app.route("/movie_cut_info")
def get_movie_cut_info():
    global selection
    m = selection['movie']
    dmin = m.duration / 60000
    apsc = cutter._apsc(m)
    eta_apsc = int((0.5 if not apsc else 0) * dmin)
    eta_cut =  int(0.7 * dmin)
    eta = eta_apsc + eta_cut
    selection['eta'] = eta
    #print(f"ETA={eta}")
    return { 'movie': m.title, 'eta': eta, 'eta_cut': eta_cut, 'eta_apsc': eta_apsc, 'apsc' : apsc }

@app.route("/cut", methods=['POST'])
def do_cut():
    global selection
    if request.method == 'POST':
        section_name = request.json['section']
        movie_name = request.json['movie_name']
        ss = request.json['ss']
        to = request.json['to']
        inplace = request.json['inplace']
        s = _update_section(section_name)
        m = _update_movie(movie_name)        
        res = f"From section '{s}', cut '{m.title}', In {ss}, Out {to}, inplace={inplace}"
        print(res)
        try:
            time.sleep(1)
            res = cutter.cut(m,ss,to,inplace)
            m.analyze()
            #time.sleep(10)
            eta_est = selection['eta']
            res += f"ETA Estimation: {eta_est}"
            return { 'result': res }
        except subprocess.CalledProcessError as e:
            print(str(e))
            return { 'result': str(e) }


@app.route("/")
def index():
    global selection
    host = request.headers.get('Host')
    return render_template('webcutter/index.html', host=host)

@app.route("/apple-touch-icon.png")
def get_icon():
    return send_file('static/apple-touch-icon.png', mimetype='image/png')

@app.route("/test")
def test():
    return render_template('test.html')

@app.route("/testmodal")
def testmodal():
    return render_template('testmodal.html')

if __name__ == '__main__':
    print('''
\033[H\033[J
******************************************
* WebCutter V0.01 (c)2022 Dieter Chvatal *
******************************************
''')
    app.run(use_reloader=True, host='0.0.0.0', port=5000, debug=True, threaded=False)
    #app.run(use_reloader=False, host='0.0.0.0', port=5000, debug=False, threaded=False) # um mount error(16): Device or resource busy Fehler zu vermeiden.
