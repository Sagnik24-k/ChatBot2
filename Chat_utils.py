# chatbot_utils.py
import json
import random
import re

# Pre-compile regular expressions for slightly better performance in preprocess_input
PREPROCESS_PUNCT_RE = re.compile(r'[^\w\s\']')  # Allows word chars, whitespace, apostrophes
PREPROCESS_SPACE_RE = re.compile(r'\s+')


def preprocess_input(text: str) -> str:
    """
    Preprocesses text by converting to lowercase, removing most punctuation,
    and standardizing whitespace.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = PREPROCESS_PUNCT_RE.sub('', text)  # Remove punctuation
    text = PREPROCESS_SPACE_RE.sub(' ', text).strip()  # Consolidate and strip spaces
    return text


def load_and_preprocess_knowledge_base(filepath="knowledge_base.json"):
    """
    Loads the knowledge base from a JSON file and preprocesses all patterns
    (text and keyword sets) for faster matching in get_response.
    Returns the processed knowledge base or None if an error occurs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_knowledge_base = json.load(f)
    except FileNotFoundError:
        print(f"Error: The knowledge base file '{filepath}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{filepath}' is not a valid JSON file. Check its format.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading the knowledge base: {e}")
        return None

    processed_intents = []
    if "intents" not in raw_knowledge_base:
        print("Error: 'intents' key not found in knowledge base.")
        return None

    for intent_data in raw_knowledge_base["intents"]:
        tag = intent_data.get("tag")
        responses = intent_data.get("responses", [])
        original_patterns = intent_data.get("patterns", [])

        current_intent_processed_patterns = []
        for pattern_text in original_patterns:
            processed_text = preprocess_input(pattern_text)
            if processed_text:  # Only include if pattern is not empty after preprocessing
                keywords = set(processed_text.split())
                current_intent_processed_patterns.append({
                    "text": processed_text,  # Preprocessed pattern string
                    "keywords": keywords  # Set of keywords from the preprocessed pattern
                })

        # Add intent if it has processed patterns or if it's a 'default' intent (which might have no patterns)
        if current_intent_processed_patterns or tag == "default":
            processed_intents.append({
                "tag": tag,
                "processed_patterns_data": current_intent_processed_patterns,  # Renamed for clarity
                "responses": responses
            })

    return {"intents": processed_intents}


def get_response(user_input: str, knowledge_base: dict):
    """
    Finds an appropriate response from the (preprocessed) knowledge base.
    The knowledge_base parameter is expected to be the output of
    load_and_preprocess_knowledge_base.
    """
    processed_user_input = preprocess_input(user_input)
    # Create keyword set from user input once
    user_input_keywords = set(processed_user_input.split())

    if not processed_user_input:  # Handle cases where input becomes empty
        default_intent_data = next(
            (intent for intent in knowledge_base.get("intents", []) if intent.get("tag") == "default"), None)
        if default_intent_data and default_intent_data.get("responses"):
            return random.choice(default_intent_data["responses"])
        return "Please say something."

    possible_matches = []

    for intent_data in knowledge_base.get("intents", []):
        if intent_data.get("tag") == "default":
            continue  # Handle default intent only if no other matches are found

        # Iterate over the pre-processed patterns data for the current intent
        for p_pattern_info in intent_data.get("processed_patterns_data", []):
            processed_pattern_text = p_pattern_info["text"]
            pattern_keywords = p_pattern_info["keywords"]  # Already a set of preprocessed keywords

            # 1. Exact phrase (substring) match using pre-processed pattern
            if processed_pattern_text in processed_user_input:
                possible_matches.append({
                    "responses": intent_data.get("responses", []),
                    "score": 100 + len(processed_pattern_text)  # Longer exact matches get higher score
                })
                # If an exact match is found for this pattern, we can skip its keyword check.
                # We continue checking other patterns in this intent or other intents.
                continue

                # 2. Keyword-based match using pre-generated keyword sets
            if not pattern_keywords:  # Should ideally be filtered out during preprocessing
                continue

            common_keywords = pattern_keywords.intersection(user_input_keywords)

            if common_keywords:
                score = len(common_keywords) * 5  # Base score on number of common keywords

                # Boost score if all keywords of the pattern are present in user input
                if common_keywords == pattern_keywords:  # Exact keyword set match
                    score += 20 + len(pattern_keywords)

                    # Boost score if a significant portion of pattern keywords match
                # (avoid division by zero if pattern_keywords is somehow empty)
                elif pattern_keywords and (len(common_keywords) / len(pattern_keywords)) > 0.6:
                    score += 10

                possible_matches.append({
                    "responses": intent_data.get("responses", []),
                    "score": score
                })

    # If there are scored matches, sort them and pick the best one
    if possible_matches:
        possible_matches.sort(key=lambda x: x["score"], reverse=True)
        best_match = possible_matches[0]
        if best_match["responses"]:  # Ensure there are responses to choose from
            return random.choice(best_match["responses"])

    # Fallback to default response if no suitable patterns matched
    default_intent_data = next(
        (intent for intent in knowledge_base.get("intents", []) if intent.get("tag") == "default"), None)
    if default_intent_data and default_intent_data.get("responses"):
        return random.choice(default_intent_data["responses"])

    # Absolute fallback if default intent is missing or has no responses
    return "I'm really not sure how to respond to that. Can you try asking differently?"