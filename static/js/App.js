    // Allgemeine Funktionen
    console.log(Vue.prototype.$host)
    const zeroPad = (num, places) => String(num).padStart(places, '0')
    const pos2str = (pos) => {
        pos = (pos >= 0) ? pos : 0 
        return `${zeroPad(Math.trunc(pos / 3600),2)}:${zeroPad(Math.trunc((pos % 3600) / 60),2)}:${zeroPad(Math.trunc(pos % 60,2),2)}`
    }
    const str2pos = (st) => {
        erg = parseInt(String(st).slice(0,2))*3600 + parseInt(String(st).slice(3,5))*60 + parseInt(String(st).slice(-2))
        //console.log(`str2pos(${st}) = ${erg}`)
        return erg
    }
        /*p = str2pos('01:25:12')
    console.log(p, pos2str(p))*/
    
    // Vue Komponenten
    const vueApp = new Vue({
        el: '#vueApp',
        data: {
            sections: [],
            section: '',
            movies: [],
            lmovie: '',
            lmovie_info: { duration: 0 },
            lpos: 0,
            t0: "00:00:00",
            t0_valid: false,
            t1: "01:00:00",
            t1_valid: false,
            inplace: false,            
            //bl_class: "btn btn-outline-dark btn-sm col mt-0 me-1",
            //br_class: "btn btn-outline-dark btn-sm col mt-0 ms-1",
            pic_name: ''
        },
        computed: {
            totalsections() {
                return this.sections.length
            },
            totalmovies() {
                return this.movies.length
            },
            movie: {
                get() {
                    this.load_movie_info()
                    this.reset_t0_t1()
                    return this.lmovie
                },
                set(val) {
                    //console.log('in movie setter')
                    this.lmovie = val
                }
            },
            cut_ok() {
                return this.t0_valid & this.t1_valid
            },         
            pos: {
                get() {
                    //console.log("pos getter ", this.lpos)
                    ret = pos2str(this.lpos) 
                    this.load_pic(ret)
                    return ret
                },
                set(newValue) {
                    this.lpos = str2pos(newValue)
                }
            },
            bleft() {
                return [
                    {name:"S15'", val:15*60, type:"abs", class:"btn btn-outline-primary btn-sm col mt-0 me-1"},
                    {name:"-30'", val:-1800, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 me-1"},
                    {name:"-10'", val:-600, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 me-1"},
                    {name:"-5'", val:-5*60, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 me-1"},
                    {name:"-1'", val:-60, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 me-1"},
                    {name:'-10"', val:-10, type:"rel", class:"btn btn-outline-secondary btn-sm col mt-0 me-1"},
                    {name:'-5"', val:-5, type:"rel", class:"btn btn-outline-secondary btn-sm col mt-0 me-1"},
                    {name:'-1"', val:-1, type:"rel", class:"btn btn-outline-secondary btn-sm col mt-0 me-1"},
                ]
            },
            bright() {
                return [
                    {name:'+1"', val:1, type:"rel", class:"btn btn-outline-secondary btn-sm col mt-0 ms-1"},
                    {name:'+5"', val:5, type:"rel", class:"btn btn-outline-secondary btn-sm col mt-0 ms-1"},                    
                    {name:'+10"', val:10, type:"rel", class:"btn btn-outline-secondary btn-sm col mt-0 ms-1"},
                    {name:"+1'", val:60, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 ms-1"},
                    {name:"+5'", val:5*60, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 ms-1"},
                    {name:"+10'", val:600, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 ms-1"},
                    {name:"+30'", val:1800, type:"rel", class:"btn btn-outline-info btn-sm col mt-0 ms-1"},
                    {name:"E15'", val:this.pos_from_end(15*60), type:"abs", class:"btn btn-outline-primary btn-sm col mt-0 ms-1"},
                ]
            }
        },
        methods: {
            toggle_inplace() {
                this.inplace = !this.inplace
            },
            notifyme() {
                return axios.post(`${Vue.prototype.$host}/update`,
                    { 
                        section: this.section
                    },
                    { 
                        headers: { 'Content-type': 'application/json', }
                    }).then((response) => {
                            //console.log('section: ' + this.section);
                            this.loadmovies();
                    }).catch( error => { 
                            console.log('error: ' + error); 
                    });
                },
            loadmovies() {
                fetch(`${Vue.prototype.$host}/movies`)
                .then(response => response.json())
                .then(json => {
                    //console.log(json)
                    this.movies = json.movies;
                    this.lmovie = json.movie;
                })
            },
            load_movie_info() {
                return axios.post(`${Vue.prototype.$host}/movie_info`,
                    { 
                        section: this.section,
                        movie: this.lmovie
                    },
                    { headers: {
                    'Content-type': 'application/json',
                    }
                }).then((response) => {
                    this.lmovie_info = response.data.movie_info
                }).catch( error => { 
                    console.log('error: ' + error); 
                });
            },
            reset_t0_t1() {
                this.t0 = "00:00:00"
                this.t0_valid = false 
                this.t1 = "01:00:00"
                this.t1_valid = false                 
            },
            hpos(b) {
                if (b.type == "rel") {
                    this.lpos += b.val
                    // console.log(this.lpos)
                    this.lpos = (this.lpos >= 0) ? this.lpos : 0
                    this.lpos = (this.lpos <= this.lmovie_info.duration * 60) ? this.lpos : this.lmovie_info.duration * 60
                    // console.log(this.lpos)
                } else if (b.type == "abs") {
                    this.lpos = b.val 
                } else if (b.type == "t0")  {
                    this.t0 = this.pos
                    this.t0_valid = true 
                }else if (b.type == "t1")  {
                    this.t1 = this.pos
                    this.t1_valid = true 
                } else {
                    alert("unknown type in hpos")
                }
            },
            pos_from_end(sec) {
                return this.lmovie_info.duration * 60 - sec
            },
            load_pic(pos) {
                //console.log(`in load pic ... request ${pos}`)
                return axios.post(`${Vue.prototype.$host}/load_pic`,
                    { 
                        pos_time: pos,
                        movie_name: this.lmovie
                    },
                    { headers: {
                    'Content-type': 'application/json',
                    }
                }).then((response) => {
                    this.pic_name = response.data.pic_name + '?' + String(Math.random()*100)
                }).catch( error => { 
                    console.log('error: ' + error); 
                });
            },
            docut() {
                msg = `Cut '${this.section}' - '${this.lmovie}' - ${this.t0} In - ${this.t1} Out`
                console.log(msg)
                if (confirm(msg)) {
                    //alert('go')
                    return axios.post(`${Vue.prototype.$host}/cut`,
                        {   
                            section: this.section, 
                            movie_name: this.lmovie,
                            ss: this.t0,
                            to: this.t1,
                            inplace: this.inplace
                        },
                        { headers: { 'Content-type': 'application/json',}}
                    ).then((response) => {
                        alert(response.data.result)
                    }).catch( error => { 
                        console.log('error: ' + error); 
                    });
                } else {
                    alert('stop')
                }
            }
        },
        created() {
            fetch(`${Vue.prototype.$host}/sections`)
                .then(response => response.json())
                .then(json => {
                    this.sections = json.sections;
                    this.section = json.section
                    this.loadmovies()
                })
        },
        delimiters: ['[[',']]']
    })