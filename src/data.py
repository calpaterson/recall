def whitelist(dict_, whitelist):
    d = {}
    for k, v in dict_.items():
        if k in whitelist:
            d[k] = v
    return d

def blacklist(dict_, blacklist):
    d = {}
    for k, v in dict_.items():
        if k not in blacklist:
            d[k] = v
    return d
