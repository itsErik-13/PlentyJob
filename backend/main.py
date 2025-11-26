from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import sys
import os
import concurrent.futures
import uuid
import time
import base64
from selenium.webdriver.common.action_chains import ActionChains

# Add parent directory to path to import search scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infojobs_search import search_infojobs
from indeed_search import search_indeed
from linkedin_search import search_linkedin

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str = ""
    location: str

class InteractionRequest(BaseModel):
    action: str # "click"
    x: int = 0
    y: int = 0

# Job Store
jobs = {}

def run_search_job(job_id, query, location):
    print(f"Starting job {job_id} for {query} in {location}")
    jobs[job_id]['status'] = 'running'
    results = []
    
    def infojobs_callback(status, driver):
        jobs[job_id]['status'] = status
        jobs[job_id]['driver'] = driver
        if status == 'waiting_input':
            # Keep driver accessible
            pass

    # Run searches in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # InfoJobs needs the callback for interaction
        future_infojobs = executor.submit(search_infojobs, query, location, infojobs_callback)
        future_indeed = executor.submit(search_indeed, query, location)
        future_linkedin = executor.submit(search_linkedin, query, location)
        
        try:
            results.extend(future_infojobs.result())
        except Exception as e:
            print(f"InfoJobs search failed: {e}")
            
        try:
            results.extend(future_indeed.result())
        except Exception as e:
            print(f"Indeed search failed: {e}")
            
        try:
            results.extend(future_linkedin.result())
        except Exception as e:
            print(f"LinkedIn search failed: {e}")
            
    jobs[job_id]['status'] = 'completed'
    jobs[job_id]['results'] = results
    jobs[job_id]['driver'] = None # Cleanup driver reference

@app.post("/jobs/start")
async def start_job(request: SearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'id': job_id,
        'status': 'pending',
        'results': [],
        'driver': None,
        'created_at': time.time()
    }
    background_tasks.add_task(run_search_job, job_id, request.query, request.location)
    return {"job_id": job_id}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "id": job['id'],
        "status": job['status'],
        "results": job['results'] if job['status'] == 'completed' else []
    }

@app.get("/jobs/{job_id}/screenshot")
async def get_screenshot(job_id: str):
    if job_id not in jobs or not jobs[job_id]['driver']:
        raise HTTPException(status_code=404, detail="Driver not active")
    
    try:
        driver = jobs[job_id]['driver']
        screenshot = driver.get_screenshot_as_png()
        return Response(content=screenshot, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobs/{job_id}/interact")
async def interact(job_id: str, request: InteractionRequest):
    if job_id not in jobs or not jobs[job_id]['driver']:
        raise HTTPException(status_code=404, detail="Driver not active")
    
    try:
        driver = jobs[job_id]['driver']
        if request.action == 'click':
            # Use CDP (Chrome DevTools Protocol) for low-level mouse interaction.
            # This works inside iframes (like reCAPTCHA) and is undetectable.
            try:
                # Move mouse
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mouseMoved",
                    "x": request.x,
                    "y": request.y
                })
                # Press
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mousePressed",
                    "x": request.x,
                    "y": request.y,
                    "button": "left",
                    "clickCount": 1
                })
                # Release
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mouseReleased",
                    "x": request.x,
                    "y": request.y,
                    "button": "left",
                    "clickCount": 1
                })
                return {"status": "clicked", "method": "CDP"}
            except Exception as cdp_error:
                print(f"CDP Click failed: {cdp_error}")
                # Fallback to ActionChains if CDP fails
                try:
                    actions = ActionChains(driver)
                    # Reset to body top-left then move
                    # Note: This might be offset by scroll if not careful, but CDP is safer.
                    # Using w3c actions pointer move
                    from selenium.webdriver.common.actions.action_builder import ActionBuilder
                    from selenium.webdriver.common.actions.mouse_button import MouseButton
                    
                    action = ActionBuilder(driver)
                    action.pointer_action.move_to_location(request.x, request.y)
                    action.pointer_action.click()
                    action.perform()
                    return {"status": "clicked", "method": "ActionChains"}
                except Exception as ac_error:
                     raise HTTPException(status_code=500, detail=f"Click failed: {ac_error}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_jobs_legacy(request: SearchRequest):
    # Keep legacy endpoint for compatibility if needed, but it blocks
    # Better to return error or redirect
    return {"error": "Use /jobs/start for interactive search"}

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Job Search API is running"}
