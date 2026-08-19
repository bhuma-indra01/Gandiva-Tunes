"""
Lightweight Asynchronous Keep-Alive Web Server for Gandiva Tunes.
Binds to $PORT for Render.com Web Service health checks and 24/7 uptime monitoring.
Credits: Syko Reddy
"""

import os
import asyncio
from aiohttp import web
from config import BOT_NAME, CREDITS_TEXT

routes = web.RouteTableDef()


@routes.get("/")
async def root_handler(request):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{BOT_NAME} - Online</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0d0e15 0%, #1a1b2e 100%);
                color: #ffffff;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 240, 255, 0.3);
                border-radius: 16px;
                padding: 40px 50px;
                text-align: center;
                box-shadow: 0 8px 32px 0 rgba(0, 240, 255, 0.15);
                max-width: 450px;
            }}
            h1 {{
                color: #00f0ff;
                font-size: 2.2rem;
                margin-bottom: 10px;
                text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
            }}
            .status-badge {{
                display: inline-block;
                background: rgba(0, 255, 136, 0.2);
                color: #00ff88;
                border: 1px solid #00ff88;
                padding: 6px 16px;
                border-radius: 20px;
                font-weight: bold;
                margin-top: 15px;
            }}
            p {{
                color: #a0a5c0;
                font-size: 1rem;
                line-height: 1.6;
            }}
            .credits {{
                margin-top: 25px;
                font-size: 0.9rem;
                color: #ff007f;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🏹 {BOT_NAME}</h1>
            <p>High-Definition Discord Music Bot with Neon Glassmorphism UI</p>
            <div class="status-badge">● BOT OPERATIONAL 24/7</div>
            <div class="credits">Developed & Maintained with ❤️ by <strong>{CREDITS_TEXT}</strong></div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type="text/html")


@routes.get("/health")
async def health_check(request):
    return web.json_response({"status": "healthy", "bot": BOT_NAME, "developer": CREDITS_TEXT})


async def start_keep_alive():
    """Start the aiohttp background web server."""
    port_str = os.getenv("PORT", "8080")
    port = int(port_str) if port_str.isdigit() else 8080

    app = web.Application()
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[✓] Keep-Alive Web Server listening on port {port} for Render / Uptime monitoring.")
