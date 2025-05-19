# app.py
# This script runs the Flask backend for JARVIS, now integrated with Gemini.
# It handles chat messages using Gemini and book review requests.
# It renders HTML templates and processes form submissions.

from flask import Flask, request, render_template_string, redirect, url_for, session
from flask_cors import CORS # Import CORS if needed
import json
import os
import google.generativeai as genai # Import the Google Generative AI library
from dotenv import load_dotenv # Import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()

# --- Configure Google Gemini API ---
# IMPORTANT: Get API key from environment variable (loaded from .env by load_dotenv())
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Use os.getenv to read from environment

    if not GEMINI_API_KEY: # Check if the key was actually loaded
         print("WARNING: GEMINI_API_KEY not found in environment variables or .env file.")
         print("Gemini chat functionality will be unavailable.")
         gemini_available = False
         gemini_model = None
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        # Initialize the Gemini model
        # You can choose a different model like 'gemini-1.5-flash-latest' or 'gemini-1.5-pro-latest'
        # based on your needs and availability.
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("JARVIS Backend: Gemini model initialized.")
        gemini_available = True

except Exception as e:
    print(f"Error configuring or initializing Gemini model: {e}")
    print("Gemini chat functionality will be unavailable.")
    gemini_model = None
    gemini_available = False


# Assuming chatbot_utils.py and wek.py are in the same directory
try:
    from Chat_utils import load_and_preprocess_knowledge_base, get_response
    from wek import fetch_book_details_from_wikipedia
except ImportError as e:
    print(f"Error importing local modules: {e}")
    print("Please ensure chatbot_utils.py and wek.py are in the same directory.")
    # Set functions to None if import fails
    load_and_preprocess_knowledge_base = None
    get_response = None
    fetch_book_details_from_wikipedia = None


app = Flask(__name__)
# Set a secret key for session management (required for using session)
# Change this to a random, long string in a real application
app.config['SECRET_KEY'] = 'your_secret_key_here_change_this'
# CORS(app) # CORS is less relevant when not using JS fetch, but can be kept if needed


# --- Load Knowledge Base ---
# Load the knowledge base when the application starts
KNOWLEDGE_BASE_FILE = "knowledge_base.json"
knowledge_base_data = None # Initialize as None

if load_and_preprocess_knowledge_base:
    print(f"JARVIS Backend: Loading knowledge base from {KNOWLEDGE_BASE_FILE}...")
    knowledge_base_data = load_and_preprocess_knowledge_base(KNOWLEDGE_BASE_FILE)

    # Check if knowledge base loaded successfully
    if not knowledge_base_data or not knowledge_base_data.get("intents"):
        print(f"JARVIS Backend: Critical error - Knowledge base not loaded or processed correctly from {KNOWLEDGE_BASE_FILE}.")
        knowledge_base_data = None # Ensure it's None if loading failed
    else:
        print("JARVIS Backend: Knowledge base loaded successfully.")


# --- HTML Template (Rendered by Flask) ---
# This is the HTML structure that Flask will render and send to the browser.
# It includes placeholders for the chat history.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS</title> {# Changed title to JARVIS #}
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom styles for Inter font */
        body {
            font-family: 'Inter', sans-serif;
        }

        /* --- Grid Layout --- */
        .grid-container {
            display: grid;
            /* Define grid columns: sidebar (fixed width), main content (takes remaining space) */
            grid-template-columns: 250px 1fr;
            /* Define grid rows: navbar (auto height), main content (takes remaining), input (auto height) */
            grid-template-rows: auto 1fr auto;
            /* Define named grid areas */
            grid-template-areas:
                "navbar main"
                "sidebar main"
                "sidebar input"; /* Input area spans below sidebar and main */
            height: 100vh; /* Full viewport height */
            gap: 1rem; /* Gap between grid items */
            padding: 1rem; /* Padding around the container */
        }

        /* Assign grid areas to elements */
        .navbar-area { grid-area: navbar; }
        .sidebar-area { grid-area: sidebar; }
        .main-area { grid-area: main; }
        .input-area { grid-area: input; }

        /* --- General Styling --- */
        body {
            background-color: black; /* Black background for the body */
            color: white; /* Default text color white for better contrast on black body */
        }

        .chat-container {
             background-color: white; /* White background for the main chat area */
             color: #1f2937; /* Dark gray text for readability on white background */
             border-radius: 0.5rem;
             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
             padding: 1.5rem;
             display: flex;
             flex-direction: column;
        }


        /* Style for chat messages */
        .chat-message {
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 0.5rem;
            max-width: 80%; /* Limit message width */
            word-wrap: break-word; /* Break long words */
            color: black; /* Set default text color for messages to black */
        }
        /* Updated styles for user and bot messages */
        .user-message {
            background-color: #dbeafe; /* Keep light blue background for user */
            /* color: #facc15; Removed yellow text color */
            align-self: flex-end; /* Align user messages to the right */
            margin-left: auto;
        }
        .bot-message {
            background-color: #e5e7eb; /* Keep light gray background for bot */
            /* color: #ffffff; Removed white text color */
            align-self: flex-start; /* Align bot messages to the left */
            margin-right: auto;
        }
        /* Style for book review messages (keeping green for distinction) */
         .book-review-message {
            background-color: #d1fae5; /* Light green */
            align-self: flex-start; /* Align to the left */
            margin-right: auto;
            border-left: 4px solid #10b981; /* Green border for visual distinction */
            padding-left: 1rem;
            color: #1f2937; /* Dark gray text for readability on light green */
        }
        /* Container for messages to enable flex column layout */
        #chatBox {
            display: flex;
            flex-direction: column;
            overflow-y: auto; /* Make chat box scrollable */
        }

        /* Style for buttons */
        .gray-button {
            background-color: #6b7280; /* Gray-500 */
            color: white;
            font-weight: bold;
            padding: 0.75rem 1.5rem; /* py-3 px-6 */
            border-radius: 0.25rem; /* rounded-lg */
            transition: background-color 0.3s ease-in-out;
        }
        .gray-button:hover {
            background-color: #4b5563; /* Gray-700 */
        }

        /* Style for the input field text color */
        .input-text-color {
             color: #1f2937; /* Dark gray text for readability on white background */
        }

        /* Style for old chat entries in the sidebar */
        .old-chat-entry {
            margin-bottom: 0.5rem;
            padding: 0.5rem;
            background-color: #4b5563; /* Darker gray for sidebar entries */
            border-radius: 0.25rem;
            font-size: 0.875rem; /* text-sm */
            color: #d1d5db; /* Light gray text */
            overflow: hidden; /* Hide overflow text */
            text-overflow: ellipsis; /* Add ellipsis for overflow */
            white-space: nowrap; /* Prevent wrapping */
        }

    </style>
</head>
{# Updated body background to black #}
<body class="bg-black">
    <div class="grid-container">

        {# Navbar Area #}
        <div class="navbar-area bg-gray-800 text-white p-4 rounded-lg">
            <h2 class="text-lg font-bold">JARVIS Nav</h2> {# Changed Navbar title #}
            {# Add navigation links or content here #}
        </div>

        {# Sidebar Area - Displaying User Questions #}
        <div class="sidebar-area bg-gray-700 text-white p-4 rounded-lg overflow-y-auto">
            <h2 class="text-lg font-bold mb-4">Your Questions</h2> {# Changed title to "Your Questions" #}
            {# Iterate through chat history and display only user messages #}
            {% for message in chat_history %}
                {% if message.sender == 'user' %}
                    <div class="old-chat-entry">
                        {{ message.text }}
                    </div>
                {% endif %}
            {% endfor %}
        </div>

        {# Main Content Area (Chat Display) #}
        <div class="main-area chat-container">
             <h1 class="text-2xl font-bold mb-4 text-center text-gray-800">JARVIS Chat</h1> {# Changed main title #}
            <div id="chatBox" class="flex-grow overflow-y-auto border border-gray-300 rounded-lg p-4 mb-4 space-y-4">
                {% for message in chat_history %}
                    <div class="chat-message {{ message.sender }}-message {% if message.type == 'book_review' %}book-review-message{% endif %}">
                        {% if message.type == 'book_review' %}
                            <strong>Book Review:</strong> {{ message.text | safe }} {# Use safe filter to render <br> #}
                        {% else %}
                            {{ message.text }}
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
        </div>

        {# Input Area #}
        {# This form submits data to the /process_input route #}
        <div class="input-area bg-gray-800 p-4 rounded-lg flex items-center justify-center">
             <form method="POST" action="{{ url_for('process_input') }}" class="flex w-full max-w-lg">
                <input
                    type="text"
                    name="user_input" {# Name attribute is important for form data #}
                    class="flex-grow shadow appearance-none border rounded-l-lg w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 input-text-color" {# Added input-text-color class #}
                    placeholder="Type your message or 'Book review <title>' here..."
                    autofocus {# Automatically focus the input field #}
                >
                {# Updated button styles to gray #}
                <button
                    type="submit" {# This button submits the form #}
                    class="gray-button rounded-r-lg focus:outline-none focus:shadow-outline"
                >
                    Send
                </button>
            </form>
        </div>

    </div>
</body>
</html>
"""

# --- Route for the main chat page ---
@app.route('/')
def index():
    """
    Renders the initial chat page or the current state of the chat.
    """
    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in session:
        initial_message = "JARVIS: Hello! I'm your friendly AI assistant."
        if gemini_available:
             initial_message += " I can answer general questions using Gemini."
        initial_message += " Type 'Book review <title>' to get details about a book."
        initial_message += " Type 'quit', 'bye', or 'exit' to end the session (in console)."

        session['chat_history'] = [{'sender': 'bot', 'text': initial_message, 'type': 'chat'}]

    # Render the HTML template with the current chat history
    return render_template_string(HTML_TEMPLATE, chat_history=session.get('chat_history', []))

# --- Route to process user input from the form ---
@app.route('/process_input', methods=['POST'])
def process_input():
    """
    Receives input from the HTML form, processes it using either
    specific commands (like Book Review) or the Gemini model for general chat,
    updates chat history, and redirects back to the index page.
    """
    # Check if knowledge base is loaded (needed for get_response and exit commands)
    if not knowledge_base_data or not knowledge_base_data.get("intents"):
         if 'chat_history' not in session:
              session['chat_history'] = []
         session['chat_history'].append({'sender': 'bot', 'text': "JARVIS: Backend error: Knowledge base not loaded.", 'type': 'chat'})
         session.modified = True
         return redirect(url_for('index'))

    # Get user input from the form data
    user_input = request.form.get('user_input', '').strip()

    if not user_input:
        # If input is empty, just redirect back without adding a message
        return redirect(url_for('index'))

    # Add user message to chat history
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({'sender': 'user', 'text': f"You: {user_input}", 'type': 'chat'})

    # --- Limit Session History Size ---
    # Keep only the last N messages to prevent the cookie from getting too large.
    # Adjust the number (e.g., 20, 30, 40) based on how long your messages are
    # and the browser's cookie limit (typically around 4093 bytes).
    # Keeping 30 messages (15 user + 15 bot) is a reasonable starting point.
    MAX_HISTORY_SIZE = 30
    if len(session['chat_history']) > MAX_HISTORY_SIZE:
        # Keep the last MAX_HISTORY_SIZE messages
        session['chat_history'] = session['chat_history'][-MAX_HISTORY_SIZE:]


    # Convert user input to lowercase for command checking
    user_input_lower = user_input.lower()

    # --- Process Input ---
    response_text = ""
    response_type = "chat"

    # Check for the "Book review" command
    if user_input_lower.startswith("book review"):
        if fetch_book_details_from_wikipedia:
            # Attempt to extract the title after "book review"
            book_title = user_input[len("book review"):].strip()
            if book_title:
                print(f"JARVIS Backend: Processing book review request for: '{book_title}'")
                response_text = fetch_book_details_from_wikipedia(book_title)
                response_type = "book_review"
                # Replace newlines with <br> for HTML rendering
                response_text = response_text.replace('\n', '<br>')
            else:
                response_text = "Please provide the book title after 'Book review'."
                response_type = "chat"
        else:
             response_text = "Book review functionality is not available due to module import errors."
             response_type = "chat"

    # Check for exit commands (these are handled by the frontend user typing them)
    # We still process them here to potentially give a final message from KB
    elif user_input_lower in ["quit", "bye", "exit"]:
        if get_response:
            response_text = get_response(user_input_lower, knowledge_base_data)
        else:
            response_text = "Chat functionality is not available due to module import errors."
        response_type = "chat"
        # In this web app, 'quit' doesn't stop the server, just gives a message.
        # You could add logic here to clear the session if desired.


    # Handle General Chat using Gemini or KB fallback
    else:
        print(f"JARVIS Backend: Processing general chat message with Gemini: '{user_input}'")
        if gemini_available and gemini_model:
            try:
                # Send the user input to the Gemini model
                gemini_response = gemini_model.generate_content(user_input)
                response_text = gemini_response.text
                response_type = "chat"
            except Exception as e:
                print(f"Error generating content with Gemini: {e}")
                response_text = "Sorry, I encountered an error trying to use the AI model."
                response_type = "chat"
        elif get_response:
             # Fallback to the knowledge base if Gemini is not available
             print("JARVIS Backend: Gemini not available, falling back to Knowledge Base.")
             response_text = get_response(user_input, knowledge_base_data)
             response_type = "chat"
        else:
            # Final fallback if neither Gemini nor KB is available
            response_text = "I'm currently unable to process chat messages."
            response_type = "chat"


    # Add bot response to chat history
    session['chat_history'].append({'sender': 'bot', 'text': f"JARVIS: {response_text}", 'type': response_type})

    # Mark the session as modified to ensure it's saved
    session.modified = True

    # Redirect back to the index page to display the updated chat history
    return redirect(url_for('index'))


# --- Basic Root Endpoint (Optional - redirects to index) ---
@app.route('/old_root')
def old_index():
    # Redirect the old root to the new index route
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Run the Flask development server
    print("JARVIS Backend: Starting Flask server (Gemini Integrated)...")
    # Use debug=True for development
    app.run(debug=True, port=5000)
