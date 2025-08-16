The resources required for understanding more on the Kalashi API can be found here - https://docs.kalshi.com/welcome

TO START THE APPLICATION
1:uvicorn Backend.API.main:app --host 0.0.0.0 --port 8000 in the BE
2: cloudflared tunnel --url http://localhost:8000 in the console
3: copy the URL it gives 