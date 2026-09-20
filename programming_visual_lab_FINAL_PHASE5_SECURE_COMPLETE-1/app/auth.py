"""Optional OAuth login for Programming Visual Lab.

Credentials stay server-side in environment variables. The UI can show Google/GitHub
login buttons even when providers are not configured; unconfigured providers return
a clear message instead of pretending authentication worked.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
COOKIE = "pvl_session"
STATE_COOKIE = "pvl_oauth_state"
SESSION_TTL = 60 * 60 * 24 * 7

def _secret():
    return os.environ.get("PVL_SESSION_SECRET", "").strip() or "change-this-development-secret"

def _pack(payload):
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    body = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    sig = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + sig

def _unpack(value):
    try:
        body, sig = value.split(".", 1)
        good = hmac.compare_digest(sig, hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest())
        if not good:
            return None
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        data = json.loads(raw.decode())
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None

def _base_url(request):
    configured = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if configured:
        return configured
    return str(request.base_url).rstrip("/")

def _set_session(response, user):
    data = dict(user)
    data["iat"] = int(time.time())
    data["exp"] = int(time.time()) + SESSION_TTL
    response.set_cookie(COOKIE, _pack(data), max_age=SESSION_TTL, httponly=True, samesite="lax", secure=_base_url_from_env_is_https())

def _base_url_from_env_is_https():
    return os.environ.get("PUBLIC_BASE_URL", "").strip().lower().startswith("https://")

def _oauth_state(response, provider):
    state = secrets.token_urlsafe(32)
    response.set_cookie(STATE_COOKIE, _pack({"state": state, "provider": provider, "exp": int(time.time()) + 600}), max_age=600, httponly=True, samesite="lax", secure=_base_url_from_env_is_https())
    return state

def _json_request(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def _github_login_url(request):
    client=os.environ.get("GITHUB_CLIENT_ID","").strip()
    if not client: return None
    callback=_base_url(request)+"/api/auth/github/callback"
    return "https://github.com/login/oauth/authorize?"+urllib.parse.urlencode({"client_id":client,"redirect_uri":callback,"scope":"read:user user:email","state":"PLACEHOLDER"})

def _google_login_url(request):
    client=os.environ.get("GOOGLE_CLIENT_ID","").strip()
    if not client: return None
    callback=_base_url(request)+"/api/auth/google/callback"
    return "https://accounts.google.com/o/oauth2/v2/auth?"+urllib.parse.urlencode({"client_id":client,"redirect_uri":callback,"response_type":"code","scope":"openid email profile","access_type":"online","state":"PLACEHOLDER"})

@router.get("/config")
def auth_config(request: Request):
    return {
        "google": bool(os.environ.get("GOOGLE_CLIENT_ID","").strip() and os.environ.get("GOOGLE_CLIENT_SECRET","").strip()),
        "github": bool(os.environ.get("GITHUB_CLIENT_ID","").strip() and os.environ.get("GITHUB_CLIENT_SECRET","").strip()),
        "public_base_url": _base_url(request),
    }

@router.get("/me")
def auth_me(request: Request):
    user=_unpack(request.cookies.get(COOKIE,""))
    return {"authenticated": bool(user), "user": user or None}

@router.post("/guest")
def guest():
    response=JSONResponse({"ok":True,"user":{"provider":"guest","name":"Guest Learner","avatar":""}})
    _set_session(response, {"provider":"guest","name":"Guest Learner","avatar":""})
    return response

@router.post("/logout")
def logout():
    response=JSONResponse({"ok":True})
    response.delete_cookie(COOKIE)
    response.delete_cookie(STATE_COOKIE)
    return response

def _start_oauth(request, provider):
    response=RedirectResponse(url="/")
    if provider=="github":
        client=os.environ.get("GITHUB_CLIENT_ID","").strip()
        if not client:
            return JSONResponse({"ok":False,"error":"GitHub login is not configured on the server yet. Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in Render Environment Variables."},status_code=503)
        callback=_base_url(request)+"/api/auth/github/callback"
        state=_oauth_state(response,"github")
        url="https://github.com/login/oauth/authorize?"+urllib.parse.urlencode({"client_id":client,"redirect_uri":callback,"scope":"read:user user:email","state":state})
    else:
        client=os.environ.get("GOOGLE_CLIENT_ID","").strip()
        if not client:
            return JSONResponse({"ok":False,"error":"Google login is not configured on the server yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Render Environment Variables."},status_code=503)
        callback=_base_url(request)+"/api/auth/google/callback"
        state=_oauth_state(response,"google")
        url="https://accounts.google.com/o/oauth2/v2/auth?"+urllib.parse.urlencode({"client_id":client,"redirect_uri":callback,"response_type":"code","scope":"openid email profile","state":state,"access_type":"online"})
    response=RedirectResponse(url=url)
    # RedirectResponse was recreated, so set state again on the final response.
    state_cookie=_pack({"state":state,"provider":provider,"exp":int(time.time())+600})
    response.set_cookie(STATE_COOKIE,state_cookie,max_age=600,httponly=True,samesite="lax",secure=_base_url_from_env_is_https())
    return response

@router.get("/github")
def github(request: Request):
    return _start_oauth(request,"github")

@router.get("/google")
def google(request: Request):
    return _start_oauth(request,"google")

def _check_state(request, provider, state):
    saved=_unpack(request.cookies.get(STATE_COOKIE,""))
    return bool(saved and saved.get("provider")==provider and state and hmac.compare_digest(saved.get("state",""),state))

@router.get("/github/callback")
def github_callback(request: Request, code: str="", state: str=""):
    if not _check_state(request,"github",state):
        return RedirectResponse("/?auth_error=Invalid+GitHub+login+state")
    client=os.environ.get("GITHUB_CLIENT_ID","").strip(); secret=os.environ.get("GITHUB_CLIENT_SECRET","").strip()
    callback=_base_url(request)+"/api/auth/github/callback"
    try:
        token=_json_request("https://github.com/login/oauth/access_token",urllib.parse.urlencode({"client_id":client,"client_secret":secret,"code":code,"redirect_uri":callback}).encode(),{"Accept":"application/json","Content-Type":"application/x-www-form-urlencoded"})
        access=token.get("access_token")
        if not access: raise ValueError("GitHub did not return an access token")
        user=_json_request("https://api.github.com/user",None,{"Accept":"application/vnd.github+json","Authorization":"Bearer "+access,"User-Agent":"Programming-Visual-Lab"})
        response=RedirectResponse("/")
        _set_session(response,{"provider":"github","name":user.get("name") or user.get("login") or "GitHub learner","avatar":user.get("avatar_url",""),"login":user.get("login","")})
        response.delete_cookie(STATE_COOKIE)
        return response
    except Exception:
        return RedirectResponse("/?auth_error=GitHub+login+failed")

@router.get("/google/callback")
def google_callback(request: Request, code: str="", state: str=""):
    if not _check_state(request,"google",state):
        return RedirectResponse("/?auth_error=Invalid+Google+login+state")
    client=os.environ.get("GOOGLE_CLIENT_ID","").strip(); secret=os.environ.get("GOOGLE_CLIENT_SECRET","").strip()
    callback=_base_url(request)+"/api/auth/google/callback"
    try:
        token=_json_request("https://oauth2.googleapis.com/token",urllib.parse.urlencode({"client_id":client,"client_secret":secret,"code":code,"redirect_uri":callback,"grant_type":"authorization_code"}).encode(),{"Content-Type":"application/x-www-form-urlencoded"})
        access=token.get("access_token")
        if not access: raise ValueError("Google did not return an access token")
        user=_json_request("https://openidconnect.googleapis.com/v1/userinfo?"+urllib.parse.urlencode({"access_token":access}),None,{"Accept":"application/json"})
        response=RedirectResponse("/")
        _set_session(response,{"provider":"google","name":user.get("name") or user.get("email") or "Google learner","avatar":user.get("picture",""),"email":user.get("email","")})
        response.delete_cookie(STATE_COOKIE)
        return response
    except Exception:
        return RedirectResponse("/?auth_error=Google+login+failed")
