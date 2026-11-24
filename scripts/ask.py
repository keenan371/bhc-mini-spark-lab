import json,os,sys,time,urllib.request
T=open(os.path.expanduser("~/.owui_token")).read().strip()
def ask(model,q):
    t=time.time()
    r=urllib.request.Request("http://127.0.0.1:8080/api/chat/completions",method="POST",
      data=json.dumps({"model":model,"stream":False,"messages":[{"role":"user","content":q}]}).encode(),
      headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
    d=json.load(urllib.request.urlopen(r,timeout=280))
    print(f"[{model}] {round(time.time()-t)}s  Q: {q}\n  A: {d['choices'][0]['message']['content'].strip()}\n")
ask(sys.argv[1],sys.argv[2])
