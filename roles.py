"""Helper: build user-id -> API token map (owner-only endpoint), and name lookups.
Tokens are held in memory only; never printed in full or written to disk."""
import pneumatic as P

def _users():
    um={}; path='/accounts/users'
    for _ in range(12):
        d=P.get(path)[1]; rows=d.get('results',d) if isinstance(d,dict) else d
        for u in rows: um[u['id']]=u
        path=d.get('next') if isinstance(d,dict) else None
        if not path: break
    return um

def build():
    um=_users()
    email2id={u.get('email'):uid for uid,u in um.items()}
    name2id={}
    for uid,u in um.items():
        nm=((u.get('first_name') or '')+' '+(u.get('last_name') or '')).strip()
        name2id[nm]=uid
    # tokens by email
    rows=P.get('/accounts/users/api-key')[1]
    tok={}
    for r in rows:
        uid=email2id.get(r.get('email'))
        if uid is not None and r.get('api_key'):
            tok[uid]=r['api_key']
    id2name={uid:((u.get('first_name') or '')+' '+(u.get('last_name') or '')).strip() for uid,u in um.items()}
    return {'users':um,'tok':tok,'name2id':name2id,'id2name':id2name}

def call(uid, method, path, body, tokmap):
    """Generic authenticated request as user uid. Returns (status, parsed_or_text)."""
    import urllib.request, json
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(P.BASE+path, data=data,
        headers={'Authorization':'Bearer '+tokmap['tok'][uid],'Content-Type':'application/json'}, method=method)
    try:
        r=urllib.request.urlopen(req); raw=r.read().decode()
        try: return r.status, json.loads(raw)
        except: return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

def complete_as(uid, wid, task_id, output, tokmap):
    """Complete a task using user uid's token via a one-off request. Returns (status, err_or_None)."""
    import urllib.request, json
    body=json.dumps({'task_id':task_id,'output':output}).encode()
    req=urllib.request.Request(P.BASE+('/workflows/%d/task-complete'%wid), data=body,
        headers={'Authorization':'Bearer '+tokmap['tok'][uid],'Content-Type':'application/json'}, method='POST')
    try:
        r=urllib.request.urlopen(req)
        return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
