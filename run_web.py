"""
Practice Manager - Web server entry point

Run with: python run_web.py
Or: uvicorn src.practice_manager.web.main:app --reload --host 0.0.0.0
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.practice_manager.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
