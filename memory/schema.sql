CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    teacher TEXT,
    exam_date TEXT,
    difficulty INTEGER DEFAULT 3,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    title TEXT NOT NULL,
    deadline TEXT,
    status TEXT DEFAULT 'todo',
    priority INTEGER DEFAULT 3,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    title TEXT,
    content TEXT,
    tags TEXT,
    created_at TEXT,
    FOREIGN KEY(course_id) REFERENCES courses(id)
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY,
    category TEXT,
    content TEXT,
    importance INTEGER DEFAULT 3,
    source TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS tool_logs (
    id INTEGER PRIMARY KEY,
    tool_name TEXT,
    arguments TEXT,
    result TEXT,
    status TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS career_opportunities (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    organization TEXT,
    opportunity_type TEXT DEFAULT 'internship',
    location TEXT,
    work_mode TEXT,
    deadline TEXT,
    status TEXT DEFAULT 'saved',
    fit_score INTEGER DEFAULT 60,
    tags TEXT,
    source TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS campus_places (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT 'food',
    location TEXT,
    tags TEXT,
    rating INTEGER DEFAULT 4,
    price_level INTEGER DEFAULT 2,
    mood TEXT,
    notes TEXT,
    last_picked_at TEXT,
    created_at TEXT,
    updated_at TEXT
);
