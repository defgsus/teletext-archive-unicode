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


def concat_split_words(text: str) -> str:
    lines = text.splitlines()
    last_line = None
    ret_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if last_line:
            first_word = line.split(maxsplit=1)[0]
            last_line += first_word
            line = line[len(first_word):].strip()
            ret_lines.append(last_line)
            last_line = None

        if line.endswith("-") and len(line) > 1 and line[-2].isalpha():
            last_line = line[:-1]
        else:
            ret_lines.append(line)

    return "\n".join(ret_lines)

