def format(number: int, decimals=18, precision=2):
    result = number / (10 ** decimals)
    return f"{result:,.{precision}f}"
