from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
from db import EcoTracker, EcoAction, Challenge, User 

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    status: str
    message: str
    user_id: Optional[int] = None
    username: Optional[str] = None

class ActionRequest(BaseModel):
    user_id: int
    action: str
    points: int

class ActionResponse(BaseModel):
    status: str
    message: str
    action_logged: Optional[str] = None
    points_earned: Optional[int] = None

class StatsResponse(BaseModel):
    total_points: int
    weekly_points: int
    total_actions: int
    current_streak: int
    longest_streak: int

class ImpactResponse(BaseModel):
    co2_saved_kg: float
    gas_saved_gallons: float
    trees_equivalent: int

class EcoBackendService:
    def __init__(self):
        self.tracker = EcoTracker()
    
    def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        try:
            user = self.tracker.user_manager.create_user(username, password)
            if user:
                return {
                    "status": "success",
                    "message": "User registered successfully",
                    "user_id": user.id,
                    "username": user.username
                }
            else:
                return {
                    "status": "error",
                    "message": "Username already exists or registration failed"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Registration error: {str(e)}"
            }

    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            user = self.tracker.user_manager.authenticate_user(username, password)
            if user:
                return {
                    "status": "success",
                    "message": "Login successful",
                    "user_id": user.id,
                    "username": user.username
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid username or password"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Login error: {str(e)}"
            }

    def log_eco_action(self, user_id: int, action: str, points: int) -> Dict[str, Any]: 
        """Log an eco-friendly action"""
        try:
            if not action or not action.strip():
                raise ValueError("Action cannot be empty")
            
            if points <= 0:
                raise ValueError("Points must be positive")
            
            self.tracker.set_current_user(user_id)
            success = self.tracker.log_action(action.strip(), points)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Successfully logged {action}",
                    "action_logged": action.strip(),
                    "points_earned": points
                }
            else:
                raise Exception("Failed to log action in database")
                
        except ValueError as ve:
            return {
                "status": "error",
                "message": str(ve)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Internal error: {str(e)}"
            }

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            self.tracker.set_current_user(user_id)
            stats = self.tracker.get_stats()
            current_streak, longest_streak = stats['streak_data']
            weekly_impact = stats['weekly_impact']
            total_impact = stats['total_impact']
        
            return {
                "status": "success",
                "data": {
                    "total_points": stats['total_points'],
                    "weekly_points": stats['weekly_points'],
                    "total_actions": stats['total_actions'],
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "recent_actions": stats['action_history'][:5],
                    "active_challenges": len([c for c in stats['challenges'] if not c[4]]),
                    "completed_challenges": len([c for c in stats['challenges'] if c[4]]),
                    "weekly_impact": {
                        "co2_saved_kg": weekly_impact.co2_saved_kg,
                        "gas_saved_gallons": weekly_impact.gas_saved_gallons,
                        "trees_equivalent": weekly_impact.trees_equivalent
                    },
                    "total_impact": {
                        "co2_saved_kg": total_impact.co2_saved_kg,
                        "gas_saved_gallons": total_impact.gas_saved_gallons,
                        "trees_equivalent": total_impact.trees_equivalent
                    }
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get stats: {str(e)}"
            }

    def get_challenges(self, user_id: int) -> Dict[str, Any]: 
        """Get user challenges"""
        try:
            self.tracker.set_current_user(user_id)
            challenges = self.tracker.challenge_manager.get_challenges(user_id)
            formatted_challenges = []
            
            for name, desc, current, target, completed in challenges:
                formatted_challenges.append({
                    "name": name,
                    "description": desc,
                    "current_count": current,
                    "target_count": target,
                    "completed": bool(completed),
                    "progress_percentage": min(100, (current / target) * 100) if target > 0 else 0
                })
            
            return {
                "status": "success",
                "data": formatted_challenges
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get challenges: {str(e)}"
            }

    def reset_user_data(self, user_id: int) -> Dict[str, Any]: 
        """Reset all user data"""
        try:
            self.tracker.set_current_user(user_id)
            success = self.tracker.reset_all_data()
            if success:
                return {
                    "status": "success",
                    "message": "All data has been reset successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to reset data"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Reset failed: {str(e)}"
            }

class EcoBackendApp:
    def __init__(self):
        self.app = FastAPI(
            title="Eco Tracker API",
            description="Backend API for the Round-2-Eco application",
            version="2.0.0"
        )
        self.service = EcoBackendService()
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        from fastapi.middleware.cors import CORSMiddleware
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "Round-2-Eco Backend API is running!",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "database": "CSV File System"
            }
        
        @self.app.post("/register", response_model=AuthResponse)
        async def register(request: RegisterRequest):
            result = self.service.register_user(request.username, request.password)
            if result["status"] == "error":
                raise HTTPException(status_code=400, detail=result["message"])
            return AuthResponse(**result)

        @self.app.post("/login", response_model=AuthResponse)
        async def login(request: LoginRequest):
            result = self.service.login_user(request.username, request.password)
            if result["status"] == "error":
                raise HTTPException(status_code=401, detail=result["message"])
            return AuthResponse(**result)

        @self.app.post("/log", response_model=ActionResponse)
        async def log_action(action_data: ActionRequest):
            result = self.service.log_eco_action(
                action_data.user_id, 
                action_data.action, 
                action_data.points
            )
            
            if result["status"] == "error":
                raise HTTPException(status_code=400, detail=result["message"])
            
            return ActionResponse(**result)
        
        @self.app.get("/stats/{user_id}")
        async def get_stats(user_id: int):
            result = self.service.get_user_stats(user_id)
            
            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result["message"])
            
            return result
        
        @self.app.get("/challenges/{user_id}")
        async def get_challenges(user_id: int):
            result = self.service.get_challenges(user_id)
            
            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result["message"])
            
            return result
        
        @self.app.post("/reset/{user_id}")
        async def reset_data(user_id: int):
            result = self.service.reset_user_data(user_id)
            
            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result["message"])
            
            return result
        
        @self.app.get("/health")
        async def health_check():
            try:
                users_data = self.service.tracker.db.read_csv_safe(
                    self.service.tracker.db.users_file
                )
                total_users = len(users_data)
                
                return {
                    "status": "healthy",
                    "database": "CSV files accessible",
                    "timestamp": datetime.now().isoformat(),
                    "sample_data": f"Total users in system: {total_users}",
                    "data_directory": self.service.tracker.db.data_dir
                }
            except Exception as e:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Service unhealthy: {str(e)}"
                )
        
        @self.app.get("/history/{user_id}")
        async def get_action_history(user_id: int):
            try:
                self.service.tracker.set_current_user(user_id)
                history = self.service.tracker.action_manager.get_action_history(user_id)
                formatted_history = [
                    {
                        "action": action,
                        "points": points,
                        "timestamp": timestamp
                    }
                    for action, points, timestamp in history[:20]
                ]
                return {
                    "status": "success",
                    "data": formatted_history,
                    "total_count": len(history)
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to get history: {str(e)}"
                )
        
        @self.app.get("/impact/{user_id}")
        async def get_environmental_impact(user_id: int):
            try:
                self.service.tracker.set_current_user(user_id)
                weekly_impact = self.service.tracker.impact_manager.get_weekly_impact(user_id)
                total_impact = self.service.tracker.impact_manager.calculate_total_impact(user_id)
        
                return {
                    "status": "success",
                    "data": {
                        "weekly": {
                            "co2_saved_kg": weekly_impact.co2_saved_kg,
                            "gas_saved_gallons": weekly_impact.gas_saved_gallons,
                            "trees_equivalent": weekly_impact.trees_equivalent
                        },
                        "total": {
                            "co2_saved_kg": total_impact.co2_saved_kg,
                            "gas_saved_gallons": total_impact.gas_saved_gallons,
                            "trees_equivalent": total_impact.trees_equivalent
                        }
                    }
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to get impact: {str(e)}"
                )

        @self.app.get("/debug/files")
        async def debug_files():
            """Debug endpoint to check file status"""
            import os
            try:
                data_dir = self.service.tracker.db.data_dir
                files_info = {}
                
                files_to_check = [
                    "users.csv", "actions.csv", "challenges.csv", "streak_data.csv"
                ]
                
                for filename in files_to_check:
                    filepath = os.path.join(data_dir, filename)
                    files_info[filename] = {
                        "exists": os.path.exists(filepath),
                        "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        "path": filepath
                    }
                
                return {
                    "status": "success",
                    "data_directory": data_dir,
                    "files": files_info
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Debug failed: {str(e)}"
                )

eco_app = EcoBackendApp()
app = eco_app.app

if __name__ == "__main__":
    print("🚀 Starting Round-2-Eco Backend Server")
    print("📊 Using CSV File Database System")
    print("📡 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🐛 Debug Files: http://localhost:8000/debug/files")
    print("=" * 50)

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped gracefully")
    except Exception as e:
        print(f"❌ Server error: {e}")
