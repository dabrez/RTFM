import os
import httpx
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional, List
from dotenv import load_dotenv
import sys

# Add parent directory to path to import Database and PostgresDatabase
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import PostgresDatabase

load_dotenv()

app = FastAPI(title="RTFM Bot Dashboard")

# Session configuration
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "super-secret-key"),
    max_age=3600 * 24 * 7 # 1 week
)

templates = Jinja2Templates(directory="dashboard/templates")

# Discord OAuth2 Configuration
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
DISCORD_API_URL = "https://discord.com/api/v10"

postgres = PostgresDatabase()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": user,
        "client_id": CLIENT_ID
    })

@app.get("/login")
async def login():
    if not CLIENT_ID or not REDIRECT_URI:
        raise HTTPException(status_code=500, detail="OAuth configuration missing")
    
    auth_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code"
        f"&scope=identify%20guilds"
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request, code: str):
    # Exchange code for token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{DISCORD_API_URL}/oauth2/token", data=data, headers=headers)
        if response.status_code != 200:
            return HTMLResponse(content=f"Error exchanging code: {response.text}", status_code=400)
        
        token_data = response.json()
        access_token = token_data["access_token"]

        # Fetch user info
        user_response = await client.get(f"{DISCORD_API_URL}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
        user_data = user_response.json()

        # Fetch user guilds
        guilds_response = await client.get(f"{DISCORD_API_URL}/users/@me/guilds", headers={"Authorization": f"Bearer {access_token}"})
        guilds_data = guilds_response.json()

        # Filter for guilds where user is admin or owner
        managed_guilds = [
            g for g in guilds_data 
            if (int(g["permissions"]) & 0x8) or g.get("owner", False) # 0x8 is ADMINISTRATOR
        ]

        # Store in session
        request.session["user"] = user_data
        request.session["guilds"] = managed_guilds
        request.session["access_token"] = access_token

    return RedirectResponse("/guilds")

@app.get("/guilds", response_class=HTMLResponse)
async def guilds(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    guilds = request.session.get("guilds", [])
    return templates.TemplateResponse("guilds.html", {"request": request, "user": user, "guilds": guilds})

@app.get("/guild/{guild_id}", response_class=HTMLResponse)
async def guild_detail(request: Request, guild_id: str):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    # Verify user manages this guild
    user_guilds = request.session.get("guilds", [])
    if not any(g["id"] == guild_id for g in user_guilds):
        raise HTTPException(status_code=403, detail="Unauthorized: You do not manage this server.")

    # Fetch query history from database for this guild
    # We'll need a new method in PostgresDatabase for this
    conn = postgres._get_conn()
    history = []
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT question, response, username, timestamp FROM query_history WHERE guild_id = %s ORDER BY timestamp DESC LIMIT 50",
                (guild_id,)
            )
            rows = cur.fetchall()
            for row in rows:
                history.append({
                    "question": row[0],
                    "response": row[1],
                    "username": row[2],
                    "timestamp": row[3].strftime("%Y-%m-%d %H:%M:%S")
                })

    return templates.TemplateResponse("guild_detail.html", {
        "request": request, 
        "user": user, 
        "guild_id": guild_id,
        "history": history
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
