"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal

# Learning platform schemas

class Question(BaseModel):
    id: str = Field(..., description="Question ID")
    text: Dict[str, str] = Field(..., description="Localized question text, keys like 'en', 'pl'")
    options: List[Dict[str, str]] = Field(..., description="List of options, each option is localized text with keys 'en','pl'")
    correct_index: int = Field(..., ge=0, description="Index of correct option")
    explanation: Dict[str, str] = Field(default_factory=dict, description="Localized explanation")

class Quiz(BaseModel):
    slug: str = Field(..., description="Unique identifier for quiz")
    title: Dict[str, str] = Field(..., description="Localized title")
    description: Dict[str, str] = Field(default_factory=dict)
    questions: List[Question] = Field(default_factory=list)
    level: Literal['beginner','intermediate','advanced'] = 'beginner'
    tags: List[str] = Field(default_factory=list)

class Submission(BaseModel):
    quiz_slug: str
    answers: List[int]
    score: Optional[int] = None
    total: Optional[int] = None
    user_id: Optional[str] = None

class CheatSection(BaseModel):
    key: str
    title: Dict[str, str]
    items: List[Dict[str, str]]

class Project(BaseModel):
    slug: str
    title: Dict[str, str]
    summary: Dict[str, str]
    steps: List[Dict[str, str]]
    difficulty: Literal['easy','medium','hard'] = 'easy'
    category: Literal['core','automation','web','data','testing'] = 'core'

# Example legacy schemas kept for reference

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
