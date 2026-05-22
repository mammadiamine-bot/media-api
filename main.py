from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import yt_dlp
import requests
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name or "video")
    return name[:80] + ".mp4"

def extract_info(url):
    opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "format": "best[ext=mp4]/best",
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.tiktok.com/"
        }
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

def get_best_url(info):
    if info.get("url"):
        return info.get("url")

    formats = info.get("formats", [])
    for f in reversed(formats):
        if f.get("url") and f.get("ext") == "mp4":
            return f.get("url")

    for f in reversed(formats):
        if f.get("url"):
            return f.get("url")

    return None

@app.get("/")
def home():
    return {"status": "Media API is running"}

@app.get("/info")
def info(url: str = Query(...)):
    try:
        data = extract_info(url)
        video_url = get_best_url(data)

        if not video_url:
            return JSONResponse({
                "success": False,
                "message": "No downloadable video found"
            }, status_code=400)

        return {
            "success": True,
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "duration": data.get("duration"),
            "platform": data.get("extractor_key"),
            "downloadUrl": f"/download-file?url={url}"
        }

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)

@app.get("/download-file")
def download_file(url: str = Query(...)):
    try:
        data = extract_info(url)
        video_url = get_best_url(data)

        if not video_url:
            return JSONResponse({
                "success": False,
                "message": "No downloadable video found"
            }, status_code=400)

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.tiktok.com/"
        }

        r = requests.get(video_url, headers=headers, stream=True, timeout=60)

        if r.status_code != 200:
            return JSONResponse({
                "success": False,
                "message": f"Video source returned {r.status_code}"
            }, status_code=400)

        filename = clean_filename(data.get("title"))

        return StreamingResponse(
            r.iter_content(chunk_size=1024 * 1024),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)
