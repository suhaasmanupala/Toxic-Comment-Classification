from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from textblob import TextBlob
from langdetect import detect
import sqlite3
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

# Initialize database
def init_db():
    try:
        with sqlite3.connect('history.db') as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS history
                            (user_id TEXT, comment TEXT, prediction TEXT, confidence REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS feedback
                            (user_id TEXT, comment TEXT, issue TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS badges
                            (user_id TEXT, badge_name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
init_db()

# Dummy training data (replace with real dataset for production)
comments = [
    "This is a nice comment", "You are an idiot", "I hate you", "Great work!",
    "This is obscene and disgusting", "You're a threat", "Insulting comment", "Wonderful job!"
]
labels = [0, 1, 1, 0, 1, 1, 1, 0]  # 0: non-toxic, 1: toxic
multi_labels = [
    [0, 0, 0, 0, 0, 0],  # nice comment
    [1, 0, 0, 0, 1, 0],  # idiot (toxic, insult)
    [1, 0, 0, 0, 0, 1],  # hate (toxic, identity_hate)
    [0, 0, 0, 0, 0, 0],  # great work
    [1, 1, 1, 0, 0, 0],  # obscene (toxic, severe_toxic, obscene)
    [1, 0, 0, 1, 0, 0],  # threat (toxic, threat)
    [1, 0, 0, 0, 1, 1],  # insulting (toxic, insult, identity_hate)
    [0, 0, 0, 0, 0, 0]   # wonderful job
]

# Train binary classifier
try:
    vectorizer = TfidfVectorizer(max_features=5000)
    X = vectorizer.fit_transform(comments)
    binary_classifier = LogisticRegression()
    binary_classifier.fit(X, labels)
    logging.info("Binary classifier trained successfully")
except Exception as e:
    logging.error(f"Failed to train binary classifier: {str(e)}")

# Train multi-label classifiers
multi_classifiers = {}
labels_types = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
try:
    for i, label_type in enumerate(labels_types):
        clf = LogisticRegression()
        clf.fit(X, [row[i] for row in multi_labels])
        multi_classifiers[label_type] = clf
    logging.info("Multi-label classifiers trained successfully")
except Exception as e:
    logging.error(f"Failed to train multi-label classifiers: {str(e)}")

def predict_toxicity(comment, user_id):
    try:
        logging.debug(f"Predicting toxicity for comment: {comment}, user_id: {user_id}")
        # Detect language
        lang = detect(comment) if comment.strip() else "en"
        
        # Sentiment analysis
        sentiment = TextBlob(comment).sentiment.polarity
        
        # Transform comment
        X_test = vectorizer.transform([comment])
        
        # Binary prediction
        prediction = binary_classifier.predict(X_test)[0]
        confidence = binary_classifier.predict_proba(X_test)[0][prediction]
        
        # Multi-label scores
        scores = []
        for label_type in labels_types:
            score = multi_classifiers[label_type].predict_proba(X_test)[0][1]
            scores.append(score)
        
        # Simple explanation (top TF-IDF words)
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = X_test.toarray()[0]
        top_indices = tfidf_scores.argsort()[-5:][::-1]
        explanation = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]
        
        # Save to history
        with sqlite3.connect('history.db') as conn:
            conn.execute('INSERT INTO history (user_id, comment, prediction, confidence) VALUES (?, ?, ?, ?)',
                        (user_id, comment, 'Toxic' if prediction == 1 else 'Non-Toxic', confidence))
        
        # Update badges
        badges = update_badges(user_id, prediction)
        
        result = {
            'prediction': 'Toxic' if prediction == 1 else 'Non-Toxic',
            'confidence': float(confidence),
            'scores': [float(score) for score in scores],
            'sentiment': float(sentiment),
            'language': lang,
            'explanation': explanation if explanation else ['none'],
            'badges': badges
        }
        logging.debug(f"Prediction result: {result}")
        return result
    except Exception as e:
        logging.error(f"Prediction failed: {str(e)}")
        return {'error': f'Prediction failed: {str(e)}'}

def update_badges(user_id, prediction):
    try:
        with sqlite3.connect('history.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM history WHERE user_id = ? AND prediction = ?', (user_id, 'Non-Toxic'))
            non_toxic_count = cursor.fetchone()[0]
            cursor.execute('SELECT badge_name FROM badges WHERE user_id = ?', (user_id,))
            existing_badges = [row[0] for row in cursor.fetchall()]
            
            new_badges = []
            if non_toxic_count >= 5 and 'Clean Commenter' not in existing_badges:
                cursor.execute('INSERT INTO badges (user_id, badge_name) VALUES (?, ?)', (user_id, 'Clean Commenter'))
                new_badges.append('Clean Commenter')
            if non_toxic_count >= 10 and 'Positive Contributor' not in existing_badges:
                cursor.execute('INSERT INTO badges (user_id, badge_name) VALUES (?, ?)', (user_id, 'Positive Contributor'))
                new_badges.append('Positive Contributor')
            
            conn.commit()
            cursor.execute('SELECT badge_name FROM badges WHERE user_id = ?', (user_id,))
            badges = [row[0] for row in cursor.fetchall()]
            logging.debug(f"Updated badges for user {user_id}: {badges}")
            return badges
    except Exception as e:
        logging.error(f"Badge update failed: {str(e)}")
        return []

# API Endpoints
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        logging.debug(f"Received predict request: {data}")
        if not data or 'comment' not in data or 'user_id' not in data:
            logging.warning("Invalid predict request: missing comment or user_id")
            return jsonify({'error': 'Invalid input: comment and user_id required'}), 400
        comment = data['comment']
        user_id = data['user_id']
        result = predict_toxicity(comment, user_id)
        if 'error' in result:
            logging.error(f"Predict endpoint error: {result['error']}")
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        logging.error(f"Predict endpoint server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json()
        logging.debug(f"Received feedback request: {data}")
        if not data or 'user_id' not in data or 'comment' not in data or 'issue' not in data:
            logging.warning("Invalid feedback request: missing user_id, comment, or issue")
            return jsonify({'error': 'Invalid input: user_id, comment, and issue required'}), 400
        user_id = data['user_id']
        comment = data['comment']
        issue = data['issue']
        with sqlite3.connect('history.db') as conn:
            conn.execute('INSERT INTO feedback (user_id, comment, issue) VALUES (?, ?, ?)', (user_id, comment, issue))
        logging.info(f"Feedback submitted successfully for user {user_id}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Feedback endpoint server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/history', methods=['GET'])
def history():
    try:
        user_id = request.args.get('user_id')
        logging.debug(f"Received history request for user_id: {user_id}")
        if not user_id:
            logging.warning("Invalid history request: missing user_id")
            return jsonify({'error': 'user_id parameter required'}), 400
        with sqlite3.connect('history.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT comment, prediction, confidence FROM history WHERE user_id = ?', (user_id,))
            history = [{'comment': row[0], 'prediction': row[1], 'confidence': float(row[2])} for row in cursor.fetchall()]
            cursor.execute('SELECT badge_name FROM badges WHERE user_id = ?', (user_id,))
            badges = [row[0] for row in cursor.fetchall()]
        logging.info(f"History retrieved successfully for user {user_id}")
        return jsonify({'history': history, 'badges': badges})
    except Exception as e:
        logging.error(f"History endpoint server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/', methods=['GET'])
def index():
    logging.info("Root endpoint accessed")
    return jsonify({'message': 'Toxic Comment Classifier API is running'})

if __name__ == '__main__':
    logging.info("Starting Flask server on http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)