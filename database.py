import sqlite3
import json
from datetime import datetime
import hashlib

def create_database():
    """Create the database and all necessary tables"""
    conn = sqlite3.connect('kazakh_learning.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        streak_days INTEGER DEFAULT 0,
        total_words_learned INTEGER DEFAULT 0,
        total_courses_completed INTEGER DEFAULT 0,
        total_trophies INTEGER DEFAULT 0,
        current_theme TEXT DEFAULT 'purple'
    )
    ''')
    
    # Courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title_en TEXT NOT NULL,
        title_kk TEXT NOT NULL,
        title_ru TEXT NOT NULL,
        description_en TEXT,
        description_kk TEXT,
        description_ru TEXT,
        level TEXT CHECK(level IN ('beginner', 'intermediate', 'advanced')),
        total_lessons INTEGER DEFAULT 0,
        order_index INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Lessons table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title_en TEXT NOT NULL,
        title_kk TEXT NOT NULL,
        title_ru TEXT NOT NULL,
        content_en TEXT,
        content_kk TEXT,
        content_ru TEXT,
        lesson_order INTEGER,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    )
    ''')
    
    # Words table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        kazakh TEXT NOT NULL,
        english TEXT NOT NULL,
        russian TEXT NOT NULL,
        pronunciation TEXT,
        example_sentence_kk TEXT,
        example_sentence_en TEXT,
        example_sentence_ru TEXT,
        word_type TEXT,
        FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
    )
    ''')
    
    # Grammar rules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grammar_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title_en TEXT NOT NULL,
        title_kk TEXT NOT NULL,
        title_ru TEXT NOT NULL,
        explanation_en TEXT,
        explanation_kk TEXT,
        explanation_ru TEXT,
        examples TEXT,
        difficulty TEXT CHECK(difficulty IN ('beginner', 'intermediate', 'advanced')),
        order_index INTEGER
    )
    ''')
    
    # User progress table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        lesson_id INTEGER,
        completed BOOLEAN DEFAULT 0,
        score INTEGER,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
        FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
        UNIQUE(user_id, lesson_id)
    )
    ''')
    
    # User learned words table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_learned_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        word_id INTEGER NOT NULL,
        learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        proficiency INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
        UNIQUE(user_id, word_id)
    )
    ''')
    
    # Course tests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS course_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        question_text_en TEXT NOT NULL,
        question_text_kk TEXT NOT NULL,
        question_text_ru TEXT NOT NULL,
        question_type TEXT CHECK(question_type IN ('multiple_choice', 'translation', 'fill_blank')),
        correct_answer TEXT NOT NULL,
        options TEXT,
        points INTEGER DEFAULT 1,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    )
    ''')
    
    # User test results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total_points INTEGER NOT NULL,
        percentage REAL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    )
    ''')
    
    # Trophies table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trophies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT NOT NULL,
        name_kk TEXT NOT NULL,
        name_ru TEXT NOT NULL,
        description_en TEXT,
        description_kk TEXT,
        description_ru TEXT,
        icon TEXT,
        requirement_type TEXT,
        requirement_value INTEGER
    )
    ''')
    
    # User trophies table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_trophies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trophy_id INTEGER NOT NULL,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (trophy_id) REFERENCES trophies(id) ON DELETE CASCADE,
        UNIQUE(user_id, trophy_id)
    )
    ''')
    
    conn.commit()
    print("✅ Database schema created successfully!")
    return conn

def populate_sample_data(conn):
    """Populate database with sample data"""
    cursor = conn.cursor()
    
    # Add sample user
    password_hash = hashlib.sha256("password123".encode()).hexdigest()
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, email, password_hash, streak_days, total_words_learned, total_courses_completed, total_trophies)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("Student123", "student@kazakh.learn", password_hash, 23, 347, 12, 8))
    
    # Add courses
    courses_data = [
        (1, "Kazakh Alphabet & Pronunciation", "Қазақ әліпбиі және айтылымы", "Казахский алфавит и произношение",
         "Learn the basics of Kazakh alphabet and correct pronunciation",
         "Қазақ әліпбиінің негіздері мен дұрыс айтылымын үйреніңіз",
         "Изучите основы казахского алфавита и правильное произношение",
         "beginner", 10, 1),
        (2, "Basic Greetings & Phrases", "Негізгі сәлемдесулер мен сөз тіркестері", "Основные приветствия и фразы",
         "Common phrases for everyday conversations",
         "Күнделікті әңгімелер үшін жалпы сөз тіркестері",
         "Общие фразы для повседневных разговоров",
         "beginner", 15, 2),
        (3, "Numbers & Counting", "Сандар мен санау", "Числа и счет",
         "Master numbers from 1 to 1000 and beyond",
         "1-ден 1000-ға дейінгі және одан әрі сандарды меңгеріңіз",
         "Освойте числа от 1 до 1000 и далее",
         "beginner", 12, 3),
        (4, "Grammar Fundamentals", "Грамматика негіздері", "Основы грамматики",
         "Understand the structure of Kazakh sentences",
         "Қазақ сөйлемдерінің құрылымын түсіну",
         "Понимание структуры казахских предложений",
         "intermediate", 20, 4),
        (5, "Conversational Kazakh", "Сөйлесу қазақшасы", "Разговорный казахский",
         "Practice real-life conversations and dialogues",
         "Нақты өмірдегі әңгімелер мен диалогтарды жаттықтыру",
         "Практикуйте реальные разговоры и диалоги",
         "intermediate", 18, 5),
        (6, "Advanced Literature", "Жоғары деңгейлі әдебиет", "Продвинутая литература",
         "Explore Kazakh poetry and prose",
         "Қазақ поэзиясы мен прозасын зерттеңіз",
         "Исследуйте казахскую поэзию и прозу",
         "advanced", 25, 6)
    ]
    
    for course in courses_data:
        cursor.execute('''
        INSERT OR IGNORE INTO courses (id, title_en, title_kk, title_ru, description_en, description_kk, description_ru, level, total_lessons, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', course)
    
    # Add sample lessons for Course 1
    lessons_data = [
        (1, "Introduction to Kazakh Alphabet", "Қазақ әліпбиіне кіріспе", "Введение в казахский алфавит",
         "The Kazakh alphabet contains 42 letters...", "Қазақ әліпбиінде 42 әріп бар...", "Казахский алфавит содержит 42 буквы...", 1),
        (2, "Vowels in Kazakh", "Қазақ дауысты дыбыстары", "Гласные в казахском",
         "Kazakh has 9 vowels...", "Қазақ тілінде 9 дауысты дыбыс бар...", "В казахском языке 9 гласных...", 2),
        (3, "Consonants Part 1", "Дауыссыз дыбыстар 1-бөлім", "Согласные часть 1",
         "Let's learn the first group of consonants...", "Дауыссыз дыбыстардың бірінші тобын үйренейік...", "Давайте изучим первую группу согласных...", 3),
    ]
    
    for lesson in lessons_data:
        cursor.execute('''
        INSERT OR IGNORE INTO lessons (course_id, title_en, title_kk, title_ru, content_en, content_kk, content_ru, lesson_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', lesson)
    
    # Add sample words for Lesson 1
    words_data = [
        (1, "Сәлем", "Hello", "Привет", "salem", "Сәлем! Қалың қалай?", "Hello! How are you?", "Привет! Как дела?", "greeting"),
        (2, "Сәлеметсіз бе", "Hello (formal)", "Здравствуйте", "salemetsize be", "Сәлеметсіз бе, мұғалім!", "Hello, teacher!", "Здравствуйте, учитель!", "greeting"),
        (3, "Рахмет", "Thank you", "Спасибо", "rahmet", "Рахмет сізге!", "Thank you!", "Спасибо вам!", "expression"),
        (4, "Кешіріңіз", "Excuse me", "Извините", "keshiriniz", "Кешіріңіз, сіз маған көмектесе аласыз ба?", "Excuse me, can you help me?", "Извините, вы можете мне помочь?", "expression"),
        (5, "Иә", "Yes", "Да", "ia", "Иә, мен келемін", "Yes, I'm coming", "Да, я иду", "answer"),
        (6, "Жоқ", "No", "Нет", "joq", "Жоқ, бұл менің кітабым емес", "No, this is not my book", "Нет, это не моя книга", "answer"),
    ]
    
    for word in words_data:
        cursor.execute('''
        INSERT OR IGNORE INTO words (lesson_id, kazakh, english, russian, pronunciation, example_sentence_kk, example_sentence_en, example_sentence_ru, word_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', word)
    
    # Add grammar rules
    grammar_data = [
        ("Vowel Harmony", "Vowel Harmony Rules", "Дауысты дыбыстардың үндесуі", "Правила гармонии гласных",
         "Kazakh uses vowel harmony, meaning vowels in a word must belong to the same group (front or back vowels).",
         "Қазақ тілінде дауысты үндесім қолданылады, яғни сөздегі дауыстылар бір топқа жатуы керек.",
         "В казахском языке используется гармония гласных, то есть гласные в слове должны принадлежать к одной группе.",
         '{"example1": "кітап (kitap) - book", "example2": "үстел (ustel) - table"}', "beginner", 1),
        ("Plural Forms", "Forming Plurals", "Көпше түрін жасау", "Образование множественного числа",
         "Add -лар/-лер or -дар/-дер or -тар/-тер depending on the last sound of the word.",
         "Сөздің соңғы дыбысына қарай -лар/-лер немесе -дар/-дер немесе -тар/-тер жалғаңыз.",
         "Добавьте -лар/-лер или -дар/-дер или -тар/-тер в зависимости от последнего звука слова.",
         '{"example1": "кітап + тар = кітаптар (books)", "example2": "бала + лар = балалар (children)"}', "beginner", 2),
        ("Personal Pronouns", "Personal Pronouns", "Жіктеу есімдіктері", "Личные местоимения",
         "Learn the personal pronouns: мен (I), сен (you), сіз (you formal), ол (he/she/it), біз (we), сендер (you plural), сіздер (you plural formal), олар (they)",
         "Жіктеу есімдіктерін үйреніңіз: мен (мен), сен (сен), сіз (сіз), ол (ол), біз (біз), сендер (сендер), сіздер (сіздер), олар (олар)",
         "Изучите личные местоимения: мен (я), сен (ты), сіз (вы), ол (он/она/оно), біз (мы), сендер (вы мн.), сіздер (вы мн. форм.), олар (они)",
         '{"example1": "Мен студентпін - I am a student", "example2": "Біз оқимыз - We study"}', "beginner", 3),
    ]
    
    for grammar in grammar_data:
        cursor.execute('''
        INSERT OR IGNORE INTO grammar_rules (category, title_en, title_kk, title_ru, explanation_en, explanation_kk, explanation_ru, examples, difficulty, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', grammar)
    
    # Add trophies
    trophies_data = [
        ("First Win", "Бірінші жеңіс", "Первая победа", "Complete your first game", "Бірінші ойынды аяқтау", "Завершите первую игру", "🏆", "games_won", 1),
        ("100 Words", "100 сөз", "100 слов", "Learn 100 words", "100 сөз үйрену", "Выучите 100 слов", "⭐", "words_learned", 100),
        ("Perfect Score", "Тамаша ұпай", "Отличный результат", "Get 100% on a test", "Тестте 100% алу", "Получите 100% на тесте", "🎯", "perfect_tests", 1),
        ("7 Day Streak", "7 күндік серия", "7-дневная серия", "Study for 7 days in a row", "7 күн қатарынан оқу", "Занимайтесь 7 дней подряд", "🔥", "streak_days", 7),
        ("Course Master", "Курс шебері", "Мастер курса", "Complete 5 courses", "5 курсты аяқтау", "Завершите 5 курсов", "💎", "courses_completed", 5),
        ("Graduate", "Түлек", "Выпускник", "Complete 10 courses", "10 курсты аяқтау", "Завершите 10 курсов", "🎓", "courses_completed", 10),
        ("Champion", "Чемпион", "Чемпион", "Win 50 games", "50 ойында жеңу", "Выиграйте 50 игр", "👑", "games_won", 50),
        ("Legend", "Аңыз", "Легенда", "Learn 1000 words", "1000 сөз үйрену", "Выучите 1000 слов", "🌟", "words_learned", 1000),
    ]
    
    for trophy in trophies_data:
        cursor.execute('''
        INSERT OR IGNORE INTO trophies (name_en, name_kk, name_ru, description_en, description_kk, description_ru, icon, requirement_type, requirement_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', trophy)
    
    # Add sample test questions for Course 1
    test_questions = [
        (1, "How many letters are in the Kazakh alphabet?", "Қазақ әліпбиінде неше әріп бар?", "Сколько букв в казахском алфавите?",
         "multiple_choice", "42", '["40", "42", "44", "38"]', 1),
        (2, "Translate 'Hello' to Kazakh", "Translate 'Hello' to Kazakh", "Переведите 'Hello' на казахский",
         "translation", "Сәлем", '[]', 1),
        (3, "How many vowels are in Kazakh?", "Қазақ тілінде неше дауысты дыбыс бар?", "Сколько гласных в казахском языке?",
         "multiple_choice", "9", '["7", "8", "9", "10"]', 1),
    ]
    
    for question in test_questions:
        cursor.execute('''
        INSERT OR IGNORE INTO course_tests (course_id, question_text_en, question_text_kk, question_text_ru, question_type, correct_answer, options, points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', question)
    
    conn.commit()
    print("✅ Sample data populated successfully!")

if __name__ == "__main__":
    print("Creating Kazakh Learning Platform Database...")
    conn = create_database()
    populate_sample_data(conn)
    conn.close()
    print("✅ Database setup complete!")
    print("\nDefault login credentials:")
    print("  Username: Student123")
    print("  Password: password123")
