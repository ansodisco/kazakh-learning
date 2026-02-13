// ============================================================
// app.js — Student frontend logic
// Uses Flask API endpoints
// ============================================================

const API_URL = '/api';         // Flask API base path
let currentLanguage = 'en';
let currentCourseId = null;
let currentLessonId = null;
let testAnswers = {};

// ─────────────────────────────────────────────
// Auth — check session on load
// ─────────────────────────────────────────────
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/check-session`, {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.authenticated) {
            document.getElementById('username-display').textContent = data.username;
            document.getElementById('user-avatar').textContent = data.username.charAt(0).toUpperCase();
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('app').style.display = 'block';
            loadDashboard();
            loadCourses();
            loadGrammar();
            loadMyWords();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

// ─────────────────────────────────────────────
// Login
// ─────────────────────────────────────────────
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });

        let data;
        try {
            data = await response.json();
        } catch (parseErr) {
            // PHP returned non-JSON (e.g. error/warning output)
            const text = await response.clone().text().catch(() => '');
            errorEl.textContent = 'Server returned an invalid response. Check PHP error logs.';
            console.error('Login parse error:', parseErr, 'Response text:', text);
            return;
        }

        if (response.ok && !data.error) {
            document.getElementById('username-display').textContent = data.user.username;
            document.getElementById('user-avatar').textContent = data.user.username.charAt(0).toUpperCase();
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('app').style.display = 'block';
            loadDashboard();
            loadCourses();
            loadGrammar();
            loadMyWords();
        } else {
            errorEl.textContent = data.error || 'Login failed';
        }
    } catch (error) {
        errorEl.textContent = 'Network error — cannot reach the server. Is Apache/XAMPP running?';
        console.error('Login network error:', error);
    }
});

// ─────────────────────────────────────────────
// Register
// ─────────────────────────────────────────────
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const errorEl = document.getElementById('register-error');
    const successEl = document.getElementById('register-success');

    errorEl.textContent = '';
    successEl.style.display = 'none';

    if (!username || !email || !password) {
        errorEl.textContent = 'All fields are required.';
        return;
    }
    if (password.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters.';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, email, password })
        });

        let data;
        try {
            data = await response.json();
        } catch (parseErr) {
            errorEl.textContent = 'Server returned an invalid response. Check PHP error logs.';
            console.error('Register parse error:', parseErr);
            return;
        }

        if (response.ok && !data.error) {
            successEl.textContent = '✅ Account created! Logging you in…';
            successEl.style.display = 'block';
            // Auto-login after registration
            setTimeout(() => {
                document.getElementById('username-display').textContent = username;
                document.getElementById('user-avatar').textContent = username.charAt(0).toUpperCase();
                document.getElementById('login-screen').style.display = 'none';
                document.getElementById('app').style.display = 'block';
                loadDashboard();
                loadCourses();
                loadGrammar();
                loadMyWords();
            }, 1000);
        } else {
            errorEl.textContent = data.error || 'Registration failed';
        }
    } catch (error) {
        errorEl.textContent = 'Network error — cannot reach the server. Is Apache/XAMPP running?';
        console.error('Register network error:', error);
    }
});

// ─────────────────────────────────────────────
// Toggle between Login ↔ Register forms
// ─────────────────────────────────────────────
function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('toggle-to-register').style.display = 'block';
    document.getElementById('toggle-to-login').style.display = 'none';
    document.getElementById('demo-hint').style.display = 'block';
    document.getElementById('login-error').textContent = '';
}

function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('toggle-to-register').style.display = 'none';
    document.getElementById('toggle-to-login').style.display = 'block';
    document.getElementById('demo-hint').style.display = 'none';
    document.getElementById('register-error').textContent = '';
    document.getElementById('register-success').style.display = 'none';
}

// ─────────────────────────────────────────────
// Logout
// ─────────────────────────────────────────────
async function logout() {
    await fetch(`${API_URL}/logout`, {
        method: 'POST',
        credentials: 'include'
    });
    location.reload();
}

// ─────────────────────────────────────────────
// Dashboard
// ─────────────────────────────────────────────
async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/user/stats`, {
            credentials: 'include'
        });
        const stats = await response.json();

        document.getElementById('stat-courses').textContent = stats.total_courses_completed;
        document.getElementById('stat-words').textContent = stats.total_words_learned;
        document.getElementById('stat-trophies').textContent = stats.total_trophies;
        document.getElementById('stat-streak').textContent = stats.streak_days;
        document.getElementById('overall-progress').textContent = stats.overall_progress + '%';

        // Update progress circle
        const circumference = 2 * Math.PI * 110;
        const offset = circumference - (stats.overall_progress / 100) * circumference;
        document.getElementById('progress-ring-fill').style.strokeDashoffset = offset;
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// ─────────────────────────────────────────────
// Courses
// ─────────────────────────────────────────────
async function loadCourses() {
    try {
        const response = await fetch(`${API_URL}/courses`, {
            credentials: 'include'
        });
        const courses = await response.json();

        const container = document.getElementById('courses-list');
        container.innerHTML = courses.map(course => `
            <div class="course-card" onclick="viewCourse(${course.id})">
                <div class="course-title">${course['title_' + currentLanguage]}</div>
                <span class="course-level level-${course.level}">${course.level}</span>
                <div class="course-description">${course['description_' + currentLanguage]}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${course.progress || 0}%"></div>
                </div>
                <div style="font-size: 0.85rem; color: var(--ink-light); margin-top: 5px;">
                    ${course.completed_lessons || 0} / ${course.total_lessons} lessons
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load courses:', error);
    }
}

// ─────────────────────────────────────────────
// View Course Detail
// ─────────────────────────────────────────────
async function viewCourse(courseId) {
    currentCourseId = courseId;
    try {
        const response = await fetch(`${API_URL}/courses/${courseId}`, {
            credentials: 'include'
        });
        const course = await response.json();

        const content = document.getElementById('course-detail-content');
        content.innerHTML = `
            <div class="card">
                <h1 style="font-size: 2rem; font-weight: 900; margin-bottom: 10px;">${course['title_' + currentLanguage]}</h1>
                <span class="course-level level-${course.level}">${course.level}</span>
                <p style="color: var(--ink-medium); margin: 20px 0;">${course['description_' + currentLanguage]}</p>
                
                <h2 style="margin: 30px 0 15px; font-weight: 700;">Lessons</h2>
                <ul class="lesson-list">
                    ${course.lessons.map(lesson => `
                        <li class="lesson-item" onclick="viewLesson(${lesson.id})">
                            <div style="font-weight: 700; margin-bottom: 5px;">${lesson['title_' + currentLanguage]}</div>
                            <div style="font-size: 0.85rem; color: var(--ink-light);">Lesson ${lesson.lesson_order}</div>
                        </li>
                    `).join('')}
                </ul>

                <button class="btn btn-primary" style="margin-top: 30px;" onclick="startTest(${courseId})">
                    Take Course Test
                </button>
            </div>
        `;

        showTab('course-detail');
    } catch (error) {
        console.error('Failed to load course:', error);
    }
}

// ─────────────────────────────────────────────
// View Lesson
// ─────────────────────────────────────────────
async function viewLesson(lessonId) {
    currentLessonId = lessonId;
    try {
        const response = await fetch(`${API_URL}/lessons/${lessonId}`, {
            credentials: 'include'
        });
        const lesson = await response.json();

        const content = document.getElementById('lesson-content');
        content.innerHTML = `
            <div class="card">
                <h1 style="font-size: 2rem; font-weight: 900; margin-bottom: 20px;">${lesson['title_' + currentLanguage]}</h1>
                <div style="color: var(--ink-dark); line-height: 1.8; margin-bottom: 30px;">
                    ${lesson['content_' + currentLanguage] || 'Lesson content...'}
                </div>

                <h2 style="margin-bottom: 20px; font-weight: 700;">Vocabulary</h2>
                <div class="word-grid">
                    ${lesson.words.map(word => `
                        <div class="word-card">
                            <div class="word-kazakh">${word.kazakh}</div>
                            <div class="word-translation">${currentLanguage === 'en' ? word.english : word.russian}</div>
                            <div class="word-pronunciation">[${word.pronunciation}]</div>
                            ${word['example_sentence_' + currentLanguage] ? `
                                <div class="word-example">
                                    ${word['example_sentence_' + currentLanguage]}
                                </div>
                            ` : ''}
                            <button class="btn btn-secondary" style="margin-top: 10px; font-size: 0.85rem; padding: 8px;" 
                                    onclick="learnWord(${word.id})">
                                Mark as Learned
                            </button>
                        </div>
                    `).join('')}
                </div>

                <button class="btn btn-primary" style="margin-top: 30px;" onclick="completeLesson(${lessonId})">
                    Complete Lesson
                </button>
            </div>
        `;

        showTab('lesson-view');
    } catch (error) {
        console.error('Failed to load lesson:', error);
    }
}

// ─────────────────────────────────────────────
// Learn Word
// ─────────────────────────────────────────────
async function learnWord(wordId) {
    try {
        await fetch(`${API_URL}/words/learn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ word_id: wordId })
        });
        alert('Word added to your learned words!');
        loadDashboard();
    } catch (error) {
        console.error('Failed to learn word:', error);
    }
}

// ─────────────────────────────────────────────
// Complete Lesson
// ─────────────────────────────────────────────
async function completeLesson(lessonId) {
    try {
        await fetch(`${API_URL}/lessons/${lessonId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        alert('Lesson completed! Great job!');
        loadDashboard();
        viewCourse(currentCourseId);
    } catch (error) {
        console.error('Failed to complete lesson:', error);
    }
}

// ─────────────────────────────────────────────
// Grammar Rules
// ─────────────────────────────────────────────
async function loadGrammar() {
    try {
        const response = await fetch(`${API_URL}/grammar`, {
            credentials: 'include'
        });
        const rules = await response.json();

        const container = document.getElementById('grammar-list');
        container.innerHTML = rules.map(rule => `
            <div class="grammar-card">
                <div class="grammar-title">${rule['title_' + currentLanguage]}</div>
                <div class="grammar-explanation">${rule['explanation_' + currentLanguage]}</div>
                ${rule.examples ? `
                    <div class="grammar-examples">
                        <strong>Examples:</strong>
                        ${Object.values(rule.examples).map(ex => `
                            <div class="grammar-example-item">${ex}</div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load grammar:', error);
    }
}

// ─────────────────────────────────────────────
// My Words
// ─────────────────────────────────────────────
async function loadMyWords() {
    try {
        const response = await fetch(`${API_URL}/words/learned`, {
            credentials: 'include'
        });
        const words = await response.json();

        const container = document.getElementById('words-list');

        if (words.length === 0) {
            container.innerHTML = '<div class="card"><p>You haven\'t learned any words yet. Start a lesson to learn new words!</p></div>';
            return;
        }

        container.innerHTML = `
            <div class="word-grid">
                ${words.map(word => `
                    <div class="word-card">
                        <div class="word-kazakh">${word.kazakh}</div>
                        <div class="word-translation">${currentLanguage === 'en' ? word.english : word.russian}</div>
                        <div class="word-pronunciation">[${word.pronunciation}]</div>
                        ${word['example_sentence_' + currentLanguage] ? `
                            <div class="word-example">
                                ${word['example_sentence_' + currentLanguage]}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Failed to load words:', error);
    }
}

// ─────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────
async function startTest(courseId) {
    try {
        const response = await fetch(`${API_URL}/courses/${courseId}/test`, {
            credentials: 'include'
        });
        const questions = await response.json();

        testAnswers = {};

        const content = document.getElementById('test-content');
        content.innerHTML = `
            <div class="card">
                <h1 style="font-size: 2rem; font-weight: 900; margin-bottom: 30px;">Course Test</h1>
                ${questions.map((q, index) => `
                    <div class="test-question">
                        <div class="question-text">${index + 1}. ${q['question_text_' + currentLanguage]}</div>
                        ${q.question_type === 'multiple_choice' ? `
                            <div class="question-options">
                                ${q.options.map(option => `
                                    <button class="option-btn" onclick="selectOption(${q.id}, '${option}', event)">
                                        ${option}
                                    </button>
                                `).join('')}
                            </div>
                        ` : `
                            <input type="text" class="form-input" 
                                   onchange="testAnswers[${q.id}] = this.value"
                                   placeholder="Type your answer here">
                        `}
                    </div>
                `).join('')}
                <button class="btn btn-primary" onclick="submitTest(${courseId})">
                    Submit Test
                </button>
            </div>
        `;

        showTab('test-view');
    } catch (error) {
        console.error('Failed to load test:', error);
    }
}

// Select Option
function selectOption(questionId, answer, event) {
    event.target.parentElement.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.classList.add('selected');
    testAnswers[questionId] = answer;
}

// Submit Test
async function submitTest(courseId) {
    try {
        const response = await fetch(`${API_URL}/courses/${courseId}/test/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ answers: testAnswers })
        });
        const result = await response.json();

        const content = document.getElementById('test-content');
        content.innerHTML = `
            <div class="test-result" style="border-color: ${result.passed ? '#6b9e7a' : '#c55a5a'}">
                <div class="result-score">${result.percentage}%</div>
                <div class="result-message">
                    ${result.passed ?
                '🎉 Congratulations! You passed the test!' :
                '📚 Keep studying! You need 70% to pass.'}
                </div>
                <p style="color: var(--ink-medium); margin-bottom: 20px;">
                    Score: ${result.score} / ${result.total_points}
                </p>
                <button class="btn btn-primary" onclick="viewCourse(${courseId})">
                    Back to Course
                </button>
            </div>
        `;

        loadDashboard();
    } catch (error) {
        console.error('Failed to submit test:', error);
    }
}

// ─────────────────────────────────────────────
// Tab switching
// ─────────────────────────────────────────────
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    document.getElementById(tabName).classList.add('active');

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.textContent.toLowerCase() === tabName) {
            item.classList.add('active');
        }
    });
}

function backToCourseDetail() {
    viewCourse(currentCourseId);
}

// ─────────────────────────────────────────────
// Language switching
// ─────────────────────────────────────────────
function switchLanguage(lang) {
    currentLanguage = lang;

    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    loadCourses();
    loadGrammar();
    loadMyWords();
}

// ─────────────────────────────────────────────
// Initialize
// ─────────────────────────────────────────────
checkAuth();
