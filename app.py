from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime, timedelta
import os
import random
import secrets
from openai import OpenAI
from dotenv import load_dotenv
import re

# Upload dir for profile images
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'muntalaq-secret-key-2024-change-in-production')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Available courses database for AI matching
AVAILABLE_COURSES = [
    {
        'id': 1,
        'title': 'أساسيات تصميم واجهة و تجربة المستخدم',
        'instructor': 'ليلى إبراهيم',
        'field': 'التصميم',
        'type': 'الدورات',
        'rating': 4.7,
        'reviews': 456,
        'level': 'مبتدئ',
        'duration': '6 أسابيع',
        'price': 0,
        'tags': ['تصميم', 'UI/UX', 'Figma'],
        'image': 'course4.jpg',
        'keywords': ['تصميم', 'واجهات', 'تجربة مستخدم', 'UI', 'UX', 'فيجما', 'Figma', 'تصميم جرافيك']
    },
    {
        'id': 2,
        'title': 'توجيه مهني فردي في علوم البيانات',
        'instructor': 'محمد حسن',
        'field': 'علوم البيانات',
        'type': 'التوجيه',
        'rating': 4.9,
        'reviews': 89,
        'level': 'متوسط',
        'duration': 'ساعة واحدة',
        'price': 150,
        'tags': ['علوم البيانات', 'مسار مهني', 'AI'],
        'image': 'course2.jpg',
        'keywords': ['علوم البيانات', 'data science', 'تحليل بيانات', 'ذكاء اصطناعي', 'AI', 'machine learning', 'بايثون', 'python']
    },
    {
        'id': 3,
        'title': 'أنماط React المتقدمة وأفضل الممارسات',
        'instructor': 'سارة أحمد',
        'field': 'هندسة الواجهة الأمامية',
        'type': 'الدورات',
        'rating': 4.5,
        'reviews': 234,
        'level': 'متقدم',
        'duration': '8 أسابيع',
        'price': 299,
        'tags': ['React', 'JavaScript', 'تطوير الويب'],
        'image': 'course3.jpg',
        'keywords': ['React', 'JavaScript', 'تطوير ويب', 'front-end', 'واجهة أمامية', 'برمجة', 'web development']
    },
    {
        'id': 4,
        'title': 'تطوير تطبيقات Flutter',
        'instructor': 'فاطمة الأحمد',
        'field': 'تطوير تطبيقات الجوال',
        'type': 'الدورات',
        'rating': 4.6,
        'reviews': 312,
        'level': 'متوسط',
        'duration': '10 أسابيع',
        'price': 349,
        'tags': ['Flutter', 'Dart', 'Mobile'],
        'image': 'course4.jpg',
        'keywords': ['Flutter', 'Dart', 'تطبيقات جوال', 'mobile', 'android', 'ios', 'تطوير تطبيقات']
    },
    {
        'id': 5,
        'title': 'استراتيجية الأعمال والقيادة',
        'instructor': 'أحمد السعيد',
        'field': 'إدارة الأعمال',
        'type': 'الدورات',
        'rating': 4.8,
        'reviews': 123,
        'level': 'متقدم',
        'duration': '6 أسابيع',
        'price': 200,
        'tags': ['استراتيجية', 'إدارة', 'قيادة'],
        'image': 'course1.jpg',
        'keywords': ['أعمال', 'إدارة', 'قيادة', 'business', 'management', 'استراتيجية', 'ريادة']
    },
    {
        'id': 6,
        'title': 'البدء بتعلم الآلة',
        'instructor': 'فهد العتيبي',
        'field': 'الذكاء الاصطناعي',
        'type': 'التوجيه',
        'rating': 4.8,
        'reviews': 178,
        'level': 'متوسط',
        'duration': 'ساعتان',
        'price': 349,
        'tags': ['Machine Learning', 'AI', 'Python'],
        'image': 'course5.jpg',
        'keywords': ['تعلم آلة', 'machine learning', 'AI', 'ذكاء اصطناعي', 'بايثون', 'python', 'deep learning']
    },
    {
        'id': 7,
        'title': 'تطوير تطبيقات الويب الحديثة',
        'instructor': 'أحمد السالم',
        'field': 'تطوير الويب',
        'type': 'الدورات',
        'rating': 4.7,
        'reviews': 290,
        'level': 'متوسط',
        'duration': '12 أسبوع',
        'price': 399,
        'tags': ['HTML', 'CSS', 'JavaScript', 'Node.js'],
        'image': 'course3.jpg',
        'keywords': ['تطوير ويب', 'web development', 'HTML', 'CSS', 'JavaScript', 'Node.js', 'برمجة']
    }
]

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL,
        university TEXT,
        major TEXT,
        graduation_year INTEGER,
        academic_year TEXT,
        gpa REAL,
        city TEXT,
        bio TEXT,
        email_notifications INTEGER DEFAULT 1,
        app_notifications INTEGER DEFAULT 1,
        profile_public INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Add columns if DB already exists (migration for old DBs)
    for col, default in [('email_notifications', 1), ('app_notifications', 1), ('profile_public', 1),
                         ('email_verified', 0)]:
        try:
            c.execute(f'ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default}')
        except sqlite3.OperationalError:
            pass
    for col_text in ['verification_token', 'profile_image']:
        try:
            c.execute(f'ALTER TABLE users ADD COLUMN {col_text} TEXT')
        except sqlite3.OperationalError:
            pass
    
    # Interests table
    c.execute('''CREATE TABLE IF NOT EXISTS interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        interest TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Evaluations table - stores individual user evaluations
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER,
        course_name TEXT,
        content_quality INTEGER,
        engagement INTEGER,
        interaction INTEGER,
        instructor_rating INTEGER,
        platform_rating INTEGER,
        would_recommend BOOLEAN,
        comments TEXT,
        strengths TEXT,
        improvements TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Evaluation responses table - stores conversation responses
    c.execute('''CREATE TABLE IF NOT EXISTS evaluation_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evaluation_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
    )''')

    # ============= NEW TABLES =============

    # Real Courses table - created by graduates (FR9)
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        graduate_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        price REAL DEFAULT 0,
        duration TEXT,
        level TEXT,
        field TEXT,
        tags TEXT,
        image TEXT DEFAULT 'course1.jpg',
        status TEXT DEFAULT 'published',  -- published | cancelled | draft
        rating REAL DEFAULT 0,
        reviews_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (graduate_id) REFERENCES users(id)
    )''')

    # Enrollments table - students enrolled in courses (FR7.3, FR7.4, FR8)
    c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        progress INTEGER DEFAULT 0,
        status TEXT DEFAULT 'current',  -- current | completed | cancelled
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id),
        FOREIGN KEY (course_id) REFERENCES courses(id),
        UNIQUE(student_id, course_id)
    )''')

    # Favorites table (FR14)
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (course_id) REFERENCES courses(id),
        UNIQUE(user_id, course_id)
    )''')

    # Graduate Evaluations - students evaluate graduates (FR5)
    c.execute('''CREATE TABLE IF NOT EXISTS graduate_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        graduate_id INTEGER NOT NULL,
        clarity INTEGER,           -- 1-5: clarity of explanation
        content_value INTEGER,     -- 1-5: content value
        interaction INTEGER,       -- 1-5: interaction / participation
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id),
        FOREIGN KEY (graduate_id) REFERENCES users(id)
    )''')

    # Community Posts (FR10)
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Post Likes
    c.execute('''CREATE TABLE IF NOT EXISTS post_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (post_id) REFERENCES posts(id),
        UNIQUE(user_id, post_id)
    )''')

    # Post Comments
    c.execute('''CREATE TABLE IF NOT EXISTS post_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )''')

    # Community Groups (FR10.6, FR10.7)
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        icon TEXT DEFAULT '👥',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (group_id) REFERENCES groups(id),
        UNIQUE(user_id, group_id)
    )''')

    # Group chat messages (real-time community chat per group)
    c.execute('''CREATE TABLE IF NOT EXISTS group_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Chat Messages (FR11.3)
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        message_type TEXT DEFAULT 'text',  -- text | course_offer
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id)
    )''')

    # Course Offers in chat (FR11.4, FR11.5)
    c.execute('''CREATE TABLE IF NOT EXISTS course_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',  -- pending | accepted | rejected
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (message_id) REFERENCES chat_messages(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )''')

    # Lessons (graduate-managed video content per course)
    c.execute('''CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        video_url TEXT,
        duration TEXT,
        order_idx INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )''')

    # Lesson completions (per-student progress tracking)
    c.execute('''CREATE TABLE IF NOT EXISTS lesson_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        lesson_id INTEGER NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id),
        FOREIGN KEY (lesson_id) REFERENCES lessons(id),
        UNIQUE(student_id, lesson_id)
    )''')

    # Password reset tokens
    c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Notifications table - stores real in-app notifications
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notif_type TEXT DEFAULT 'general',
        link TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Seed default groups
    c.execute('SELECT COUNT(*) FROM groups')
    if c.fetchone()[0] == 0:
        default_groups = [
            ('مطورو الويب', 'مجتمع لمطوري الويب ومصممي الواجهات', '💻'),
            ('علوم البيانات', 'نقاش حول علوم البيانات والذكاء الاصطناعي', '📊'),
            ('التصميم الإبداعي', 'مجتمع المصممين UI/UX والجرافيك', '🎨'),
            ('ريادة الأعمال', 'نقاش حول ريادة الأعمال والاستراتيجية', '🚀'),
            ('تطوير الجوال', 'مطوري تطبيقات iOS و Android', '📱'),
        ]
        c.executemany('INSERT INTO groups (name, description, icon) VALUES (?, ?, ?)', default_groups)

    conn.commit()
    conn.close()

def seed_demo_data():
    """Seed the DB with demo graduates + courses so fresh installs have content."""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Only seed if there are no graduates yet
    c.execute("SELECT COUNT(*) FROM users WHERE user_type='graduate'")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    demo_pwd = generate_password_hash('Demo@123')

    demo_graduates = [
        ('أحمد السالم', 'ahmad.salem@muntalaq.com', '0550000001', 'graduate', 'جامعة الملك سعود', 'هندسة البرمجيات', 2023, 'الرياض',
         'مطور ويب خبير مع 8 سنوات في مجال تطوير تطبيقات الويب الحديثة و React.'),
        ('ليلى إبراهيم', 'layla.ibrahim@muntalaq.com', '0550000002', 'graduate', 'جامعة الأميرة نورة', 'تصميم الجرافيك', 2022, 'الرياض',
         'مصممة UI/UX شغوفة بتحسين تجربة المستخدم في المنتجات الرقمية.'),
        ('محمد حسن', 'mohammad.hassan@muntalaq.com', '0550000003', 'graduate', 'جامعة الملك عبدالعزيز', 'علوم البيانات', 2021, 'جدة',
         'عالم بيانات متخصص في التعلم الآلي وتحليل البيانات الضخمة.'),
        ('فاطمة الأحمد', 'fatima.ahmad@muntalaq.com', '0550000004', 'graduate', 'جامعة الملك فهد', 'هندسة الحاسب', 2022, 'الدمام',
         'مطورة تطبيقات جوال خبيرة في Flutter و React Native.'),
        ('أحمد السعيد', 'ahmad.saeed@muntalaq.com', '0550000005', 'graduate', 'جامعة الملك سعود', 'إدارة الأعمال', 2020, 'الرياض',
         'مستشار أعمال واستراتيجية مع خبرة في الشركات الناشئة.'),
        ('لينا', 'lina@muntalaq.com', '0550000006', 'graduate', 'جامعة الملك سعود', 'هندسة البرمجيات', 2023, 'الرياض',
         'مهندسة جودة برمجيات متخصصة في اختبار البرمجيات والاختبار الآلي.'),
    ]

    grad_ids = []
    for name, email, phone, utype, uni, major, grad_year, city, bio in demo_graduates:
        c.execute('''INSERT INTO users (full_name, email, phone, password, user_type, university, major, graduation_year, city, bio, email_verified)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                  (name, email, phone, demo_pwd, utype, uni, major, grad_year, city, bio))
        grad_ids.append(c.lastrowid)

    # Demo courses taught by these graduates
    demo_courses = [
        (grad_ids[0], 'تطوير تطبيقات الويب الحديثة', 'دورة شاملة لتعلم تطوير تطبيقات الويب من الصفر باستخدام أحدث التقنيات.', 299, '12 أسبوع', 'متوسط', 'تطوير الويب', 'HTML,CSS,JavaScript,React', 'course3.jpg', 'published', 4.7, 290),
        (grad_ids[0], 'أنماط React المتقدمة', 'تعلم الأنماط المتقدمة في React وأفضل ممارسات تطوير الواجهات الأمامية.', 349, '8 أسابيع', 'متقدم', 'هندسة الواجهة الأمامية', 'React,JavaScript,TypeScript', 'course3.jpg', 'published', 4.5, 234),
        (grad_ids[1], 'أساسيات تصميم واجهة المستخدم', 'تعلم أساسيات UI/UX وتصميم تجارب مستخدم متميزة.', 0, '6 أسابيع', 'مبتدئ', 'التصميم', 'UI,UX,Figma', 'course4.jpg', 'published', 4.7, 456),
        (grad_ids[2], 'البدء بتعلم الآلة', 'مقدمة عملية لتعلم الآلة باستخدام Python و scikit-learn.', 399, '10 أسابيع', 'متوسط', 'الذكاء الاصطناعي', 'Python,Machine Learning,AI', 'course5.jpg', 'published', 4.8, 178),
        (grad_ids[2], 'توجيه مهني في علوم البيانات', 'جلسة توجيه فردي لرسم مسارك المهني في علوم البيانات.', 150, 'ساعة واحدة', 'متوسط', 'علوم البيانات', 'Data Science,Career', 'course2.jpg', 'published', 4.9, 89),
        (grad_ids[3], 'تطوير تطبيقات Flutter', 'بناء تطبيقات جوال احترافية باستخدام Flutter و Dart.', 349, '10 أسابيع', 'متوسط', 'تطوير تطبيقات الجوال', 'Flutter,Dart,Mobile', 'course4.jpg', 'published', 4.6, 312),
        (grad_ids[4], 'استراتيجية الأعمال والقيادة', 'طور مهاراتك القيادية وتعلم كيف تصنع استراتيجية أعمال ناجحة.', 200, '6 أسابيع', 'متقدم', 'إدارة الأعمال', 'Business,Strategy,Leadership', 'course1.jpg', 'published', 4.8, 123),
        (grad_ids[5], 'Introduction to Software Testing', 'دورة شاملة تُعرّفك بأساسيات اختبار البرمجيات، وأنواع الاختبارات المختلفة كالاختبار اليدوي والآلي، وأفضل الأدوات والممارسات المستخدمة في ضمان جودة البرمجيات.', 199, '6 أسابيع', 'مبتدئ', 'هندسة البرمجيات', 'Testing,QA,Software Quality,Automation', 'Software-Testing.webp', 'published', 4.6, 150),
    ]

    course_ids = []
    for course in demo_courses:
        c.execute('''INSERT INTO courses (graduate_id, title, description, price, duration, level, field, tags, image, status, rating, reviews_count)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', course)
        course_ids.append(c.lastrowid)

    # Seed sample lessons per demo course so progress works out of the box
    sample_lessons = [
        ('الوحدة 1: مقدمة في الموضوع', 'https://www.youtube.com/embed/dQw4w9WgXcQ', '12:30'),
        ('الوحدة 2: المفاهيم الأساسية', 'https://www.youtube.com/embed/dQw4w9WgXcQ', '18:45'),
        ('الوحدة 3: تطبيقات عملية', 'https://www.youtube.com/embed/dQw4w9WgXcQ', '22:10'),
        ('الوحدة 4: مشروع تطبيقي', 'https://www.youtube.com/embed/dQw4w9WgXcQ', '30:00'),
    ]
    # Lessons for all courses except the last one (Software Testing has its own videos)
    for cid in course_ids[:-1]:
        for idx, (title, vurl, dur) in enumerate(sample_lessons):
            c.execute(
                'INSERT INTO lessons (course_id, title, video_url, duration, order_idx) VALUES (?, ?, ?, ?, ?)',
                (cid, title, vurl, dur, idx)
            )

    # Lessons for Introduction to Software Testing with real YouTube videos
    software_testing_lessons = [
        ('الوحدة 1: مقدمة في اختبار البرمجيات', 'https://www.youtube.com/embed/e7X0l8xBS30', ''),
        ('الوحدة 2: أنواع الاختبارات وأدواتها',  'https://www.youtube.com/embed/yETBjKV4cz0', ''),
        ('الوحدة 3: تطبيقات عملية في الاختبار',  'https://www.youtube.com/embed/8yX4Gv5tfn4', ''),
    ]
    for idx, (title, vurl, dur) in enumerate(software_testing_lessons):
        c.execute(
            'INSERT INTO lessons (course_id, title, video_url, duration, order_idx) VALUES (?, ?, ?, ?, ?)',
            (course_ids[-1], title, vurl, dur, idx)
        )

    # --- Demo students with enrollments and completions ---
    demo_students = [
        ('سارة محمد',    'sara.m@student.com',  '0560000001', 'جامعة الملك سعود',     'علوم الحاسب',       2025, 'الرياض'),
        ('عمر الشمري',   'omar.sh@student.com', '0560000002', 'جامعة الملك عبدالعزيز', 'هندسة البرمجيات',  2025, 'جدة'),
        ('نورا الغامدي', 'nora.g@student.com',  '0560000003', 'جامعة الأميرة نورة',   'نظم المعلومات',    2026, 'الرياض'),
    ]
    student_ids = []
    for name, email, phone, uni, major, yr, city in demo_students:
        c.execute('''INSERT INTO users (full_name, email, phone, password, user_type, university, major,
                     graduation_year, city, email_verified) VALUES (?,?,?,?,?,?,?,?,?,1)''',
                  (name, email, phone, demo_pwd, 'student', uni, major, yr, city))
        student_ids.append(c.lastrowid)

    enrollments_data = [
        (student_ids[0], course_ids[0], 'current'),
        (student_ids[0], course_ids[2], 'current'),
        (student_ids[0], course_ids[3], 'completed'),
        (student_ids[1], course_ids[1], 'current'),
        (student_ids[1], course_ids[5], 'current'),
        (student_ids[2], course_ids[3], 'completed'),
        (student_ids[2], course_ids[7], 'current'),
    ]
    for sid, cid, status in enrollments_data:
        try:
            c.execute('INSERT INTO enrollments (student_id, course_id, status) VALUES (?,?,?)', (sid, cid, status))
        except Exception:
            pass

    # Fetch lesson IDs per course for completions
    all_lesson_ids = {}
    for row in c.execute('SELECT id, course_id FROM lessons').fetchall():
        all_lesson_ids.setdefault(row[1], []).append(row[0])

    base_date = datetime.utcnow()
    demo_completions = []
    for i, lid in enumerate(all_lesson_ids.get(course_ids[0], [])[:2]):
        demo_completions.append((student_ids[0], lid, (base_date - timedelta(days=15-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for i, lid in enumerate(all_lesson_ids.get(course_ids[2], [])[:3]):
        demo_completions.append((student_ids[0], lid, (base_date - timedelta(days=12-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for i, lid in enumerate(all_lesson_ids.get(course_ids[3], [])):
        demo_completions.append((student_ids[0], lid, (base_date - timedelta(days=8-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for i, lid in enumerate(all_lesson_ids.get(course_ids[1], [])[:2]):
        demo_completions.append((student_ids[1], lid, (base_date - timedelta(days=10-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for i, lid in enumerate(all_lesson_ids.get(course_ids[5], [])[:3]):
        demo_completions.append((student_ids[1], lid, (base_date - timedelta(days=6-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for i, lid in enumerate(all_lesson_ids.get(course_ids[3], [])):
        demo_completions.append((student_ids[2], lid, (base_date - timedelta(days=7-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for i, lid in enumerate(all_lesson_ids.get(course_ids[7], [])[:2]):
        demo_completions.append((student_ids[2], lid, (base_date - timedelta(days=3-i)).strftime('%Y-%m-%d %H:%M:%S')))
    for sid, lid, ts in demo_completions:
        try:
            c.execute('INSERT INTO lesson_completions (student_id, lesson_id, completed_at) VALUES (?,?,?)', (sid, lid, ts))
        except Exception:
            pass

    conn.commit()
    conn.close()

# Initialize database on first run
if not os.path.exists('database.db'):
    init_db()
    seed_demo_data()
else:
    # Migration: ensure new tables/columns exist on older databases
    _mig_conn = sqlite3.connect('database.db')
    _mig_conn.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notif_type TEXT DEFAULT 'general',
        link TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    _mig_conn.execute('''CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        video_url TEXT,
        duration TEXT,
        order_idx INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    _mig_conn.execute('''CREATE TABLE IF NOT EXISTS lesson_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        lesson_id INTEGER NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, lesson_id)
    )''')
    _mig_conn.execute('''CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used INTEGER DEFAULT 0
    )''')
    for col, default in [('email_verified', 0)]:
        try:
            _mig_conn.execute(f'ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default}')
        except sqlite3.OperationalError:
            pass
    for col_text in ['verification_token', 'profile_image']:
        try:
            _mig_conn.execute(f'ALTER TABLE users ADD COLUMN {col_text} TEXT')
        except sqlite3.OperationalError:
            pass
    # Pre-existing demo accounts should be considered verified so they can log in
    _mig_conn.execute("UPDATE users SET email_verified=1 WHERE email_verified IS NULL OR email_verified=0")
    _mig_conn.commit()
    _mig_conn.close()

# Helper function
def get_db():
    db_path = app.config.get("DATABASE", "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def generate_token(nbytes=24):
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(nbytes)


def simulate_email(to_email, subject, body, link=None):
    """
    Stand-in for a real SMTP send. Logs to the console and stores the message
    so demo reviewers can see what would have been emailed without needing
    an SMTP server. Returns the simulated body for display in flash messages.
    """
    print('=' * 60)
    print(f'[SIMULATED EMAIL] to={to_email}')
    print(f'Subject: {subject}')
    print(body)
    if link:
        print(f'Link: {link}')
    print('=' * 60)
    return body


def normalize_youtube_url(url):
    """Convert any common YouTube URL form into an embeddable iframe URL.

    Accepts: https://www.youtube.com/watch?v=ID, https://youtu.be/ID,
             https://www.youtube.com/shorts/ID, /embed/ID, with extra params.
    Returns the original string unchanged if no YouTube ID can be extracted.
    """
    if not url:
        return url
    url = url.strip()
    patterns = [
        r'(?:youtube\.com/watch\?[^ ]*?v=)([A-Za-z0-9_-]{11})',
        r'(?:youtu\.be/)([A-Za-z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})',
        r'(?:youtube\.com/live/)([A-Za-z0-9_-]{11})',
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return f'https://www.youtube.com/embed/{m.group(1)}'
    return url


def add_notification(user_id, title, message, notif_type='general', link=None):
    """Insert a notification record for a user."""
    conn = get_db()
    conn.execute(
        'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
        (user_id, title, message, notif_type, link)
    )
    conn.commit()
    conn.close()


# --- Content Moderation ---

# Patterns that indicate a student is asking a graduate to do their academic work
_CHEATING_PATTERNS = [
    # Arabic
    'حل الواجب', 'حل واجبي', 'حل واجب', 'حل الاختبار', 'حل اختبار',
    'حل الامتحان', 'حل امتحان', 'حل التمرين', 'حل المسألة لي',
    'اكتب الكود', 'اكتب الكود لي', 'اكتب لي الكود', 'اكتب لي الحل',
    'اكتب الحل', 'ابعث لي الحل', 'ارسل لي الحل', 'ارسل الحل',
    'عطني الحل', 'اعطني الاجابة', 'اعطني الإجابة',
    'اجابة الاختبار', 'إجابة الاختبار', 'اجابة الامتحان', 'إجابة الامتحان',
    'اكتب لي المقال', 'اكتب لي التقرير', 'اكتب لي المشروع',
    'افعل الواجب', 'افعل واجبي', 'نفذ الواجب', 'حل التكليف',
    'حل الكويز', 'حل quiz', 'حل ال quiz',
    # English
    'solve my homework', 'do my homework', 'write my assignment',
    'solve my assignment', 'do my assignment', 'write the code for me',
    'solve my quiz', 'answer the exam', 'write my essay for me',
    'complete my project for me', 'do my project for me',
    'give me the answer', 'send me the solution',
]

# Basic offensive/spam words for community moderation (Arabic + English)
_OFFENSIVE_WORDS = [
    'كلب', 'حمار', 'غبي', 'تافه', 'احمق', 'بغيض',
    'spam', 'scam', 'fake',
]


def moderate_message(content):
    """
    Check if a message violates platform rules (academic dishonesty requests).
    Returns (allowed: bool, reason: str|None).
    """
    content_lower = content.lower()
    for pattern in _CHEATING_PATTERNS:
        if pattern in content_lower or pattern in content:
            return False, (
                'تم رفض رسالتك. لا يُسمح بطلب حل الواجبات أو الاختبارات أو الكويزات. '
                'منصة منطلق مخصصة للتعلم والإرشاد المهني، وليس لإنجاز المهام الأكاديمية نيابةً عنك.'
            )
    return True, None


def moderate_post(content):
    """
    Check community post/comment for offensive content.
    Returns (allowed: bool, reason: str|None).
    """
    content_lower = content.lower()
    for word in _OFFENSIVE_WORDS:
        if word in content_lower:
            return False, 'تم رفض المحتوى. يحتوي على ألفاظ غير لائقة أو مخالفة لقواعد المنصة.'
    if len(content) > 5000:
        return False, 'المحتوى طويل جداً. الحد الأقصى 5000 حرف.'
    return True, None


@app.context_processor
def inject_notification_count():
    """Inject unread notification count into all templates."""
    count = 0
    if 'user_id' in session:
        try:
            conn = get_db()
            row = conn.execute(
                'SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND is_read=0',
                (session['user_id'],)
            ).fetchone()
            conn.close()
            count = row['c'] if row else 0
        except Exception:
            count = 0
    return {'unread_notif_count': count}


# Simple AR/EN translation registry for high-traffic UI strings.
# Templates call t('key') to switch based on session language.
TRANSLATIONS = {
    'ar': {
        'dashboard': 'لوحة التحكم',
        'courses': 'الدورات',
        'my_courses': 'دوراتي',
        'graduates': 'الخريجون',
        'community': 'المجتمع',
        'recommendations': 'التوصيات',
        'search_placeholder': 'ابحث عن دورات، موجهين، أو محتوى...',
        'settings': 'الإعدادات',
        'profile': 'الملف الشخصي',
        'notifications': 'الإشعارات',
        'messages': 'الرسائل',
        'favorites': 'المفضلة',
        'logout': 'تسجيل الخروج',
        'welcome': 'مرحباً',
        'mark_all_read': 'تحديد الكل كمقروء',
        'language': 'اللغة',
        'change': 'تغيير',
        # Settings page
        'settings_title': 'الإعدادات ⚙️',
        'settings_subtitle': 'إدارة حسابك وتفضيلاتك',
        'account_section': 'الحساب',
        'email_label': 'البريد الإلكتروني',
        'password_label': 'كلمة المرور',
        'password_hint': 'قم بتغيير كلمة المرور بانتظام للأمان',
        'notifications_section': 'الإشعارات',
        'email_notifications': '📧 إشعارات البريد',
        'email_notifications_hint': 'تلقي تحديثات عبر البريد الإلكتروني',
        'app_notifications': '🔔 إشعارات التطبيق',
        'app_notifications_hint': 'تلقي إشعارات داخل المنصة (دورات جديدة، رسائل، إنجازات)',
        'privacy_section': 'الخصوصية',
        'profile_visibility': '👤 عرض الملف الشخصي',
        'profile_visibility_hint': 'السماح للآخرين برؤية ملفك الشخصي',
        'language_section': 'اللغة',
        'app_language': '🌐 لغة التطبيق',
        'app_language_hint': 'اختر اللغة التي يظهر بها التطبيق',
        'arabic': 'العربية',
        'english': 'English',
        'session_section': 'الجلسة',
        'logout_hint': 'إنهاء الجلسة الحالية',
        'setting_saved': 'تم حفظ الإعداد',
        'enabled': 'تم التفعيل ✓',
        'disabled': 'تم الإيقاف',
        'save_failed': 'فشل الحفظ، حاول مرة أخرى',
        'connection_failed': 'فشل الاتصال',
        'lang_tooltip': 'تغيير اللغة',
        'role_graduate': '🎓 خريج',
        'role_student': '👤 طالب',
        'chatbot_title': 'المساعد الذكي',
        'chatbot_subtitle': 'أنا هنا لمساعدتك!',
        'quick_actions_label': 'إجراءات سريعة:',
        'qa_courses': '📚 الدورات',
        'qa_help': '❓ مساعدة',
        'qa_account': '👤 الحساب',
        'qa_technical': '🔧 مشكلة تقنية',
        'chatbot_welcome': 'مرحباً {name}! 👋<br>أنا المساعد الذكي لمنصة منطلق. كيف يمكنني مساعدتك اليوم؟',
        'chatbot_placeholder': 'اكتب رسالتك...',
        'chatbot_send': 'إرسال',
        'chatbot_error': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.',
        'chatbot_offline': 'عذراً، لا أستطيع الاتصال الآن. يرجى المحاولة لاحقاً.',
        'qa_msg_courses': 'أريد معرفة المزيد عن الدورات المتاحة',
        'qa_msg_help': 'أحتاج مساعدة في استخدام المنصة',
        'qa_msg_account': 'لدي سؤال عن حسابي',
        'qa_msg_technical': 'أواجه مشكلة تقنية',
        'close': 'إغلاق',
        # Common
        'sar': 'ر.س',
        'free': 'مجاني',
        'details': 'التفاصيل',
        'search': 'بحث',
        'clear': 'مسح',
        'cancel': 'إلغاء',
        'save': 'حفظ',
        'send': 'إرسال',
        'edit': 'تعديل',
        'delete': 'حذف',
        'view': 'عرض',
        'back': 'العودة',
        'submit': 'إرسال',
        'continue': 'متابعة',
        'reset': 'إعادة تعيين',
        'confirm': 'تأكيد',
        'loading': 'جارٍ التحميل...',
        'completed_lower': 'مكتمل',
        'student_unit': 'طالب',
        'students_label': 'طلاب',
        'rating_unit': 'تقييم',
        'course_unit': 'دورة',
        'member_unit': 'عضو',
        'level_beginner': 'مبتدئ',
        'level_intermediate': 'متوسط',
        'level_advanced': 'متقدم',
        'level_all': 'جميع المستويات',
        # Dashboard (student)
        'page_dashboard_title': 'لوحة التحكم',
        'dashboard_welcome': 'مرحباً، {name}! 👋',
        'dashboard_subtitle': 'إليك ملخص لتقدمك وأنشطتك الأخيرة',
        'stats_completed_courses': 'دورة مكتملة',
        'stats_learning_hours': 'ساعة تعلم',
        'stats_goals_achieved': 'أهداف محققة',
        'stats_streak_days': 'أيام متتالية',
        'quick_actions': 'الإجراءات السريعة',
        'continue_learning': 'تابع التعلم',
        'view_all': 'عرض الكل ←',
        'no_courses_yet': 'لم تسجّل في أي دورة بعد.',
        'browse_courses': 'تصفح الدورات',
        'recent_activity': 'النشاط الأخير',
        'no_recent_activity': 'لا يوجد نشاط حديث بعد.',
        'welcome_modal_greeting': 'أهلاً وسهلاً، {name}!',
        'welcome_modal_back': 'يسعدنا عودتك إلى',
        'welcome_modal_subtitle_student': 'استعد لمواصلة رحلتك التعليمية واكتشاف دورات جديدة',
        'welcome_modal_start_student': 'ابدأ التعلم 🚀',
        # Dashboard (graduate)
        'page_dashboard_graduate_title': 'لوحة الخريج',
        'dashboard_welcome_graduate': 'أهلاً، {name}! 🎓',
        'dashboard_subtitle_graduate': 'إدارة دوراتك ومتابعة طلابك من مكان واحد',
        'stats_published_courses': 'دورات منشورة',
        'stats_total_students': 'طلاب مسجلين',
        'stats_avg_rating': 'متوسط التقييم',
        'stats_unread_messages': 'رسائل واردة',
        'graduate_quick_actions': 'إجراءات الخريج السريعة',
        'create_course': 'إنشاء دورة',
        'latest_courses': 'أحدث دوراتك',
        'no_courses_published': 'لم تنشر أي دورة بعد.',
        'create_first_course': 'أنشئ دورتك الأولى',
        'student_enrolled': 'طالب مسجل',
        'manage_content': 'إدارة المحتوى',
        'no_recent_activity_short': 'لا يوجد نشاط حديث.',
        'welcome_modal_subtitle_graduate': 'تابع دوراتك وطلابك وابدأ في نشر المعرفة',
        'welcome_modal_start_graduate': 'ابدأ الآن 🚀',
        # Courses list
        'page_courses_title': 'الدورات',
        'browse_courses_title': 'تصفح الدورات 📚',
        'browse_courses_subtitle': 'اكتشف دورات جديدة وسجّل فيها مباشرة',
        'create_new_course': '+ إنشاء دورة جديدة',
        'search_courses_placeholder': 'ابحث بالعنوان، المدرب، أو الوسوم...',
        'all_prices': 'كل الأسعار',
        'free_only': 'مجانية فقط',
        'paid_only': 'مدفوعة فقط',
        'free_label': 'مجانية',
        'paid_label': 'مدفوعة',
        'found_courses_prefix': 'تم العثور على',
        'found_courses_suffix': 'دورة',
        'matching_query': 'تطابق',
        'level_label_dash': '— المستوى:',
        'no_courses_available': 'لا توجد دورات متاحة حالياً',
        'check_back_soon': 'تحقق مرة أخرى قريباً!',
        # My courses (student)
        'page_my_courses_title': 'دوراتي',
        'my_courses_title': 'دوراتي 📚',
        'my_courses_subtitle': 'تابع تقدمك في الدورات المسجلة',
        'filter_all': 'الكل',
        'filter_current': 'الحالية',
        'filter_completed': 'المكتملة',
        'filter_cancelled': 'الملغاة',
        'status_completed': '✅ مكتملة',
        'status_cancelled': '❌ ملغاة',
        'no_courses': 'لا توجد دورات',
        'enroll_new_course': 'ابدأ بالتسجيل في دورة جديدة!',
        'continue_action': 'متابعة',
        'view_action': 'عرض',
        # My courses (graduate)
        'my_courses_graduate_title': 'دوراتي 🎓',
        'my_courses_graduate_subtitle': 'إدارة الدورات التي أنشأتها',
        'status_published': '✓ منشورة',
        'status_cancelled_short': '✕ ملغاة',
        'status_draft': 'مسودة',
        'manage_content_videos': '🎬 إدارة المحتوى والفيديوهات',
        'cancel_course_action': '❌ إلغاء',
        'republish_action': '↻ إعادة النشر',
        'confirm_cancel_course': 'هل أنت متأكد من إلغاء هذه الدورة؟',
        'no_courses_created': 'لم تنشئ أي دورة بعد',
        'share_expertise': 'شارك خبرتك مع الطلاب وابدأ تعليم اليوم!',
        'create_first_course_btn': '+ أنشئ دورتك الأولى',
        # Course details
        'back_to_courses': '← العودة للدورات',
        'reviews_count_suffix': 'تقييم',
        'about_course': 'عن الدورة',
        'no_description': 'لا يوجد وصف متاح لهذه الدورة.',
        'course_content_label': 'محتوى الدورة',
        'continue_learning_btn': '▶ متابعة التعلم',
        'enroll_to_access': 'سجّل في الدورة للوصول إلى جميع الوحدات',
        'watch_action': '▶ مشاهدة',
        'locked': 'مقفل',
        'no_lessons_yet': 'لم يقم المدرب بإضافة محتوى للدورة بعد.',
        'enrolled_status': '✅ أنت مسجل في هذه الدورة',
        'go_to_my_courses': 'انتقل إلى دوراتي',
        'pay_and_enroll': '💳 ادفع وسجّل —',
        'enroll_free': '🎓 سجّل مجاناً',
        'remove_from_favorites': '❤️ إزالة من المفضلة',
        'add_to_favorites': '🤍 أضف للمفضلة',
        'instructor_label': 'المدرب',
        # Course content
        'back_to_course_details': '← العودة لتفاصيل الدورة',
        'progress_label': 'التقدم:',
        'instructor_dot': '👤 المدرب:',
        'lesson_completed_count': 'درس مكتمل',
        'course_outline': '📋 محتوى الدورة',
        'no_lessons_added': 'لم يقم المدرب بإضافة دروس بعد.',
        'toggle_complete_title': 'تبديل الإكمال',
        'cancel_short': 'إلغاء',
        'mark_complete': 'إكمال',
        'no_video_for_lesson': 'لا يوجد فيديو لهذا الدرس بعد',
        # Course lessons
        'page_course_lessons_title': 'إدارة محتوى',
        'back_to_my_courses': '← العودة لدوراتي',
        'manage_course_content_title': 'إدارة محتوى الدورة 🎬',
        'add_new_lesson': 'إضافة درس جديد',
        'lesson_title_label': 'عنوان الدرس *',
        'lesson_title_placeholder': 'مثال: الوحدة 1 — مقدمة في الموضوع',
        'youtube_link_label': 'رابط فيديو يوتيوب',
        'youtube_link_placeholder': 'https://www.youtube.com/watch?v=... أو https://youtu.be/...',
        'youtube_link_hint': 'يمكنك لصق أي رابط يوتيوب وسنحوّله تلقائياً للعرض داخل المنصة.',
        'duration_label': 'المدة',
        'duration_placeholder': 'مثال: 12:30',
        'add_lesson_btn': '+ إضافة الدرس',
        'existing_lessons': 'الدروس الحالية',
        'preview': 'معاينة',
        'confirm_delete_lesson': 'حذف هذا الدرس؟',
        'no_lessons_yet_admin': 'لم تضِف أي درس بعد. ابدأ بإضافة أول درس أعلاه.',
        # Course new
        'page_course_new_title': 'إنشاء دورة جديدة',
        'create_course_title': 'إنشاء دورة جديدة ✨',
        'create_course_subtitle': 'شارك خبرتك مع طلاب منصة منطلق',
        'course_title_label': 'عنوان الدورة *',
        'course_title_placeholder': 'مثال: أساسيات React للمبتدئين',
        'course_description_label': 'وصف الدورة *',
        'course_description_placeholder': 'اشرح ما سيتعلمه الطالب وما الذي تغطيه الدورة...',
        'price_sar_label': 'السعر (ر.س)',
        'leave_zero_free': 'اترك 0 لجعلها مجانية',
        'duration_input_placeholder': 'مثال: 6 أسابيع',
        'level_label': 'المستوى',
        'field_label': 'المجال',
        'field_placeholder': 'مثال: تطوير الويب',
        'tags_label': 'الوسوم',
        'tags_placeholder': 'React, JavaScript, Frontend (افصل بفاصلة)',
        'course_image_label': 'صورة الدورة',
        'image_business': 'صورة 1 - أعمال',
        'image_data': 'صورة 2 - بيانات',
        'image_web': 'صورة 3 - تطوير ويب',
        'image_design': 'صورة 4 - تصميم / موبايل',
        'image_ai': 'صورة 5 - ذكاء اصطناعي',
        'publish_course': '✨ نشر الدورة',
        # Checkout
        'page_checkout_title': 'الدفع',
        'checkout_back': '← العودة لتفاصيل الدورة',
        'checkout_title': 'إتمام عملية الدفع',
        'checkout_subtitle': 'أكمل بيانات الدفع للتسجيل في الدورة',
        'fix_errors_below': 'يرجى تصحيح الأخطاء التالية:',
        'card_data_section': '💳 بيانات البطاقة البنكية',
        'cardholder_name': 'اسم حامل البطاقة *',
        'cardholder_name_placeholder': 'الاسم كما يظهر على البطاقة',
        'card_number': 'رقم البطاقة *',
        'expiry_date': 'تاريخ الانتهاء *',
        'cvv_code': 'رمز CVV *',
        'accepted_cards': 'البطاقات المقبولة:',
        'ssl_notice': 'جميع بيانات الدفع مشفرة وآمنة. لن يتم حفظ معلومات بطاقتك.',
        'pay_action': 'ادفع',
        'pay_action_suffix': 'والتسجيل في الدورة',
        'order_summary': 'ملخص الطلب',
        'instructor_inline': 'المدرب:',
        'course_price_label': 'سعر الدورة',
        'total_label': 'الإجمالي',
        'refund_guarantee': '✓ ضمان استرداد المبلغ خلال 7 أيام',
        'processing_payment': '⏳ جاري معالجة الدفع...',
        # Community
        'page_community_title': 'المجتمع',
        'community_title': 'المجتمع 👥',
        'community_subtitle': 'انضم للمجموعات وشارك الأفكار',
        'view_posts': '📝 عرض المنشورات',
        'posts_label': 'منشور',
        'comments_label': 'تعليق',
        'likes_label': 'إعجاب',
        'trending_topics': '🔥 الموضوعات الأكثر رواجاً',
        'available_groups': 'المجموعات المتاحة',
        'open_chat': '💬 افتح الدردشة',
        'leave_group_confirm': 'مغادرة المجموعة؟',
        'member_click_to_leave': '✓ عضو (اضغط للمغادرة)',
        'join_group': '+ انضم للمجموعة',
        # Community posts
        'page_posts_title': 'المنشورات',
        'posts_title': 'المنشورات 📝',
        'community_groups_link': '← المجتمع والمجموعات',
        'search_posts_placeholder': '🔍 ابحث في المنشورات...',
        'share_thoughts': 'شارك أفكارك مع المجتمع...',
        'tags_input_placeholder': 'وسوم (افصل بفاصلة)',
        'publish_post': '📤 نشر',
        'no_results': 'لا توجد نتائج',
        'no_posts_yet': 'لا توجد منشورات بعد',
        'try_different_keywords': 'جرب كلمات بحث مختلفة',
        'be_first_to_post': 'كن أول من ينشر!',
        'add_comment_placeholder': 'أضف تعليقاً...',
        'comment_added': '✓ تم إضافة التعليق',
        'failed_add_comment': 'فشل إضافة التعليق',
        # Group chat
        'back_to_community': '← العودة للمجتمع',
        'leave_group_btn': 'مغادرة',
        'join_to_chat': 'انضم للمجموعة للمشاركة في الدردشة وقراءة الرسائل.',
        'group_chat_label': '💬 الدردشة الجماعية',
        'no_messages_be_first': 'لا توجد رسائل بعد. كن أول من يبدأ الدردشة!',
        'message_placeholder': 'اكتب رسالة...',
        'members_label': 'الأعضاء',
        'graduate_role': 'خريج',
        'student_role': 'طالب',
        'graduate_role_full': '👨‍🎓 خريج',
        'student_role_full': '🎓 طالب',
        'message_blocked': 'لم يُسمح بإرسال هذه الرسالة.',
        # Graduates
        'page_graduates_title': 'تقييم الخريجين',
        'graduates_title': 'تقييم الخريجين ⭐',
        'graduates_subtitle': 'قيّم الخريجين الذين تعلمت منهم وساعد الآخرين في اختيار الأفضل',
        'top_rated': '🏆 الأعلى تقييماً',
        'search_graduate_placeholder': '🔍 ابحث عن خريج بالاسم...',
        'all_graduates': 'جميع الخريجين',
        'view_profile_btn': '👁 عرض الملف',
        'rate_btn': '⭐ تقييم',
        'try_different_search': 'جرب البحث بكلمات مختلفة',
        # Graduate profile
        'back_to_graduates': '← العودة للخريجين',
        'rate_now_btn': '⭐ قيّم الآن',
        'message_btn': '💬 راسل',
        'overall_rating': 'التقييم العام',
        'clarity_rating': 'وضوح الشرح',
        'content_value_rating': 'قيمة المحتوى',
        'interaction_rating': 'التفاعل',
        'about_prefix': 'عن',
        'courses_of_prefix': 'دورات',
        'no_published_courses': 'لا توجد دورات منشورة',
        'recent_reviews': 'آخر التقييمات',
        'graduation_class': 'دفعة',
        # Profile
        'page_profile_title': 'الملف الشخصي',
        'change_photo': '📷 تغيير الصورة',
        'gpa_label': '📊 معدل:',
        'edit_profile_btn': 'تعديل الملف',
        'personal_info': 'المعلومات الشخصية',
        'full_name_label': 'الاسم الكامل',
        'phone_label': 'رقم الجوال',
        'city_label': 'المدينة',
        'university_label': 'الجامعة',
        'major_label': 'التخصص',
        'gpa_full_label': 'المعدل التراكمي',
        'bio_label': 'نبذة عني',
        'save_changes': '✓ حفظ التغييرات',
        'cancel_no_save': '✕ إلغاء بدون حفظ',
        'interests': 'الاهتمامات',
        'new_interest_placeholder': 'اهتمام جديد',
        'contact_info': 'معلومات الاتصال',
        'email_short': 'البريد',
        'phone_short': 'الجوال',
        'not_specified': 'غير محدد',
        'unsaved_changes_confirm': 'لديك تغييرات غير محفوظة. هل أنت متأكد من الإلغاء؟',
        'upload_failed': 'تعذر رفع الصورة',
        'upload_failed_general': 'فشل رفع الصورة',
        # Recommendations
        'page_recommendations_title': 'التوصيات الذكية',
        'smart_recommendations': 'التوصيات الذكية',
        'recommendations_subtitle': 'محتوى مخصص لك بناءً على اهتماماتك وأهدافك',
        'view_details_btn': 'عرض التفاصيل',
        'sar_currency': 'ريال',
        'analyze_my_profile': '🔍 تحليل ملفي الشخصي',
        'profile_analysis': '🔍 تحليل ملفك الشخصي',
        'ai_assistant': 'المساعد الذكي',
        'ai_help_choose': 'دعني أساعدك في اختيار الدورات المناسبة لك',
        'ai_welcome_msg': 'مرحباً! 👋 أنا المساعد الذكي في منصة منطلق. سأساعدك في اختيار الدورات المناسبة لأهدافك. فضلا اكتب كلمه ابدأ',
        'message_placeholder_here': 'اكتب رسالتك هنا...',
        'quick_analyze_profile': '⚡ تحليل سريع بناءً على ملفي الشخصي',
        'personalized_advice': '💡 نصائح مخصصة لك',
        'suggested_path': '🎯 مسارك التعليمي المقترح',
        'recommended_courses': 'الدورات الموصى بها',
        'thinking': 'جاري التفكير...',
        'sorry_error': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.',
        'get_recommendations_now': '✨ احصل على توصياتي الآن',
        'error_generating': 'حدث خطأ أثناء توليد التوصيات',
        'analyzing_profile': 'جاري تحليل ملفك الشخصي...',
        'analyzing_profile_short': 'جارٍ تحليل ملفك...',
        'strengths': '💪 نقاط القوة',
        'recommended_fields': '🎯 المجالات الموصى بها',
        'suggested_skills': '🛠 مهارات مقترحة',
        'career_path': '🚀 المسار المهني المقترح',
        'analysis_failed': 'تعذر التحليل الآن.',
        'analysis_error': 'حدث خطأ أثناء التحليل.',
        # Favorites
        'page_favorites_title': 'المفضلة',
        'favorites_title': 'المفضلة ❤️',
        'favorites_subtitle': 'الدورات التي حفظتها',
        'favorites_empty': 'قائمة المفضلة فارغة',
        'add_courses_to_favorites': 'أضف دورات للمفضلة لتجدها هنا بسهولة',
        # Messages
        'page_messages_title': 'الرسائل',
        'messages_title': 'الرسائل 💬',
        'conversations': 'المحادثات',
        'no_conversations_yet': 'لا توجد محادثات بعد',
        'start_chat_from_graduates': 'ابدأ محادثة مع خريج من صفحة تقييم الخريجين',
        'online': '● متصل',
        'share_course_btn': '📚 مشاركة دورة',
        'choose_course_to_share': 'اختر دورة لمشاركتها:',
        'course_offer': '📚 عرض دورة',
        'accept_offer': '✓ قبول',
        'reject_offer': '✕ رفض',
        'offer_accepted': '✓ تم القبول',
        'offer_rejected': '✕ مرفوض',
        'student_accepted_offer': '✓ قبل الطالب العرض',
        'student_rejected_offer': '✕ رفض الطالب العرض',
        'awaiting_response': '⏳ بانتظار الرد',
        'send_msg_short': '➤ إرسال',
        'choose_chat': 'اختر محادثة',
        'choose_chat_subtitle': 'اختر محادثة من القائمة الجانبية للبدء',
        'failed_send_msg': 'فشل إرسال الرسالة',
        'failed_share_course': 'فشل مشاركة الدورة',
        # Notifications
        'page_notifications_title': 'الإشعارات',
        'notifications_title': 'الإشعارات 🔔',
        'no_notifications_yet': 'لا توجد إشعارات بعد',
        'updating': 'جارٍ التحديث...',
        'done_check': '✓ تم',
        # Evaluation
        'page_evaluation_title': 'لوحة التقييم',
        'evaluation_dashboard': 'لوحة التقييم 📊',
        'content_quality': 'جودة المحتوى',
        'engagement': 'التفاعل',
        'responsiveness': 'الاستجابة',
        'overall_rating_label': 'التقييم الإجمالي',
        'total_reviews': 'إجمالي التقييمات',
        # Evaluate graduate
        'page_evaluate_graduate_title': 'تقييم',
        'back_to_profile': '← العودة للملف',
        'evaluate_graduate_prefix': 'تقييم',
        'rating_criteria': 'معايير التقييم',
        'rate_each_criterion': 'قيّم كل معيار من 1 إلى 5 نجوم',
        'clarity_q': '1. وضوح الشرح',
        'clarity_hint': 'هل كانت الشروحات واضحة ومفهومة؟',
        'content_value_q': '2. قيمة المحتوى',
        'content_value_hint': 'هل كان المحتوى مفيداً ومناسباً للمستوى؟',
        'interaction_q': '3. التفاعل والمشاركة',
        'interaction_hint': 'هل كان الخريج متفاعلاً ومشاركاً؟',
        'additional_notes': 'ملاحظات إضافية',
        'share_experience_placeholder': 'شاركنا تجربتك مع هذا الخريج...',
        'rating_result': 'نتيجة التقييم',
        'out_of_5': 'من 5',
        'submit_rating': '✓ إرسال التقييم',
        'reset_rating': '↻ إعادة تعيين',
        'reset_confirm': 'هل تريد إعادة تعيين التقييم؟',
        'rate_all_criteria': 'يرجى تقييم جميع المعايير الثلاثة قبل الإرسال.',
        # Evaluation form
        'page_evaluation_form_title': 'تقييم المنصة',
        'rate_your_experience': '📝 قيّم تجربتك',
        'help_improve_subtitle': 'ساعدنا في تحسين المنصة من خلال مشاركة تجربتك',
        'eval_assistant': 'مساعد التقييم الذكي',
        'eval_assistant_subtitle': 'سأطرح عليك بعض الأسئلة البسيطة عن تجربتك',
        'eval_welcome_msg': 'مرحباً! 🎉 شكراً لك على وقتك لتقييم تجربتك معنا. دعنا نبدأ - كيف تقيم جودة المحتوى التعليمي الذي تلقيته؟ (من 0% إلى 100%)',
        'answer_here_placeholder': 'اكتب إجابتك هنا...',
        'question_n_of': 'السؤال {n} من 9',
        'completed_label': 'مكتمل! 🎉',
        'finish_evaluation': '✅ إنهاء التقييم',
        'eval_saved': '✅ تم حفظ تقييمك بنجاح!',
        'eval_save_error': 'حدث خطأ أثناء حفظ التقييم',
        'eval_error_prefix': 'حدث خطأ:',
        # Evaluation aggregate
        'page_evaluation_agg_title': 'التقييم الشامل',
        'evaluation_agg_title': 'لوحة التقييم الشاملة 📊',
        'evaluation_agg_subtitle': 'تقييمات جميع المستخدمين للمنصة',
        'my_personal_eval': '👤 تقييمي الشخصي',
        'recommend_percentage': 'يوصون بالمنصة',
        'avg_ratings': 'متوسط التقييمات',
        'recent_evaluations': 'آخر التقييمات',
        'recommends': '✅ يوصي',
        'does_not_recommend': '❌ لا يوصي',
        'content_short': 'المحتوى',
        'no_evaluations_yet': 'لا توجد تقييمات بعد',
        'be_first_evaluate': 'كن أول من يقيم المنصة!',
        'start_evaluation': '✏️ ابدأ التقييم الآن',
        # Evaluation personal
        'page_eval_personal_title': 'تقييمي',
        'my_personal_evaluation': 'تقييمي الشخصي',
        'view_aggregate': 'عرض التقييم الشامل',
        'new_evaluation': 'تقييم جديد',
        'thanks_for_time': 'شكراً لك على وقتك!',
        'rating_helps_improve': 'تقييمك يساعدنا في تحسين المنصة وتقديم تجربة أفضل',
        'will_recommend': 'سأوصي بالمنصة',
        'wont_recommend': 'لن أوصي بالمنصة حالياً',
        'detailed_ratings': 'تقييمات تفصيلية',
        'instructor_rating_label': 'تقييم المدرب',
        'platform_rating_label': 'تقييم المنصة',
        'strengths_label': 'نقاط القوة',
        'improvements_label': '🔧 مجالات التحسين',
        'extra_comments_label': '💬 تعليقات إضافية',
        'evaluated_on': 'تم التقييم في:',
        # Auth - login
        'page_login_title': 'تسجيل الدخول',
        'login_title': 'تسجيل الدخول',
        'login_welcome_back': 'مرحباً بعودتك إلى منطلق',
        'login_as': 'تسجيل الدخول كـ',
        'login_as_student': 'طالب 🎓',
        'login_as_graduate': 'خريج 👨‍🎓',
        'email_field_label': 'البريد الإلكتروني',
        'password_field_label': 'كلمة المرور',
        'enter_password_placeholder': 'أدخل كلمة المرور',
        'remember_me': 'تذكرني',
        'forgot_password_q': 'نسيت كلمة المرور؟',
        'login_btn': 'تسجيل الدخول',
        'no_account': 'ليس لديك حساب؟',
        'join_thousands': 'انضم إلى آلاف الطلاب والخريجين على منطلق',
        'create_account_btn': 'إنشاء حساب جديد',
        'learn_about_platform': 'تعرّف على المنصة ←',
        # Account selection
        'page_account_select_title': 'اختر نوع الحساب',
        'choose_account_type': 'اختر نوع حسابك',
        'choose_account_subtitle': 'سجل كطالب للتعلم أو كخريج للتوجيه',
        'student_role_short': 'طالب',
        'graduate_role_short': 'خريج',
        'for_learning': 'للتعلم والتطوير',
        'for_mentoring': 'للتوجيه والإرشاد',
        'continue_as_student': 'متابعة كطالب',
        'continue_as_graduate': 'متابعة كخريج',
        'have_account': 'لديك حساب بالفعل؟',
        'login_link': 'تسجيل الدخول',
        'back_home': 'العودة للرئيسية',
        # Signup
        'page_student_signup_title': 'إنشاء حساب طالب',
        'page_graduate_signup_title': 'إنشاء حساب خريج',
        'create_student_account': 'إنشاء حساب طالب',
        'create_graduate_account': 'إنشاء حساب خريج',
        'start_journey': 'ابدأ رحلتك التعليمية معنا',
        'share_expertise_subtitle': 'شارك خبرتك ووجّه الطلاب نحو المستقبل',
        'full_name_required': 'الاسم الكامل *',
        'enter_full_name': 'أدخل اسمك الكامل',
        'email_required': 'البريد الإلكتروني *',
        'phone_required': 'رقم الجوال *',
        'university_required': 'الجامعة *',
        'choose_university': 'اختر الجامعة',
        'university_other': 'أخرى',
        'major_required': 'التخصص *',
        'major_placeholder_student': 'مثال: علوم الحاسب',
        'major_placeholder_graduate': 'مثال: هندسة البرمجيات',
        'academic_year_required': 'السنة الدراسية *',
        'choose_year': 'اختر السنة',
        'year_1': 'السنة الأولى',
        'year_2': 'السنة الثانية',
        'year_3': 'السنة الثالثة',
        'year_4': 'السنة الرابعة',
        'year_5': 'السنة الخامسة',
        'graduation_year_required': 'سنة التخرج *',
        'year_2015_or_before': '2015 أو قبل',
        'password_required': 'كلمة المرور *',
        'enter_strong_password': 'أدخل كلمة مرور قوية',
        'req_min_length': '6 أحرف على الأقل',
        'req_uppercase': 'حرف كبير واحد على الأقل (A-Z)',
        'req_number': 'رقم واحد على الأقل (0-9)',
        'req_special': 'رمز خاص واحد على الأقل (@.-_/)',
        'confirm_password_required': 'تأكيد كلمة المرور *',
        'reenter_password': 'أعد إدخال كلمة المرور',
        'passwords_dont_match': 'كلمات المرور غير متطابقة',
        'agree_terms_prefix': 'أوافق على',
        'terms_link': 'الشروط والأحكام',
        'and': 'و',
        'privacy_link': 'سياسة الخصوصية',
        'create_account_submit': 'إنشاء الحساب',
        'back_to_account_type': 'العودة لاختيار نوع الحساب',
        'password_validation_alert': 'يرجى التأكد من استيفاء جميع متطلبات كلمة المرور',
        # Forgot/reset password
        'page_forgot_title': 'استعادة كلمة المرور',
        'forgot_title': 'استعادة كلمة المرور',
        'forgot_subtitle': 'أدخل بريدك الإلكتروني وسنرسل لك رابط استعادة',
        'send_reset_link': 'إرسال رابط الاستعادة',
        'back_to_login': '← العودة لتسجيل الدخول',
        'page_reset_title': 'إعادة تعيين كلمة المرور',
        'reset_title': 'تعيين كلمة مرور جديدة',
        'reset_subtitle': 'اختر كلمة مرور قوية لحسابك',
        'new_password_label': 'كلمة المرور الجديدة',
        'password_rules_inline': '6 أحرف على الأقل · حرف كبير · رقم · رمز خاص (@.-_/)',
        'confirm_password_label': 'تأكيد كلمة المرور',
        'update_password_btn': 'تحديث كلمة المرور',
        # Landing
        'page_landing_title': 'منطلق - ابدأ رحلتك التعليمية والمهنية',
        'hero_heading': 'منطلق... منصتك للإرشاد<br>والتطوير المهني',
        'hero_subtitle': 'منصة تربط بين الطلاب والخريجين لتبادل الخبرات والمعرفة في رحلة النجاح المهني',
        'start_journey_btn': 'ابدأ رحلتك',
        'how_can_we_help': 'كيف يمكننا مساعدتك؟',
        'feature_analytics': 'تحليل وتقارير',
        'feature_analytics_desc': 'تحليل شامل لأدائك ونموك المهني مع تقارير مفصلة',
        'feature_explore': 'دروس الاستكشاف',
        'feature_explore_desc': 'اكتشف مجالات جديدة ووسع آفاقك المهنية',
        'feature_courses': 'دورات متنوعة',
        'feature_courses_desc': 'مكتبة واسعة من الدورات في مختلف المجالات',
        'feature_connect': 'خدمات ربط',
        'feature_connect_desc': 'تواصل مع خريجين ناجحين في مجالك',
        'gpa_calc_title': ' احسب المعدل التراكمي',
        'gpa_calc_subtitle': 'احسب معدلك الفصلي والتراكمي بسهولة من خلال إدخال المواد ومساعداتها ودرجاتك',
        'prev_gpa_section': '* المعدل التراكمي السابق (اختياري)',
        'prev_gpa_label': 'المعدل التراكمي السابق',
        'prev_gpa_placeholder': 'مثال: 4.50',
        'prev_credits_label': 'عدد الساعات المجتازة',
        'prev_credits_placeholder': 'مثال: 60',
        'add_subject_btn': '+ إضافة مادة',
        'current_semester_subjects': '* المواد الدراسية للفصل الحالي',
        'subject_name': 'اسم المادة',
        'credit_hours': 'الساعات',
        'grade_label': 'الدرجة',
        'subject_placeholder': 'مثال: حساب التفاضل والتكامل',
        'choose_grade': 'اختر',
        'calculate_gpa': 'احسب المعدل',
        'cumulative_gpa': 'المعدل التراكمي',
        'semester_gpa': 'المعدل الفصلي',
        'out_of_5_max': 'من 5.00',
        'grade_scale': 'مقياس الدرجات',
        'recommended_for_you': 'موصى به لك',
        'recommended_for_you_subtitle': 'دورات مخصصة بناءً على اهتماماتك وأهدافك المهنية',
        'all_btn': 'الكل',
        'courses_btn_short': 'دورات',
        'badge_course': 'دورة',
        'badge_mentoring': 'توجيه',
        'badge_tip': 'نصيحة',
        'weeks_unit': 'أسابيع',
        'weeks_6': '6 أسابيع',
        'weeks_4': '4 أسابيع',
        'weeks_8': '8 أسابيع',
        'weeks_10': '10 أسابيع',
        'one_hour': 'ساعة واحدة',
        'two_hours': 'ساعتان',
        'all_levels': 'جميع المستويات',
        'start_now_btn': 'ابدأ الآن',
        'book_session': 'احجز جلسة',
        'view_more_recommendations': 'عرض المزيد من التوصيات',
        'muntalaq_in_numbers': 'منطلق بالأرقام',
        'active_students': 'طالب نشط',
        'graduate_collaborators': 'خريج متعاون',
        'available_courses': 'دورة متاحة',
        'about_platform': 'عن المنصة',
        'faq_what_is': 'ما هي منصة منطلق؟',
        'faq_what_is_a': 'منطلق هي منصة تعليمية ومهنية تربط بين الطلاب والخريجين الناجحين، توفر دورات تدريبية متنوعة، توجيه مهني فردي، وأدوات مثل حاسبة المعدل التراكمي لدعم رحلتك الأكاديمية والمهنية.',
        'faq_how_works': 'كيف تعمل منصة منطلق؟',
        'faq_how_works_a': 'يمكنك التسجيل كطالب أو كخريج، استكشاف الدورات المتاحة، حجز جلسات توجيه مهني، المشاركة في المجتمع، وتتبع تقدمك الأكاديمي من خلال لوحة التحكم الشخصية.',
        'faq_who_advisors': 'من هم المستشارون في منطلق؟',
        'faq_who_advisors_a': 'المستشارون هم خريجون ناجحون في مختلف المجالات المهنية، يمتلكون خبرات عملية واسعة ومستعدون لمشاركة معرفتهم ودعم الطلاب في رحلتهم المهنية.',
        'faq_who_for': 'لمن تناسب منصة منطلق؟',
        'faq_who_for_a': 'تناسب منطلق الطلاب الذين يبحثون عن التوجيه والتطوير المهني، والخريجين الذين يرغبون في مشاركة خبراتهم، وأي شخص يسعى لتطوير مهاراته في بيئة تعليمية داعمة.',
        'testimonials': 'آراء عملائنا',
        'testimonial_1': 'منصة رائعة ساعدتني في تطوير مهاراتي والتواصل مع خبراء في مجالي',
        'testimonial_2': 'تجربة مميزة! الدورات عالية الجودة والتوجيه المهني احترافي جداً',
        'testimonial_3': 'أفضل منصة للتطوير المهني! نصائح عملية ومفيدة جداً من خريجين محترفين',
        'cta_start_today': 'ابدأ رحلتك اليوم',
        'cta_start_subtitle': 'انضم إلى آلاف الطلاب والخريجين على منطلق',
        'cta_start_free': 'ابدأ مجاناً الآن',
        'platform_tagline': 'منصة تربط الطلاب بالخريجين للتوجيه المهني وتطوير المهارات',
        'quick_links': 'روابط سريعة',
        'contact_us': 'تواصل معنا',
        'about_us': 'من نحن',
        'mentors': 'الموجهون',
        'policy_privacy_section': 'السياسة والخصوصية',
        'terms_conditions': 'الشروط والأحكام',
        'privacy_policy': 'سياسة الخصوصية',
        'refund_policy': 'سياسة الاسترجاع',
        'important_links': 'روابط مهمة',
        'help_center': 'مركز المساعدة',
        'faqs': 'الأسئلة الشائعة',
        'copyright_line': '© 2024 منطلق. جميع الحقوق محفوظة | تم التطوير بواسطة فريق منطلق',
        # Terms
        'page_terms_title': 'الشروط والأحكام وسياسة الخصوصية',
        'terms_title': 'الشروط والأحكام وسياسة الخصوصية',
        'last_updated': 'آخر تحديث: أبريل 2025',
        'terms_section_heading': 'الشروط والأحكام',
        'terms_para_1': 'بإنشاء حساب على منصة <strong>منطلق</strong>، يوافق المستخدمون على تقديم معلومات دقيقة وكاملة أثناء التسجيل. تجمع المنصة المعلومات الشخصية والأكاديمية الأساسية كالاسم والبريد الإلكتروني والجامعة والتخصص، وذلك بهدف تحسين تجربة المستخدم وتقديم توصيات مخصصة.',
        'terms_para_2': 'يتحمل المستخدمون المسؤولية الكاملة عن الحفاظ على سرية بيانات اعتماد حساباتهم، وعن جميع الأنشطة التي تجري من خلال حساباتهم. يُحظر مشاركة بيانات الدخول مع أي طرف آخر.',
        'academic_integrity_title': '⚠️ سياسة النزاهة الأكاديمية',
        'academic_integrity_body': 'تُطبّق المنصة آليات فلترة محتوى تمنع استخدام المنصة لطلب الحلول الأكاديمية المباشرة، بما يشمل طلب حل الواجبات والاختبارات والكويزات. أي محاولة لانتهاك هذه السياسة قد تؤدي إلى تعليق الحساب.',
        'terms_para_3': 'تستخدم المنصة الذكاء الاصطناعي لتقديم خدمات التوصيات والدعم. يوافق المستخدمون على أن تعاملاتهم قد تُحلَّل بهدف تحسين أداء النظام ودقة التوصيات.',
        'privacy_section_heading': 'سياسة الخصوصية',
        'data_we_collect': 'البيانات التي نجمعها',
        'data_full_name': 'الاسم الكامل',
        'data_email': 'البريد الإلكتروني',
        'data_university_major': 'الجامعة والتخصص',
        'data_phone': 'رقم الجوال',
        'data_year_gpa': 'السنة الأكاديمية والمعدل',
        'data_career_interests': 'الاهتمامات المهنية',
        'how_we_use_data': 'كيف نستخدم بياناتك',
        'use_data_1': 'تحسين تجربة المستخدم وتقديم توصيات مخصصة بناءً على ملفك الأكاديمي',
        'use_data_2': 'تمكين التواصل بين الطلاب والخريجين عبر المنصة',
        'use_data_3': 'تحليل التفاعلات لتحسين أداء النظام ودقة التوصيات',
        'use_data_4': 'إرسال الإشعارات المتعلقة بالدورات والرسائل والمجتمع',
        'cybersecurity_title': '🛡️ الأمن السيبراني وحماية البيانات',
        'cyber_1': 'جميع بيانات المستخدمين مخزّنة بشكل آمن ولن تُشارَك مع أي طرف ثالث.',
        'cyber_2': 'كلمات المرور مشفّرة باستخدام خوارزميات تجزئة قوية ولا يمكن الاطلاع عليها حتى للمشغّلين.',
        'cyber_3': 'تُطبّق المنصة خوارزميات فلترة المحتوى بالذكاء الاصطناعي لمنع المحتوى غير اللائق والضار والاستخدام في الغش الأكاديمي.',
        'cyber_4': 'بيانات الدفع مشفّرة بالكامل ولا تُخزَّن على خوادم المنصة.',
        'cyber_5': 'تُستخدم البيانات المجمّعة فقط لتحسين وظائف النظام، التخصيص، وتعزيز تجربة المستخدم بشكل عام.',
        'user_rights': 'حقوق المستخدم',
        'right_access': 'الحق في الوصول لبياناتك',
        'right_correct': 'الحق في تصحيح بياناتك',
        'right_delete': 'الحق في حذف حسابك',
        'right_export': 'الحق في تصدير بياناتك',
        'agreement_banner': 'باستخدام منصة <strong>منطلق</strong>، فإنك توافق على جميع الشروط والأحكام المذكورة أعلاه. للاستفسار أو لممارسة حقوقك، تواصل معنا عبر البريد الإلكتروني: <strong>privacy@muntalaq.com</strong>',
        'back_btn': '← العودة',
    },
    'en': {
        'dashboard': 'Dashboard',
        'courses': 'Courses',
        'my_courses': 'My Courses',
        'graduates': 'Graduates',
        'community': 'Community',
        'recommendations': 'Recommendations',
        'search_placeholder': 'Search for courses, mentors, or content...',
        'settings': 'Settings',
        'profile': 'Profile',
        'notifications': 'Notifications',
        'messages': 'Messages',
        'favorites': 'Favorites',
        'logout': 'Logout',
        'welcome': 'Welcome',
        'mark_all_read': 'Mark all as read',
        'language': 'Language',
        'change': 'Change',
        # Settings page
        'settings_title': 'Settings ⚙️',
        'settings_subtitle': 'Manage your account and preferences',
        'account_section': 'Account',
        'email_label': 'Email',
        'password_label': 'Password',
        'password_hint': 'Change your password regularly for security',
        'notifications_section': 'Notifications',
        'email_notifications': '📧 Email Notifications',
        'email_notifications_hint': 'Receive updates by email',
        'app_notifications': '🔔 App Notifications',
        'app_notifications_hint': 'Receive in-app notifications (new courses, messages, achievements)',
        'privacy_section': 'Privacy',
        'profile_visibility': '👤 Profile Visibility',
        'profile_visibility_hint': 'Allow others to see your profile',
        'language_section': 'Language',
        'app_language': '🌐 App Language',
        'app_language_hint': 'Choose the language the app is shown in',
        'arabic': 'العربية',
        'english': 'English',
        'session_section': 'Session',
        'logout_hint': 'End the current session',
        'setting_saved': 'Setting saved',
        'enabled': 'Enabled ✓',
        'disabled': 'Disabled',
        'save_failed': 'Save failed, please try again',
        'connection_failed': 'Connection failed',
        'lang_tooltip': 'Change language',
        'role_graduate': '🎓 Graduate',
        'role_student': '👤 Student',
        'chatbot_title': 'AI Assistant',
        'chatbot_subtitle': "I'm here to help!",
        'quick_actions_label': 'Quick actions:',
        'qa_courses': '📚 Courses',
        'qa_help': '❓ Help',
        'qa_account': '👤 Account',
        'qa_technical': '🔧 Technical Issue',
        'chatbot_welcome': 'Hi {name}! 👋<br>I\'m the Muntalaq AI assistant. How can I help you today?',
        'chatbot_placeholder': 'Type your message...',
        'chatbot_send': 'Send',
        'chatbot_error': 'Sorry, an error occurred. Please try again.',
        'chatbot_offline': "Sorry, I can't connect right now. Please try later.",
        'qa_msg_courses': 'I want to know more about available courses',
        'qa_msg_help': 'I need help using the platform',
        'qa_msg_account': 'I have a question about my account',
        'qa_msg_technical': "I'm experiencing a technical issue",
        'close': 'Close',
        # Common
        'sar': 'SAR',
        'free': 'Free',
        'details': 'Details',
        'search': 'Search',
        'clear': 'Clear',
        'cancel': 'Cancel',
        'save': 'Save',
        'send': 'Send',
        'edit': 'Edit',
        'delete': 'Delete',
        'view': 'View',
        'back': 'Back',
        'submit': 'Submit',
        'continue': 'Continue',
        'reset': 'Reset',
        'confirm': 'Confirm',
        'loading': 'Loading...',
        'completed_lower': 'complete',
        'student_unit': 'student',
        'students_label': 'students',
        'rating_unit': 'reviews',
        'course_unit': 'course',
        'member_unit': 'members',
        'level_beginner': 'Beginner',
        'level_intermediate': 'Intermediate',
        'level_advanced': 'Advanced',
        'level_all': 'All Levels',
        # Dashboard (student)
        'page_dashboard_title': 'Dashboard',
        'dashboard_welcome': 'Hi {name}! 👋',
        'dashboard_subtitle': "Here's a summary of your progress and recent activity",
        'stats_completed_courses': 'Completed Courses',
        'stats_learning_hours': 'Learning Hours',
        'stats_goals_achieved': 'Goals Achieved',
        'stats_streak_days': 'Day Streak',
        'quick_actions': 'Quick Actions',
        'continue_learning': 'Continue Learning',
        'view_all': 'View All →',
        'no_courses_yet': "You haven't enrolled in any course yet.",
        'browse_courses': 'Browse Courses',
        'recent_activity': 'Recent Activity',
        'no_recent_activity': 'No recent activity yet.',
        'welcome_modal_greeting': 'Welcome, {name}!',
        'welcome_modal_back': 'Glad to have you back at',
        'welcome_modal_subtitle_student': 'Get ready to continue your learning journey and discover new courses',
        'welcome_modal_start_student': 'Start Learning 🚀',
        # Dashboard (graduate)
        'page_dashboard_graduate_title': 'Graduate Dashboard',
        'dashboard_welcome_graduate': 'Hi {name}! 🎓',
        'dashboard_subtitle_graduate': 'Manage your courses and track your students from one place',
        'stats_published_courses': 'Published Courses',
        'stats_total_students': 'Enrolled Students',
        'stats_avg_rating': 'Average Rating',
        'stats_unread_messages': 'Inbox Messages',
        'graduate_quick_actions': 'Graduate Quick Actions',
        'create_course': 'Create Course',
        'latest_courses': 'Your Latest Courses',
        'no_courses_published': "You haven't published any course yet.",
        'create_first_course': 'Create your first course',
        'student_enrolled': 'students enrolled',
        'manage_content': 'Manage Content',
        'no_recent_activity_short': 'No recent activity.',
        'welcome_modal_subtitle_graduate': 'Track your courses and students and start sharing knowledge',
        'welcome_modal_start_graduate': 'Get Started 🚀',
        # Courses list
        'page_courses_title': 'Courses',
        'browse_courses_title': 'Browse Courses 📚',
        'browse_courses_subtitle': 'Discover new courses and enroll directly',
        'create_new_course': '+ Create New Course',
        'search_courses_placeholder': 'Search by title, instructor, or tags...',
        'all_prices': 'All Prices',
        'free_only': 'Free only',
        'paid_only': 'Paid only',
        'free_label': 'Free',
        'paid_label': 'Paid',
        'found_courses_prefix': 'Found',
        'found_courses_suffix': 'course(s)',
        'matching_query': 'matching',
        'level_label_dash': '— Level:',
        'no_courses_available': 'No courses available right now',
        'check_back_soon': 'Check back soon!',
        # My courses (student)
        'page_my_courses_title': 'My Courses',
        'my_courses_title': 'My Courses 📚',
        'my_courses_subtitle': 'Track your progress in enrolled courses',
        'filter_all': 'All',
        'filter_current': 'Current',
        'filter_completed': 'Completed',
        'filter_cancelled': 'Cancelled',
        'status_completed': '✅ Completed',
        'status_cancelled': '❌ Cancelled',
        'no_courses': 'No courses',
        'enroll_new_course': 'Start by enrolling in a new course!',
        'continue_action': 'Continue',
        'view_action': 'View',
        # My courses (graduate)
        'my_courses_graduate_title': 'My Courses 🎓',
        'my_courses_graduate_subtitle': 'Manage the courses you created',
        'status_published': '✓ Published',
        'status_cancelled_short': '✕ Cancelled',
        'status_draft': 'Draft',
        'manage_content_videos': '🎬 Manage Content & Videos',
        'cancel_course_action': '❌ Cancel',
        'republish_action': '↻ Republish',
        'confirm_cancel_course': 'Are you sure you want to cancel this course?',
        'no_courses_created': "You haven't created any course yet",
        'share_expertise': 'Share your expertise with students and start teaching today!',
        'create_first_course_btn': '+ Create your first course',
        # Course details
        'back_to_courses': '← Back to Courses',
        'reviews_count_suffix': 'reviews',
        'about_course': 'About the Course',
        'no_description': 'No description available for this course.',
        'course_content_label': 'Course Content',
        'continue_learning_btn': '▶ Continue Learning',
        'enroll_to_access': 'Enroll in the course to access all units',
        'watch_action': '▶ Watch',
        'locked': 'Locked',
        'no_lessons_yet': "The instructor hasn't added content yet.",
        'enrolled_status': '✅ You are enrolled in this course',
        'go_to_my_courses': 'Go to My Courses',
        'pay_and_enroll': '💳 Pay & Enroll —',
        'enroll_free': '🎓 Enroll for Free',
        'remove_from_favorites': '❤️ Remove from Favorites',
        'add_to_favorites': '🤍 Add to Favorites',
        'instructor_label': 'Instructor',
        # Course content
        'back_to_course_details': '← Back to Course Details',
        'progress_label': 'Progress:',
        'instructor_dot': '👤 Instructor:',
        'lesson_completed_count': 'lessons completed',
        'course_outline': '📋 Course Content',
        'no_lessons_added': "The instructor hasn't added lessons yet.",
        'toggle_complete_title': 'Toggle completion',
        'cancel_short': 'Undo',
        'mark_complete': 'Complete',
        'no_video_for_lesson': 'No video for this lesson yet',
        # Course lessons
        'page_course_lessons_title': 'Manage Content',
        'back_to_my_courses': '← Back to My Courses',
        'manage_course_content_title': 'Manage Course Content 🎬',
        'add_new_lesson': 'Add a New Lesson',
        'lesson_title_label': 'Lesson Title *',
        'lesson_title_placeholder': 'Example: Unit 1 — Introduction',
        'youtube_link_label': 'YouTube Video URL',
        'youtube_link_placeholder': 'https://www.youtube.com/watch?v=... or https://youtu.be/...',
        'youtube_link_hint': 'You can paste any YouTube link and we will embed it automatically.',
        'duration_label': 'Duration',
        'duration_placeholder': 'Example: 12:30',
        'add_lesson_btn': '+ Add Lesson',
        'existing_lessons': 'Existing Lessons',
        'preview': 'Preview',
        'confirm_delete_lesson': 'Delete this lesson?',
        'no_lessons_yet_admin': "You haven't added any lesson yet. Start by adding your first one above.",
        # Course new
        'page_course_new_title': 'Create New Course',
        'create_course_title': 'Create a New Course ✨',
        'create_course_subtitle': 'Share your expertise with Muntalaq students',
        'course_title_label': 'Course Title *',
        'course_title_placeholder': 'Example: React Basics for Beginners',
        'course_description_label': 'Course Description *',
        'course_description_placeholder': 'Explain what students will learn and what the course covers...',
        'price_sar_label': 'Price (SAR)',
        'leave_zero_free': 'Leave 0 to make it free',
        'duration_input_placeholder': 'Example: 6 weeks',
        'level_label': 'Level',
        'field_label': 'Field',
        'field_placeholder': 'Example: Web Development',
        'tags_label': 'Tags',
        'tags_placeholder': 'React, JavaScript, Frontend (comma separated)',
        'course_image_label': 'Course Image',
        'image_business': 'Image 1 - Business',
        'image_data': 'Image 2 - Data',
        'image_web': 'Image 3 - Web Development',
        'image_design': 'Image 4 - Design / Mobile',
        'image_ai': 'Image 5 - AI',
        'publish_course': '✨ Publish Course',
        # Checkout
        'page_checkout_title': 'Checkout',
        'checkout_back': '← Back to Course Details',
        'checkout_title': 'Complete Your Payment',
        'checkout_subtitle': 'Complete your payment details to enroll in the course',
        'fix_errors_below': 'Please fix the following errors:',
        'card_data_section': '💳 Card Details',
        'cardholder_name': 'Cardholder Name *',
        'cardholder_name_placeholder': 'Name as shown on the card',
        'card_number': 'Card Number *',
        'expiry_date': 'Expiry Date *',
        'cvv_code': 'CVV *',
        'accepted_cards': 'Accepted Cards:',
        'ssl_notice': 'All payment data is encrypted and secure. We will not store your card details.',
        'pay_action': 'Pay',
        'pay_action_suffix': 'and enroll',
        'order_summary': 'Order Summary',
        'instructor_inline': 'Instructor:',
        'course_price_label': 'Course Price',
        'total_label': 'Total',
        'refund_guarantee': '✓ 7-day money-back guarantee',
        'processing_payment': '⏳ Processing payment...',
        # Community
        'page_community_title': 'Community',
        'community_title': 'Community 👥',
        'community_subtitle': 'Join groups and share ideas',
        'view_posts': '📝 View Posts',
        'posts_label': 'posts',
        'comments_label': 'comments',
        'likes_label': 'likes',
        'trending_topics': '🔥 Trending Topics',
        'available_groups': 'Available Groups',
        'open_chat': '💬 Open Chat',
        'leave_group_confirm': 'Leave the group?',
        'member_click_to_leave': '✓ Member (click to leave)',
        'join_group': '+ Join Group',
        # Community posts
        'page_posts_title': 'Posts',
        'posts_title': 'Posts 📝',
        'community_groups_link': '← Community & Groups',
        'search_posts_placeholder': '🔍 Search posts...',
        'share_thoughts': 'Share your thoughts with the community...',
        'tags_input_placeholder': 'tags (comma separated)',
        'publish_post': '📤 Publish',
        'no_results': 'No results',
        'no_posts_yet': 'No posts yet',
        'try_different_keywords': 'Try different keywords',
        'be_first_to_post': 'Be the first to post!',
        'add_comment_placeholder': 'Add a comment...',
        'comment_added': '✓ Comment added',
        'failed_add_comment': 'Failed to add comment',
        # Group chat
        'back_to_community': '← Back to Community',
        'leave_group_btn': 'Leave',
        'join_to_chat': 'Join the group to participate in the chat and read messages.',
        'group_chat_label': '💬 Group Chat',
        'no_messages_be_first': 'No messages yet. Be the first to start the chat!',
        'message_placeholder': 'Type a message...',
        'members_label': 'Members',
        'graduate_role': 'Graduate',
        'student_role': 'Student',
        'graduate_role_full': '👨‍🎓 Graduate',
        'student_role_full': '🎓 Student',
        'message_blocked': 'This message is not allowed.',
        # Graduates
        'page_graduates_title': 'Rate Graduates',
        'graduates_title': 'Rate Graduates ⭐',
        'graduates_subtitle': "Rate the graduates you've learned from and help others choose",
        'top_rated': '🏆 Top Rated',
        'search_graduate_placeholder': '🔍 Search graduate by name...',
        'all_graduates': 'All Graduates',
        'view_profile_btn': '👁 View Profile',
        'rate_btn': '⭐ Rate',
        'try_different_search': 'Try searching with different keywords',
        # Graduate profile
        'back_to_graduates': '← Back to Graduates',
        'rate_now_btn': '⭐ Rate Now',
        'message_btn': '💬 Message',
        'overall_rating': 'Overall Rating',
        'clarity_rating': 'Clarity of Explanation',
        'content_value_rating': 'Content Value',
        'interaction_rating': 'Interaction',
        'about_prefix': 'About',
        'courses_of_prefix': 'Courses by',
        'no_published_courses': 'No published courses',
        'recent_reviews': 'Recent Reviews',
        'graduation_class': 'Class of',
        # Profile
        'page_profile_title': 'Profile',
        'change_photo': '📷 Change Photo',
        'gpa_label': '📊 GPA:',
        'edit_profile_btn': 'Edit Profile',
        'personal_info': 'Personal Information',
        'full_name_label': 'Full Name',
        'phone_label': 'Phone Number',
        'city_label': 'City',
        'university_label': 'University',
        'major_label': 'Major',
        'gpa_full_label': 'Cumulative GPA',
        'bio_label': 'About Me',
        'save_changes': '✓ Save Changes',
        'cancel_no_save': '✕ Cancel without saving',
        'interests': 'Interests',
        'new_interest_placeholder': 'New interest',
        'contact_info': 'Contact Info',
        'email_short': 'Email',
        'phone_short': 'Phone',
        'not_specified': 'Not specified',
        'unsaved_changes_confirm': 'You have unsaved changes. Are you sure you want to cancel?',
        'upload_failed': 'Failed to upload image',
        'upload_failed_general': 'Image upload failed',
        # Recommendations
        'page_recommendations_title': 'Smart Recommendations',
        'smart_recommendations': 'Smart Recommendations',
        'recommendations_subtitle': 'Personalized content based on your interests and goals',
        'view_details_btn': 'View Details',
        'sar_currency': 'SAR',
        'analyze_my_profile': '🔍 Analyze my profile',
        'profile_analysis': '🔍 Profile Analysis',
        'ai_assistant': 'AI Assistant',
        'ai_help_choose': 'Let me help you choose the right courses',
        'ai_welcome_msg': "Hi! 👋 I'm the Muntalaq AI assistant. I'll help you choose courses that match your goals. Please type the word start.",
        'message_placeholder_here': 'Type your message...',
        'quick_analyze_profile': '⚡ Quick analysis based on my profile',
        'personalized_advice': '💡 Personalized Advice',
        'suggested_path': '🎯 Suggested Learning Path',
        'recommended_courses': 'Recommended Courses',
        'thinking': 'Thinking...',
        'sorry_error': 'Sorry, an error occurred. Please try again.',
        'get_recommendations_now': '✨ Get my recommendations now',
        'error_generating': 'An error occurred while generating recommendations',
        'analyzing_profile': 'Analyzing your profile...',
        'analyzing_profile_short': 'Analyzing your profile...',
        'strengths': '💪 Strengths',
        'recommended_fields': '🎯 Recommended Fields',
        'suggested_skills': '🛠 Suggested Skills',
        'career_path': '🚀 Suggested Career Path',
        'analysis_failed': "Couldn't analyze right now.",
        'analysis_error': 'An error occurred during analysis.',
        # Favorites
        'page_favorites_title': 'Favorites',
        'favorites_title': 'Favorites ❤️',
        'favorites_subtitle': "Courses you've saved",
        'favorites_empty': 'Your favorites list is empty',
        'add_courses_to_favorites': 'Add courses to favorites to find them here easily',
        # Messages
        'page_messages_title': 'Messages',
        'messages_title': 'Messages 💬',
        'conversations': 'Conversations',
        'no_conversations_yet': 'No conversations yet',
        'start_chat_from_graduates': 'Start a chat with a graduate from the Rate Graduates page',
        'online': '● Online',
        'share_course_btn': '📚 Share Course',
        'choose_course_to_share': 'Choose a course to share:',
        'course_offer': '📚 Course Offer',
        'accept_offer': '✓ Accept',
        'reject_offer': '✕ Reject',
        'offer_accepted': '✓ Accepted',
        'offer_rejected': '✕ Rejected',
        'student_accepted_offer': '✓ The student accepted the offer',
        'student_rejected_offer': '✕ The student rejected the offer',
        'awaiting_response': '⏳ Awaiting response',
        'send_msg_short': '➤ Send',
        'choose_chat': 'Choose a conversation',
        'choose_chat_subtitle': 'Pick a conversation from the side panel to start',
        'failed_send_msg': 'Failed to send message',
        'failed_share_course': 'Failed to share course',
        # Notifications
        'page_notifications_title': 'Notifications',
        'notifications_title': 'Notifications 🔔',
        'no_notifications_yet': 'No notifications yet',
        'updating': 'Updating...',
        'done_check': '✓ Done',
        # Evaluation
        'page_evaluation_title': 'Evaluation Dashboard',
        'evaluation_dashboard': 'Evaluation Dashboard 📊',
        'content_quality': 'Content Quality',
        'engagement': 'Engagement',
        'responsiveness': 'Responsiveness',
        'overall_rating_label': 'Overall Rating',
        'total_reviews': 'Total Reviews',
        # Evaluate graduate
        'page_evaluate_graduate_title': 'Rate',
        'back_to_profile': '← Back to Profile',
        'evaluate_graduate_prefix': 'Rate',
        'rating_criteria': 'Rating Criteria',
        'rate_each_criterion': 'Rate each criterion from 1 to 5 stars',
        'clarity_q': '1. Clarity of Explanation',
        'clarity_hint': 'Were the explanations clear and understandable?',
        'content_value_q': '2. Content Value',
        'content_value_hint': 'Was the content useful and appropriate for the level?',
        'interaction_q': '3. Interaction & Participation',
        'interaction_hint': 'Was the graduate engaged and responsive?',
        'additional_notes': 'Additional Notes',
        'share_experience_placeholder': 'Share your experience with this graduate...',
        'rating_result': 'Rating Score',
        'out_of_5': 'out of 5',
        'submit_rating': '✓ Submit Rating',
        'reset_rating': '↻ Reset',
        'reset_confirm': 'Reset this rating?',
        'rate_all_criteria': 'Please rate all three criteria before submitting.',
        # Evaluation form
        'page_evaluation_form_title': 'Platform Evaluation',
        'rate_your_experience': '📝 Rate your experience',
        'help_improve_subtitle': 'Help us improve the platform by sharing your experience',
        'eval_assistant': 'Evaluation AI Assistant',
        'eval_assistant_subtitle': "I'll ask you a few simple questions about your experience",
        'eval_welcome_msg': "Hi! 🎉 Thanks for taking the time to share your experience. Let's start — how would you rate the quality of the educational content you received? (0% to 100%)",
        'answer_here_placeholder': 'Type your answer here...',
        'question_n_of': 'Question {n} of 9',
        'completed_label': 'Completed! 🎉',
        'finish_evaluation': '✅ Finish evaluation',
        'eval_saved': '✅ Your evaluation has been saved!',
        'eval_save_error': 'An error occurred while saving the evaluation',
        'eval_error_prefix': 'Error:',
        # Evaluation aggregate
        'page_evaluation_agg_title': 'Aggregate Evaluation',
        'evaluation_agg_title': 'Aggregate Evaluation Dashboard 📊',
        'evaluation_agg_subtitle': 'All user evaluations of the platform',
        'my_personal_eval': '👤 My Personal Evaluation',
        'recommend_percentage': 'Recommend the platform',
        'avg_ratings': 'Average Ratings',
        'recent_evaluations': 'Recent Evaluations',
        'recommends': '✅ Recommends',
        'does_not_recommend': "❌ Doesn't recommend",
        'content_short': 'Content',
        'no_evaluations_yet': 'No evaluations yet',
        'be_first_evaluate': 'Be the first to rate the platform!',
        'start_evaluation': '✏️ Start Evaluation',
        # Evaluation personal
        'page_eval_personal_title': 'My Evaluation',
        'my_personal_evaluation': 'My Personal Evaluation',
        'view_aggregate': 'View Aggregate Evaluation',
        'new_evaluation': 'New Evaluation',
        'thanks_for_time': 'Thanks for your time!',
        'rating_helps_improve': 'Your rating helps us improve the platform and offer a better experience',
        'will_recommend': "I'll recommend the platform",
        'wont_recommend': "I won't recommend the platform right now",
        'detailed_ratings': 'Detailed Ratings',
        'instructor_rating_label': 'Instructor Rating',
        'platform_rating_label': 'Platform Rating',
        'strengths_label': 'Strengths',
        'improvements_label': '🔧 Areas for Improvement',
        'extra_comments_label': '💬 Additional Comments',
        'evaluated_on': 'Evaluated on:',
        # Auth - login
        'page_login_title': 'Login',
        'login_title': 'Login',
        'login_welcome_back': 'Welcome back to Muntalaq',
        'login_as': 'Login as',
        'login_as_student': 'Student 🎓',
        'login_as_graduate': 'Graduate 👨‍🎓',
        'email_field_label': 'Email',
        'password_field_label': 'Password',
        'enter_password_placeholder': 'Enter your password',
        'remember_me': 'Remember me',
        'forgot_password_q': 'Forgot password?',
        'login_btn': 'Login',
        'no_account': "Don't have an account?",
        'join_thousands': 'Join thousands of students and graduates on Muntalaq',
        'create_account_btn': 'Create new account',
        'learn_about_platform': 'Learn about the platform ←',
        # Account selection
        'page_account_select_title': 'Choose Account Type',
        'choose_account_type': 'Choose your account type',
        'choose_account_subtitle': 'Sign up as a student to learn or as a graduate to mentor',
        'student_role_short': 'Student',
        'graduate_role_short': 'Graduate',
        'for_learning': 'For learning and growth',
        'for_mentoring': 'For mentoring and guidance',
        'continue_as_student': 'Continue as Student',
        'continue_as_graduate': 'Continue as Graduate',
        'have_account': 'Already have an account?',
        'login_link': 'Login',
        'back_home': 'Back to Home',
        # Signup
        'page_student_signup_title': 'Create Student Account',
        'page_graduate_signup_title': 'Create Graduate Account',
        'create_student_account': 'Create Student Account',
        'create_graduate_account': 'Create Graduate Account',
        'start_journey': 'Start your learning journey with us',
        'share_expertise_subtitle': 'Share your expertise and guide students toward the future',
        'full_name_required': 'Full Name *',
        'enter_full_name': 'Enter your full name',
        'email_required': 'Email *',
        'phone_required': 'Phone Number *',
        'university_required': 'University *',
        'choose_university': 'Choose university',
        'university_other': 'Other',
        'major_required': 'Major *',
        'major_placeholder_student': 'Example: Computer Science',
        'major_placeholder_graduate': 'Example: Software Engineering',
        'academic_year_required': 'Academic Year *',
        'choose_year': 'Choose year',
        'year_1': 'First Year',
        'year_2': 'Second Year',
        'year_3': 'Third Year',
        'year_4': 'Fourth Year',
        'year_5': 'Fifth Year',
        'graduation_year_required': 'Graduation Year *',
        'year_2015_or_before': '2015 or earlier',
        'password_required': 'Password *',
        'enter_strong_password': 'Enter a strong password',
        'req_min_length': 'At least 6 characters',
        'req_uppercase': 'At least one uppercase letter (A-Z)',
        'req_number': 'At least one number (0-9)',
        'req_special': 'At least one special character (@.-_/)',
        'confirm_password_required': 'Confirm Password *',
        'reenter_password': 'Re-enter your password',
        'passwords_dont_match': "Passwords don't match",
        'agree_terms_prefix': 'I agree to the',
        'terms_link': 'Terms & Conditions',
        'and': 'and',
        'privacy_link': 'Privacy Policy',
        'create_account_submit': 'Create Account',
        'back_to_account_type': 'Back to account type',
        'password_validation_alert': 'Please make sure all password requirements are met',
        # Forgot/reset password
        'page_forgot_title': 'Recover Password',
        'forgot_title': 'Recover Password',
        'forgot_subtitle': "Enter your email and we'll send you a recovery link",
        'send_reset_link': 'Send recovery link',
        'back_to_login': '← Back to Login',
        'page_reset_title': 'Reset Password',
        'reset_title': 'Set a new password',
        'reset_subtitle': 'Choose a strong password for your account',
        'new_password_label': 'New Password',
        'password_rules_inline': 'At least 6 characters · Uppercase · Number · Special character (@.-_/)',
        'confirm_password_label': 'Confirm Password',
        'update_password_btn': 'Update Password',
        # Landing
        'page_landing_title': 'Muntalaq - Start your learning and career journey',
        'hero_heading': 'Muntalaq... your platform for mentoring<br>and career growth',
        'hero_subtitle': 'A platform connecting students and graduates to share knowledge and experience on the path to career success',
        'start_journey_btn': 'Start your journey',
        'how_can_we_help': 'How can we help you?',
        'feature_analytics': 'Analytics & Reports',
        'feature_analytics_desc': 'Comprehensive analysis of your performance and career growth with detailed reports',
        'feature_explore': 'Exploration Lessons',
        'feature_explore_desc': 'Explore new fields and broaden your career horizons',
        'feature_courses': 'Diverse Courses',
        'feature_courses_desc': 'A broad library of courses across different fields',
        'feature_connect': 'Connection Services',
        'feature_connect_desc': 'Connect with successful graduates in your field',
        'gpa_calc_title': ' Calculate Your GPA',
        'gpa_calc_subtitle': 'Easily calculate your semester and cumulative GPA by entering subjects, credits, and grades',
        'prev_gpa_section': '* Previous Cumulative GPA (optional)',
        'prev_gpa_label': 'Previous Cumulative GPA',
        'prev_gpa_placeholder': 'Example: 4.50',
        'prev_credits_label': 'Credits Completed',
        'prev_credits_placeholder': 'Example: 60',
        'add_subject_btn': '+ Add Subject',
        'current_semester_subjects': '* Current Semester Subjects',
        'subject_name': 'Subject Name',
        'credit_hours': 'Credits',
        'grade_label': 'Grade',
        'subject_placeholder': 'Example: Calculus',
        'choose_grade': 'Choose',
        'calculate_gpa': 'Calculate GPA',
        'cumulative_gpa': 'Cumulative GPA',
        'semester_gpa': 'Semester GPA',
        'out_of_5_max': 'out of 5.00',
        'grade_scale': 'Grading Scale',
        'recommended_for_you': 'Recommended for You',
        'recommended_for_you_subtitle': 'Courses tailored to your interests and career goals',
        'all_btn': 'All',
        'courses_btn_short': 'Courses',
        'badge_course': 'Course',
        'badge_mentoring': 'Mentoring',
        'badge_tip': 'Tip',
        'weeks_unit': 'weeks',
        'weeks_6': '6 weeks',
        'weeks_4': '4 weeks',
        'weeks_8': '8 weeks',
        'weeks_10': '10 weeks',
        'one_hour': '1 hour',
        'two_hours': '2 hours',
        'all_levels': 'All Levels',
        'start_now_btn': 'Start now',
        'book_session': 'Book a session',
        'view_more_recommendations': 'View more recommendations',
        'muntalaq_in_numbers': 'Muntalaq in Numbers',
        'active_students': 'Active Students',
        'graduate_collaborators': 'Graduate Collaborators',
        'available_courses': 'Available Courses',
        'about_platform': 'About the Platform',
        'faq_what_is': 'What is Muntalaq?',
        'faq_what_is_a': 'Muntalaq is an educational and career platform that connects students with successful graduates, offering diverse courses, individual career mentoring, and tools like a GPA calculator to support your academic and career journey.',
        'faq_how_works': 'How does Muntalaq work?',
        'faq_how_works_a': 'You can sign up as a student or a graduate, explore the available courses, book career mentoring sessions, participate in the community, and track your academic progress through your personal dashboard.',
        'faq_who_advisors': 'Who are the advisors on Muntalaq?',
        'faq_who_advisors_a': 'The advisors are successful graduates across many fields with broad practical experience, ready to share their knowledge and support students on their career journey.',
        'faq_who_for': 'Who is Muntalaq for?',
        'faq_who_for_a': 'Muntalaq is for students seeking mentoring and career growth, graduates who want to share their experience, and anyone who wants to develop their skills in a supportive learning environment.',
        'testimonials': 'What our users say',
        'testimonial_1': 'A great platform that helped me grow my skills and connect with experts in my field',
        'testimonial_2': 'A wonderful experience! High-quality courses and very professional career mentoring',
        'testimonial_3': 'The best platform for career growth! Practical and very useful advice from real professionals',
        'cta_start_today': 'Start your journey today',
        'cta_start_subtitle': 'Join thousands of students and graduates on Muntalaq',
        'cta_start_free': 'Start free now',
        'platform_tagline': 'A platform connecting students with graduates for career mentoring and skill development',
        'quick_links': 'Quick Links',
        'contact_us': 'Contact Us',
        'about_us': 'About Us',
        'mentors': 'Mentors',
        'policy_privacy_section': 'Policy & Privacy',
        'terms_conditions': 'Terms & Conditions',
        'privacy_policy': 'Privacy Policy',
        'refund_policy': 'Refund Policy',
        'important_links': 'Important Links',
        'help_center': 'Help Center',
        'faqs': 'FAQs',
        'copyright_line': '© 2024 Muntalaq. All rights reserved | Built by the Muntalaq team',
        # Terms
        'page_terms_title': 'Terms & Conditions and Privacy Policy',
        'terms_title': 'Terms & Conditions and Privacy Policy',
        'last_updated': 'Last updated: April 2025',
        'terms_section_heading': 'Terms & Conditions',
        'terms_para_1': 'By creating an account on the <strong>Muntalaq</strong> platform, users agree to provide accurate and complete information during registration. The platform collects basic personal and academic information such as name, email, university, and major to improve the user experience and provide personalized recommendations.',
        'terms_para_2': 'Users are fully responsible for maintaining the confidentiality of their account credentials and for all activities performed through their accounts. Sharing login credentials with any third party is prohibited.',
        'academic_integrity_title': '⚠️ Academic Integrity Policy',
        'academic_integrity_body': 'The platform applies content filters that prevent its use for requesting direct academic solutions, including assignments, exams, and quizzes. Any attempt to violate this policy may lead to account suspension.',
        'terms_para_3': 'The platform uses AI to provide recommendations and support. Users agree that their interactions may be analyzed to improve system performance and recommendation accuracy.',
        'privacy_section_heading': 'Privacy Policy',
        'data_we_collect': 'Data We Collect',
        'data_full_name': 'Full Name',
        'data_email': 'Email',
        'data_university_major': 'University & Major',
        'data_phone': 'Phone Number',
        'data_year_gpa': 'Academic Year & GPA',
        'data_career_interests': 'Career Interests',
        'how_we_use_data': 'How We Use Your Data',
        'use_data_1': 'Improve user experience and provide personalized recommendations based on your academic profile',
        'use_data_2': 'Enable communication between students and graduates on the platform',
        'use_data_3': 'Analyze interactions to improve system performance and recommendation accuracy',
        'use_data_4': 'Send notifications related to courses, messages, and the community',
        'cybersecurity_title': '🛡️ Cybersecurity & Data Protection',
        'cyber_1': 'All user data is stored securely and will not be shared with any third party.',
        'cyber_2': 'Passwords are hashed using strong algorithms and cannot be viewed even by operators.',
        'cyber_3': 'The platform applies AI content filtering to prevent inappropriate or harmful content and academic cheating.',
        'cyber_4': 'Payment data is fully encrypted and is not stored on platform servers.',
        'cyber_5': 'Aggregated data is used only to improve system functionality, personalization, and overall user experience.',
        'user_rights': 'User Rights',
        'right_access': 'Right to access your data',
        'right_correct': 'Right to correct your data',
        'right_delete': 'Right to delete your account',
        'right_export': 'Right to export your data',
        'agreement_banner': 'By using the <strong>Muntalaq</strong> platform, you agree to all the terms and conditions above. For inquiries or to exercise your rights, contact us by email: <strong>privacy@muntalaq.com</strong>',
        'back_btn': '← Back',
    },
}


@app.context_processor
def inject_i18n():
    lang = session.get('lang', 'ar')
    if lang not in TRANSLATIONS:
        lang = 'ar'
    bundle = TRANSLATIONS[lang]
    def t(key):
        return bundle.get(key, TRANSLATIONS['ar'].get(key, key))
    return {
        't': t,
        'current_lang': lang,
        'page_dir': 'rtl' if lang == 'ar' else 'ltr',
    }


@app.context_processor
def inject_current_user():
    """Inject current user (with profile image) for the global header."""
    if 'user_id' not in session:
        return {'current_user': None}
    try:
        conn = get_db()
        u = conn.execute(
            'SELECT id, full_name, email, user_type, profile_image FROM users WHERE id=?',
            (session['user_id'],)
        ).fetchone()
        conn.close()
        return {'current_user': dict(u) if u else None}
    except Exception:
        return {'current_user': None}




def validate_password(password):
    """
    Validate password strength:
    - At least 6 characters
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 special character (@.-_/)
    """
    if len(password) < 6:
        return False, "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
    
    if not re.search(r'[A-Z]', password):
        return False, "كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل"
    
    if not re.search(r'\d', password):
        return False, "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
    
    if not re.search(r'[@.\-_/]', password):
        return False, "كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل (@.-_/)"
    
    return True, "كلمة المرور صالحة"

# ============= ROUTES =============

# Landing Page — kept accessible at /home
@app.route('/home')
def landing():
    return render_template('landing.html')

# Root redirects to login (or dashboard if already signed in)
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Account Selection
@app.route('/account-selection')
def account_selection():
    return render_template('account_selection.html')

# Student Signup - UPDATED
@app.route('/student-signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            email = (request.form.get('email') or '').strip().lower()
            phone = request.form.get('phone')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            university = request.form.get('university')
            major = request.form.get('major')
            academic_year = request.form.get('academic_year')
            terms_agreed = request.form.get('terms_agreed')

            # FR1.2 — must agree to terms & privacy
            if not terms_agreed:
                flash('يجب الموافقة على الشروط والأحكام وسياسة الخصوصية', 'error')
                return redirect(url_for('student_signup'))

            # Check if passwords match
            if password != confirm_password:
                flash('كلمات المرور غير متطابقة', 'error')
                return redirect(url_for('student_signup'))

            # Validate password strength
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, 'error')
                return redirect(url_for('student_signup'))

            # Hash password
            hashed_password = generate_password_hash(password)

            conn = get_db()
            # Check if email already exists (case-insensitive)
            existing = conn.execute(
                'SELECT user_type FROM users WHERE LOWER(email)=?', (email,)
            ).fetchone()
            if existing:
                conn.close()
                if existing['user_type'] == 'graduate':
                    flash(
                        'هذا البريد الإلكتروني مسجّل بالفعل كحساب خريج، وليس طالباً. '
                        'سجّل الدخول بحسابك الحالي أو استخدم بريداً آخر.',
                        'error'
                    )
                else:
                    flash('البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد إلكتروني آخر.', 'error')
                return redirect(url_for('student_signup'))

            c = conn.cursor()
            c.execute('''INSERT INTO users
                        (full_name, email, phone, password, user_type, university, major, academic_year,
                         email_verified, verification_token)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, NULL)''',
                     (full_name, email, phone, hashed_password, 'student', university, major, academic_year))
            conn.commit()
            conn.close()

            flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash('البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد إلكتروني آخر', 'error')
            return redirect(url_for('student_signup'))
        except Exception as e:
            flash('حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى', 'error')
            print(f"Error in student signup: {str(e)}")
            return redirect(url_for('student_signup'))

    return render_template('student_signup.html')

# Graduate Signup - UPDATED
@app.route('/graduate-signup', methods=['GET', 'POST'])
def graduate_signup():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            email = (request.form.get('email') or '').strip().lower()
            phone = request.form.get('phone')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            university = request.form.get('university')
            major = request.form.get('major')
            graduation_year = request.form.get('graduation_year')
            terms_agreed = request.form.get('terms_agreed')

            # FR1.2 — must agree to terms & privacy
            if not terms_agreed:
                flash('يجب الموافقة على الشروط والأحكام وسياسة الخصوصية', 'error')
                return redirect(url_for('graduate_signup'))

            # Check if passwords match
            if password != confirm_password:
                flash('كلمات المرور غير متطابقة', 'error')
                return redirect(url_for('graduate_signup'))
            
            # Validate password strength
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, 'error')
                return redirect(url_for('graduate_signup'))
            
            # Hash password
            hashed_password = generate_password_hash(password)

            conn = get_db()
            # Check if email already exists (case-insensitive)
            existing = conn.execute(
                'SELECT user_type FROM users WHERE LOWER(email)=?', (email,)
            ).fetchone()
            if existing:
                conn.close()
                if existing['user_type'] == 'student':
                    # Redirect to login with a clear explanation
                    flash(
                        'هذا البريد الإلكتروني مسجّل بالفعل كحساب طالب، وليس خريجاً. '
                        'سجّل الدخول بحسابك الحالي أو استخدم بريداً آخر لإنشاء حساب خريج.',
                        'error'
                    )
                    return redirect(url_for('login'))
                else:
                    flash('البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد إلكتروني آخر.', 'error')
                    return redirect(url_for('graduate_signup'))

            c = conn.cursor()
            c.execute('''INSERT INTO users
                        (full_name, email, phone, password, user_type, university, major, graduation_year,
                         email_verified, verification_token)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, NULL)''',
                     (full_name, email, phone, hashed_password, 'graduate', university, major, graduation_year))
            conn.commit()
            conn.close()

            flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash('البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد إلكتروني آخر', 'error')
            return redirect(url_for('graduate_signup'))
        except Exception as e:
            flash('حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى', 'error')
            print(f"Error in graduate signup: {str(e)}")
            return redirect(url_for('graduate_signup'))
    
    return render_template('graduate_signup.html')

# Login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = (request.form.get('email') or '').strip().lower()
            password = request.form.get('password')

            # Validate input
            if not email or not password:
                flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'error')
                return redirect(url_for('login'))

            # Try to get user from database
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE LOWER(email) = ?', (email,))
            user = c.fetchone()
            conn.close()

            # Login as needs to match account type if provided
            requested_type = (request.form.get('login_as') or '').strip().lower()

            # Check if user exists and password is correct
            if user and check_password_hash(user['password'], password):
                # FR1.4 — block sign-in until email is verified
                if not user['email_verified']:
                    flash('يجب تأكيد بريدك الإلكتروني أولاً.', 'error')
                    return redirect(url_for('login'))

                # If a specific account type was requested, ensure it matches the email's actual type
                if requested_type in ('student', 'graduate') and requested_type != user['user_type']:
                    actual_label = 'خريج' if user['user_type'] == 'graduate' else 'طالب'
                    requested_label = 'خريج' if requested_type == 'graduate' else 'طالب'
                    flash(
                        f'هذا البريد الإلكتروني مسجّل كحساب {actual_label}، وليس {requested_label}. '
                        f'سجّل الدخول كـ{actual_label} أو استخدم بريداً آخر.',
                        'error'
                    )
                    return redirect(url_for('login'))

                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_type'] = user['user_type']
                session['user_email'] = user['email']
                return redirect(url_for('dashboard', welcome=1))
            else:
                # If the email exists but password is wrong, hint at the actual account type
                if user:
                    actual_label = 'خريج' if user['user_type'] == 'graduate' else 'طالب'
                    if requested_type in ('student', 'graduate') and requested_type != user['user_type']:
                        requested_label = 'خريج' if requested_type == 'graduate' else 'طالب'
                        flash(
                            f'هذا البريد الإلكتروني مسجّل كحساب {actual_label}، وليس {requested_label}. '
                            f'سجّل الدخول كـ{actual_label} أو استخدم بريداً آخر.',
                            'error'
                        )
                    else:
                        flash(
                            f'كلمة المرور غير صحيحة. هذا البريد الإلكتروني مسجّل كحساب {actual_label}.',
                            'error'
                        )
                else:
                    flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
                return redirect(url_for('login'))
                
        except sqlite3.Error as db_error:
            flash('حدث خطأ في قاعدة البيانات. يرجى المحاولة مرة أخرى', 'error')
            print(f"Database error in login: {str(db_error)}")
            return redirect(url_for('login'))
        except Exception as e:
            flash('حدث خطأ أثناء تسجيل الدخول. يرجى المحاولة مرة أخرى', 'error')
            print(f"Error in login: {str(e)}")
            return redirect(url_for('login'))
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('landing'))

# Dashboard — dynamic stats from DB, separate views for student vs graduate
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    uid = session['user_id']
    user_type = session.get('user_type', 'student')
    conn = get_db()

    if user_type == 'graduate':
        # Graduate-focused stats
        published = conn.execute(
            "SELECT COUNT(*) AS c FROM courses WHERE graduate_id=? AND status='published'", (uid,)
        ).fetchone()['c']
        total_students = conn.execute('''
            SELECT COUNT(DISTINCT e.student_id) AS c
            FROM enrollments e JOIN courses c ON e.course_id = c.id
            WHERE c.graduate_id = ?
        ''', (uid,)).fetchone()['c']
        avg_rating = conn.execute('''
            SELECT ROUND(AVG((clarity + content_value + interaction)/3.0), 1) AS r
            FROM graduate_evaluations WHERE graduate_id = ?
        ''', (uid,)).fetchone()['r']
        unread_msgs = conn.execute(
            'SELECT COUNT(*) AS c FROM chat_messages WHERE receiver_id=?', (uid,)
        ).fetchone()['c']

        # Recent enrollments in this graduate's courses
        recent_courses = [dict(r) for r in conn.execute('''
            SELECT c.id, c.title, c.image,
                   (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id) AS students
            FROM courses c
            WHERE c.graduate_id = ? AND c.status='published'
            ORDER BY c.created_at DESC LIMIT 4
        ''', (uid,)).fetchall()]

        recent_activity = [dict(r) for r in conn.execute('''
            SELECT n.title, n.message, n.created_at
            FROM notifications n WHERE n.user_id=?
            ORDER BY n.created_at DESC LIMIT 5
        ''', (uid,)).fetchall()]
        conn.close()

        stats = {
            'published_courses': published,
            'total_students': total_students,
            'avg_rating': avg_rating if avg_rating is not None else '—',
            'unread_messages': unread_msgs,
        }
        return render_template('dashboard_graduate.html',
                               stats=stats,
                               recent_courses=recent_courses,
                               recent_activity=recent_activity)

    # Student stats
    completed = conn.execute(
        "SELECT COUNT(*) AS c FROM enrollments WHERE student_id=? AND status='completed'", (uid,)
    ).fetchone()['c']
    enrolled_count = conn.execute(
        "SELECT COUNT(*) AS c FROM enrollments WHERE student_id=?", (uid,)
    ).fetchone()['c']
    lessons_done = conn.execute(
        "SELECT COUNT(*) AS c FROM lesson_completions WHERE student_id=?", (uid,)
    ).fetchone()['c']
    # Rough learning hours: 30 minutes per completed lesson
    learning_hours = round(lessons_done * 0.5, 1)
    goals_total = enrolled_count if enrolled_count else 0
    goals_achieved = f'{completed}/{goals_total}' if goals_total else '0/0'

    # Streak: count distinct days with a completion in the last 30 days, capped
    streak_row = conn.execute('''
        SELECT COUNT(DISTINCT DATE(completed_at)) AS d
        FROM lesson_completions WHERE student_id=?
          AND completed_at >= DATE('now', '-30 day')
    ''', (uid,)).fetchone()
    streak_days = streak_row['d'] if streak_row else 0

    # Recent enrollments for "continue learning"
    continue_courses = [dict(r) for r in conn.execute('''
        SELECT e.progress, e.status, c.id, c.title, c.image, u.full_name AS instructor,
               (SELECT COUNT(*) FROM lessons WHERE course_id = c.id) AS lessons_total,
               (SELECT COUNT(*) FROM lesson_completions lc
                  JOIN lessons l ON l.id = lc.lesson_id
                  WHERE l.course_id = c.id AND lc.student_id = e.student_id) AS lessons_done
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN users u ON c.graduate_id = u.id
        WHERE e.student_id = ? AND e.status != 'cancelled'
        ORDER BY e.enrolled_at DESC LIMIT 4
    ''', (uid,)).fetchall()]
    for c in continue_courses:
        t = c.get('lessons_total') or 0
        d = c.get('lessons_done') or 0
        c['real_progress'] = int(round(100.0 * d / t)) if t else 0

    recent_activity = [dict(r) for r in conn.execute('''
        SELECT title, message, created_at, notif_type
        FROM notifications WHERE user_id=?
        ORDER BY created_at DESC LIMIT 5
    ''', (uid,)).fetchall()]
    conn.close()

    stats = {
        'completed_courses': completed,
        'learning_hours': learning_hours,
        'goals_achieved': goals_achieved,
        'streak_days': streak_days,
    }

    return render_template('dashboard.html', stats=stats,
                           continue_courses=continue_courses,
                           recent_activity=recent_activity)

# Profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn = get_db()
        c = conn.cursor()
        
        # Update basic info
        c.execute('''UPDATE users SET 
                    full_name = ?, phone = ?, city = ?, 
                    university = ?, major = ?, graduation_year = ?, 
                    gpa = ?, bio = ?
                    WHERE id = ?''',
                 (request.form.get('full_name'), request.form.get('phone'), 
                  request.form.get('city'), request.form.get('university'),
                  request.form.get('major'), request.form.get('graduation_year'),
                  request.form.get('gpa'), request.form.get('bio'), 
                  session['user_id']))
        
        conn.commit()
        conn.close()
        
        session['user_name'] = request.form.get('full_name')
        flash('تم تحديث الملف الشخصي بنجاح!', 'success')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    
    c.execute('SELECT interest FROM interests WHERE user_id = ?', (session['user_id'],))
    interests = [row['interest'] for row in c.fetchall()]
    conn.close()
    
    return render_template('profile.html', user=user, interests=interests)

# Profile picture upload
@app.route('/api/profile/upload-image', methods=['POST'])
def profile_upload_image():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'غير مصرح'}), 401
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم اختيار صورة'}), 400
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'الملف فارغ'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_IMAGE_EXTS:
        return jsonify({'success': False, 'error': 'صيغة غير مدعومة'}), 400
    fname = secure_filename(f"user_{session['user_id']}_{int(datetime.utcnow().timestamp())}.{ext}")
    path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(path)
    rel = f'uploads/{fname}'
    conn = get_db()
    conn.execute('UPDATE users SET profile_image=? WHERE id=?', (rel, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'url': url_for('static', filename=rel)})


# Notifications: mark all as read
@app.route('/api/notifications/mark-all-read', methods=['POST'])
def notifications_mark_all_read():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    conn = get_db()
    conn.execute('UPDATE notifications SET is_read=1 WHERE user_id=?', (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/notifications/recent', methods=['GET'])
def notifications_recent():
    """Return the user's most recent notifications for toast polling."""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    conn = get_db()
    rows = conn.execute(
        'SELECT id, title, message, notif_type, is_read, link, created_at '
        'FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 10',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return jsonify({'success': True, 'notifications': [dict(r) for r in rows]})


# Add Interest API
@app.route('/api/add-interest', methods=['POST'])
def add_interest():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 401
    
    interest = request.json.get('interest')
    if interest:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO interests (user_id, interest) VALUES (?, ?)', 
                 (session['user_id'], interest))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 400

# Remove Interest API
@app.route('/api/remove-interest', methods=['POST'])
def remove_interest():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    interest = request.json.get('interest')
    if interest:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM interests WHERE user_id = ? AND interest = ?', 
                 (session['user_id'], interest))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 400

# Smart Recommendations
@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    # Fake AI-powered recommendations
    recs = [
        {
            'title': 'أساسيات تصميم واجهة وتجربة المستخدم',
            'instructor': 'ليلى إبراهيم',
            'field': 'التصميم',
            'type': 'الدورات',
            'rating': 4.7,
            'reviews': 456,
            'level': 'مبتدئ',
            'duration': '6 أسابيع',
            'price': 0,
            'tags': ['تصميم', 'UI/UX', 'Figma'],
            'image': 'course4.jpg'  # UI/UX Design
        },
        {
            'title': 'توجيه مهني فردي في علوم البيانات',
            'instructor': 'محمد حسن',
            'field': 'علوم البيانات',
            'type': 'التوجيه',
            'rating': 4.9,
            'reviews': 89,
            'level': 'متوسط',
            'duration': 'ساعة واحدة',
            'price': 150,
            'tags': ['علوم البيانات', 'مسار مهني', 'AI'],
            'image': 'course2.jpg'  # Data Science
        },
        {
            'title': 'أنماط React المتقدمة وأفضل الممارسات',
            'instructor': 'سارة أحمد',
            'field': 'هندسة الواجهة الأمامية',
            'type': 'الدورات',
            'rating': 4.5,
            'reviews': 234,
            'level': 'متقدم',
            'duration': '8 أسابيع',
            'price': 299,
            'tags': ['React', 'JavaScript', 'تطوير الويب'],
            'image': 'course3.jpg'  # React/Web Development
        }
    ]
    
    return render_template('recommendations_ai.html', recommendations=recs)

# My Courses
# My Courses and Course Content are now defined later (FR8, FR9).



# Notifications
@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50',
        (session['user_id'],)
    ).fetchall()
    # Mark all as read
    conn.execute('UPDATE notifications SET is_read=1 WHERE user_id=?', (session['user_id'],))
    conn.commit()
    conn.close()

    notifs = [dict(r) for r in rows]
    return render_template('notifications.html', notifications=notifs)

# Favorites is now defined later (FR14).



# Evaluation (for graduates)
@app.route('/evaluation')
def evaluation():
    """
    Main evaluation page - redirects to appropriate view
    Shows personal dashboard if user has completed evaluation, otherwise shows form
    """
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    # Check if user has any evaluations
    conn = get_db()
    user_eval = conn.execute(
        'SELECT * FROM evaluations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if user_eval:
        # User has evaluation, show their personal dashboard
        return redirect(url_for('evaluation_personal'))
    else:
        # No evaluation yet, show the form
        return redirect(url_for('evaluation_form'))

@app.route('/evaluation/form')
def evaluation_form():
    """
    AI-powered evaluation conversation form
    """
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    return render_template('evaluation_form.html')

@app.route('/evaluation/personal')
def evaluation_personal():
    """
    Personal evaluation dashboard - shows individual user's results
    """
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # Get user's latest evaluation
    user_eval = conn.execute(
        'SELECT * FROM evaluations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (session['user_id'],)
    ).fetchone()
    
    if not user_eval:
        conn.close()
        return redirect(url_for('evaluation_form'))
    
    # Convert to dict
    eval_data = {
        'content_quality': user_eval['content_quality'],
        'engagement': user_eval['engagement'],
        'interaction': user_eval['interaction'],
        'instructor_rating': user_eval['instructor_rating'],
        'platform_rating': user_eval['platform_rating'],
        'overall_rating': round((user_eval['instructor_rating'] + user_eval['platform_rating']) / 2, 1),
        'would_recommend': user_eval['would_recommend'],
        'comments': user_eval['comments'],
        'strengths': user_eval['strengths'],
        'improvements': user_eval['improvements'],
        'created_at': user_eval['created_at']
    }
    
    conn.close()
    
    return render_template('evaluation_personal.html', evaluation=eval_data)

@app.route('/evaluation/aggregate')
def evaluation_aggregate():
    """
    Aggregate evaluation dashboard - shows all users' combined results
    """
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # Get aggregate statistics
    stats = conn.execute('''
        SELECT 
            ROUND(AVG(content_quality), 0) as avg_content_quality,
            ROUND(AVG(engagement), 0) as avg_engagement,
            ROUND(AVG(interaction), 0) as avg_interaction,
            ROUND(AVG(instructor_rating), 1) as avg_instructor_rating,
            ROUND(AVG(platform_rating), 1) as avg_platform_rating,
            COUNT(*) as total_evaluations,
            SUM(CASE WHEN would_recommend = 1 THEN 1 ELSE 0 END) as recommend_count
        FROM evaluations
    ''').fetchone()
    
    # Get all evaluations for detailed view
    all_evaluations = conn.execute('''
        SELECT e.*, u.full_name 
        FROM evaluations e
        JOIN users u ON e.user_id = u.id
        ORDER BY e.created_at DESC
        LIMIT 50
    ''').fetchall()
    
    conn.close()
    
    # Calculate overall rating
    overall_rating = round((stats['avg_instructor_rating'] + stats['avg_platform_rating']) / 2, 1) if stats['total_evaluations'] > 0 else 0
    recommendation_percentage = round((stats['recommend_count'] / stats['total_evaluations'] * 100), 0) if stats['total_evaluations'] > 0 else 0
    
    eval_data = {
        'content_quality': int(stats['avg_content_quality']) if stats['avg_content_quality'] else 0,
        'engagement': int(stats['avg_engagement']) if stats['avg_engagement'] else 0,
        'interaction': int(stats['avg_interaction']) if stats['avg_interaction'] else 0,
        'overall_rating': overall_rating,
        'total_reviews': stats['total_evaluations'],
        'recommendation_percentage': recommendation_percentage,
        'all_evaluations': [dict(e) for e in all_evaluations]
    }
    
    return render_template('evaluation_aggregate.html', evaluation=eval_data)

# Settings
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    if request.method == 'POST':
        # Save settings (FR15.3)
        email_notif = 1 if request.form.get('email_notifications') == 'on' else 0
        app_notif = 1 if request.form.get('app_notifications') == 'on' else 0
        profile_public = 1 if request.form.get('profile_public') == 'on' else 0
        conn.execute(
            'UPDATE users SET email_notifications=?, app_notifications=?, profile_public=? WHERE id=?',
            (email_notif, app_notif, profile_public, session['user_id'])
        )
        conn.commit()
        conn.close()
        flash('تم تحديث الإعدادات بنجاح!', 'success')
        return redirect(url_for('settings'))

    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('settings.html', user=dict(user) if user else {})


# API: toggle a single setting (FR15.3)
@app.route('/api/settings/toggle', methods=['POST'])
def settings_toggle():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    data = request.json or {}
    field = data.get('field')
    value = 1 if data.get('value') else 0
    allowed = {'email_notifications', 'app_notifications', 'profile_public'}
    if field not in allowed:
        return jsonify({'success': False, 'error': 'حقل غير صالح'}), 400
    conn = get_db()
    conn.execute(f'UPDATE users SET {field}=? WHERE id=?', (value, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'field': field, 'value': value})

# Fake AI Chat API (will replace with real OpenAI later)
@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_message = data.get('message', '')
    
    # Fake AI responses
    fake_responses = [
        'شكراً على سؤالك! أنا هنا للمساعدة في رحلتك التعليمية.',
        'بناءً على ملفك الشخصي، أنصحك بالتركيز على تطوير مهاراتك في البرمجة.',
        'يمكنني مساعدتك في اختيار المسار المهني المناسب لك.',
        'دعني أقترح عليك بعض الدورات التي تناسب اهتماماتك.',
        'هذا سؤال رائع! دعني أساعدك في إيجاد الإجابة المناسبة.'
    ]
    
    response = random.choice(fake_responses)
    
    return jsonify({
        'success': True,
        'response': response,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# ============= AI EVALUATION SYSTEM =============

# ============= AI EVALUATION SYSTEM =============

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """
    Comprehensive AI chatbot for platform support
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول أولاً'}), 401
    
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        # Get user info for personalization
        user_name = session.get('user_name', 'المستخدم')
        user_type = session.get('user_type', 'student')
        
        # Create comprehensive chatbot system prompt
        system_prompt = f"""أنت مساعد ذكي متخصص في منصة "منطلق" التعليمية. أنت تساعد {user_name} الذي هو {'طالب' if user_type == 'student' else 'خريج'}.

مهامك:
1. **الإجابة عن الأسئلة**: 
   - شرح كيفية استخدام المنصة
   - معلومات عن الدورات المتاحة
   - كيفية التسجيل والتقييم
   - الإعدادات والحساب

2. **الدورات المتاحة في المنصة**:
   - أساسيات تصميم واجهة وتجربة المستخدم (UI/UX)
   - توجيه مهني فردي في علوم البيانات
   - أنماط React المتقدمة وأفضل الممارسات
   - تطوير تطبيقات Flutter
   - استراتيجية الأعمال والقيادة
   - البدء بتعلم الآلة
   - تطوير تطبيقات الويب الحديثة

3. **مساعدة فنية**:
   - حل المشاكل التقنية
   - شرح الميزات
   - إرشاد للصفحات المناسبة

4. **التوجيه**:
   - اقتراح دورات مناسبة
   - نصائح تعليمية
   - المسار المهني

**إرشادات المحادثة**:
- كن ودوداً ومحترفاً
- أجب بإيجاز وفائدة
- استخدم العربية الفصحى البسيطة
- إذا سأل عن دورة معينة، أعطِ معلومات مفصلة
- إذا كانت مشكلة تقنية، قدم خطوات حل واضحة
- اقترح صفحات مفيدة: /recommendations, /my-courses, /evaluation, /community, /profile

**ملاحظات مهمة**:
- لا تخترع معلومات غير موجودة
- إذا لم تعرف، قل "دعني أحيلك إلى فريق الدعم"
- شجع المستخدم على استكشاف المنصة"""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-10:])  # Last 10 messages only
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        print(f"Chatbot error: {str(e)}")
        # Fallback responses
        fallback_responses = [
            "عذراً، أواجه مشكلة مؤقتة. يمكنك تصفح المنصة أو التواصل مع الدعم.",
            "أنا هنا لمساعدتك! هل يمكنك إعادة صياغة سؤالك؟",
            "دعني أساعدك. يمكنك استكشاف الدورات من صفحة 'التوصيات' أو 'دوراتي'."
        ]
        return jsonify({
            'success': True,
            'response': random.choice(fallback_responses)
        })

@app.route('/api/evaluation-chat', methods=['POST'])
def evaluation_chat():
    """
    Handle AI conversation for evaluation
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول أولاً'}), 401
    
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        # Create evaluation-focused conversation
        messages = [
            {"role": "system", "content": """أنت مقيّم ذكي في منصة "منطلق" التعليمية. مهمتك جمع تقييم شامل من المستخدم.

اسأل المستخدم بشكل ودي عن:
1. جودة المحتوى التعليمي (من 0-100%)
2. مستوى التفاعل مع الدورة (من 0-100%)
3. تجربة الاستجابة والتواصل (من 0-100%)
4. تقييم المدرب (من 1-5 نجوم)
5. تقييم المنصة بشكل عام (من 1-5 نجوم)
6. هل سيوصي بالمنصة للآخرين؟ (نعم/لا)
7. ما أفضل ما أعجبه في الدورة؟
8. ما الذي يمكن تحسينه؟
9. تعليقات إضافية؟

اطرح سؤالاً واحداً في كل مرة بشكل طبيعي ومشجع. استخدم اللغة العربية الودية."""}
        ]
        
        # Add conversation history
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        print(f"Error in evaluation chat: {str(e)}")
        return jsonify({
            'success': True,
            'response': 'شكراً على مشاركتك! هل يمكنك إخباري المزيد عن تجربتك؟'
        })

@app.route('/api/evaluation-submit', methods=['POST'])
def evaluation_submit():
    """
    Process evaluation conversation and save to database
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول أولاً'}), 401
    
    try:
        data = request.json
        conversation_text = data.get('conversation', '')
        
        # Use AI to extract structured data from conversation
        analysis_prompt = f"""قم بتحليل المحادثة التالية واستخرج البيانات المطلوبة بصيغة JSON فقط:

المحادثة:
{conversation_text}

استخرج:
- content_quality: رقم من 0-100 (جودة المحتوى)
- engagement: رقم من 0-100 (التفاعل)
- interaction: رقم من 0-100 (الاستجابة)
- instructor_rating: رقم من 1-5 (تقييم المدرب)
- platform_rating: رقم من 1-5 (تقييم المنصة)
- would_recommend: true أو false
- comments: أي تعليقات إضافية
- strengths: نقاط القوة التي ذكرها المستخدم
- improvements: مجالات التحسين المقترحة

الرد بصيغة JSON فقط:
{{
  "content_quality": 85,
  "engagement": 75,
  "interaction": 90,
  "instructor_rating": 4.5,
  "platform_rating": 4.0,
  "would_recommend": true,
  "comments": "...",
  "strengths": "...",
  "improvements": "..."
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت محلل بيانات. استخرج البيانات من المحادثة واستجب بصيغة JSON فقط."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse AI response
        import json
        evaluation_data = json.loads(response.choices[0].message.content)
        
        # Save to database
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO evaluations (
                user_id, content_quality, engagement, interaction,
                instructor_rating, platform_rating, would_recommend,
                comments, strengths, improvements
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            evaluation_data.get('content_quality', 75),
            evaluation_data.get('engagement', 70),
            evaluation_data.get('interaction', 80),
            evaluation_data.get('instructor_rating', 4.5),
            evaluation_data.get('platform_rating', 4.0),
            1 if evaluation_data.get('would_recommend', True) else 0,
            evaluation_data.get('comments', ''),
            evaluation_data.get('strengths', ''),
            evaluation_data.get('improvements', '')
        ))
        
        evaluation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'evaluation_id': evaluation_id,
            'message': 'تم حفظ تقييمك بنجاح!'
        })
        
    except Exception as e:
        print(f"Error in evaluation submit: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ أثناء حفظ التقييم'
        }), 500

# ============= AI RECOMMENDATION SYSTEM =============

def get_ai_recommendations(user_interests, user_major, career_goals, skill_level):
    """
    Use OpenAI GPT to analyze user profile and match with courses
    """
    try:
        # Create a detailed prompt for the AI
        prompt = f"""أنت مستشار تعليمي ومهني خبير في منصة "منطلق" التعليمية. مهمتك هي تحليل اهتمامات المستخدم وتقديم توصيات دقيقة للدورات المناسبة.

معلومات المستخدم:
- التخصص: {user_major}
- الاهتمامات: {user_interests}
- الأهداف المهنية: {career_goals}
- مستوى المهارة: {skill_level}

الدورات المتاحة في المنصة:
{_format_courses_for_ai()}

المطلوب منك:
1. حلل ملف المستخدم بعناية
2. اختر من 2 إلى 4 دورات من القائمة أعلاه التي تناسب اهتماماته وأهدافه
3. قدم نصائح مهنية مخصصة (3-4 نصائح)
4. اقترح مسار تعليمي واضح

يجب أن يكون الرد بصيغة JSON فقط كالتالي:
{{
  "recommended_course_ids": [1, 3, 6],
  "advice": [
    "نصيحة 1",
    "نصيحة 2",
    "نصيحة 3"
  ],
  "learning_path": "وصف مختصر للمسار التعليمي المقترح",
  "personalized_message": "رسالة تحفيزية شخصية للمستخدم"
}}

تأكد من اختيار الدورات بناءً على التطابق الفعلي مع اهتمامات المستخدم."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o-mini for cost-effectiveness and good performance
            messages=[
                {"role": "system", "content": "أنت مستشار تعليمي ومهني خبير. تقدم توصيات دقيقة ومفيدة باللغة العربية. استجب دائماً بصيغة JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        # Parse the AI response
        import json
        ai_result = json.loads(response.choices[0].message.content)
        
        # Get the actual course objects
        recommended_courses = [
            course for course in AVAILABLE_COURSES 
            if course['id'] in ai_result.get('recommended_course_ids', [])
        ]
        
        return {
            'success': True,
            'courses': recommended_courses,
            'advice': ai_result.get('advice', []),
            'learning_path': ai_result.get('learning_path', ''),
            'personalized_message': ai_result.get('personalized_message', '')
        }
        
    except Exception as e:
        print(f"AI Recommendation Error: {str(e)}")
        # Graceful fallback - return useful default recommendations so user never sees an error
        return {
            'success': True,
            'courses': AVAILABLE_COURSES[:3],
            'advice': [
                'ابدأ بالأساسيات وبناء قاعدة معرفية قوية',
                'مارس ما تتعلمه من خلال مشاريع عملية',
                'انضم للمجتمع وتواصل مع الخبراء'
            ],
            'learning_path': 'ابدأ بتعلم المهارات الأساسية ثم انتقل إلى المواضيع المتقدمة تدريجياً',
            'personalized_message': 'نحن هنا لدعمك في رحلتك التعليمية!'
        }

def _format_courses_for_ai():
    """Format courses list for AI prompt"""
    courses_text = ""
    for course in AVAILABLE_COURSES:
        courses_text += f"""
ID: {course['id']}
العنوان: {course['title']}
المجال: {course['field']}
المستوى: {course['level']}
الكلمات المفتاحية: {', '.join(course['keywords'])}
---"""
    return courses_text

# API endpoint for AI conversation
@app.route('/api/ai-recommendations', methods=['POST'])
def ai_recommendations():
    """
    Handle AI-powered recommendations request
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول أولاً'}), 401
    
    try:
        data = request.json
        user_major = data.get('major', '')
        user_interests = data.get('interests', '')
        career_goals = data.get('career_goals', '')
        skill_level = data.get('skill_level', 'مبتدئ')
        
        # Get AI recommendations
        result = get_ai_recommendations(user_interests, user_major, career_goals, skill_level)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in AI recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى.'
        }), 500

# API endpoint for conversational AI chat
@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """
    Handle conversational AI interactions for gathering user information
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول أولاً'}), 401
    
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        # Create conversation context
        messages = [
            {"role": "system", "content": """أنت مساعد ذكي في منصة "منطلق" التعليمية. مهمتك:
1. الترحيب بالمستخدم بشكل ودي
2. اسأل عن تخصصه الدراسي أو المهني
3. اسأل عن اهتماماته ومجالات التعلم المفضلة
4. اسأل عن أهدافه المهنية
5. اسأل عن مستوى خبرته (مبتدئ، متوسط، متقدم)
6. كن محادثاً طبيعياً ومشجعاً

استخدم اللغة العربية الفصحى البسيطة. اطرح سؤالاً واحداً في كل مرة."""}
        ]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=200
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        print(f"Error in AI chat: {str(e)}")
        # Graceful fallback so the user-facing flow doesn't break
        fallback_questions = [
            'أهلاً! ما هو تخصصك الدراسي أو مجال عملك؟',
            'ما هي اهتماماتك ومجالات التعلم التي تفضلها؟',
            'ما هي أهدافك المهنية في السنوات القادمة؟',
            'كيف تصف مستوى خبرتك؟ (مبتدئ، متوسط، متقدم)',
            'رائع! هل هناك شيء محدد تريد تعلمه الآن؟'
        ]
        return jsonify({
            'success': True,
            'response': random.choice(fallback_questions)
        })

# ============================================================================
# =========== NEW FEATURES (Requirements update - FR5, FR6-9, FR10, FR11) ====
# ============================================================================

# ---------- Helpers ----------
def _row_to_dict(row):
    return dict(row) if row else None


# =====================================================================
# FR6, FR7 - Browse Courses + Course Details
# =====================================================================
@app.route('/courses')
def courses_list():
    """Browse all published courses with search + filters (FR6.1, FR6.2)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    level_filter = request.args.get('level', '')
    price_filter = request.args.get('price', '')  # free | paid

    conn = get_db()

    conditions = ["c.status = 'published'"]
    params = []

    if q:
        conditions.append("(c.title LIKE ? OR c.description LIKE ? OR u.full_name LIKE ? OR c.tags LIKE ?)")
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'])
    if level_filter:
        conditions.append("c.level = ?")
        params.append(level_filter)
    if price_filter == 'free':
        conditions.append("(c.price = 0 OR c.price IS NULL)")
    elif price_filter == 'paid':
        conditions.append("c.price > 0")

    where = ' AND '.join(conditions)
    query = f'''
        SELECT c.*, u.full_name AS instructor
        FROM courses c JOIN users u ON c.graduate_id = u.id
        WHERE {where}
        ORDER BY c.created_at DESC
    '''
    courses = [dict(r) for r in conn.execute(query, params).fetchall()]

    for c in courses:
        c['tags_list'] = [t.strip() for t in (c.get('tags') or '').split(',') if t.strip()]

    fav_rows = conn.execute('SELECT course_id FROM favorites WHERE user_id = ?',
                            (session['user_id'],)).fetchall()
    fav_ids = {r['course_id'] for r in fav_rows}
    conn.close()

    return render_template('courses_list.html', courses=courses, fav_ids=fav_ids,
                           search=q, level_filter=level_filter, price_filter=price_filter)


@app.route('/courses/<int:course_id>')
def course_details(course_id):
    """Course details page (FR7)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    course = conn.execute('''
        SELECT c.*, u.full_name AS instructor, u.bio AS instructor_bio, u.major AS instructor_major, u.id AS instructor_id
        FROM courses c JOIN users u ON c.graduate_id = u.id
        WHERE c.id = ?
    ''', (course_id,)).fetchone()

    if not course:
        conn.close()
        flash('الدورة غير موجودة', 'error')
        return redirect(url_for('courses_list'))

    course = dict(course)
    course['tags_list'] = [t.strip() for t in (course.get('tags') or '').split(',') if t.strip()]

    # Check if already enrolled
    enrolled = conn.execute(
        'SELECT * FROM enrollments WHERE student_id = ? AND course_id = ?',
        (session['user_id'], course_id)
    ).fetchone()

    # Favorite?
    is_fav = conn.execute(
        'SELECT 1 FROM favorites WHERE user_id = ? AND course_id = ?',
        (session['user_id'], course_id)
    ).fetchone() is not None

    # Real lessons added by the graduate (FR9 — control content)
    lessons = [dict(r) for r in conn.execute(
        'SELECT id, title, duration, order_idx FROM lessons WHERE course_id=? ORDER BY order_idx ASC, id ASC',
        (course_id,)
    ).fetchall()]
    conn.close()

    return render_template('course_details.html', course=course,
                           enrolled=enrolled, is_fav=is_fav, lessons=lessons)


@app.route('/courses/<int:course_id>/checkout', methods=['GET', 'POST'])
def course_checkout(course_id):
    """Payment page before enrolling in a paid course."""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    course = conn.execute('''
        SELECT c.*, u.full_name AS instructor, u.id AS instructor_id
        FROM courses c JOIN users u ON c.graduate_id = u.id
        WHERE c.id = ? AND c.status = 'published'
    ''', (course_id,)).fetchone()

    if not course:
        conn.close()
        flash('الدورة غير موجودة', 'error')
        return redirect(url_for('courses_list'))

    course = dict(course)

    # If already enrolled, skip checkout
    enrolled = conn.execute(
        'SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?',
        (session['user_id'], course_id)
    ).fetchone()
    if enrolled:
        conn.close()
        flash('أنت مسجل بالفعل في هذه الدورة', 'info')
        return redirect(url_for('my_courses'))

    # Free course — enroll directly, no payment needed
    if not course['price'] or course['price'] == 0:
        try:
            conn.execute(
                'INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                (session['user_id'], course_id)
            )
            conn.commit()
            # Notify the user themselves about the enrollment
            conn.execute(
                'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'],
                 'تم التسجيل في دورة 🎓',
                 f'تم تسجيلك في دورة "{course["title"]}" بنجاح',
                 'course',
                 f'/courses/{course_id}')
            )
            # Notify graduate that someone enrolled in their course
            conn.execute(
                'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
                (course['graduate_id'],
                 'تسجيل جديد في دورتك 🎓',
                 f'قام {session.get("user_name", "مستخدم")} بالتسجيل في دورة "{course["title"]}"',
                 'course',
                 f'/courses/{course_id}')
            )
            conn.commit()
            flash('تم التسجيل في الدورة المجانية بنجاح! 🎉', 'success')
        except sqlite3.IntegrityError:
            flash('أنت مسجل بالفعل في هذه الدورة', 'error')
        conn.close()
        return redirect(url_for('my_courses'))

    if request.method == 'POST':
        # Simulated payment processing
        card_number = (request.form.get('card_number') or '').replace(' ', '')
        expiry = request.form.get('expiry', '').strip()
        cvv = request.form.get('cvv', '').strip()
        card_name = request.form.get('card_name', '').strip()

        errors = []
        if len(card_number) < 13:
            errors.append('رقم البطاقة غير صحيح')
        if not re.match(r'^\d{2}/\d{2}$', expiry):
            errors.append('تاريخ الانتهاء غير صحيح (MM/YY)')
        if len(cvv) < 3:
            errors.append('رمز CVV غير صحيح')
        if not card_name:
            errors.append('اسم حامل البطاقة مطلوب')

        if errors:
            conn.close()
            return render_template('checkout.html', course=course, errors=errors,
                                   form=request.form)

        # Payment succeeded — enroll student
        try:
            conn.execute(
                'INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                (session['user_id'], course_id)
            )
            conn.commit()

            # Notify the user themselves about the enrollment
            conn.execute(
                'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'],
                 'تم التسجيل في دورة 🎓',
                 f'تم تسجيلك في دورة "{course["title"]}" بنجاح',
                 'course',
                 f'/courses/{course_id}')
            )
            # Notify graduate that a user enrolled
            graduate_id = course['graduate_id']
            student_name = session.get('user_name', 'مستخدم')
            conn.execute(
                'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
                (graduate_id,
                 'تسجيل جديد في دورتك 🎓',
                 f'قام {student_name} بالتسجيل في دورة "{course["title"]}"',
                 'course',
                 f'/courses/{course_id}')
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
        flash('تمت عملية الدفع والتسجيل بنجاح! 🎉', 'success')
        return redirect(url_for('my_courses'))

    conn.close()
    return render_template('checkout.html', course=course, errors=[], form={})


@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
def enroll_course(course_id):
    """Legacy direct-enroll (free courses only / chat offer acceptance)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'غير مصرح'}), 401

    conn = get_db()
    # Block direct enroll for paid courses — must go through checkout
    course_row = conn.execute('SELECT price FROM courses WHERE id=?', (course_id,)).fetchone()
    if course_row and course_row['price'] and course_row['price'] > 0:
        conn.close()
        flash('هذه الدورة مدفوعة. يرجى إتمام الدفع أولاً.', 'error')
        return redirect(url_for('course_checkout', course_id=course_id))

    try:
        conn.execute(
            'INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
            (session['user_id'], course_id)
        )
        conn.commit()
        flash('تم التسجيل في الدورة بنجاح! 🎉', 'success')
    except sqlite3.IntegrityError:
        flash('أنت مسجل بالفعل في هذه الدورة', 'error')
    finally:
        conn.close()

    return redirect(url_for('my_courses'))


@app.route('/courses/<int:course_id>/content')
def course_content(course_id):
    """Course content / learning page — only accessible to enrolled students."""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    # Verify enrollment
    enrollment = conn.execute(
        "SELECT * FROM enrollments WHERE student_id=? AND course_id=?",
        (session['user_id'], course_id)
    ).fetchone()
    if not enrollment:
        conn.close()
        flash('يجب التسجيل في الدورة أولاً للوصول إلى المحتوى', 'error')
        return redirect(url_for('course_details', course_id=course_id))

    course_row = conn.execute('''
        SELECT c.*, u.full_name AS instructor
        FROM courses c JOIN users u ON c.graduate_id = u.id
        WHERE c.id = ?
    ''', (course_id,)).fetchone()
    conn.close()

    if not course_row:
        flash('الدورة غير موجودة', 'error')
        return redirect(url_for('my_courses'))

    # Use real lessons from DB + per-student completion state
    db = get_db()
    lessons_rows = db.execute(
        'SELECT * FROM lessons WHERE course_id=? ORDER BY order_idx ASC, id ASC',
        (course_id,)
    ).fetchall()
    completed_ids = {r['lesson_id'] for r in db.execute(
        'SELECT lesson_id FROM lesson_completions WHERE student_id=?',
        (session['user_id'],)
    ).fetchall()}
    db.close()

    lessons = []
    for r in lessons_rows:
        d = dict(r)
        d['completed'] = d['id'] in completed_ids
        lessons.append(d)

    total = len(lessons)
    done = sum(1 for l in lessons if l['completed'])
    progress = int(round(100.0 * done / total)) if total else 0

    course_data = dict(course_row)
    course_data['progress'] = progress
    course_data['lessons'] = lessons
    course_data['lessons_total'] = total
    course_data['lessons_done'] = done
    course_data['current_video'] = lessons[0]['title'] if lessons else 'لا توجد دروس بعد'

    return render_template('course_content.html', course=course_data)


# =====================================================================
# FR8 - My Courses (real data from DB)
# =====================================================================
@app.route('/my-courses')
def my_courses():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    status_filter = request.args.get('status', 'all')  # all | current | completed | cancelled
    user_type = session.get('user_type')

    conn = get_db()

    if user_type == 'graduate':
        # Graduates see the courses THEY created
        courses = conn.execute('''
            SELECT c.*,
                   (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id) AS students_count
            FROM courses c
            WHERE c.graduate_id = ?
            ORDER BY c.created_at DESC
        ''', (session['user_id'],)).fetchall()
        courses = [dict(c) for c in courses]
        conn.close()
        return render_template('my_courses_graduate.html', courses=courses)

    # Students see enrolled courses with progress derived from lesson completions
    base_query = '''
        SELECT e.*, c.title, c.image, c.duration, c.level, u.full_name AS instructor,
               (SELECT COUNT(*) FROM lessons WHERE course_id = c.id) AS lessons_total,
               (SELECT COUNT(*) FROM lesson_completions lc
                  JOIN lessons l ON l.id = lc.lesson_id
                  WHERE l.course_id = c.id AND lc.student_id = e.student_id) AS lessons_done
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN users u ON c.graduate_id = u.id
        WHERE e.student_id = ?
    '''
    if status_filter == 'all':
        enrollments = conn.execute(base_query + ' ORDER BY e.enrolled_at DESC',
                                   (session['user_id'],)).fetchall()
    else:
        enrollments = conn.execute(base_query + ' AND e.status = ? ORDER BY e.enrolled_at DESC',
                                   (session['user_id'], status_filter)).fetchall()

    enrollments = [dict(e) for e in enrollments]
    for e in enrollments:
        total = e.get('lessons_total') or 0
        done = e.get('lessons_done') or 0
        e['progress'] = int(round(100.0 * done / total)) if total else 0
    conn.close()
    return render_template('my_courses.html', courses=enrollments, current_filter=status_filter)


# =====================================================================
# FR9 - Course Management (graduate creates/publishes/cancels courses)
# =====================================================================
@app.route('/courses/new', methods=['GET', 'POST'])
def course_new():
    """Create a new course (FR9.1, FR9.2) - graduate only"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    if session.get('user_type') != 'graduate':
        flash('هذه الصفحة للخريجين فقط', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price', 0)
        duration = request.form.get('duration')
        level = request.form.get('level')
        field = request.form.get('field')
        tags = request.form.get('tags', '')
        image = request.form.get('image') or 'course1.jpg'

        if not title or not description:
            flash('العنوان والوصف مطلوبان', 'error')
            return redirect(url_for('course_new'))

        try:
            price = float(price)
        except (TypeError, ValueError):
            price = 0

        conn = get_db()
        cursor = conn.execute('''
            INSERT INTO courses (graduate_id, title, description, price, duration, level, field, tags, image, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'published')
        ''', (session['user_id'], title, description, price, duration, level, field, tags, image))
        new_course_id = cursor.lastrowid
        conn.commit()

        # Notify students who have previously chatted with this graduate
        graduate_name = session.get('user_name', 'خريج')
        price_label = f'{int(price)} ر.س' if price > 0 else 'مجانية'
        students_to_notify = conn.execute('''
            SELECT DISTINCT sender_id AS student_id FROM chat_messages
            WHERE receiver_id = ?
            UNION
            SELECT DISTINCT receiver_id AS student_id FROM chat_messages
            WHERE sender_id = ?
        ''', (session['user_id'], session['user_id'])).fetchall()

        for row in students_to_notify:
            sid = row['student_id']
            # Only notify actual students (not other graduates)
            user_check = conn.execute(
                "SELECT user_type FROM users WHERE id=? AND user_type='student'", (sid,)
            ).fetchone()
            if user_check:
                conn.execute(
                    'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
                    (sid,
                     f'دورة جديدة من {graduate_name} 📚',
                     f'أضاف {graduate_name} دورة جديدة: "{title}" ({price_label})',
                     'course',
                     f'/courses/{new_course_id}')
                )
        conn.commit()
        conn.close()

        flash('تم إنشاء الدورة بنجاح! أضف الآن الدروس والفيديوهات 🎬', 'success')
        return redirect(url_for('course_lessons', course_id=new_course_id))

    return render_template('course_new.html')


@app.route('/courses/<int:course_id>/lessons', methods=['GET', 'POST'])
def course_lessons(course_id):
    """Graduate-only page to manage lessons (videos) of a course."""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE id=?', (course_id,)).fetchone()
    if not course or course['graduate_id'] != session['user_id']:
        conn.close()
        flash('غير مصرح بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('my_courses'))

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        video_url = (request.form.get('video_url') or '').strip()
        duration = (request.form.get('duration') or '').strip()
        if not title:
            flash('عنوان الدرس مطلوب', 'error')
            return redirect(url_for('course_lessons', course_id=course_id))
        if video_url:
            video_url = normalize_youtube_url(video_url)
        max_idx = conn.execute(
            'SELECT COALESCE(MAX(order_idx), -1) AS m FROM lessons WHERE course_id=?',
            (course_id,)
        ).fetchone()['m']
        conn.execute(
            'INSERT INTO lessons (course_id, title, video_url, duration, order_idx) VALUES (?, ?, ?, ?, ?)',
            (course_id, title, video_url, duration, max_idx + 1)
        )
        conn.commit()
        conn.close()
        flash('تمت إضافة الدرس بنجاح ✅', 'success')
        return redirect(url_for('course_lessons', course_id=course_id))

    lessons = [dict(r) for r in conn.execute(
        'SELECT * FROM lessons WHERE course_id=? ORDER BY order_idx ASC, id ASC',
        (course_id,)
    ).fetchall()]
    conn.close()
    return render_template('course_lessons.html', course=dict(course), lessons=lessons)


@app.route('/courses/<int:course_id>/lessons/<int:lesson_id>/delete', methods=['POST'])
def lesson_delete(course_id, lesson_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    course = conn.execute('SELECT graduate_id FROM courses WHERE id=?', (course_id,)).fetchone()
    if not course or course['graduate_id'] != session['user_id']:
        conn.close()
        flash('غير مصرح', 'error')
        return redirect(url_for('my_courses'))
    conn.execute('DELETE FROM lesson_completions WHERE lesson_id=?', (lesson_id,))
    conn.execute('DELETE FROM lessons WHERE id=? AND course_id=?', (lesson_id, course_id))
    conn.commit()
    conn.close()
    flash('تم حذف الدرس', 'success')
    return redirect(url_for('course_lessons', course_id=course_id))


@app.route('/api/lessons/<int:lesson_id>/complete', methods=['POST'])
def lesson_complete(lesson_id):
    """Toggle lesson completion for the current student. Returns updated course progress."""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    conn = get_db()
    lesson = conn.execute('SELECT course_id FROM lessons WHERE id=?', (lesson_id,)).fetchone()
    if not lesson:
        conn.close()
        return jsonify({'success': False, 'error': 'الدرس غير موجود'}), 404

    course_id = lesson['course_id']

    # Must be enrolled in this course
    enr = conn.execute(
        'SELECT id FROM enrollments WHERE student_id=? AND course_id=?',
        (session['user_id'], course_id)
    ).fetchone()
    if not enr:
        conn.close()
        return jsonify({'success': False, 'error': 'يجب التسجيل في الدورة أولاً'}), 403

    existing = conn.execute(
        'SELECT 1 FROM lesson_completions WHERE student_id=? AND lesson_id=?',
        (session['user_id'], lesson_id)
    ).fetchone()
    if existing:
        conn.execute('DELETE FROM lesson_completions WHERE student_id=? AND lesson_id=?',
                     (session['user_id'], lesson_id))
        completed = False
    else:
        conn.execute('INSERT INTO lesson_completions (student_id, lesson_id) VALUES (?, ?)',
                     (session['user_id'], lesson_id))
        completed = True

    # Recompute course progress for this student
    total = conn.execute('SELECT COUNT(*) AS c FROM lessons WHERE course_id=?',
                         (course_id,)).fetchone()['c']
    done = conn.execute('''
        SELECT COUNT(*) AS c FROM lesson_completions lc
        JOIN lessons l ON l.id = lc.lesson_id
        WHERE lc.student_id=? AND l.course_id=?
    ''', (session['user_id'], course_id)).fetchone()['c']
    progress = int(round(100.0 * done / total)) if total else 0
    new_status = 'completed' if total and done >= total else 'current'
    conn.execute(
        'UPDATE enrollments SET progress=?, status=? WHERE student_id=? AND course_id=?',
        (progress, new_status, session['user_id'], course_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'completed': completed, 'progress': progress, 'status': new_status})


@app.route('/courses/<int:course_id>/cancel', methods=['POST'])
def course_cancel(course_id):
    """Cancel a course (FR9.3) - graduate only, own courses"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'غير مصرح'}), 401

    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

    if not course:
        conn.close()
        flash('الدورة غير موجودة', 'error')
        return redirect(url_for('my_courses'))

    if course['graduate_id'] != session['user_id']:
        conn.close()
        flash('لا يمكنك إلغاء دورة لا تملكها', 'error')
        return redirect(url_for('my_courses'))

    conn.execute("UPDATE courses SET status = 'cancelled' WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash('تم إلغاء الدورة', 'success')
    return redirect(url_for('my_courses'))


@app.route('/courses/<int:course_id>/republish', methods=['POST'])
def course_republish(course_id):
    """Re-publish a cancelled course."""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course or course['graduate_id'] != session['user_id']:
        conn.close()
        flash('غير مصرح', 'error')
        return redirect(url_for('my_courses'))

    conn.execute("UPDATE courses SET status = 'published' WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash('تم إعادة نشر الدورة', 'success')
    return redirect(url_for('my_courses'))


# =====================================================================
# FR5 - Graduates Evaluation (student evaluates graduates)
# =====================================================================
@app.route('/graduates')
def graduates_list():
    """Graduates evaluation dashboard (FR5.1, FR5.2, FR5.3)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    search = request.args.get('q', '').strip()
    conn = get_db()

    if search:
        rows = conn.execute('''
            SELECT u.id, u.full_name, u.major, u.bio, u.university,
                   (SELECT COUNT(*) FROM courses WHERE graduate_id = u.id AND status='published') AS sessions_count,
                   (SELECT ROUND(AVG((clarity + content_value + interaction)/3.0), 1)
                    FROM graduate_evaluations WHERE graduate_id = u.id) AS rating,
                   (SELECT COUNT(*) FROM graduate_evaluations WHERE graduate_id = u.id) AS reviews_count
            FROM users u
            WHERE u.user_type = 'graduate' AND u.full_name LIKE ?
            ORDER BY rating DESC NULLS LAST
        ''', (f'%{search}%',)).fetchall()
    else:
        rows = conn.execute('''
            SELECT u.id, u.full_name, u.major, u.bio, u.university,
                   (SELECT COUNT(*) FROM courses WHERE graduate_id = u.id AND status='published') AS sessions_count,
                   (SELECT ROUND(AVG((clarity + content_value + interaction)/3.0), 1)
                    FROM graduate_evaluations WHERE graduate_id = u.id) AS rating,
                   (SELECT COUNT(*) FROM graduate_evaluations WHERE graduate_id = u.id) AS reviews_count
            FROM users u
            WHERE u.user_type = 'graduate'
            ORDER BY rating DESC NULLS LAST
        ''').fetchall()

    graduates = [dict(r) for r in rows]

    # Top-rated graduates (FR5.9)
    top_rated = [g for g in graduates if g.get('rating') is not None][:5]

    conn.close()
    return render_template('graduates.html', graduates=graduates, top_rated=top_rated, search=search)


@app.route('/graduates/<int:graduate_id>')
def graduate_profile(graduate_id):
    """View graduate profile (FR5.10)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    graduate = conn.execute('SELECT * FROM users WHERE id = ? AND user_type=?',
                            (graduate_id, 'graduate')).fetchone()
    if not graduate:
        conn.close()
        flash('الخريج غير موجود', 'error')
        return redirect(url_for('graduates_list'))

    graduate = dict(graduate)

    # FR15.3 — privacy: only the owner can view a private profile
    if not graduate.get('profile_public') and graduate['id'] != session['user_id']:
        conn.close()
        flash('هذا الملف الشخصي خاص ولا يمكن عرضه.', 'error')
        return redirect(url_for('graduates_list'))

    stats = conn.execute('''
        SELECT ROUND(AVG(clarity), 1) AS avg_clarity,
               ROUND(AVG(content_value), 1) AS avg_content,
               ROUND(AVG(interaction), 1) AS avg_interaction,
               COUNT(*) AS total_reviews
        FROM graduate_evaluations WHERE graduate_id = ?
    ''', (graduate_id,)).fetchone()

    courses = conn.execute('''
        SELECT * FROM courses WHERE graduate_id = ? AND status='published'
        ORDER BY created_at DESC
    ''', (graduate_id,)).fetchall()

    recent_evals = conn.execute('''
        SELECT ge.*, u.full_name AS student_name
        FROM graduate_evaluations ge
        JOIN users u ON ge.student_id = u.id
        WHERE ge.graduate_id = ?
        ORDER BY ge.created_at DESC LIMIT 10
    ''', (graduate_id,)).fetchall()
    conn.close()

    overall = None
    if stats['total_reviews']:
        overall = round(((stats['avg_clarity'] or 0) + (stats['avg_content'] or 0) + (stats['avg_interaction'] or 0)) / 3, 1)

    return render_template('graduate_profile.html', graduate=graduate,
                           stats=dict(stats), overall=overall,
                           courses=[dict(c) for c in courses],
                           recent_evals=[dict(e) for e in recent_evals])


@app.route('/graduates/<int:graduate_id>/evaluate', methods=['GET', 'POST'])
def evaluate_graduate(graduate_id):
    """Evaluate a graduate (FR5.4 - FR5.8)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    graduate = conn.execute('SELECT * FROM users WHERE id = ? AND user_type=?',
                            (graduate_id, 'graduate')).fetchone()
    if not graduate:
        conn.close()
        flash('الخريج غير موجود', 'error')
        return redirect(url_for('graduates_list'))

    if request.method == 'POST':
        try:
            clarity = int(request.form.get('clarity', 0))
            content_value = int(request.form.get('content_value', 0))
            interaction = int(request.form.get('interaction', 0))
        except ValueError:
            flash('قيم التقييم غير صالحة', 'error')
            return redirect(url_for('evaluate_graduate', graduate_id=graduate_id))

        notes = request.form.get('notes', '')

        if not (1 <= clarity <= 5 and 1 <= content_value <= 5 and 1 <= interaction <= 5):
            flash('يجب أن تكون التقييمات من 1 إلى 5', 'error')
            return redirect(url_for('evaluate_graduate', graduate_id=graduate_id))

        conn.execute('''
            INSERT INTO graduate_evaluations (student_id, graduate_id, clarity, content_value, interaction, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], graduate_id, clarity, content_value, interaction, notes))
        conn.commit()

        # Calc result to show (FR5.8)
        result = round((clarity + content_value + interaction) / 3, 1)
        conn.close()

        flash(f'تم إرسال التقييم بنجاح! النتيجة: {result}/5 ⭐', 'success')
        return redirect(url_for('graduate_profile', graduate_id=graduate_id))

    conn.close()
    return render_template('evaluate_graduate.html', graduate=dict(graduate))


# =====================================================================
# FR10 - Community (posts, likes, comments, groups, search)
# =====================================================================
@app.route('/community')
def community():
    """Community hub (FR10.6, FR10.8, FR10.9)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    # Groups with member count + whether current user joined
    groups = conn.execute('''
        SELECT g.*,
               (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) AS members,
               EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_id = ?) AS joined
        FROM groups g
        ORDER BY members DESC
    ''', (session['user_id'],)).fetchall()

    # Community stats (FR10.8)
    stats = conn.execute('''
        SELECT
            (SELECT COUNT(*) FROM posts) AS total_posts,
            (SELECT COUNT(*) FROM post_comments) AS total_comments,
            (SELECT COUNT(*) FROM post_likes) AS total_likes
    ''').fetchone()

    # Trending hashtags (FR10.9) - simple: most common tags in recent posts
    recent = conn.execute(
        'SELECT tags FROM posts WHERE tags IS NOT NULL AND tags != "" ORDER BY created_at DESC LIMIT 100'
    ).fetchall()
    conn.close()

    tag_counts = {}
    for r in recent:
        for t in (r['tags'] or '').split(','):
            t = t.strip()
            if t:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    trending = sorted(tag_counts.items(), key=lambda x: -x[1])[:6]
    trending = [{'tag': t, 'count': c} for t, c in trending]

    return render_template('community.html',
                           groups=[dict(g) for g in groups],
                           stats=dict(stats),
                           trending=trending)


@app.route('/community/posts')
def community_posts():
    """Posts feed + search (FR10.1, FR10.3, FR10.5)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    conn = get_db()

    if q:
        rows = conn.execute('''
            SELECT p.*, u.full_name AS author,
                   (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) AS likes,
                   (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id) AS comments,
                   EXISTS(SELECT 1 FROM post_likes WHERE post_id = p.id AND user_id = ?) AS liked
            FROM posts p JOIN users u ON p.user_id = u.id
            WHERE p.content LIKE ? OR p.tags LIKE ?
            ORDER BY p.created_at DESC
        ''', (session['user_id'], f'%{q}%', f'%{q}%')).fetchall()
    else:
        rows = conn.execute('''
            SELECT p.*, u.full_name AS author,
                   (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) AS likes,
                   (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id) AS comments,
                   EXISTS(SELECT 1 FROM post_likes WHERE post_id = p.id AND user_id = ?) AS liked
            FROM posts p JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
        ''', (session['user_id'],)).fetchall()

    posts = []
    for r in rows:
        d = dict(r)
        d['avatar'] = (d['author'][:1] if d['author'] else '?').upper()
        d['tags_list'] = [t.strip() for t in (d.get('tags') or '').split(',') if t.strip()]
        posts.append(d)
    conn.close()
    return render_template('community_posts.html', posts=posts, search=q)


@app.route('/community/posts/new', methods=['POST'])
def post_create():
    """Create a new post (FR10.2) with content moderation."""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    content = request.form.get('content', '').strip()
    tags = request.form.get('tags', '').strip()
    if not content:
        flash('لا يمكن نشر منشور فارغ', 'error')
        return redirect(url_for('community_posts'))

    allowed, reason = moderate_post(content)
    if not allowed:
        flash(f'تم رفض المنشور: {reason}', 'error')
        return redirect(url_for('community_posts'))

    conn = get_db()
    conn.execute('INSERT INTO posts (user_id, content, tags) VALUES (?, ?, ?)',
                 (session['user_id'], content, tags))
    conn.commit()
    conn.close()
    flash('تم نشر منشورك!', 'success')
    return redirect(url_for('community_posts'))


@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def post_like(post_id):
    """Toggle like on a post (FR10.4)"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    conn = get_db()
    existing = conn.execute('SELECT 1 FROM post_likes WHERE user_id=? AND post_id=?',
                            (session['user_id'], post_id)).fetchone()
    if existing:
        conn.execute('DELETE FROM post_likes WHERE user_id=? AND post_id=?',
                     (session['user_id'], post_id))
        liked = False
    else:
        conn.execute('INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)',
                     (session['user_id'], post_id))
        liked = True
    conn.commit()
    count = conn.execute('SELECT COUNT(*) as c FROM post_likes WHERE post_id=?',
                         (post_id,)).fetchone()['c']
    conn.close()
    return jsonify({'success': True, 'liked': liked, 'count': count})


@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def post_comment(post_id):
    """Add comment to post (FR10.4) with content moderation."""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    content = (request.json or {}).get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'التعليق فارغ'}), 400

    allowed, reason = moderate_post(content)
    if not allowed:
        return jsonify({'success': False, 'moderated': True, 'error': reason}), 200

    conn = get_db()
    conn.execute('INSERT INTO post_comments (user_id, post_id, content) VALUES (?, ?, ?)',
                 (session['user_id'], post_id, content))
    conn.commit()
    count = conn.execute('SELECT COUNT(*) as c FROM post_comments WHERE post_id=?',
                         (post_id,)).fetchone()['c']
    conn.close()
    return jsonify({'success': True, 'count': count})


@app.route('/community/groups/<int:group_id>/join', methods=['POST'])
def group_join(group_id):
    """Join a community group (FR10.7)"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    conn = get_db()
    group = conn.execute('SELECT name FROM groups WHERE id=?', (group_id,)).fetchone()
    group_name = group['name'] if group else 'المجموعة'
    try:
        conn.execute('INSERT INTO group_members (user_id, group_id) VALUES (?, ?)',
                     (session['user_id'], group_id))
        conn.execute(
            'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'],
             'انضممت إلى مجموعة 👥',
             f'تم انضمامك إلى "{group_name}" بنجاح',
             'general',
             '/community')
        )
        conn.commit()
        flash('انضممت للمجموعة!', 'success')
    except sqlite3.IntegrityError:
        # leave group
        conn.execute('DELETE FROM group_members WHERE user_id=? AND group_id=?',
                     (session['user_id'], group_id))
        conn.commit()
        flash('تم المغادرة من المجموعة', 'success')
    conn.close()
    return redirect(url_for('community'))


@app.route('/community/groups/<int:group_id>')
def group_chat(group_id):
    """Group chat page — view members + send/read real messages."""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    group = conn.execute('SELECT * FROM groups WHERE id=?', (group_id,)).fetchone()
    if not group:
        conn.close()
        flash('المجموعة غير موجودة', 'error')
        return redirect(url_for('community'))

    is_member = conn.execute(
        'SELECT 1 FROM group_members WHERE user_id=? AND group_id=?',
        (session['user_id'], group_id)
    ).fetchone() is not None

    members = conn.execute('''
        SELECT u.id, u.full_name, u.user_type, u.profile_image
        FROM group_members gm JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
        ORDER BY gm.joined_at ASC
    ''', (group_id,)).fetchall()

    messages = []
    if is_member:
        messages = conn.execute('''
            SELECT m.id, m.content, m.created_at, m.user_id,
                   u.full_name, u.user_type, u.profile_image
            FROM group_messages m JOIN users u ON m.user_id = u.id
            WHERE m.group_id = ?
            ORDER BY m.id ASC
            LIMIT 200
        ''', (group_id,)).fetchall()
    conn.close()

    return render_template('group_chat.html',
                           group=dict(group),
                           members=[dict(m) for m in members],
                           messages=[dict(m) for m in messages],
                           is_member=is_member)


@app.route('/api/groups/<int:group_id>/messages', methods=['GET', 'POST'])
def api_group_messages(group_id):
    """Send/list messages in a group. Members only."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    conn = get_db()
    is_member = conn.execute(
        'SELECT 1 FROM group_members WHERE user_id=? AND group_id=?',
        (session['user_id'], group_id)
    ).fetchone() is not None
    if not is_member:
        conn.close()
        return jsonify({'success': False, 'error': 'not_a_member'}), 403

    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        content = (payload.get('content') or '').strip()
        if not content:
            conn.close()
            return jsonify({'success': False, 'error': 'empty'}), 400
        if len(content) > 2000:
            content = content[:2000]

        allowed, reason = moderate_post(content)
        if not allowed:
            conn.close()
            return jsonify({'success': False, 'moderated': True, 'error': reason}), 200

        conn.execute(
            'INSERT INTO group_messages (group_id, user_id, content) VALUES (?, ?, ?)',
            (group_id, session['user_id'], content)
        )
        conn.commit()

    after = request.args.get('after', type=int) or 0
    rows = conn.execute('''
        SELECT m.id, m.content, m.created_at, m.user_id,
               u.full_name, u.user_type, u.profile_image
        FROM group_messages m JOIN users u ON m.user_id = u.id
        WHERE m.group_id = ? AND m.id > ?
        ORDER BY m.id ASC
        LIMIT 200
    ''', (group_id, after)).fetchall()
    conn.close()

    return jsonify({
        'success': True,
        'messages': [dict(r) for r in rows],
        'me': session['user_id'],
    })


# =====================================================================
# FR11 - Messages (real chat + course offers)
# =====================================================================
@app.route('/messages')
def messages():
    """Messages page (FR11.1, FR11.2)"""
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    uid = session['user_id']
    partner_id = request.args.get('with', type=int)

    conn = get_db()

    # List of conversation partners (anyone we messaged or messaged us)
    partners = conn.execute('''
        SELECT u.id, u.full_name AS name, u.user_type,
               (SELECT content FROM chat_messages
                WHERE (sender_id=u.id AND receiver_id=?) OR (sender_id=? AND receiver_id=u.id)
                ORDER BY created_at DESC LIMIT 1) AS last_message,
               (SELECT created_at FROM chat_messages
                WHERE (sender_id=u.id AND receiver_id=?) OR (sender_id=? AND receiver_id=u.id)
                ORDER BY created_at DESC LIMIT 1) AS last_time
        FROM users u
        WHERE u.id IN (
            SELECT DISTINCT CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END
            FROM chat_messages WHERE sender_id=? OR receiver_id=?
        )
        ORDER BY last_time DESC
    ''', (uid, uid, uid, uid, uid, uid, uid)).fetchall()

    partners = [dict(p) for p in partners]
    for p in partners:
        p['avatar'] = (p['name'][:2] if p['name'] else '?').upper()

    # Active conversation
    active_messages = []
    active_partner = None
    if partner_id:
        active_partner = conn.execute('SELECT id, full_name, user_type FROM users WHERE id=?',
                                       (partner_id,)).fetchone()
        if active_partner:
            active_partner = dict(active_partner)
            active_partner['avatar'] = (active_partner['full_name'][:2]).upper()
            msgs = conn.execute('''
                SELECT m.*,
                       co.status AS offer_status, co.course_id AS offer_course_id,
                       co.id AS offer_id,
                       c.title AS course_title, c.price AS course_price,
                       c.duration AS course_duration, c.image AS course_image
                FROM chat_messages m
                LEFT JOIN course_offers co ON co.message_id = m.id
                LEFT JOIN courses c ON co.course_id = c.id
                WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?)
                ORDER BY m.created_at ASC
            ''', (uid, partner_id, partner_id, uid)).fetchall()
            active_messages = [dict(m) for m in msgs]

    # Graduate's own courses - for "share course offer" (FR11.4)
    my_courses_for_offer = []
    if session.get('user_type') == 'graduate':
        my_courses_for_offer = [dict(c) for c in conn.execute(
            "SELECT id, title, price, duration FROM courses WHERE graduate_id=? AND status='published'",
            (uid,)
        ).fetchall()]

    conn.close()
    return render_template('messages.html',
                           partners=partners,
                           active_partner=active_partner,
                           active_messages=active_messages,
                           my_courses=my_courses_for_offer)


@app.route('/api/messages/send', methods=['POST'])
def messages_send():
    """Send a text message (FR11.3) with content moderation and notification."""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    data = request.json or {}
    receiver_id = data.get('receiver_id')
    content = (data.get('content') or '').strip()
    if not receiver_id or not content:
        return jsonify({'success': False, 'error': 'البيانات ناقصة'}), 400

    # Content moderation — block academic dishonesty requests
    allowed, reason = moderate_message(content)
    if not allowed:
        return jsonify({'success': False, 'moderated': True, 'error': reason}), 200

    conn = get_db()
    conn.execute('INSERT INTO chat_messages (sender_id, receiver_id, content) VALUES (?, ?, ?)',
                 (session['user_id'], receiver_id, content))
    conn.commit()

    # Notify the receiver
    sender_name = session.get('user_name', 'أحد المستخدمين')
    conn.execute(
        'INSERT INTO notifications (user_id, title, message, notif_type, link) VALUES (?, ?, ?, ?, ?)',
        (receiver_id,
         'رسالة جديدة 💬',
         f'لديك رسالة جديدة من {sender_name}',
         'message',
         f'/messages?with={session["user_id"]}')
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/messages/start', methods=['POST'])
def messages_start():
    """Start a chat with a graduate (FR11.2)"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    data = request.json or {}
    partner_id = data.get('partner_id')
    if not partner_id:
        return jsonify({'success': False}), 400
    conn = get_db()
    existing = conn.execute('''
        SELECT 1 FROM chat_messages
        WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
        LIMIT 1
    ''', (session['user_id'], partner_id, partner_id, session['user_id'])).fetchone()
    if not existing:
        conn.execute('INSERT INTO chat_messages (sender_id, receiver_id, content) VALUES (?, ?, ?)',
                     (session['user_id'], partner_id, 'مرحباً! 👋'))
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'url': url_for('messages', **{'with': partner_id})})


@app.route('/api/messages/share-course', methods=['POST'])
def messages_share_course():
    """Graduate shares a course offer card (FR11.4)"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    if session.get('user_type') != 'graduate':
        return jsonify({'success': False, 'error': 'الميزة للخريجين فقط'}), 403
    data = request.json or {}
    receiver_id = data.get('receiver_id')
    course_id = data.get('course_id')
    if not receiver_id or not course_id:
        return jsonify({'success': False, 'error': 'البيانات ناقصة'}), 400
    conn = get_db()
    course = conn.execute('SELECT * FROM courses WHERE id=? AND graduate_id=?',
                          (course_id, session['user_id'])).fetchone()
    if not course:
        conn.close()
        return jsonify({'success': False, 'error': 'لا تملك هذه الدورة'}), 403
    cursor = conn.execute('''
        INSERT INTO chat_messages (sender_id, receiver_id, content, message_type)
        VALUES (?, ?, ?, 'course_offer')
    ''', (session['user_id'], receiver_id, f'عرض دورة: {course["title"]}'))
    msg_id = cursor.lastrowid
    conn.execute('INSERT INTO course_offers (message_id, course_id) VALUES (?, ?)',
                 (msg_id, course_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/offer/<int:offer_id>/respond', methods=['POST'])
def offer_respond(offer_id):
    """Student accepts/rejects course offer (FR11.5)"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    action = (request.json or {}).get('action')  # accept | reject
    if action not in ('accept', 'reject'):
        return jsonify({'success': False}), 400
    conn = get_db()
    offer = conn.execute('''
        SELECT co.*, m.receiver_id
        FROM course_offers co JOIN chat_messages m ON co.message_id = m.id
        WHERE co.id = ?
    ''', (offer_id,)).fetchone()
    if not offer or offer['receiver_id'] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'error': 'غير مصرح'}), 403

    new_status = 'accepted' if action == 'accept' else 'rejected'
    conn.execute('UPDATE course_offers SET status=? WHERE id=?', (new_status, offer_id))

    # If accepted, auto-enroll
    if action == 'accept':
        try:
            conn.execute('INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                         (session['user_id'], offer['course_id']))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'status': new_status})


# =====================================================================
# FR14 - Favorites (real DB)
# =====================================================================
@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    rows = conn.execute('''
        SELECT c.*, u.full_name AS instructor
        FROM favorites f
        JOIN courses c ON f.course_id = c.id
        JOIN users u ON c.graduate_id = u.id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('favorites.html', courses=[dict(c) for c in rows])


@app.route('/api/favorites/<int:course_id>', methods=['POST'])
def toggle_favorite(course_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    conn = get_db()
    existing = conn.execute('SELECT 1 FROM favorites WHERE user_id=? AND course_id=?',
                            (session['user_id'], course_id)).fetchone()
    if existing:
        conn.execute('DELETE FROM favorites WHERE user_id=? AND course_id=?',
                     (session['user_id'], course_id))
        is_fav = False
    else:
        conn.execute('INSERT INTO favorites (user_id, course_id) VALUES (?, ?)',
                     (session['user_id'], course_id))
        is_fav = True
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'favorite': is_fav})


# =====================================================================
# FR15.2 - Language toggle
# =====================================================================
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ('ar', 'en'):
        session['lang'] = lang
        flash('تم تغيير اللغة' if lang == 'ar' else 'Language changed', 'success')
    return redirect(request.referrer or url_for('dashboard'))


# =====================================================================
# FR16.6 - Analyze my profile
# =====================================================================
@app.route('/api/analyze-profile', methods=['POST'])
def analyze_profile():
    """Profile-based analysis to improve recommendations (FR16.6)"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    interests = [r['interest'] for r in conn.execute(
        'SELECT interest FROM interests WHERE user_id=?', (session['user_id'],)
    ).fetchall()]
    conn.close()

    if not user:
        return jsonify({'success': False}), 404

    user = dict(user)
    profile_text = f"""
- الاسم: {user.get('full_name')}
- التخصص: {user.get('major') or 'غير محدد'}
- الجامعة: {user.get('university') or 'غير محدد'}
- السنة الأكاديمية: {user.get('academic_year') or user.get('graduation_year') or 'غير محدد'}
- المعدل: {user.get('gpa') or 'غير محدد'}
- نبذة: {user.get('bio') or 'لا يوجد'}
- الاهتمامات: {', '.join(interests) if interests else 'لا توجد'}
""".strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مستشار تعليمي خبير. حلل الملف الشخصي للمستخدم وقدم تحليلاً مفيداً بصيغة JSON."},
                {"role": "user", "content": f"""حلل ملف المستخدم التالي واستجب بصيغة JSON فقط:

{profile_text}

استجب بهذا التنسيق:
{{
  "strengths": ["قوة 1", "قوة 2", "قوة 3"],
  "recommended_fields": ["مجال 1", "مجال 2"],
  "suggested_skills": ["مهارة 1", "مهارة 2", "مهارة 3"],
  "career_path": "وصف مختصر للمسار المهني المقترح",
  "summary": "تحليل شخصي موجز في فقرة واحدة"
}}"""}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        import json as _json
        analysis = _json.loads(response.choices[0].message.content)
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        print(f"Analyze profile error: {e}")
        return jsonify({
            'success': True,
            'analysis': {
                'strengths': ['شغف بالتعلم', 'التزام بالتقدم', 'اهتمام بتطوير المهارات'],
                'recommended_fields': [user.get('major') or 'التقنية', 'تطوير المهارات العامة'],
                'suggested_skills': ['التفكير النقدي', 'حل المشكلات', 'التواصل الفعال'],
                'career_path': 'استمر في تطوير مهاراتك وابنِ مشاريع عملية.',
                'summary': 'ملفك يعكس اهتماماً حقيقياً بالنمو المهني. نوصي بالتركيز على اكتساب خبرة عملية.'
            }
        })


# =====================================================================
# Terms & Conditions / Privacy Policy
# =====================================================================
@app.route('/terms')
def terms():
    return render_template('terms.html')


# =====================================================================
# FR1.3, FR1.4 - Email verification
# =====================================================================
@app.route('/verify-email/<token>')
def verify_email(token):
    conn = get_db()
    user = conn.execute(
        'SELECT id, full_name, email_verified FROM users WHERE verification_token=?', (token,)
    ).fetchone()
    if not user:
        conn.close()
        flash('رابط التأكيد غير صالح أو منتهي.', 'error')
        return redirect(url_for('login'))
    if user['email_verified']:
        conn.close()
        flash('تم تأكيد بريدك الإلكتروني مسبقاً. يمكنك تسجيل الدخول.', 'success')
        return redirect(url_for('login'))
    conn.execute('UPDATE users SET email_verified=1 WHERE id=?', (user['id'],))
    conn.commit()
    conn.close()
    flash(f'تم تأكيد بريدك الإلكتروني بنجاح يا {user["full_name"]}! يمكنك الآن تسجيل الدخول.', 'success')
    return redirect(url_for('login'))


# =====================================================================
# FR2.3 - Forgot password (real reset-token flow)
# =====================================================================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        if not email:
            flash('يرجى إدخال البريد الإلكتروني', 'error')
            return redirect(url_for('forgot_password'))
        conn = get_db()
        user = conn.execute('SELECT id, full_name FROM users WHERE LOWER(email)=?', (email,)).fetchone()
        if user:
            token = generate_token()
            conn.execute(
                'INSERT INTO password_resets (user_id, token) VALUES (?, ?)',
                (user['id'], token)
            )
            conn.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            simulate_email(email, 'استعادة كلمة المرور',
                           f'مرحباً {user["full_name"]},\nاضغط على الرابط لإعادة تعيين كلمة المرور:\n{reset_link}',
                           link=reset_link)
            flash('تم إرسال رابط الاستعادة. تحقق من بريدك الإلكتروني.', 'success')
        else:
            # Don't leak whether the email exists
            flash('إذا كان هذا البريد مسجلاً لدينا، فقد أرسلنا إليه رابط الاستعادة.', 'success')
        conn.close()
        return redirect(url_for('login'))
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db()
    reset = conn.execute(
        'SELECT * FROM password_resets WHERE token=? AND used=0', (token,)
    ).fetchone()
    if not reset:
        conn.close()
        flash('رابط الاستعادة غير صالح أو مستخدم.', 'error')
        return redirect(url_for('forgot_password'))

    # Tokens expire after 1 hour
    try:
        created = datetime.strptime(reset['created_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() - created > timedelta(hours=1):
            conn.close()
            flash('انتهت صلاحية رابط الاستعادة. الرجاء طلب رابط جديد.', 'error')
            return redirect(url_for('forgot_password'))
    except Exception:
        pass

    if request.method == 'POST':
        new_password = request.form.get('password') or ''
        confirm = request.form.get('confirm_password') or ''
        if new_password != confirm:
            conn.close()
            flash('كلمات المرور غير متطابقة', 'error')
            return redirect(url_for('reset_password', token=token))
        is_valid, message = validate_password(new_password)
        if not is_valid:
            conn.close()
            flash(message, 'error')
            return redirect(url_for('reset_password', token=token))
        conn.execute('UPDATE users SET password=? WHERE id=?',
                     (generate_password_hash(new_password), reset['user_id']))
        conn.execute('UPDATE password_resets SET used=1 WHERE id=?', (reset['id'],))
        conn.commit()
        conn.close()
        flash('تم تحديث كلمة المرور بنجاح. يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('login'))

    conn.close()
    return render_template('reset_password.html', token=token)




if __name__ == '__main__':
    print(" Starting Muntalaq Platform...")
    print("📍 Server running on http://localhost:5001")
    print(" Arabic RTL interface ready!")
    app.run(debug=True, host="127.0.0.1", port=5001)

