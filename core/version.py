__VERSION__ = (0, 8, 2)


def get_version() -> str:
    return str(__VERSION__).strip("()").replace(",", ".").replace(" ", "")
