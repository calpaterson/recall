from application import app, nyi

@app.get("/people/")
def users():
    nyi()

@app.get("/people/<who>/")
def user(who):
    nyi()

@app.get("/people/<who>/self")
def self_(who):
    nyi()

@app.post("/people/<who>/")
def request_invite(who):
    nyi()

@app.post("/people/<who>/<token>")
def verify_email(who, token):
    nyi()

@app.route("/people/<who>/marks/", method="PATCH")
def import_(who):
    nyi()

@app.get("/people/<who>/marks/")
def export(who):
    nyi()
