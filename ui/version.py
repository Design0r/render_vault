__VERSION__ = (0, 7, 9)


def get_version() -> str:
    return str(__VERSION__).strip("()").replace(",", ".").replace(" ", "")
