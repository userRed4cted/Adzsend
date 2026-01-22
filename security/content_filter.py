# Content Filter Configuration
# Add words/phrases to block in advertisement messages

# Blacklisted words and phrases (case-insensitive)
BLACKLISTED_WORDS = [
    'child porn',
    'cp',
    'loli',
    'shota',
    'porn',
    'sex',
    'nigger',
    'nigga',
    'free nitro',
    'discord nitro free',
    'free money',
    'free robux',
    'molest',
    'rape',
    'rapist',
    'teen'

]

# Phrase exceptions - if a blacklisted word appears within these phrases, it's allowed
# Format: { 'blacklisted_word': ['exception1', 'exception2', ...] }
PHRASE_EXCEPTIONS = {
    'cp': ['scp', 'scpf'],
    'teen': ['canteen', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'],
    'rapist': ['therapist'],
}


def is_word_in_exception(word, message_lower):
    """
    Check if a blacklisted word appears only within allowed exception phrases.
    Returns True if the word should be allowed (it's part of an exception).
    """
    word_lower = word.lower()
    exceptions = PHRASE_EXCEPTIONS.get(word_lower, [])

    if not exceptions:
        return False  # No exceptions defined, word is blocked

    # Find all occurrences of the blacklisted word in the message
    import re
    pattern = re.escape(word_lower)

    for match in re.finditer(pattern, message_lower):
        start = match.start()
        end = match.end()

        # Check if this occurrence is part of any exception phrase
        is_exception = False
        for exception in exceptions:
            exception_lower = exception.lower()
            # Find the exception in the message
            exc_start = message_lower.find(exception_lower)
            while exc_start != -1:
                exc_end = exc_start + len(exception_lower)
                # Check if the blacklisted word occurrence falls within this exception
                if exc_start <= start and end <= exc_end:
                    is_exception = True
                    break
                exc_start = message_lower.find(exception_lower, exc_start + 1)

            if is_exception:
                break

        # If any occurrence is NOT part of an exception, the word is blocked
        if not is_exception:
            return False

    # All occurrences are within exceptions
    return True


def check_message_content(message, user_id=None):
    """
    Check if message contains any blacklisted content.
    Returns (is_valid, reason) tuple.
    If user_id is provided and blacklisted content is found, flags the user.
    """
    if not message or not message.strip():
        return False, "Message cannot be empty"

    message_lower = message.lower()

    # Check blacklist - find ALL prohibited words
    found_words = []
    for word in BLACKLISTED_WORDS:
        if word.lower() in message_lower:
            # Check if this word is part of an exception phrase
            if not is_word_in_exception(word, message_lower):
                found_words.append(word)

    if found_words:
        # Create comprehensive flag reason with all prohibited words and full message
        prohibited_list = "', '".join(found_words)
        reason = f"Prohibited content: '{prohibited_list}'\n\nFull message:\n{message}"

        # Flag the user if user_id is provided and get ban status
        was_banned = False
        if user_id:
            try:
                from database import flag_user
                flag_count, was_banned = flag_user(user_id, reason)
            except Exception as e:

        # Return error message with ALL prohibited words to user
        if len(found_words) == 1:
            error_msg = f"Message contains prohibited content: '{found_words[0]}'"
        else:
            error_msg = f"Message contains prohibited content: '{prohibited_list}'"
        return False, error_msg, was_banned

    return True, None, False


def get_blacklist_count():
    """Returns the number of blacklisted words."""
    return len(BLACKLISTED_WORDS)


def add_blacklisted_word(word):
    """Add a word to the blacklist (for dynamic updates)."""
    if word and word not in BLACKLISTED_WORDS:
        BLACKLISTED_WORDS.append(word)
        return True
    return False


def remove_blacklisted_word(word):
    """Remove a word from the blacklist (for dynamic updates)."""
    if word in BLACKLISTED_WORDS:
        BLACKLISTED_WORDS.remove(word)
        return True
    return False
