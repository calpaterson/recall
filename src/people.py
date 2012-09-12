import bottle

app = bottle.Bottle()

@app.get("/")
def users():
    nyi()

@app.get("/<who>/")
def user(who):
    nyi()

@app.get("/<who>/self")
def self_(who):
    nyi()

@app.post("/<who>/")
def request_invite(who):
    nyi()

@app.post("/<who>/<token>")
def verify_email(who, token):
    nyi()
