import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from database import create_document, get_documents, db
from schemas import Quiz, Submission, CheatSection, Project

app = FastAPI(title="PyMastery API", description="Backend for bilingual Python learning platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PyMastery backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# ---------------------- Seed Data ----------------------

@app.post("/api/seed", tags=["admin"])
def seed_content():
    """Seed quizzes, cheat sections, and projects if empty"""
    # Only seed if empty
    created = {"quizzes": 0, "cheats": 0, "projects": 0}

    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    if db.quiz.count_documents({}) == 0:
        intro_quiz = Quiz(
            slug="python-basics",
            title={"en": "Python Basics", "pl": "Podstawy Pythona"},
            description={
                "en": "Test your knowledge of variables, types and control flow.",
                "pl": "Sprawdź wiedzę o zmiennych, typach i instrukcjach sterujących."
            },
            level="beginner",
            tags=["basics", "syntax"],
            questions=[
                {
                    "id": "q1",
                    "text": {"en": "What is the output of print(type(3.0))?", "pl": "Jaki będzie wynik print(type(3.0))?"},
                    "options": [
                        {"en": "<class 'int'>", "pl": "<class 'int'>"},
                        {"en": "<class 'float'>", "pl": "<class 'float'>"},
                        {"en": "<class 'str'>", "pl": "<class 'str'>"}
                    ],
                    "correct_index": 1,
                    "explanation": {
                        "en": "Numbers with a decimal point are floats in Python.",
                        "pl": "Liczby z częścią dziesiętną to w Pythonie float."
                    }
                },
                {
                    "id": "q2",
                    "text": {"en": "Which keyword starts a function?", "pl": "Jakie słowo kluczowe rozpoczyna funkcję?"},
                    "options": [
                        {"en": "func", "pl": "func"},
                        {"en": "def", "pl": "def"},
                        {"en": "function", "pl": "function"}
                    ],
                    "correct_index": 1,
                    "explanation": {
                        "en": "Functions start with def name():", 
                        "pl": "Funkcje zaczynamy od def nazwa():"
                    }
                }
            ]
        )
        create_document("quiz", intro_quiz)
        created["quizzes"] += 1

    if db.cheatsection.count_documents({}) == 0:
        cheats = [
            CheatSection(
                key="strings",
                title={"en": "Strings", "pl": "Napisy"},
                items=[
                    {"en": "f-strings: f\"Hello {name}\"", "pl": "f-napisy: f\"Cześć {name}\""},
                    {"en": "Methods: .upper(), .split()", "pl": "Metody: .upper(), .split()"}
                ]
            ),
            CheatSection(
                key="lists",
                title={"en": "Lists", "pl": "Listy"},
                items=[
                    {"en": "Comprehension: [x*x for x in xs]", "pl": "Zrozumienia listowe: [x*x for x in xs]"},
                    {"en": "Slicing: xs[a:b]", "pl": "Wycinki: xs[a:b]"}
                ]
            )
        ]
        for c in cheats:
            create_document("cheatsection", c)
            created["cheats"] += 1

    if db.project.count_documents({}) == 0:
        projects = [
            Project(
                slug="auto-report",
                title={"en": "Email Automation: Weekly Report", "pl": "Automatyzacja e-mail: Tygodniowy raport"},
                summary={"en": "Generate and send a weekly CSV summary.", "pl": "Generuj i wysyłaj tygodniowe podsumowanie CSV."},
                steps=[
                    {"en": "Read CSV with pandas", "pl": "Wczytaj CSV w pandas"},
                    {"en": "Aggregate metrics", "pl": "Agreguj metryki"},
                    {"en": "Send via SMTP", "pl": "Wyślij przez SMTP"}
                ],
                difficulty="medium",
                category="automation"
            )
        ]
        for p in projects:
            create_document("project", p)
            created["projects"] += 1

    return {"seeded": created}

# ---------------------- Quizzes ----------------------

@app.get("/api/quizzes", response_model=List[Dict])
def list_quizzes():
    docs = get_documents("quiz")
    # Convert ObjectId to string and return raw dicts
    return [
        {
            **{k: v for k, v in d.items() if k != "_id"},
            "id": str(d.get("_id", ""))
        } for d in docs
    ]

class SubmissionIn(BaseModel):
    quiz_slug: str
    answers: List[int]

@app.post("/api/quizzes/submit")
def submit_quiz(payload: SubmissionIn):
    docs = get_documents("quiz", {"slug": payload.quiz_slug})
    if not docs:
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz = docs[0]
    questions = quiz.get("questions", [])
    score = 0
    for i, q in enumerate(questions):
        if i < len(payload.answers) and payload.answers[i] == q.get("correct_index"):
            score += 1
    result = Submission(quiz_slug=payload.quiz_slug, answers=payload.answers, score=score, total=len(questions))
    create_document("submission", result)
    return {"score": score, "total": len(questions)}

# ---------------------- Cheat Sheet ----------------------

@app.get("/api/cheats", response_model=List[Dict])
def get_cheats():
    docs = get_documents("cheatsection")
    return [
        {
            **{k: v for k, v in d.items() if k != "_id"},
            "id": str(d.get("_id", ""))
        } for d in docs
    ]

# ---------------------- Projects ----------------------

@app.get("/api/projects", response_model=List[Dict])
def list_projects():
    docs = get_documents("project")
    return [
        {
            **{k: v for k, v in d.items() if k != "_id"},
            "id": str(d.get("_id", ""))
        } for d in docs
    ]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
