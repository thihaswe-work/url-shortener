from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Pages"])


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/api-keys")
def api_keys_page(request: Request):
    return templates.TemplateResponse("api_keys.html", {"request": request})


@router.get("/stats/{short_code}")
def stats_page(request: Request, short_code: str):
    return templates.TemplateResponse("stats.html", {"request": request})
