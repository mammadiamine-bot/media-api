from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Media API is running"}

@app.get("/download")
def get_download(url: str = Query(...)):
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "format": "best[ext=mp4]/best"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        download_url = info.get("url")

        if not download_url and "formats" in info:
            for f in reversed(info["formats"]):
                if f.get("url"):
                    download_url = f.get("url")
                    break

        if not download_url:
            return JSONResponse({
                "success": False,
                "message": "No downloadable URL found"
            }, status_code=400)

        return {
            "success": True,
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "downloadUrl": download_url,
            "platform": info.get("extractor_key")
        }

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)
