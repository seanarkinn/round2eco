from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Eco backend working!"}

# Placeholder for logging an action
@app.post("/log")
def log_action(action: str):
    return {"status": "success", "logged_action": action}