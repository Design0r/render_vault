__VERSION__ = (0, 8, 3)


def get_version() -> str:
    return str(__VERSION__).strip("()").replace(",", ".").replace(" ", "")
