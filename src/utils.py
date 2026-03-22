def validate_input(user_ratings):
    """Validate user ratings input format and values."""
    if not isinstance(user_ratings, dict):
        return False, "Request body must be a JSON object (dict)"

    if not user_ratings:
        return False, "Request body cannot be empty"

    for title, rating in user_ratings.items():
        if not isinstance(title, str):
            return False, f"Movie title must be a string, got {type(title).__name__}"

        if not title:
            return False, "Movie title cannot be empty"

        if len(title) > 1023:
            return False, f"Movie title exceeds maximum length of 1023 characters (length: {len(title)})"

        if not isinstance(rating, (int, float)):
            return False, f"Rating for '{title}' must be a number, got {type(rating).__name__}"

        try:
            rating_float = float(rating)
        except (TypeError, ValueError):
            return False, f"Rating for '{title}' cannot be converted to a number"

        if rating_float < 1.0 or rating_float > 5.0:
            return False, f"Rating for '{title}' must be between 1 and 5 (inclusive), got {rating_float}"

    return True, ""
