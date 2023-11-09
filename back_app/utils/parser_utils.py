import re


def parse_message(text):
    # Split the text by new lines and ignore empty lines or lines that are just dashes
    lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('---------')]
    # This pattern looks for any text followed by a colon and then any number of spaces before the actual value
    pattern = re.compile(r'^(.*?):\s*(.*)$')

    parsed_dict = {}
    for line in lines:
        match = pattern.search(line)
        if match:
            label, value = match.groups()
            try:
                parsed_value = float(value.replace(',', '')) if not value.endswith('%') else value
            except ValueError:
                parsed_value = value
            parsed_dict[label] = parsed_value
    return parsed_dict
