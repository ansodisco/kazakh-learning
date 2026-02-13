from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__, static_folder='.')
app.secret_key = 'your-secret-key-change-in-production'
CORS(app, supports_credentials=True)

# ============= STATIC FILE SERVING =============

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images) from root directory"""
    if os.path.exists(path) and not path.startswith('api'):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

DATABASE = 'kazakh_learning.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============= AUTH ENDPOINTS =============

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute('''
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute('''
    SELECT id, username, email FROM users 
    WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    
    if user:
        # Update last login
        cursor.execute('''
        UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now(), user['id']))
        conn.commit()
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        conn.close()
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    else:
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# ============= USER ENDPOINTS =============

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get current user profile"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, username, email, streak_days, total_words_learned, 
           total_courses_completed, total_trophies, current_theme, created_at
    FROM users WHERE id = ?
    ''', (session['user_id'],))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user)), 200
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get user statistics and progress"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute('''
    SELECT streak_days, total_words_learned, total_courses_completed, total_trophies
    FROM users WHERE id = ?
    ''', (session['user_id'],))
    
    stats = dict(cursor.fetchone())
    
    # Calculate overall progress
    cursor.execute('SELECT COUNT(*) as total FROM courses')
    total_courses = cursor.fetchone()['total']
    
    if total_courses > 0:
        progress_percent = (stats['total_courses_completed'] / total_courses) * 100
    else:
        progress_percent = 0
    
    stats['overall_progress'] = round(progress_percent)
    
    # Get earned trophies
    cursor.execute('''
    SELECT t.id, t.name_en, t.name_kk, t.name_ru, t.icon, ut.earned_at
    FROM trophies t
    JOIN user_trophies ut ON t.id = ut.trophy_id
    WHERE ut.user_id = ?
    ORDER BY ut.earned_at DESC
    ''', (session['user_id'],))
    
    stats['earned_trophies'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(stats), 200

@app.route('/api/user/update', methods=['PUT'])
def update_user():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    if 'username' in data:
        cursor.execute('UPDATE users SET username = ? WHERE id = ?', 
                      (data['username'], session['user_id']))
    if 'email' in data:
        cursor.execute('UPDATE users SET email = ? WHERE id = ?', 
                      (data['email'], session['user_id']))
    if 'current_theme' in data:
        cursor.execute('UPDATE users SET current_theme = ? WHERE id = ?', 
                      (data['current_theme'], session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

# ============= COURSES ENDPOINTS =============

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM courses ORDER BY order_index
    ''')
    
    courses = [dict(row) for row in cursor.fetchall()]
    
    # If user is logged in, get their progress
    if 'user_id' in session:
        for course in courses:
            cursor.execute('''
            SELECT COUNT(*) as completed FROM user_progress
            WHERE user_id = ? AND course_id = ? AND completed = 1
            ''', (session['user_id'], course['id']))
            
            completed = cursor.fetchone()['completed']
            total_lessons = course['total_lessons']
            
            if total_lessons > 0:
                course['progress'] = (completed / total_lessons) * 100
            else:
                course['progress'] = 0
            
            course['completed_lessons'] = completed
    
    conn.close()
    return jsonify(courses), 200

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get specific course details"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    
    if not course:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404
    
    course = dict(course)
    
    # Get lessons
    cursor.execute('''
    SELECT * FROM lessons WHERE course_id = ? ORDER BY lesson_order
    ''', (course_id,))
    
    course['lessons'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(course), 200

@app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    """Get specific lesson with words"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,))
    lesson = cursor.fetchone()
    
    if not lesson:
        conn.close()
        return jsonify({'error': 'Lesson not found'}), 404
    
    lesson = dict(lesson)
    
    # Get words for this lesson
    cursor.execute('''
    SELECT * FROM words WHERE lesson_id = ?
    ''', (lesson_id,))
    
    lesson['words'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(lesson), 200

@app.route('/api/lessons/<int:lesson_id>/complete', methods=['POST'])
def complete_lesson():
    """Mark lesson as completed"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    lesson_id = request.view_args['lesson_id']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get course_id from lesson
    cursor.execute('SELECT course_id FROM lessons WHERE id = ?', (lesson_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return jsonify({'error': 'Lesson not found'}), 404
    
    course_id = result['course_id']
    
    # Mark as completed
    cursor.execute('''
    INSERT OR REPLACE INTO user_progress (user_id, course_id, lesson_id, completed, completed_at)
    VALUES (?, ?, ?, 1, ?)
    ''', (session['user_id'], course_id, lesson_id, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Lesson completed successfully'}), 200

# ============= WORDS ENDPOINTS =============

@app.route('/api/words/learn', methods=['POST'])
def learn_word():
    """Mark word as learned"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    word_id = data.get('word_id')
    
    if not word_id:
        return jsonify({'error': 'Word ID required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO user_learned_words (user_id, word_id, proficiency)
    VALUES (?, ?, ?)
    ''', (session['user_id'], word_id, 1))
    
    # Update total words learned count
    cursor.execute('''
    UPDATE users SET total_words_learned = (
        SELECT COUNT(*) FROM user_learned_words WHERE user_id = ?
    )
    WHERE id = ?
    ''', (session['user_id'], session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Word learned successfully'}), 200

@app.route('/api/words/learned', methods=['GET'])
def get_learned_words():
    """Get all learned words for current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT w.*, ulw.learned_at, ulw.proficiency
    FROM words w
    JOIN user_learned_words ulw ON w.id = ulw.word_id
    WHERE ulw.user_id = ?
    ORDER BY ulw.learned_at DESC
    ''', (session['user_id'],))
    
    words = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(words), 200

# ============= GRAMMAR ENDPOINTS =============

@app.route('/api/grammar', methods=['GET'])
def get_grammar_rules():
    """Get all grammar rules"""
    difficulty = request.args.get('difficulty')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if difficulty:
        cursor.execute('''
        SELECT * FROM grammar_rules WHERE difficulty = ? ORDER BY order_index
        ''', (difficulty,))
    else:
        cursor.execute('SELECT * FROM grammar_rules ORDER BY order_index')
    
    rules = [dict(row) for row in cursor.fetchall()]
    
    # Parse examples JSON
    for rule in rules:
        if rule['examples']:
            rule['examples'] = json.loads(rule['examples'])
    
    conn.close()
    return jsonify(rules), 200

@app.route('/api/grammar/<int:rule_id>', methods=['GET'])
def get_grammar_rule(rule_id):
    """Get specific grammar rule"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM grammar_rules WHERE id = ?', (rule_id,))
    rule = cursor.fetchone()
    
    if not rule:
        conn.close()
        return jsonify({'error': 'Grammar rule not found'}), 404
    
    rule = dict(rule)
    if rule['examples']:
        rule['examples'] = json.loads(rule['examples'])
    
    conn.close()
    return jsonify(rule), 200

# ============= TEST ENDPOINTS =============

@app.route('/api/courses/<int:course_id>/test', methods=['GET'])
def get_course_test(course_id):
    """Get test questions for a course"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM course_tests WHERE course_id = ?
    ''', (course_id,))
    
    questions = [dict(row) for row in cursor.fetchall()]
    
    # Parse options JSON
    for question in questions:
        if question['options']:
            question['options'] = json.loads(question['options'])
        # Don't send correct answer to client
        question.pop('correct_answer', None)
    
    conn.close()
    return jsonify(questions), 200

@app.route('/api/courses/<int:course_id>/test/submit', methods=['POST'])
def submit_test(course_id):
    """Submit test answers and get results"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    answers = data.get('answers', {})  # {question_id: user_answer}
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all test questions
    cursor.execute('''
    SELECT id, correct_answer, points FROM course_tests WHERE course_id = ?
    ''', (course_id,))
    
    questions = cursor.fetchall()
    
    score = 0
    total_points = 0
    results = []
    
    for question in questions:
        q_id = str(question['id'])
        correct_answer = question['correct_answer']
        points = question['points']
        total_points += points
        
        user_answer = answers.get(q_id, '').strip().lower()
        is_correct = user_answer == correct_answer.strip().lower()
        
        if is_correct:
            score += points
        
        results.append({
            'question_id': question['id'],
            'correct': is_correct,
            'correct_answer': correct_answer
        })
    
    percentage = (score / total_points * 100) if total_points > 0 else 0
    
    # Save test result
    cursor.execute('''
    INSERT INTO user_test_results (user_id, course_id, score, total_points, percentage)
    VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], course_id, score, total_points, percentage))
    
    # If score is 100%, check for trophy
    if percentage == 100:
        cursor.execute('''
        INSERT OR IGNORE INTO user_trophies (user_id, trophy_id)
        SELECT ?, id FROM trophies WHERE requirement_type = 'perfect_tests'
        ''', (session['user_id'],))
    
    # If test passed (>70%), mark course as completed
    if percentage >= 70:
        cursor.execute('''
        UPDATE users SET total_courses_completed = total_courses_completed + 1
        WHERE id = ? AND id NOT IN (
            SELECT user_id FROM user_test_results 
            WHERE course_id = ? AND percentage >= 70 AND user_id = ?
            GROUP BY user_id
            HAVING COUNT(*) > 1
        )
        ''', (session['user_id'], course_id, session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'score': score,
        'total_points': total_points,
        'percentage': round(percentage, 2),
        'passed': percentage >= 70,
        'results': results
    }), 200

# ============= TROPHIES ENDPOINTS =============

@app.route('/api/trophies', methods=['GET'])
def get_trophies():
    """Get all trophies"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM trophies')
    trophies = [dict(row) for row in cursor.fetchall()]
    
    # If user logged in, mark which they've earned
    if 'user_id' in session:
        cursor.execute('''
        SELECT trophy_id FROM user_trophies WHERE user_id = ?
        ''', (session['user_id'],))
        
        earned_ids = [row['trophy_id'] for row in cursor.fetchall()]
        
        for trophy in trophies:
            trophy['earned'] = trophy['id'] in earned_ids
    
    conn.close()
    return jsonify(trophies), 200

# ============= UTILITY ENDPOINTS =============

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session['username']
        }), 200
    else:
        return jsonify({'authenticated': False}), 200

if __name__ == '__main__':
    print("Starting Kazakh Learning Platform API Server...")
    print("Server running on http://localhost:5000")
    app.run(debug=True, port=5000)
