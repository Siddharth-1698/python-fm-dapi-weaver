from fastapi import FastAPI, HTTPException, Header, Request
import requests

app = FastAPI()

async def validate_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Authorization header is missing or invalid")
    return authorization.split(" ")[1]

async def validate_session(req: Request):
    basic_auth_token = req.headers.get("Authorization")
    body = await req.json()

    session = body.get("session") if body else {}
    token = session.get("token")
    required = session.get("required", False)
    method_body = body.get("methodBody", {})
    database = method_body.get("database")
    fm_server = body.get("fmServer")

    should_call_next = False  # Flag to track if next() should be called

    if not session or not token:
        try:
            fm_session_token = fm_login(fm_server, database, basic_auth_token)
            
            if fm_session_token:
                is_session_valid = fm_validate_session(fm_server, fm_session_token)

                if is_session_valid:
                    req.state.fm_session_token = fm_session_token
                    should_call_next = True
                else:
                    raise HTTPException(status_code=401, detail="Session token validation failed")
        except Exception as error:
            raise HTTPException(status_code=401, detail=str(error))
    else:
        try:
            is_session_valid = fm_validate_session(fm_server, token)

            if is_session_valid:
                req.state.fm_session_token = token
                should_call_next = True
            else:
                if token and (not required or required is False):
                    try:
                        fm_session_token = fm_login(fm_server, database, basic_auth_token)
                        
                        if fm_session_token:
                            is_session_valid = fm_validate_session(fm_server, fm_session_token)

                            if is_session_valid:
                                req.state.fm_session_token = fm_session_token
                                should_call_next = True
                            else:
                                raise HTTPException(status_code=401, detail="Re-validation of session token failed")
                        else:
                            raise HTTPException(status_code=401, detail="Re-authentication failed")
                    except Exception as error:
                        raise HTTPException(status_code=401, detail=str(error))
                else:
                    raise HTTPException(status_code=401, detail="Invalid session token")

        except Exception as error:
            raise HTTPException(status_code=401, detail=str(error))

    if should_call_next:
        return True


# Utility Functions

def fm_validate_session(fm_server: str, session_token: str):
    url = f"https://{fm_server}/fmi/data/vLatest/validateSession"
    headers = {
        "Authorization": f"Bearer {session_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        return response_data["messages"][0]["message"] == "OK"
    except Exception as error:
        return False


def fm_login(fm_server, database, basic_auth_token):
    url = f"https://{fm_server}/fmi/data/vLatest/databases/{database}/sessions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {basic_auth_token}"
    }

    try:
        response = requests.post(url, headers=headers)
        response_data = response.json()
        return response_data["response"]["token"]
    except requests.exceptions.RequestException as error:
        print("fmLogin Error: ", error)
        response_json = {
            "error": "An error occurred while logging in."
        }
        if response and response.status_code:
            response_json["statusText"] = response.status_code
            response_json["error"] = response.text

        raise ValueError(response_json)
