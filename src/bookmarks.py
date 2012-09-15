import bottle

import plugins

app = bottle.Bottle()
app.install(plugins.ppjson)

@app.get("/")
def bookmarks():
    bottle.abort(501)

@app.get("/url/<url>/")
def url(url):
    bottle.abort(501)

@app.get("/<who>/")
def private_bookmarks(who):
    bottle.abort(501)

@app.route("/<who>/", method="PATCH")
def import_(who):
    bottle.abort(501)

@app.get("/<who>/recent/")
def recent(who):
    bottle.abort(501)

@app.post("/<who>/<when>/")
def add(url):
    bottle.abort(501)

@app.post("/<who>/<when>/edits/<who_edited>/<time_editted/")
def update(who, when, who_edited, time_editted):
    bottle.abort(501)
