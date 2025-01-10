from flask import Flask, render_template, request, jsonify,url_for
import requests
import time

app = Flask(__name__)

# Function to send a Telegram message
def send_telegram_message(message):
    bot_token = "6982141096:AAFpEspslCkO0KWNbONnmWjUU_87jib__g8"  # Replace with your bot token
    chat_id = 854578633  # Replace with your chat ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
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

    return response.json()['deck_data_id']

# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        topic = request.form['topic']
        num_questions_level = request.form['num_questions']
        question_types = request.form.getlist('question_types')

        try:
            deck_data_id = mcq_generator(topic, num_questions_level, question_types)
            exam_link = url_for('view_exam', deck_data_id=deck_data_id, _external=True)

            # Send Telegram message
            telegram_message = f"""
            📝 New Quiz Created
            - Quiz ID: {deck_data_id}
            - Number of Questions: {num_questions_level}
            - Questions Type: {','.join(question_types)}
            - Link: {exam_link}
            """
            send_telegram_message(telegram_message)

            # Render the index page with the exam link
            return render_template('index.html', exam_ready=True, exam_link=exam_link)
        except Exception as e:
            return render_template('index.html', exam_ready=False, error_message=str(e))

    return render_template('index.html', exam_ready=False, exam_link=None)

# Exam route
@app.route('/exam/<deck_data_id>')
def view_exam(deck_data_id):
    return render_template('exam.html', exam_id=deck_data_id)

# Route to fetch questions dynamically
@app.route('/fetch_questions/<deck_data_id>')
def fetch_questions(deck_data_id):
    try:
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

        response = requests.post(
            f'https://wisdolia-backend-2-ywnn.zeet-wisdolia.zeet.app/cards/get_all_cards_data_for_deck_and_subdecks/{deck_data_id}',
            headers=headers,
            json={'user_id': 'qnpzdCAWX7VOkFp61r9WR365kkd2'},
        )

        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch questions'}), 500

        data = response.json()
        questions = data.get('all_cards_for_deck', [])
        is_complete = len(questions) > 0  # Assume completion if questions are returned

        return jsonify({
            'questions': questions,
            'is_complete': is_complete,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Run the app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
