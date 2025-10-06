import json

def save_log(log_data):
    with open("checklist_log.json","w") as f:
        json.dump(log_data,f,indent=2)