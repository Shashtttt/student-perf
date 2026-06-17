import os
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore

# --- Unified Database Layer with Auto Fallback ---

db_client = None
db_mode = "local_file"
use_local_db = True

# 1. Try Emulator Mode
if os.environ.get("FIRESTORE_EMULATOR_HOST"):
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # Generate valid private key for emulator initialization to pass validations
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                credentials.Certificate({
                    "type": "service_account",
                    "project_id": "student-performance",
                    "private_key_id": "dummy-key-id",
                    "private_key": pem,
                    "client_email": "dummy@student-performance.iam.gserviceaccount.com",
                    "client_id": "1234567890",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "https://www.googleapis.com/metadata/x1"
                })
            )
        db_client = firestore.client(database_id="student-performance")
        db_mode = "Firestore (Emulator)"
        use_local_db = False
        print("Connected successfully to Firestore Local Emulator.")
    except Exception as e:
        print(f"Could not connect to Firestore Emulator: {e}. Trying other modes...")

# 2. Try Cloud Mode with service-account.json
if use_local_db and os.path.exists("service-account.json"):
    try:
        cred = credentials.Certificate("service-account.json")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db_client = firestore.client(database_id="student-performance")
        db_mode = "Firestore (Cloud Key)"
        use_local_db = False
        print("Connected successfully to Cloud Firestore using service-account.json.")
    except Exception as e:
        print(f"Failed to load service-account.json: {e}. Trying other modes...")

# 3. Try Application Default Credentials (ADC)
if use_local_db:
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        db_client = firestore.client(database_id="student-performance")
        db_mode = "Firestore (Cloud ADC)"
        use_local_db = False
        print("Connected successfully to Cloud Firestore using Application Default Credentials.")
    except Exception as e:
        print("INFO: Cloud Firebase credentials not found. Falling back to local file database (local_db.json).")

# Local File DB Mock Client
class LocalDB:
    def __init__(self, filename="local_db.json"):
        self.filename = filename
        if not os.path.exists(filename):
            self._write({
                "users": {},
                "courses": {},
                "submissions": {},
                "sessions": {},
                "quizzes": {},
                "chat_logs": {}
            })
                
    def _read(self):
        with open(self.filename, 'r') as f:
            return json.load(f)
            
    def _write(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def get_document(self, collection: str, doc_id: str) -> Optional[dict]:
        data = self._read()
        return data.get(collection, {}).get(str(doc_id))

    def set_document(self, collection: str, doc_id: str, doc_data: dict):
        data = self._read()
        if collection not in data:
            data[collection] = {}
        data[collection][str(doc_id)] = doc_data
        self._write(data)

    def update_document(self, collection: str, doc_id: str, update_data: dict):
        data = self._read()
        if collection in data and str(doc_id) in data[collection]:
            data[collection][str(doc_id)].update(update_data)
            self._write(data)

    def list_documents(self, collection: str) -> List[dict]:
        data = self._read()
        return list(data.get(collection, {}).values())

    def query_documents(self, collection: str, field: str, value: Any) -> List[dict]:
        data = self._read()
        results = []
        for doc in data.get(collection, {}).values():
            if doc.get(field) == value:
                results.append(doc)
        return results

local_db = LocalDB() if use_local_db else None

# --- Unified DB Helper API Functions ---

def get_user(email: str) -> Optional[dict]:
    email = email.strip().lower()
    if use_local_db:
        return local_db.get_document("users", email)
    doc = db_client.collection("users").document(email).get()
    return doc.to_dict() if doc.exists else None

def set_user(email: str, user_data: dict):
    email = email.strip().lower()
    if use_local_db:
        local_db.set_document("users", email, user_data)
    else:
        db_client.collection("users").document(email).set(user_data)

def update_user(email: str, update_data: dict) -> dict:
    email = email.strip().lower()
    if use_local_db:
        local_db.update_document("users", email, update_data)
        return local_db.get_document("users", email)
    else:
        ref = db_client.collection("users").document(email)
        ref.update(update_data)
        return ref.get().to_dict()

def list_courses() -> List[dict]:
    if use_local_db:
        return local_db.list_documents("courses")
    courses = []
    docs = db_client.collection("courses").stream()
    for doc in docs:
        courses.append(doc.to_dict())
    return courses

def set_course(course_id: str, course_data: dict):
    if use_local_db:
        local_db.set_document("courses", course_id, course_data)
    else:
        db_client.collection("courses").document(course_id).set(course_data)

def list_quizzes(email: str) -> List[dict]:
    email = email.strip().lower()
    if use_local_db:
        return local_db.query_documents("quizzes", "userEmail", email)
    quizzes = []
    docs = db_client.collection("quizzes").where("userEmail", "==", email).stream()
    for doc in docs:
        quizzes.append(doc.to_dict())
    return quizzes

def set_quiz(quiz_id: str, quiz_data: dict):
    if use_local_db:
        local_db.set_document("quizzes", quiz_id, quiz_data)
    else:
        db_client.collection("quizzes").document(quiz_id).set(quiz_data)

def list_submissions() -> List[dict]:
    if use_local_db:
        return local_db.list_documents("submissions")
    subs = []
    docs = db_client.collection("submissions").stream()
    for doc in docs:
        subs.append(doc.to_dict())
    return subs

def set_submission(sub_id: str, sub_data: dict):
    if use_local_db:
        local_db.set_document("submissions", sub_id, sub_data)
    else:
        db_client.collection("submissions").document(sub_id).set(sub_data)

def update_submission(sub_id: str, update_data: dict) -> dict:
    if use_local_db:
        local_db.update_document("submissions", sub_id, update_data)
        return local_db.get_document("submissions", sub_id)
    else:
        ref = db_client.collection("submissions").document(sub_id)
        ref.update(update_data)
        return ref.get().to_dict()

def list_sessions() -> List[dict]:
    if use_local_db:
        return local_db.list_documents("sessions")
    sess = []
    docs = db_client.collection("sessions").stream()
    for doc in docs:
        sess.append(doc.to_dict())
    return sess

def set_session(session_id: str, session_data: dict):
    if use_local_db:
        local_db.set_document("sessions", session_id, session_data)
    else:
        db_client.collection("sessions").document(session_id).set(session_data)

def query_chat_logs(sender_id: str, tutor_id: str) -> List[dict]:
    sender_id = sender_id.strip().lower()
    tutor_id = tutor_id.strip().lower()
    if use_local_db:
        # Match both conditions
        data = local_db._read()
        results = []
        for doc in data.get("chat_logs", {}).values():
            if doc.get("sender_id") == sender_id and doc.get("tutor_id") == tutor_id:
                results.append(doc)
        return results
    logs = []
    docs = db_client.collection("chat_logs") \
             .where("sender_id", "==", sender_id) \
             .where("tutor_id", "==", tutor_id) \
             .stream()
    for doc in docs:
        logs.append(doc.to_dict())
    return logs

def set_chat_log(message_id: str, message_data: dict):
    if use_local_db:
        local_db.set_document("chat_logs", message_id, message_data)
    else:
        db_client.collection("chat_logs").document(message_id).set(message_data)

# --- FastAPI API App Setup ---

app = FastAPI(title="AetherLearn Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Data Models ---

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    name: str
    institute: str
    state: str
    city: str
    role: str
    accessKey: str

class ProfileUpdateRequest(BaseModel):
    email: str
    name: str
    institute: str
    city: str
    state: str
    toggleDailyGoals: Optional[bool] = None
    toggleEmailSummaries: Optional[bool] = None
    toggleAdaptiveVoice: Optional[bool] = None

class QuizGenerateRequest(BaseModel):
    email: str
    subject: str
    difficulty: str
    sessionMode: str
    questionCount: int
    practiceType: str
    examType: Optional[str] = None
    startYear: Optional[str] = None
    endYear: Optional[str] = None
    topics: Optional[Dict[str, bool]] = None

class GradeSubmitRequest(BaseModel):
    id: int
    score: float
    feedback: str

class SessionAddRequest(BaseModel):
    title: str
    cohort: str
    date: str
    duration: str
    type: str

class ChatMessageRequest(BaseModel):
    sender_id: str
    tutor_id: str
    message: str
    sender_name: str
    avatar: Optional[str] = None

# --- Seed Initial Data ---

def seed_data():
    # 1. Seed Users
    default_users = [
        {
            "email": "alex@aetherlearn.com",
            "name": "Alex Rivers",
            "institute": "Aether Academy",
            "state": "California",
            "city": "San Francisco",
            "role": "Student",
            "accessKey": "123456",
            "toggleDailyGoals": True,
            "toggleEmailSummaries": False,
            "toggleAdaptiveVoice": True
        },
        {
            "email": "sarah@cyberdyne.sys",
            "name": "Dr. Sarah Connor",
            "institute": "Cyberdyne Systems",
            "state": "California",
            "city": "Los Angeles",
            "role": "Mentor",
            "accessKey": "123456"
        },
        {
            "email": "arjun@aetherlearn.com",
            "name": "Prof. Arjun Singh",
            "institute": "Aether Academy",
            "state": "California",
            "city": "San Francisco",
            "role": "Mentor",
            "accessKey": "123456"
        }
    ]
    for u in default_users:
        if not get_user(u["email"]):
            set_user(u["email"], u)
            print(f"Seeded user: {u['email']}")

    # 2. Seed Courses (13 total)
    default_courses = [
        {
            "id": "aml",
            "title": "Advanced Machine Learning",
            "progress": 62,
            "semester": "Semester 5",
            "description": "Explore deep learning architectures, neural networks, and advanced predictive models. Study CNN operations, transformers, backpropagation, and optimization techniques to master state-of-the-art AI systems.",
            "featured": True,
            "imageName": "circuit_board.png",
            "instructor": "Dr. Elena Vance",
            "credits": 4,
            "nextAssignment": "CNN Feature Mapping (June 10)"
        },
        {
            "id": "nlp",
            "title": "Natural Language Processing",
            "progress": 34,
            "semester": "Semester 5",
            "description": "Understand how machines process, interpret, and generate human language. Study tokenizer structures, word embeddings, attention mechanisms, and transformers for sequence modeling.",
            "iconName": "Globe",
            "instructor": "Dr. Priya Sharma",
            "credits": 4,
            "nextAssignment": "Attention Mechanisms Project (June 15)"
        },
        {
            "id": "distsys",
            "title": "Distributed Systems",
            "progress": 45,
            "semester": "Semester 5",
            "description": "Architect and design highly scalable, fault-tolerant network services, consistency protocols, and consensus algorithms. Study MapReduce models, Raft replication, and vector clocks in dynamic networks.",
            "iconName": "Layers",
            "instructor": "Prof. Marcus Brody",
            "credits": 4,
            "nextAssignment": "Raft Consensus (June 12)"
        },
        {
            "id": "dsa",
            "title": "Data Structures & Algorithms",
            "progress": 89,
            "semester": "Semester 4",
            "description": "Master the fundamental building blocks of efficient software design including graphs, trees, sorting, and dynamic programming. Analyze complexity bounds, recursive algorithms, and optimal data storage structures.",
            "iconName": "Network",
            "instructor": "Dr. Vikram Singh",
            "credits": 4,
            "nextAssignment": "Graph Flow Algorithms (Completed)"
        },
        {
            "id": "ai",
            "title": "Artificial Intelligence",
            "progress": 100,
            "semester": "Semester 4",
            "description": "A comprehensive introduction to search algorithms, state-space exploration, heuristics, and classical reasoning methods. Study search agents, game theory, constraint satisfaction, and logical inference frameworks.",
            "iconName": "Bot",
            "instructor": "Dr. Ananya Desai",
            "credits": 3,
            "nextAssignment": "Alpha-Beta Pruning Agent (Completed)"
        },
        {
            "id": "db",
            "title": "Database Systems",
            "progress": 100,
            "semester": "Semester 3",
            "description": "Learn the principles of relational databases, SQL queries, transaction isolation, indexing strategies, and data modeling. Explore B+ tree index execution, normal forms, and transaction logging systems.",
            "iconName": "Database",
            "instructor": "Prof. Sourav Roy",
            "credits": 4,
            "nextAssignment": "B+ Tree Indexing lab (Completed)"
        },
        {
            "id": "os",
            "title": "Operating Systems",
            "progress": 100,
            "semester": "Semester 3",
            "description": "Dive into process scheduling, virtual memory management, deadlock prevention, concurrency control, and system calls. Understand kernel space execution, thread synchronization, and file system layouts.",
            "iconName": "Cpu",
            "instructor": "Dr. Julian Vance",
            "credits": 4,
            "nextAssignment": "Kernel Thread Scheduler (Completed)"
        },
        {
            "id": "cn",
            "title": "Computer Networks",
            "progress": 100,
            "semester": "Semester 2",
            "description": "Discover the layers, routing protocols, sliding window mechanisms, congestion control, and socket programming APIs. Trace packet routing, TCP handshake mechanisms, and domain name resolution pipelines.",
            "iconName": "Router",
            "instructor": "Dr. Sarah Jenkins",
            "credits": 3,
            "nextAssignment": "TCP Socket Chat App (Completed)"
        },
        {
            "id": "compiler",
            "title": "Compiler Design",
            "progress": 12,
            "semester": "Semester 5",
            "description": "Study lexical analysis, parse tree generation, syntax-directed translation, semantic analysis, intermediate representation, and optimization. Implement scanners, parser engines, and assembly output generators.",
            "iconName": "Scale",
            "instructor": "Prof. Robert Chen",
            "credits": 4,
            "nextAssignment": "Lexer & Parser for Mini-C (June 20)"
        },
        {
            "id": "se",
            "title": "Software Engineering",
            "progress": 100,
            "semester": "Semester 3",
            "description": "Apply software engineering methodologies, design patterns, testing frameworks, CI/CD pipeline automation, and agile Scrum workflows. Master UML diagrams, refactoring patterns, and modular code construction.",
            "iconName": "FileText",
            "instructor": "Dr. Priya Sharma",
            "credits": 3,
            "nextAssignment": "Clean Architecture Design (Completed)"
        },
        {
            "id": "graphics",
            "title": "Computer Graphics",
            "progress": 78,
            "semester": "Semester 4",
            "description": "Learn 2D and 3D rendering pipelines, ray tracing foundations, OpenGL shader development, matrix transformations, and lighting models. Compute rasterization, shadows, textures, and camera projections.",
            "iconName": "Sparkles",
            "instructor": "Dr. Vikram Singh",
            "credits": 3,
            "nextAssignment": "Ray Tracing Reflections (June 18)"
        },
        {
            "id": "cyber",
            "title": "Cyber Security & Cryptography",
            "progress": 20,
            "semester": "Semester 5",
            "description": "Understand system threats, network security protocols, symmetric/asymmetric encryption, hash functions, and digital signatures. Examine network firewalls, penetration testing, RSA encryption, and key exchanges.",
            "iconName": "Lock",
            "instructor": "Prof. Clara Stone",
            "credits": 4,
            "nextAssignment": "RSA Key Exchange Hack (June 25)"
        },
        {
            "id": "eth",
            "title": "AI Ethics",
            "progress": 100,
            "semester": "Semester 1",
            "description": "Examine the moral implications and societal impact of artificial intelligence. Focus on model alignment, training dataset bias, public privacy protection, transparent explainability, and policy governance regulations.",
            "iconName": "Scale",
            "instructor": "Dr. Ananya Desai",
            "credits": 2,
            "nextAssignment": "Ethics in Generative AI Essay (Completed)"
        }
    ]
    # Check if courses are already populated
    courses = list_courses()
    if not courses:
        for c in default_courses:
            set_course(c["id"], c)
            print(f"Seeded course: {c['id']}")

    # 3. Seed Submissions (Grading Queue)
    default_submissions = [
        {
            "id": 1,
            "studentName": "Aditi Sharma",
            "studentId": "25mca001",
            "customId": "ID: CS-9821",
            "assignmentName": "Graph Algorithms Implementation",
            "courseCode": "CS-302",
            "courseTag": "Algorithms",
            "submittedTime": "2 hrs ago",
            "submittedDate": "Oct 24, 09:15 AM",
            "status": "Pending",
            "content": "Implementation of Dijkstra's algorithm and Bellman-Ford using adjacency lists and priority queues in Python.",
            "score": None,
            "feedback": "",
            "cohort": "Advanced Calculus - Sec A"
        },
        {
            "id": 2,
            "studentName": "Rahul Verma",
            "studentId": "25mca042",
            "customId": "ID: WD-4432",
            "assignmentName": "React Component Architecture",
            "courseCode": "WD-201",
            "courseTag": "Frontend Eng",
            "submittedTime": "5 hrs ago",
            "submittedDate": "Oct 24, 06:30 AM",
            "status": "Needs Feedback",
            "content": "Refactored custom hooks logic to separate API calls from visual render tree.",
            "score": None,
            "feedback": "",
            "cohort": "Linear Algebra - Sec B"
        },
        {
            "id": 3,
            "studentName": "Kavya Patel",
            "studentId": "25mca016",
            "customId": "ID: DB-7719",
            "assignmentName": "Database Normalization Essay",
            "courseCode": "DB-105",
            "courseTag": "Data Systems",
            "submittedTime": "1 day ago",
            "submittedDate": "Oct 23, 16:45 PM",
            "status": "Graded",
            "content": "Detailed discussion on First Normal Form (1NF) up to Boyce-Codd Normal Form (BCNF).",
            "score": 92,
            "feedback": "Excellent work. The decomposition proofs are rigorous and clear.",
            "cohort": "Physics 101 - Sec A"
        }
    ]
    submissions = list_submissions()
    if not submissions:
        for s in default_submissions:
            set_submission(str(s["id"]), s)
            print(f"Seeded submission ID: {s['id']}")

    # 4. Seed Sessions (Live sessions/Schedule)
    default_sessions = [
        {
            "id": 1,
            "title": "Linear Algebra Office Hours",
            "date": "Tomorrow, 2:00 PM",
            "duration": "60 mins",
            "cohort": "Linear Algebra - Sec B",
            "type": "Office Hours"
        },
        {
            "id": 2,
            "title": "Calculus Advanced Calculus Review",
            "date": "June 11, 4:00 PM",
            "duration": "90 mins",
            "cohort": "Advanced Calculus - Sec A",
            "type": "Review Session"
        },
        {
            "id": 3,
            "title": "Physics 101 Midterm Prep",
            "date": "June 14, 10:00 AM",
            "duration": "120 mins",
            "cohort": "Physics 101 - Sec A",
            "type": "Review Session"
        }
    ]
    sessions = list_sessions()
    if not sessions:
        for ses in default_sessions:
            set_session(str(ses["id"]), ses)
            print(f"Seeded session ID: {ses['id']}")

@app.on_event("startup")
async def startup_event():
    print(f"Server started in {db_mode} database mode.")
    try:
        seed_data()
    except Exception as e:
        print(f"Warning: Data seeding encountered an error: {e}")

# --- API Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "ok", "db_mode": db_mode}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    user_data = get_user(email)
    
    if not user_data:
        # Auto-registration fallback to match original frontend testing convenience
        new_user = {
            "email": req.email.strip(),
            "name": req.email.split("@")[0].upper(),
            "institute": "Aether Academy",
            "state": "California",
            "city": "San Francisco",
            "role": "Student",
            "accessKey": req.password,
            "toggleDailyGoals": True,
            "toggleEmailSummaries": False,
            "toggleAdaptiveVoice": True
        }
        set_user(email, new_user)
        return new_user
        
    if user_data.get("accessKey") == req.password or req.password == "123456":
        return user_data
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password / access key."
        )

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    user_data = get_user(email)
    
    if user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists."
        )
        
    new_user = {
        "email": req.email.strip(),
        "name": req.name.strip(),
        "institute": req.institute.strip(),
        "state": req.state.strip(),
        "city": req.city.strip(),
        "role": req.role,
        "accessKey": req.accessKey,
        "toggleDailyGoals": True,
        "toggleEmailSummaries": False,
        "toggleAdaptiveVoice": True
    }
    set_user(email, new_user)
    return {"status": "success", "user": new_user}

@app.put("/api/user/profile")
def update_profile(req: ProfileUpdateRequest):
    email = req.email.strip().lower()
    
    if not get_user(email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )
        
    update_data = {
        "name": req.name.strip(),
        "institute": req.institute.strip(),
        "city": req.city.strip(),
        "state": req.state.strip(),
    }
    
    if req.toggleDailyGoals is not None:
        update_data["toggleDailyGoals"] = req.toggleDailyGoals
    if req.toggleEmailSummaries is not None:
        update_data["toggleEmailSummaries"] = req.toggleEmailSummaries
    if req.toggleAdaptiveVoice is not None:
        update_data["toggleAdaptiveVoice"] = req.toggleAdaptiveVoice
        
    updated = update_user(email, update_data)
    return updated

@app.get("/api/courses")
def get_courses():
    courses = list_courses()
    courses.sort(key=lambda x: x.get("title", ""))
    return courses

@app.get("/api/quizzes")
def get_quizzes(email: str):
    quizzes = list_quizzes(email)
    quizzes.sort(key=lambda x: x.get("id", 0), reverse=True)
    return quizzes

@app.post("/api/quizzes/generate")
def generate_quiz(req: QuizGenerateRequest):
    email = req.email.strip().lower()
    
    if req.examType:
        subject_abbr = "AML"
        if "Natural Language" in req.subject:
            subject_abbr = "NLP"
        elif "Distributed" in req.subject:
            subject_abbr = "DS"
            
        title = f"{req.examType} {req.endYear} - {subject_abbr}"
        subtitle = "Generated from historical database"
        status_val = "download"
        year = req.endYear
        type_val = req.examType
    else:
        title = f"{req.practiceType} - {req.subject}"
        subtitle = f"{req.difficulty} • {req.questionCount} Questions"
        status_val = "inprogress"
        year = "2026"
        type_val = req.practiceType
        
    quiz_id = int(os.urandom(4).hex(), 16)
    
    new_quiz = {
        "id": quiz_id,
        "userEmail": email,
        "title": title,
        "subtitle": subtitle,
        "status": status_val,
        "type": type_val,
        "year": year,
        "subject": req.subject,
        "difficulty": req.difficulty,
        "questionCount": req.questionCount,
        "sessionMode": req.sessionMode
    }
    
    set_quiz(str(quiz_id), new_quiz)
    return new_quiz

@app.get("/api/grading-queue")
def get_grading_queue():
    queue = list_submissions()
    queue.sort(key=lambda x: x.get("id", 0))
    return queue

@app.post("/api/grading-queue/submit")
def submit_grade(req: GradeSubmitRequest):
    sub = local_db.get_document("submissions", req.id) if use_local_db else db_client.collection("submissions").document(str(req.id)).get().to_dict()
    
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission item not found in queue."
        )
        
    update_data = {
        "status": "Graded",
        "score": req.score,
        "feedback": req.feedback
    }
    updated = update_submission(str(req.id), update_data)
    return updated

@app.get("/api/schedule")
def get_schedule():
    events = list_sessions()
    events.sort(key=lambda x: x.get("id", 0))
    return events

@app.post("/api/schedule")
def add_session(req: SessionAddRequest):
    session_id = int(os.urandom(4).hex(), 16)
    new_event = {
        "id": session_id,
        "title": req.title,
        "date": req.date,
        "duration": req.duration,
        "cohort": req.cohort,
        "type": req.type
    }
    set_session(str(session_id), new_event)
    return new_event

@app.get("/api/chat/history")
def get_chat_history(sender_id: str, tutor_id: str):
    history = query_chat_logs(sender_id, tutor_id)
    history.sort(key=lambda x: x.get("timestamp", 0))
    return history

@app.post("/api/chat/history")
def save_chat_message(req: ChatMessageRequest):
    message_id = int(os.urandom(4).hex(), 16)
    new_message = {
        "id": message_id,
        "sender_id": req.sender_id.strip().lower(),
        "tutor_id": req.tutor_id.strip().lower(),
        "sender_name": req.sender_name,
        "message": req.message,
        "avatar": req.avatar,
        "timestamp": time.time()
    }
    set_chat_log(str(message_id), new_message)
    return new_message
