from typing import Optional, List


STRIP_CHARS = "*@#,:;.…!?-'\"„“»«()[]&<>+-%\\/"


def tokenize(
        text: str,
        lowercase: bool = False,
        strip_chars: Optional[str] = None,
) -> List[str]:
    if strip_chars is None:
        strip_chars = STRIP_CHARS

    tokens = []
    for tok in text.split():
        tok = tok.strip(strip_chars)
        if tok:
            tokens.append(tok.lower() if lowercase else tok)
    return tokens
