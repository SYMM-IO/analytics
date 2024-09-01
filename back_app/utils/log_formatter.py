from typing import List

from app import LogTransaction, LogSpan


def print_data(item, level):
    padding = "  " * level
    print(f"{padding}{item.__class__.__name__}: {item.label}")
    if item.data:
        for key, value in item.data.items():
            print(f"{padding}  {key.split('::')[1]}: {value['value']}")


def print_transaction(transaction: LogTransaction):
    # Find the overall start and end times
    start_time = transaction.start_time
    end_time = transaction.end_time
    all_spans: List[LogSpan] = transaction.spans
    if all_spans:
        start_time = min(start_time, min(span.start_time for span in all_spans))
        end_time = max(end_time, max(span.end_time for span in all_spans))

    total_duration = (end_time - start_time).total_seconds()
    chart_width = 50  # Adjust this for wider or narrower chart

    def time_to_position(time):
        return int(((time - start_time).total_seconds() / total_duration) * chart_width)

    def print_bar(label, start, end, level, color):
        start_pos = time_to_position(start)
        end_pos = time_to_position(end)
        padding = "  " * level
        bar = f"{color}{'▓' * (end_pos - start_pos)}{'░' * (chart_width - end_pos)}\\033[0m"
        print(f"{padding}{label:<20} │{bar}│ {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}")

    # Print timeline
    timeline = "".join([str(i % 10) for i in range(chart_width)])
    print(f"{'Timeline':<20} │{timeline}│")
    print(f"{'─' * 20}─┼{'─' * chart_width}┤")

    # Print transaction
    print_bar(transaction.label, transaction.start_time, transaction.end_time, 0, "\033[94m")  # Blue

    # Sort and print spans
    sorted_spans = sorted(all_spans, key=lambda x: x.start_time)
    level = 1
    stack = []
    for span in sorted_spans:
        while stack and stack[-1].end_time <= span.start_time:
            level -= 1
            stack.pop()
        print_bar(span.label, span.start_time, span.end_time, level, "\033[92m")  # Green
        if stack and span.end_time > stack[-1].end_time:
            stack.append(span)
            level += 1
        elif not stack:
            stack.append(span)

    # Print data
    print("\nData:")
    print_data(transaction, 0)
    for span in sorted_spans:
        print_data(span, 1)
