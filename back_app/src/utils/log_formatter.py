from datetime import datetime
from random import choice

from src.app import LogTransaction


def get_rgb_str(fg_r, fg_g, fg_b, text):
    return f"\033[38;2;{fg_r};{fg_g};{fg_b}m{text}\033[0m"


def light_color_generator():
    chosen = [(0, 255, 0)]
    step64 = [0, 64, 128, 192, 255]
    while True:
        i, j, k = choice(step64), choice(step64), choice(step64)
        if is_light(i, j, k) and (i, j, k) not in chosen:
            chosen.append((i, j, k))
            yield i, j, k


def is_light(r, g, b):
    # Calculate the brightness using the luminance formula
    brightness = 0.299 * r + 0.587 * g + 0.114 * b

    # Define the threshold to classify as light or dark
    if brightness > 128:
        return True  # light
    return False  # dark


def print_gantt_transaction(transaction: LogTransaction, file_name):
    file = open(file_name, "w")
    print("Transaction Gantt Chart:", file=file)

    # Find the overall start and end times
    start_time = transaction.start_time
    end_time = transaction.end_time
    all_spans = transaction.spans
    if all_spans:
        start_time = min(start_time, min(span.start_time for span in all_spans))
        end_time = max(end_time, max(span.end_time for span in all_spans))

    total_duration = (end_time - start_time).total_seconds()
    chart_width = 50  # Adjust this for wider or narrower chart

    # Calculate the maximum label length
    all_labels = [transaction.label] + [span.label for span in all_spans]
    max_label_length = max(len(label) for label in all_labels)
    label_width = max_label_length + 5

    def time_to_position(time):
        return int(((time - start_time).total_seconds() / total_duration) * chart_width)

    def print_bar(label, start, end, r, g, b):
        start_pos = time_to_position(start)
        end_pos = time_to_position(end)
        bar = f"{'░' * start_pos}{'▓' * (end_pos - start_pos)}{'░' * (chart_width - end_pos)}"
        print(get_rgb_str(r, g, b, f"{label:<{label_width}} │{bar}│ duration: {end - start}"), file=file)

    # Print timeline
    timeline = "".join([str(i % 10) for i in range(chart_width)])
    print(f"{'Timeline':<{label_width}} │{timeline}│", file=file)
    print(f"{'─' * label_width}─┼{'─' * chart_width}┤", file=file)

    # Print transaction
    print_bar(transaction.label, transaction.start_time, transaction.end_time, 0, 255, 0)

    # Sort and print spans
    sorted_spans = sorted(all_spans, key=lambda x: x.start_time)
    gen = light_color_generator()
    colors = [next(gen) for _ in range(len(sorted_spans))]
    stack = []
    for color, span in zip(colors, sorted_spans):
        while stack and stack[-1].end_time <= span.start_time:
            stack.pop()
        print_bar(span.label, span.start_time, span.end_time, color[0], color[1], color[2])
        if stack and span.end_time > stack[-1].end_time:
            stack.append(span)
        elif not stack:
            stack.append(span)

    # Print data
    print("\nData:", file=file)
    print_data(transaction, 0, label_width, 0, 255, 0, file)
    for color, span in zip(colors, sorted_spans):
        print_data(span, 1, label_width, color[0], color[1], color[2], file)


def print_data(item, level, label_width, r, g, b, file):
    padding = "    " * level
    res = [f"{padding}{item.__class__.__name__}: {item.label}"]
    if item.data:
        for k, v in item.data.items():
            v["time"] = datetime.fromtimestamp(v["time"])
        sorted_items = sorted(item.data.items(), key=lambda i: i[1]["time"])
        for key, value in sorted_items:
            try:
                key_parts = key.split("::")
                if len(key_parts) > 1:
                    key_display = key_parts[1]
                else:
                    key_display = key
                values = value.items()
                res.append(f"{padding}  {key_display:{label_width - 4}} : " + "{")
                for k, v in values:
                    if type(v) == dict:
                        for _k, _v in v.items():
                            res.append(f"{padding}  {' ':{label_width}} {_k}: {_v},")
                    if type(v) == list:
                        for i in v:
                            res.append(f"{padding}  {' ':{label_width}} {i},")
                    else:
                        res.append(f"{padding}  {' ':{label_width}} {k}: {v},")
                res.append(f"{padding}  {' ':{label_width - 2}} " + "}")
            except (IndexError, KeyError, AttributeError):
                res.append(f"{padding}  {key:{label_width - 4}} : {value}")
    print(get_rgb_str(r, g, b, "\n".join(res)), file=file)
