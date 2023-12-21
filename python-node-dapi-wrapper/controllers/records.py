import requests
import json
from fastapi import APIRouter, HTTPException

record = APIRouter()

@record.post("/create_record")
async def create_record(req: dict):
    token = req["fmSessionToken"]
    record = req["body"]["methodBody"]["record"]
    database = req["body"]["methodBody"]["database"]
    layout = req["body"]["methodBody"]["layout"]
    fm_server = req["body"]["fmServer"]

    apiUrl = f"https://{fm_server}/fmi/data/vLatest/databases/{database}/layouts/{layout}/records"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    requestData = {
        "fieldData": record
    }

    try:
        response = requests.post(apiUrl, headers=headers, json=requestData, verify=False)
        response.raise_for_status()
        recordId = response.json().get("response", {}).get("recordId")
        return {
            "status": "created",
            "recordId": recordId,
            "fieldData": record,
            "session": req["fmSessionToken"]
        }
    except requests.HTTPError as e:
        error_message = "An error occurred while creating the record."
        if e.response:
            error_message = e.response.json()
        raise HTTPException(status_code=500, detail=error_message)
