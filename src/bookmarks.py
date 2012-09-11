from application import app, nyi

@app.get("/<who>/bookmarks/<search_term>/")
def search_marks_as_email(who, search_term):
    nyi()

@app.get("/<who>/recent/")
def recent(who):
    nyi()

@app.get("/bookmarks/search/")
def search():
    nyi()

@app.get("/bookmarks/<url>/")
def url(url):
    nyi()

@app.post("/bookmarks/<who>/<when>/")
def add(url):
    nyi()

@app.post("/bookmarks/<who>/<when>/edits/<who_edited>/<time_editted/")
def update(who, when, who_edited, time_editted):
    nyi()
