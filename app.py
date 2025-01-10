from flask import Flask, render_template, request, redirect, url_for
import requests
import time
import sqlite3
import uuid

app = Flask(__name__)

# SQLite database setup
DATABASE = 'mcq_exams.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                num_questions_level TEXT,
                question_types TEXT,
                questions TEXT
            )
        ''')
        conn.commit()

init_db()
def send_telegram_message(message):
    """Send a message to Telegram using the Bot API."""
    bot_token = "6982141096:AAFpEspslCkO0KWNbONnmWjUU_87jib__g8"  # Replace with your bot token
    chat_id = 854578633  # Replace with your chat ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("Telegram message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
# Function to generate MCQs
def mcq_generator(topic, num_questions_level='high', question_types=None):
    if question_types is None:
        question_types = ['Multiple Choice Question', 'Case Scenario Multiple Choice Question']

    headers = {
        'Host': 'wisdolia-backend-2-ywnn.zeet-wisdolia.zeet.app',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Baggage': 'sentry-environment=production,sentry-public_key=d37a47553d2adbda37b7008aeb1a15ad,sentry-trace_id=9e3953c62ed34b3c9f8761cec1356d87',
        'Sentry-Trace': '9e3953c62ed34b3c9f8761cec1356d87-a24f75e20b65b0fd-1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://app.jungleai.com',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://app.jungleai.com/',
        'Priority': 'u=1, i',
    }

    json_data = {
        'page_text': str(topic),
        'page_text_sentences_array': [],
        'page_url': '',
        'page_title': '',
        'content_medium_type': 'PDF',
        'uploaded_file_s3_object_key': '',
        'pdfStartingPage': 1,
        'pdfEndingPage': 1000,
        'user_id': 'qnpzdCAWX7VOkFp61r9WR365kkd2',
        'question_types_user_selected_to_generate': question_types,
        'session_id': 'ca8cc206-0a32-4d3f-b370-531ec8b89d29',
        'platform': 'Web',
        'youtubeTranscriptStartMinute': 0,
        'youtubeTranscriptEndMinute': 0,
        'did_user_input_url_for_pdf': False,
        'level_for_amount_of_cards_to_generate': num_questions_level,
        'selected_images_for_occlusion': [],
        'pdf_file_name': '',
        'video_or_audio_starting_minute': 0,
        'video_or_audio_ending_minute': None,
        'video_or_audio_num_minutes': 0,
    }

    response = requests.post(
        'https://wisdolia-backend-2-ywnn.zeet-wisdolia.zeet.app/run_all_generations_for_file_or_url',
        headers=headers,
        json=json_data,
    )

    if response.status_code != 200:
        raise Exception(f"Failed to start generation process. Status code: {response.status_code}")

    deck_data_id = response.json()['deck_data_id']

    previous_question_length = -1
    current_question_length = 0

    while True:
        response = requests.post(
            f'https://wisdolia-backend-2-ywnn.zeet-wisdolia.zeet.app/cards/get_all_cards_data_for_deck_and_subdecks/{deck_data_id}',
            headers=headers,
            json={'user_id': 'qnpzdCAWX7VOkFp61r9WR365kkd2'},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch questions. Status code: {response.status_code}")

        data = response.json()
        current_question_length = len(data.get('all_cards_for_deck', []))

        if current_question_length > 0 and current_question_length == previous_question_length:
            print(data['all_cards_for_deck'])
            return data['all_cards_for_deck'], deck_data_id
        else:
            previous_question_length = current_question_length
            time.sleep(6)

# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        topic = request.form['topic']
        num_questions_level = request.form['num_questions']  # Updated to use the hidden input
        question_types = request.form.getlist('question_types')

        questions, exam_id = mcq_generator(topic, num_questions_level, question_types)
        telegram_message = f"""
        📝 New Quiz Created
        - Quiz ID: {exam_id}
        - Number of Questions: {num_questions_level}
        - Questions Type: {','.join(question_types)}
        - Link: {request.host_url}quiz/{exam_id}
                """
        send_telegram_message(telegram_message)
        # Save the exam to the database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exams (id, num_questions_level, question_types, questions)
                VALUES (?, ?, ?, ?, ?)
            ''', (exam_id, num_questions_level, ','.join(question_types), str(questions)))
            conn.commit()

        # Generate the exam link
        exam_link = url_for('view_exam', exam_id=exam_id, _external=True)

        # Return the exam link to the index page
        return render_template('index.html', exam_ready=True, exam_link=exam_link)

    return render_template('index.html', exam_ready=False, exam_link=None)

# Exam route
@app.route('/exam/<exam_id>')
def view_exam(exam_id):
    # Fetch the exam from the database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT questions FROM exams WHERE id = ?', (exam_id,))
        result = cursor.fetchone()

    if result:
        questions = eval(result[0])  # Convert string back to list
        return render_template('exam.html', questions=questions, exam_id=exam_id)
    else:
        return "Exam not found.", 404

# Run the app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)