# 🤖 JARVIS - Your AI-Powered Study Assistant

## 📚 Project Overview

*JARVIS* is a web-based study chatbot powered by the *Google Gemini AI model. It assists users with general conversations, answers study-related questions, and fetches book reviews from Wikipedia. Built using **Python (Flask)* for the backend and *HTML/CSS* for the frontend, JARVIS acts as a smart, lightweight assistant to enhance your learning experience.

---

## 📌 What JARVIS Can Do

1. *Engage in General Conversation*  
   Leverages the Google Gemini model to chat about a wide range of topics.

2. *Provide Book Reviews*  
   Type: Book review <book title>  
   JARVIS will summarize the book from Wikipedia.

3. *Answer Study-Related Questions*  
   Get instant AI-generated responses to any educational queries.

4. *Display Your Question History*  
   Shows a sidebar with previously asked questions for easy reference.

---

## 🚀 Upcoming Features

- 🔒 User Authentication  
- ✏ Prompt Editing Option  
- 🖼 Picture Upload and Explanation Feature

---

## ⚙ Tech Stack

| Component  | Technology     |
|------------|----------------|
| Frontend   | HTML, CSS      |
| Backend    | Python (Flask) |
| AI Layer   | Gemini API     |

---

## 🏗 Architecture

The project follows a client-server architecture and includes the following key components:

### 1. app.py
- *Backend Logic:* Main Flask app
- *Session Management:* Keeps chat history
- *Gemini Integration:* Uses google.generativeai with key from .env
- *Routing:*
  - /: Displays chat interface
  - /process_input: Handles user input

### 2. Chat_utils.py
- Handles:
  - Input preprocessing
  - Knowledge base loading
  - Response generation using predefined intents

### 3. wek.py
- Fetches book reviews from Wikipedia using the wikipedia Python library
- Handles PageError, DisambiguationError, and ensures relevance

### 4. knowledge_base.json
- Stores intents, example patterns, and responses
- Supports fallback and custom replies (e.g., bot name, greetings)

### 5. .env
- Stores the Gemini API key securely

### 6. index.html (Flask Template)
- *HTML5 Structure:* Semantic layout using Tailwind CSS
- *Sidebar:* Lists all previously asked questions
- *Main Panel:* Displays conversation history
- *Input Box:* For submitting new queries

---

## 🌐 Interaction Flow

1. User opens http://127.0.0.1:5000/
2. Flask loads previous chat history (if available)
3. User submits a question → POST request sent to /process_input
4. Flask:
   - Checks for Book review → calls wek.py
   - Else → uses Gemini API or falls back to knowledge_base.json
5. Response stored and user redirected to / to view updated chat

---

## 📁 Project Structure
