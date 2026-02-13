-- ============================================================
-- setup.sql — Run this once to create all tables and seed data
-- Usage: mysql -u root -p kazakh_learning < setup.sql
-- Or paste into phpMyAdmin's SQL tab
-- ============================================================

-- Create database (skip if it already exists)
CREATE DATABASE IF NOT EXISTS kazakh_learning
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE kazakh_learning;

-- -------------------------------------------------------
-- USERS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    username                VARCHAR(100) UNIQUE NOT NULL,
    email                   VARCHAR(255) UNIQUE NOT NULL,
    password_hash           VARCHAR(64) NOT NULL,             -- SHA-256 hex = 64 chars
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login              DATETIME DEFAULT NULL,
    streak_days             INT DEFAULT 0,
    total_words_learned     INT DEFAULT 0,
    total_courses_completed INT DEFAULT 0,
    total_trophies          INT DEFAULT 0,
    current_theme           VARCHAR(50) DEFAULT 'purple',
    last_activity_date      DATE DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- COURSES
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title_en        VARCHAR(255) NOT NULL,
    title_kk        VARCHAR(255) NOT NULL,
    title_ru        VARCHAR(255) NOT NULL,
    description_en  TEXT,
    description_kk  TEXT,
    description_ru  TEXT,
    level           ENUM('beginner','intermediate','advanced') NOT NULL,
    total_lessons   INT DEFAULT 0,
    order_index     INT DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- LESSONS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS lessons (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    title_en     VARCHAR(255) NOT NULL,
    title_kk     VARCHAR(255) NOT NULL,
    title_ru     VARCHAR(255) NOT NULL,
    content_en   TEXT,
    content_kk   TEXT,
    content_ru   TEXT,
    lesson_order INT DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- WORDS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS words (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    lesson_id           INT NOT NULL,
    kazakh              VARCHAR(255) NOT NULL,
    english             VARCHAR(255) NOT NULL,
    russian             VARCHAR(255) NOT NULL,
    pronunciation       VARCHAR(255),
    example_sentence_kk TEXT,
    example_sentence_en TEXT,
    example_sentence_ru TEXT,
    word_type           VARCHAR(100),
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- GRAMMAR RULES
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS grammar_rules (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    category        VARCHAR(100) NOT NULL,
    title_en        VARCHAR(255) NOT NULL,
    title_kk        VARCHAR(255) NOT NULL,
    title_ru        VARCHAR(255) NOT NULL,
    explanation_en  TEXT,
    explanation_kk  TEXT,
    explanation_ru  TEXT,
    examples        JSON,
    difficulty      ENUM('beginner','intermediate','advanced'),
    order_index     INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- USER PROGRESS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_progress (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    course_id    INT NOT NULL,
    lesson_id    INT,
    completed    TINYINT(1) DEFAULT 0,
    score        INT DEFAULT NULL,
    completed_at DATETIME DEFAULT NULL,
    UNIQUE KEY uq_user_lesson (user_id, lesson_id),
    FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- USER LEARNED WORDS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_learned_words (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    word_id     INT NOT NULL,
    learned_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    proficiency INT DEFAULT 1,
    UNIQUE KEY uq_user_word (user_id, word_id),
    FOREIGN KEY (user_id) REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES words(id)  ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- COURSE TESTS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS course_tests (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    course_id        INT NOT NULL,
    question_text_en TEXT NOT NULL,
    question_text_kk TEXT NOT NULL,
    question_text_ru TEXT NOT NULL,
    question_type    ENUM('multiple_choice','translation','fill_blank'),
    correct_answer   TEXT NOT NULL,
    options          JSON,
    points           INT DEFAULT 1,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- USER TEST RESULTS
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_test_results (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    course_id    INT NOT NULL,
    score        INT NOT NULL,
    total_points INT NOT NULL,
    percentage   DECIMAL(5,2),
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- TROPHIES
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS trophies (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    name_en           VARCHAR(100) NOT NULL,
    name_kk           VARCHAR(100) NOT NULL,
    name_ru           VARCHAR(100) NOT NULL,
    description_en    TEXT,
    description_kk    TEXT,
    description_ru    TEXT,
    icon              VARCHAR(10),
    requirement_type  VARCHAR(100),
    requirement_value INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------
-- USER TROPHIES
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_trophies (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    trophy_id  INT NOT NULL,
    earned_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_trophy (user_id, trophy_id),
    FOREIGN KEY (user_id)   REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (trophy_id) REFERENCES trophies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ==============================================================
-- SEED DATA
-- ==============================================================

-- Default user  (password: password123)
INSERT IGNORE INTO users (username, email, password_hash, streak_days, total_words_learned, total_courses_completed, total_trophies)
VALUES ('Student123', 'student@kazakh.learn',
        SHA2('password123', 256),
        23, 347, 12, 8);

-- Courses
INSERT IGNORE INTO courses (id, title_en, title_kk, title_ru, description_en, description_kk, description_ru, level, total_lessons, order_index) VALUES
(1, 'Kazakh Alphabet & Pronunciation', 'Қазақ әліпбиі және айтылымы', 'Казахский алфавит и произношение',
 'Learn the basics of Kazakh alphabet and correct pronunciation',
 'Қазақ әліпбиінің негіздері мен дұрыс айтылымын үйреніңіз',
 'Изучите основы казахского алфавита и правильное произношение',
 'beginner', 10, 1),
(2, 'Basic Greetings & Phrases', 'Негізгі сәлемдесулер мен сөз тіркестері', 'Основные приветствия и фразы',
 'Common phrases for everyday conversations',
 'Күнделікті әңгімелер үшін жалпы сөз тіркестері',
 'Общие фразы для повседневных разговоров',
 'beginner', 15, 2),
(3, 'Numbers & Counting', 'Сандар мен санау', 'Числа и счет',
 'Master numbers from 1 to 1000 and beyond',
 '1-ден 1000-ға дейінгі және одан әрі сандарды меңгеріңіз',
 'Освойте числа от 1 до 1000 и далее',
 'beginner', 12, 3),
(4, 'Grammar Fundamentals', 'Грамматика негіздері', 'Основы грамматики',
 'Understand the structure of Kazakh sentences',
 'Қазақ сөйлемдерінің құрылымын түсіну',
 'Понимание структуры казахских предложений',
 'intermediate', 20, 4),
(5, 'Conversational Kazakh', 'Сөйлесу қазақшасы', 'Разговорный казахский',
 'Practice real-life conversations and dialogues',
 'Нақты өмірдегі әңгімелер мен диалогтарды жаттықтыру',
 'Практикуйте реальные разговоры и диалоги',
 'intermediate', 18, 5),
(6, 'Advanced Literature', 'Жоғары деңгейлі әдебиет', 'Продвинутая литература',
 'Explore Kazakh poetry and prose',
 'Қазақ поэзиясы мен прозасын зерттеңіз',
 'Исследуйте казахскую поэзию и прозу',
 'advanced', 25, 6);

-- Lessons for Course 1
INSERT IGNORE INTO lessons (course_id, title_en, title_kk, title_ru, content_en, content_kk, content_ru, lesson_order) VALUES
(1, 'Introduction to Kazakh Alphabet', 'Қазақ әліпбиіне кіріспе', 'Введение в казахский алфавит',
 'The Kazakh alphabet contains 42 letters.', 'Қазақ әліпбиінде 42 әріп бар.', 'Казахский алфавит содержит 42 буквы.', 1),
(1, 'Vowels in Kazakh', 'Қазақ дауысты дыбыстары', 'Гласные в казахском',
 'Kazakh has 9 vowels.', 'Қазақ тілінде 9 дауысты дыбыс бар.', 'В казахском языке 9 гласных.', 2),
(1, 'Consonants Part 1', 'Дауыссыз дыбыстар 1-бөлім', 'Согласные часть 1',
 'Let''s learn the first group of consonants.', 'Дауыссыз дыбыстардың бірінші тобын үйренейік.', 'Давайте изучим первую группу согласных.', 3);

-- Words for Lesson 1
INSERT IGNORE INTO words (lesson_id, kazakh, english, russian, pronunciation, example_sentence_kk, example_sentence_en, example_sentence_ru, word_type) VALUES
(1, 'Сәлем',         'Hello',          'Привет',        'salem',          'Сәлем! Қалың қалай?',                             'Hello! How are you?',          'Привет! Как дела?',              'greeting'),
(1, 'Сәлеметсіз бе', 'Hello (formal)', 'Здравствуйте',  'salemetsize be', 'Сәлеметсіз бе, мұғалім!',                         'Hello, teacher!',              'Здравствуйте, учитель!',         'greeting'),
(1, 'Рахмет',        'Thank you',      'Спасибо',       'rahmet',         'Рахмет сізге!',                                    'Thank you!',                   'Спасибо вам!',                   'expression'),
(1, 'Кешіріңіз',     'Excuse me',      'Извините',      'keshiriniz',     'Кешіріңіз, сіз маған көмектесе аласыз ба?',        'Excuse me, can you help me?',  'Извините, вы можете мне помочь?','expression'),
(1, 'Иә',            'Yes',            'Да',            'ia',             'Иә, мен келемін',                                  'Yes, I am coming',             'Да, я иду',                      'answer'),
(1, 'Жоқ',           'No',             'Нет',           'joq',            'Жоқ, бұл менің кітабым емес',                      'No, this is not my book',      'Нет, это не моя книга',          'answer');

-- Grammar rules
INSERT IGNORE INTO grammar_rules (category, title_en, title_kk, title_ru, explanation_en, explanation_kk, explanation_ru, examples, difficulty, order_index) VALUES
('Vowel Harmony', 'Vowel Harmony Rules', 'Дауысты дыбыстардың үндесуі', 'Правила гармонии гласных',
 'Kazakh uses vowel harmony — vowels in a word must belong to the same group (front or back).',
 'Қазақ тілінде дауысты үндесім қолданылады.',
 'В казахском используется гармония гласных.',
 '{"example1": "кітап (kitap) - book", "example2": "үстел (ustel) - table"}', 'beginner', 1),
('Plural Forms', 'Forming Plurals', 'Көпше түрін жасау', 'Образование множественного числа',
 'Add -лар/-лер or -дар/-дер or -тар/-тер depending on the last sound.',
 'Сөздің соңғы дыбысына қарай жалғаңыз.',
 'Добавьте суффикс в зависимости от последнего звука.',
 '{"example1": "кітап + тар = кітаптар (books)", "example2": "бала + лар = балалар (children)"}', 'beginner', 2),
('Personal Pronouns', 'Personal Pronouns', 'Жіктеу есімдіктері', 'Личные местоимения',
 'мен (I), сен (you), сіз (you formal), ол (he/she), біз (we), олар (they)',
 'мен, сен, сіз, ол, біз, олар',
 'мен (я), сен (ты), сіз (вы), ол (он/она), біз (мы), олар (они)',
 '{"example1": "Мен студентпін - I am a student", "example2": "Біз оқимыз - We study"}', 'beginner', 3);

-- Trophies
INSERT IGNORE INTO trophies (name_en, name_kk, name_ru, description_en, description_kk, description_ru, icon, requirement_type, requirement_value) VALUES
('First Win',     'Бірінші жеңіс', 'Первая победа',     'Complete your first game',   'Бірінші ойынды аяқтау',   'Завершите первую игру',        '🏆', 'games_won',       1),
('100 Words',     '100 сөз',       '100 слов',           'Learn 100 words',             '100 сөз үйрену',          'Выучите 100 слов',             '⭐', 'words_learned',   100),
('Perfect Score', 'Тамаша ұпай',   'Отличный результат', 'Get 100% on a test',          'Тестте 100% алу',         'Получите 100% на тесте',       '🎯', 'perfect_tests',   1),
('7 Day Streak',  '7 күндік серия','7-дневная серия',    'Study for 7 days in a row',   '7 күн қатарынан оқу',     'Занимайтесь 7 дней подряд',    '🔥', 'streak_days',     7),
('Course Master', 'Курс шебері',   'Мастер курса',       'Complete 5 courses',          '5 курсты аяқтау',         'Завершите 5 курсов',           '💎', 'courses_completed',5),
('Graduate',      'Түлек',         'Выпускник',          'Complete 10 courses',         '10 курсты аяқтау',        'Завершите 10 курсов',          '🎓', 'courses_completed',10),
('Champion',      'Чемпион',       'Чемпион',            'Win 50 games',                '50 ойында жеңу',          'Выиграйте 50 игр',             '👑', 'games_won',       50),
('Legend',        'Аңыз',          'Легенда',            'Learn 1000 words',            '1000 сөз үйрену',         'Выучите 1000 слов',            '🌟', 'words_learned',   1000);

-- Test questions for Course 1
INSERT IGNORE INTO course_tests (course_id, question_text_en, question_text_kk, question_text_ru, question_type, correct_answer, options, points) VALUES
(1, 'How many letters are in the Kazakh alphabet?', 'Қазақ әліпбиінде неше әріп бар?', 'Сколько букв в казахском алфавите?',
 'multiple_choice', '42', '["40","42","44","38"]', 1),
(1, 'Translate Hello to Kazakh', 'Hello сөзін қазақшаға аударыңыз', 'Переведите Hello на казахский',
 'translation', 'Сәлем', '[]', 1),
(1, 'How many vowels are in Kazakh?', 'Қазақ тілінде неше дауысты дыбыс бар?', 'Сколько гласных в казахском языке?',
 'multiple_choice', '9', '["7","8","9","10"]', 1);
