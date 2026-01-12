from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
from db import supabase
import functools
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

from datetime import datetime, timedelta

def to_ist(value):
    if not value:
        return ''
    try:
        value = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(value)
        ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime('%Y-%m-%d %I:%M %p')
    except Exception:
        return value

app.jinja_env.filters['to_ist'] = to_ist

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and not session.get('is_admin'):
            flash('Please login first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    elif session.get('user_id'):
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            session['is_admin'] = True
            session['username'] = 'Admin'
            flash('Logged in as Admin.', 'success')
            return redirect(url_for('admin_dashboard'))
        elif username == os.getenv('ADMIN_USERNAME'):
            flash('Invalid admin credentials.', 'error')
            return redirect(url_for('login'))
        
        try:
            res = supabase.table('users').select('*').eq('username', username).execute()
            user = res.data[0] if res.data else None
            
            if user:
                if user.get('password') and check_password_hash(user['password'], password):
                     session['user_id'] = user['id']
                     session['username'] = user['username']
                     flash('Welcome back!', 'success')
                     return redirect(url_for('user_dashboard'))
                elif not user.get('password'):
                     hashed_pw = generate_password_hash(password)
                     supabase.table('users').update({'password': hashed_pw}).eq('id', user['id']).execute()
                     session['user_id'] = user['id']
                     session['username'] = user['username']
                     flash('Password set. Logged in.', 'success')
                     return redirect(url_for('user_dashboard'))
                else:
                    flash('Invalid password.', 'error')
            else:
                hashed_pw = generate_password_hash(password)
                res = supabase.table('users').insert({'username': username, 'password': hashed_pw}).execute()
                new_user = res.data[0]
                session['user_id'] = new_user['id']
                session['username'] = new_user['username']
                flash('Account created and logged in.', 'success')
                return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f"Error logging in: {str(e)}", 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    quizzes_res = supabase.table('quizzes').select('*').execute()
    quizzes = quizzes_res.data

    for quiz in quizzes:
        q_res = supabase.table('questions').select('*, options(*)').eq('quiz_id', quiz['id']).execute()
        quiz['questions'] = q_res.data
        
        r_res = supabase.table('results').select('score, total_questions').eq('quiz_id', quiz['id']).execute()
        results = r_res.data
        if results:
            total_percent = sum([(r['score'] / r['total_questions']) * 100 for r in results if r['total_questions'] > 0])
            quiz['avg_score'] = total_percent / len(results)
        else:
            quiz['avg_score'] = None

    return render_template('admin_dashboard.html', quizzes=quizzes)

@app.route('/admin/quiz/<quiz_id>')
@admin_required
def quiz_details(quiz_id):
    q_res = supabase.table('quizzes').select('*').eq('id', quiz_id).execute()
    if not q_res.data:
        flash('Quiz not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    quiz = q_res.data[0]
    
    qs_res = supabase.table('questions').select('*, options(*)').eq('quiz_id', quiz_id).order('created_at').execute()
    questions = qs_res.data
    
    r_res = supabase.table('results').select('*, users(username)').eq('quiz_id', quiz_id).order('completed_at', desc=True).execute()
    results = r_res.data
    
    return render_template('quiz_details.html', quiz=quiz, questions=questions, results=results)

@app.route('/admin/toggle_score/<quiz_id>', methods=['POST'])
@admin_required
def toggle_score(quiz_id):
    if request.is_json:
        data = request.get_json()
        show_score = data.get('show_score', False)
    else:
        show_score = request.form.get('show_score') == 'on'

    try:
        supabase.table('quizzes').update({'show_score': show_score}).eq('id', quiz_id).execute()
        if request.is_json:
            return {'success': True}
        flash('Score visibility updated.', 'success')
    except Exception as e:
        if request.is_json:
            return {'success': False, 'error': str(e)}, 500
        flash(f'Error updating settings: {e}', 'error')
    return redirect(url_for('quiz_details', quiz_id=quiz_id))

@app.route('/admin/toggle_reattempts/<quiz_id>', methods=['POST'])
@admin_required
def toggle_reattempts(quiz_id):
    if request.is_json:
        data = request.get_json()
        allow = data.get('allow_reattempts', False)
    else:
        allow = request.form.get('allow_reattempts') == 'on'

    try:
        supabase.table('quizzes').update({'allow_reattempts': allow}).eq('id', quiz_id).execute()
        if request.is_json:
            return {'success': True}
        flash('Reattempt settings updated.', 'success')
    except Exception as e:
        if request.is_json:
            return {'success': False, 'error': str(e)}, 500
        flash(f'Error updating settings: {e}', 'error')
    return redirect(url_for('quiz_details', quiz_id=quiz_id))

@app.route('/admin/delete_question/<question_id>', methods=['POST'])
@admin_required
def delete_question(question_id):
    quiz_id = request.form.get('quiz_id')
    
    if request.is_json:
        pass

    try:
        supabase.table('questions').delete().eq('id', question_id).execute()
        if request.is_json:
            return {'success': True}
        flash('Question deleted.', 'success')
    except Exception as e:
        if request.is_json:
            return {'success': False, 'error': str(e)}, 500
        flash(f'Error deleting question: {e}', 'error')
        
    return redirect(url_for('quiz_details', quiz_id=quiz_id))

@app.route('/admin/create_quiz', methods=['POST'])
@admin_required
def create_quiz():
    title = request.form.get('title')
    description = request.form.get('description')
    
    try:
        hours = int(request.form.get('hours', 0))
        minutes = int(request.form.get('minutes', 10))
        seconds = int(request.form.get('seconds', 0))
        duration = (hours * 3600) + (minutes * 60) + seconds
    except ValueError:
        duration = 600

    try:
        res = supabase.table('quizzes').insert({
            'title': title, 
            'description': description,
            'duration': duration
        }).execute()
        
        if res.data:
            new_quiz_id = res.data[0]['id']
            flash('Quiz created.', 'success')
            return redirect(url_for('quiz_details', quiz_id=new_quiz_id))
        
        flash('Quiz created, but could not redirect.', 'success')
    except Exception as e:
        flash(f'Error creating quiz: {e}', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_quiz/<quiz_id>', methods=['POST'])
@admin_required
def delete_quiz(quiz_id):
    supabase.table('quizzes').delete().eq('id', quiz_id).execute()
    flash('Quiz deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_question/<question_id>', methods=['POST'])
@admin_required
def update_question(question_id):
    q_text = request.form.get('question_text')
    
    image_url = None
    image_file = request.files.get('image')
    
    if image_file and image_file.filename:
        try:
            import time
            from werkzeug.utils import secure_filename
            filename = secure_filename(image_file.filename)
            file_path = f"updates/{int(time.time())}_{filename}"
            file_content = image_file.read()
            
            supabase.storage.from_('quiz-images').upload(file_path, file_content, {"content-type": image_file.content_type})
            image_url = supabase.storage.from_('quiz-images').get_public_url(file_path)
        except Exception as e:
            print(f"Upload Error: {e}")

    try:
        update_data = {'text': q_text}
        if image_url:
            update_data['image_url'] = image_url
            
        supabase.table('questions').update(update_data).eq('id', question_id).execute()
        
        current_opts_res = supabase.table('options').select('id').eq('question_id', question_id).order('id').execute()
        current_opts = current_opts_res.data
        
        for i in range(1, 5):
            opt_text = request.form.get(f'option_{i}')
            is_correct = request.form.get(f'is_correct_{i}') == 'on'
            
            if i <= len(current_opts):
                opt_id = current_opts[i-1]['id']
                supabase.table('options').update({'text': opt_text, 'is_correct': is_correct}).eq('id', opt_id).execute()
            else:
                supabase.table('options').insert({'question_id': question_id, 'text': opt_text, 'is_correct': is_correct}).execute()

        if request.is_json or request.accept_mimetypes.accept_json:
             updated_q_res = supabase.table('questions').select('*, options(*)').eq('id', question_id).execute()
             return {'success': True, 'question': updated_q_res.data[0]}

        flash('Question updated.', 'success')
    except Exception as e:
        if request.is_json or request.accept_mimetypes.accept_json:
            return {'success': False, 'error': str(e)}, 500
        flash(f'Error updating question: {e}', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_question/<quiz_id>', methods=['POST'])
@admin_required
def add_question(quiz_id):
    if request.is_json:
        data = request.get_json()
        q_text = data.get('question_text')
        options_data = [
            {'text': data.get('option_1'), 'is_correct': data.get('is_correct_1')},
            {'text': data.get('option_2'), 'is_correct': data.get('is_correct_2')},
            {'text': data.get('option_3'), 'is_correct': data.get('is_correct_3')},
            {'text': data.get('option_4'), 'is_correct': data.get('is_correct_4')},
        ]
        image_url = None 
    else:
        q_text = request.form.get('question_text')
        options_data = []
        for i in range(1, 5):
            opt_text = request.form.get(f'option_{i}')
            is_correct = request.form.get(f'is_correct_{i}') == 'on'
            options_data.append({'text': opt_text, 'is_correct': is_correct})
            
        image_file = request.files.get('image')
        image_url = None
        if image_file and image_file.filename:
            try:
                import time
                from werkzeug.utils import secure_filename
                filename = secure_filename(image_file.filename)
                file_path = f"{quiz_id}/{int(time.time())}_{filename}"
                file_content = image_file.read()
                
                supabase.storage.from_('quiz-images').upload(file_path, file_content, {"content-type": image_file.content_type})
                
                image_url = supabase.storage.from_('quiz-images').get_public_url(file_path)
            except Exception as e:
                print(f"Upload Error: {e}")
    
    try:
        q_res = supabase.table('questions').insert({
            'quiz_id': quiz_id, 
            'text': q_text,
            'image_url': image_url
        }).execute()
        question_id = q_res.data[0]['id']
        
        opts_to_insert = [{'question_id': question_id, 'text': o['text'], 'is_correct': o['is_correct']} for o in options_data]
        opts_res = supabase.table('options').insert(opts_to_insert).execute()
        
        if request.is_json or request.accept_mimetypes.accept_json:
            new_q = q_res.data[0]
            new_q['options'] = opts_res.data
            return {'success': True, 'question': new_q}

        flash('Question added.', 'success')
    except Exception as e:
        if request.is_json or request.accept_mimetypes.accept_json:
            return {'success': False, 'error': str(e)}, 500
        flash(f'Error adding question: {e}', 'error')
        
    return redirect(url_for('quiz_details', quiz_id=quiz_id))

@app.route('/admin/update_quiz_settings/<quiz_id>', methods=['POST'])
@admin_required
def update_quiz_settings(quiz_id):
    data = request.get_json()
    try:
        hours = int(data.get('hours', 0))
        minutes = int(data.get('minutes', 0))
        seconds = int(data.get('seconds', 0))
        duration = (hours * 3600) + (minutes * 60) + seconds
        
        supabase.table('quizzes').update({'duration': duration}).eq('id', quiz_id).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/admin/result/<result_id>')
@admin_required
def admin_result_details(result_id):
    res = supabase.table('results').select('*, users(username), quizzes(title)').eq('id', result_id).execute()
    if not res.data:
        flash('Result not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    result = res.data[0]
    
    ans_res = supabase.table('user_answers').select('*, questions(id, text, image_url, options(id, text, is_correct))').eq('result_id', result_id).execute()
    user_answers = ans_res.data
    
    return render_template('result_details.html', result=result, answers=user_answers)

@app.route('/dashboard')
@login_required
def user_dashboard():
    res = supabase.table('quizzes').select('*').eq('is_visible', True).execute()
    return render_template('user_dashboard.html', quizzes=res.data)

@app.route('/quiz/<quiz_id>')
@login_required
def take_quiz(quiz_id):
    q_res = supabase.table('quizzes').select('*').eq('id', quiz_id).execute()
    if not q_res.data:
        flash('Quiz not found.', 'error')
        return redirect(url_for('user_dashboard'))
    
    quiz = q_res.data[0]
    
    if not quiz.get('duration'):
        quiz['duration'] = 600
    
    qs_res = supabase.table('questions').select('*, options(*)').eq('quiz_id', quiz_id).execute()
    quiz['questions'] = qs_res.data
    
    allow_reattempts = quiz.get('allow_reattempts', False)
    
    if not allow_reattempts:
        user_id = session.get('user_id')
        res_check = supabase.table('results').select('id').eq('quiz_id', quiz_id).eq('user_id', user_id).execute()
        if res_check.data:
            flash('You have already attempted this quiz. Reattempts are not allowed.', 'error')
            return redirect(url_for('user_dashboard'))

    return render_template('quiz.html', quiz=quiz)

@app.route('/quiz/<quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    user_id = session.get('user_id')
    
    q_res = supabase.table('quizzes').select('allow_reattempts').eq('id', quiz_id).execute()
    if q_res.data and not q_res.data[0].get('allow_reattempts'):
        res_check = supabase.table('results').select('id').eq('quiz_id', quiz_id).eq('user_id', user_id).execute()
        if res_check.data:
            flash('Reattempts not allowed.', 'error')
            return redirect(url_for('user_dashboard'))

    qs_res = supabase.table('questions').select('id, options(id, is_correct)').eq('quiz_id', quiz_id).execute()
    questions = qs_res.data
    
    score = 0
    total_questions = len(questions)
    user_answers_to_insert = []
    
    for q in questions:
        selected_opt_id = request.form.get(f'q-{q["id"]}')
        
        is_correct = False
        if selected_opt_id:
            for opt in q['options']:
                if str(opt['id']) == str(selected_opt_id):
                    if opt['is_correct']:
                        score += 1
                        is_correct = True
                    break
        
            user_answers_to_insert.append({
                'question_id': q['id'],
                'selected_option_id': selected_opt_id,
                'is_correct': is_correct
            })
        else:
             user_answers_to_insert.append({
                'question_id': q['id'],
                'selected_option_id': None, 
                'is_correct': False
            })

    try:
        res = supabase.table('results').insert({
            'user_id': user_id,
            'quiz_id': quiz_id,
            'score': score,
            'total_questions': total_questions
        }).execute()
        
        result_id = res.data[0]['id']
        
        if user_answers_to_insert:
            for ans in user_answers_to_insert:
                ans['result_id'] = result_id
            
            supabase.table('user_answers').insert(user_answers_to_insert).execute()
        
        return render_template('result.html', score=score, total=total_questions, quiz_id=quiz_id)
        
    except Exception as e:
        flash(f'Error submitting quiz: {e}', 'error')
        return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
