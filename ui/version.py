__VERSION__ = (0, 7, 6)


def get_version() -> str:
    return str(__VERSION__).strip("()").replace(",", ".").replace(" ", "")
