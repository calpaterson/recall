import bottle

app = bottle.Bottle()

def nyi(*args, **kwargs):
    raise NotimplementedError()

@app.get("/")
def info():
    nyi()
