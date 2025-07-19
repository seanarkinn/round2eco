from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from db import EcoDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionRequest(BaseModel):
    action: str = Field(..., min_length=1)
    points: int = Field(..., gt=0)

class ActionResponse(BaseModel):
    id: Optional[int] = None
    action: str
    points: int
    timestamp: str

class StatsResponse(BaseModel):
    total_points: int
    weekly_points: int
    total_actions: int

class HistoryResponse(BaseModel):
    actions: List[ActionResponse]
    total_count: int

class Challenge(BaseModel):
    id: int
    description: str
    target_count: int
    start_date: str
    end_date: str
    completed: int

class ChallengeCreate(BaseModel):
    description: str
    target_count: int
    start_date: str
    end_date: str

class EcoBackendService:
    def __init__(self, db: EcoDatabase):
        self.db = db
        self.weekly_cap = 1000

    def log_action(self, action_request: ActionRequest) -> ActionResponse:
        weekly_points = self.db.get_weekly_points()
        if weekly_points + action_request.points > self.weekly_cap:
            raise HTTPException(status_code=400, detail=f"Weekly cap of {self.weekly_cap} points exceeded")

        success = self.db.insert_action(action_request.action, action_request.points)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to log action")

        self.db.update_challenge_completion()

        return ActionResponse(
            action=action_request.action,
            points=action_request.points,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def get_stats(self) -> StatsResponse:
        return StatsResponse(
            total_points=self.db.get_total_points(),
            weekly_points=self.db.get_weekly_points(),
            total_actions=len(self.db.get_action_history())
        )

    def get_history(self, limit: Optional[int] = None) -> HistoryResponse:
        history_data = self.db.get_action_history()
        if limit:
            history_data = history_data[:limit]
        actions = [ActionResponse(action=action, points=points, timestamp=timestamp) for action, points, timestamp in history_data]
        return HistoryResponse(actions=actions, total_count=len(self.db.get_action_history()))

    def reset_data(self) -> dict:
        if not self.db.reset_all_data():
            raise HTTPException(status_code=500, detail="Failed to reset data")
        return {"message": "All data reset successfully"}

    def get_weekly_chart_data(self) -> List[dict]:
        return [{"date": date, "points": points} for date, points in self.db.get_points_per_day_last_week()]

    def get_challenges(self) -> List[Challenge]:
        raw = self.db.get_active_challenges()
        return [Challenge(id=id, description=desc, target_count=target, start_date=start, end_date=end, completed=completed) for id, desc, target, start, end, completed in raw]

    def create_challenge(self, challenge: ChallengeCreate):
        self.db.insert_challenge(challenge.description, challenge.target_count, challenge.start_date, challenge.end_date)
        return {"message": "Challenge created"}

class EcoAPI:
    def __init__(self):
        self.app = FastAPI(title="Eco Tracker API", description="Track eco-friendly actions", version="2.0.0")
        self.db = EcoDatabase()
        self.service = EcoBackendService(self.db)
        self._setup_routes()
        self.db.init_db()

    def get_service(self) -> EcoBackendService:
        return self.service

    def _setup_routes(self):
        @self.app.get("/", summary="Health check")
        async def root():
            return {"message": "Eco Tracker API v2.0 - Ready!", "status": "healthy"}

        @self.app.post("/log", response_model=ActionResponse)
        async def log_action(action_request: ActionRequest, service: EcoBackendService = Depends(self.get_service)):
            logger.info(f"Logging action: {action_request.action} for {action_request.points} points")
            return service.log_action(action_request)

        @self.app.get("/stats", response_model=StatsResponse)
        async def get_stats(service: EcoBackendService = Depends(self.get_service)):
            return service.get_stats()

        @self.app.get("/history", response_model=HistoryResponse)
        async def get_history(limit: Optional[int] = None, service: EcoBackendService = Depends(self.get_service)):
            return service.get_history(limit)

        @self.app.delete("/reset")
        async def reset_data(service: EcoBackendService = Depends(self.get_service)):
            logger.warning("Data reset requested")
            return service.reset_data()

        @self.app.get("/chart/weekly")
        async def get_weekly_chart_data(service: EcoBackendService = Depends(self.get_service)):
            return service.get_weekly_chart_data()

        @self.app.get("/challenges", response_model=List[Challenge])
        async def get_challenges(service: EcoBackendService = Depends(self.get_service)):
            return service.get_challenges()

        @self.app.post("/challenges")
        async def create_challenge(challenge: ChallengeCreate, service: EcoBackendService = Depends(self.get_service)):
            return service.create_challenge(challenge)

eco_api = EcoAPI()
app = eco_api.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
