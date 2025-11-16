# 🧠 Toxic Comment Classification System  
A full-stack machine learning web application that detects toxic comments in real-time using **Flask**, **Scikit-Learn**, **TextBlob**, **TF-IDF**, and a clean, responsive **TailwindCSS** frontend.

---

## 🚀 Features

### 🔍 **1. Comment Toxicity Prediction**
- Classifies each comment as **Toxic** or **Non-Toxic**
- Shows **confidence score (%)**
- Detects the **language**
- Uses **sentiment analysis** (positive / negative / neutral)
- Highlights **important keywords** influencing the prediction

### 🧪 **2. Multi-Label Classification**
The model predicts six toxicity types:
- Toxic  
- Severe Toxic  
- Obscene  
- Threat  
- Insult  
- Identity Hate  

Results are shown in a **radar chart**.

### 🧠 **3. Real-Time AI Feedback**
As the user types, the system gives instant feedback:
- Toxicity  
- Confidence  
- Sentiment  

### 📊 **4. Analytics & Visualization**
- Radar Chart (Chart.js)
- Word Cloud (WordCloud2)

### 📝 **5. User History Tracking (SQLite)**
Stores:
- Past comments
- Predictions
- Confidence scores
- Timestamp

Each user is identified by a unique **User ID** stored in `localStorage`.

### 🏅 **6. Achievement Badges**
Earn badges such as:
- **Clean Commenter**
- **Positive Contributor**

Based on user's non-toxic history count.

### 🛠️ **7. Feedback System**
Users can report incorrect predictions.

### 🌗 **8. Modern UI**
- Light/Dark Mode  
- High Contrast Mode (Accessibility)  
- TailwindCSS styling  
- Smooth animation effects  

---

## 📂 Project Structure

Toxic-Comment-Classification
├── app.py # Flask backend & ML model
├── history.db # SQLite database
├── index.html # Frontend UI
├── script.js # Frontend logic
├── style.css # Additional animations + accessibility styles
├── requirements.txt # Python dependencies
└── README.md # Project documentation



---

## ⚙️ Installation & Setup

### **1. Clone the Repository**
```sh
git clone https://github.com/suhaasmanupala/Toxic-Comment-Classification.git
cd Toxic-Comment-Classification


3. Install Dependencies
pip install -r requirements.txt

4. Run the Flask Server
python app.py
