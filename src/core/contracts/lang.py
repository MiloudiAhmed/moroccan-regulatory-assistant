"""Question and chunk language (00-shared §4b). Owned by P3; used by P1, P3, P4."""


def detect_language(text: str) -> str:
    """ "fr" if more than half of the letters are Latin, else "ar".

    Arabic and Darija written in Arabic script give "ar". Text with no letters gives "ar".
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "ar"
    latin = sum(1 for c in letters if c.isascii() or "À" <= c <= "ɏ")
    return "fr" if latin * 2 > len(letters) else "ar"
