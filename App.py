from flask import Flask, request, redirect, url_for, render_template
from webcutter.dplex import PlexInterface
from webcutter.dcut import CutterInterface
import os
import time
from pprint import pprint as pp

fileserver = '192.168.15.10'
baseurl = 'http://192.168.15.10:32400'
token = '7YgcyPLqGVM-PVxq2QVo'

plex = PlexInterface(baseurl,token)
cutter = CutterInterface(fileserver)
app= Flask(__name__)

selection = { 
    'section'  : 'Plex Recordings',
    'sections' : [s for s in plex.sections if s.type == 'movie'],
    'pos_time' : '00:00:00',
    'frame'  : '' 
    }

def update_section(section_name):
    global selection
    sec = plex.server.library.section(section_name)
    mvs = [m for m in sec.recentlyAdded()]
    default_movie = mvs[5]
    selection.update({ 'section' : sec, 'movies' : mvs, 'movie' : default_movie })
    return selection['section']    

def update_movie(movie_name):
    global selection
    m = [m for m in selection['movies'] if m.title == movie_name ] if movie_name != None else None
    selection['movie'] = m[0] if m else selection['movie']
    return selection['movie']

@app.route("/sections")
def sections():
    global selection
    return { 'sections': [s.title for s in selection['sections']], 'section': selection['section'].title }

@app.route("/movies")
def movies():
    global selection
    return { 'movies': [m.title for m in selection['movies']], 'movie': selection['movie'].title }

@app.route("/movie_info", methods=['POST'])
def movie_info():
    global selection
    if request.method == 'POST':
        #pp(request.json)
        movie_name = request.json['movie']
        if movie_name != '':
            m = update_movie(movie_name)
            m_i = plex.movie_rec(m)
            #pp(m_i)
            return { 'movie_info': m_i }
        else:
            return { 'movie_info': { 'duration':0 } }

@app.route("/load_pic", methods=['POST'])
def load_pic():
    global selection
    if request.method == 'POST':
        print("in '/load_pic', nach if request ...:")
        pp(request.json)
        pos_time = request.json['pos_time']
        movie_name = request.json['movie_name']
        m = update_movie(movie_name)
        if (pos_time != '' and movie_name != ''):
            pic_name = cutter.frame(m ,pos_time ,os.path.dirname(__file__) + "/static/")
            print("in '/load_pic', nach cutter. ...:")
            ret = url_for('static', filename=pic_name)
            pp(ret)
            return { 'pic_name': ret }
        else: 
            return { 'pic_name': '' }

@app.route("/pos")
def pos():
    global selection
    return { 'pos': selection['pos_time'] }

@app.route("/update", methods=['POST'])
def updateme():
    global selection
    if request.method == 'POST':
        print("in '/update':")
        pp(request.json)
        section_name = request.json['section']
        update_section(section_name)
        return redirect(url_for('index'))

@app.route("/movie_cut_info")
def movie_cut_info():
    global selection
    m = selection['movie']
    dmin = m.duration / 60000
    apsc = cutter._apsc(m)
    eta_apsc = int((0.7 if not apsc else 0) * dmin)
    eta_cut =  int(0.93 * dmin)
    return { 'movie': m.title, 'eta': eta_apsc + eta_cut, 'eta_cut': eta_cut, 'eta_apsc': eta_apsc, 'apsc' : apsc }

@app.route("/cut", methods=['POST'])
def cut():
    global selection
    if request.method == 'POST':
        print("in '/cut':")
        pp(request.json)
        section_name = request.json['section']
        s = update_section(section_name)
        movie_name = request.json['movie_name']
        m = update_movie(movie_name)
        ss = request.json['ss']
        to = request.json['to']
        inplace = request.json['inplace']
        res = f"cutter.cut({m.title},{ss},{to},inplace={inplace})"
        print(res)
        try:
            res = cutter.cut(m,ss,to,inplace)
            m.analyze()
            #time.sleep(10)
            return { 'result': res }
        except Exception as e:
            return { 'result': str(e) }

@app.route("/")
def index():
    global selection
    host = request.headers.get('Host')
    return render_template('webcutter/index.html', host=host)

@app.route("/test")
def test():
    return render_template('test.html')

@app.route("/testmodal")
def testmodal():
    return render_template('testmodal.html')

if __name__ == '__main__':
    update_section('Plex Recordings')
    app.run(use_reloader=True, host='0.0.0.0', port=5000, debug=True)