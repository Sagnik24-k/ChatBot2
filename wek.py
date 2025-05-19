import wikipedia

def fetch_book_details_from_wikipedia(book_title):
    """
    Fetches a summary of a specific book from Wikipedia,
    attempting to verify if the page is indeed about a book.

    Args:
        book_title: The exact title of the book to search for on Wikipedia.

    Returns:
        A string containing the summary of the book's Wikipedia page,
        or an informative message if:
        - The book is not found.
        - There's a disambiguation error.
        - A page is found but does not appear to be about a book
          based on its categories.
        - Another error occurs.
    """
    try:
        # Set language to English (default is usually English, but good to be explicit)
        wikipedia.set_lang("en")

        # Get the Wikipedia page for the book title
        # auto_suggest=False is used to try and get an exact match
        page = wikipedia.page(book_title, auto_suggest=False)

        # --- Book Verification (Heuristic) ---
        # Check categories to see if it's likely a book page
        book_categories_keywords = [
            "novels", "fiction", "literature", "books", "works",
            "fantasy", "science fiction", "mystery", "thriller",
            "historical novels", "children's books", "young adult fiction",
            "romance novels", "horror novels", "biographies", "autobiographies"
            # Add more keywords as needed
        ]

        is_likely_book = False
        page_categories = [cat.lower() for cat in page.categories]

        for keyword in book_categories_keywords:
            if any(keyword in category for category in page_categories):
                is_likely_book = True
                break

        if is_likely_book:
            # Return the summary if it seems to be a book page
            return page.summary
        else:
            # Return a message if a page was found but doesn't seem to be a book
            return f"A Wikipedia page was found for '{book_title}', but it does not appear to be about a book based on its categories."

    except wikipedia.exceptions.PageError:
        return f"Could not find a Wikipedia page for the book '{book_title}'."
    except wikipedia.exceptions.DisambiguationError as e:
        # Handle disambiguation errors by listing potential options
        options = e.options
        return f"Multiple Wikipedia pages found for '{book_title}'. Please be more specific. Options: {', '.join(options)}"
    except Exception as e:
        return f"An error occurred: {e}"

# --- Main Function or Execution Block ---
