<img width="182" height="34" alt="image" src="https://github.com/user-attachments/assets/cb33e768-69be-42d0-a217-8c6d74198804" /># Round-2-Eco 🌱
The Round-2-Eco is a simple desktop application which helps people to track/monitor their eco-friendly actions 
such as recycling, saving electricity or even riding a bike. Each of these eco-friendly activities has a 
score/rating and it lets the users know how much impact they are contributing as an individual or maybe 
as a group. It uses Python as its coding language and other tools to keep it simple and easy to use.

**Sprint 1 prototype** featuring (7/5/2025):
- Basic interface using **Flet**
- Local database setup with **SQLite**
- Sample backend with **FastAPI**
- Runs in your **browser** (via Flet browser mode)

 **Sprint 2 prototype** featuring (7/11/25):
- Weekly Point Tracking Chart - Visual representation of your daily eco-points over the last 7 days
- Achievement System - Earn badges for reaching point milestones (50, 100, 200, etc.)
- Weekly Point Cap - 1000 point limit per week to encourage consistent daily actions
- Enhanced UI Layout - Two-column design with achievements and stats sidebar
- Improved Data Visualization - Interactive charts showing your progress

  **Sprint 3 prototype** featuring (7/19/25):
-  Refactored Code to Object-Oriented Design - Separated logic into well-structured classes: EcoTrackerUI, EcoDatabase, AchievementManager, ChartGenerator, etc.
-  Basic Challenges - Monthly challenges like "Complete 20 eco actions" with updating progress
-  Instant UI Feedback on Action Logging - Fixed delayed bug, the progress bars now update immediately
-  Dynamic Challenge Cards - Each challenge displays description, date range, live action count, and % complete.

## 🔧 How to Run

1. Open a terminal
2. Install Flet (pip install flet)
3. Install matplotlib (pip install matplotlib)
4. Run python db.py to initialize local database
5. Run python main.py
