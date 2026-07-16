"""Sandbox helpers for template 69 (Test Completion by All)."""
import pneumatic as P, roles, json, copy

BASE = json.load(open('_tpl69_backup.json'))

def set_step1(performers, rcba=True):
    t = copy.deepcopy(BASE)
    t['tasks'][0]['raw_performers'] = performers
    t['tasks'][0]['require_completion_by_all'] = rcba
    s,r = P.req('PUT','/templates/69',t)
    assert s==200, (s,str(r)[:300])
    return r

def U(uid,label): return {'api_name':'rp-u%d'%uid,'source_id':str(uid),'type':'user','label':label}
def G(gid,label): return {'api_name':'rp-g%d'%gid,'source_id':str(gid),'type':'group','label':label}

def start(R, starter=93):
    s,w = roles.call(starter,'POST','/templates/69/run',{'name':'rcba probe'},R)
    assert s in (200,201), (s,str(w)[:300])
    return w['id']

def wf(wid):
    s,w = P.get('/workflows/%d'%wid); return w

def task1(wid):
    w = wf(wid)
    for tk in w['tasks']:
        if tk['number']==1: return tk
    return None

def active_nums(wid):
    w=wf(wid)
    return [tk['number'] for tk in w['tasks'] if tk.get('status')=='active' or tk['id']==w.get('current_task_id')]

def perf(wid):
    tk=task1(wid)
    return [(p.get('type'),p.get('source_id'),p.get('is_completed')) for p in (tk.get('performers') or tk.get('raw_performers') or [])], tk

def cleanup(wid):
    P.req('DELETE','/workflows/%d'%wid, None)
