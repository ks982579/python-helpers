#!/usr/bin/env python3

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


def parse_time(time_str: str) -> int:
    """Convert time string like '09:00' to minutes since midnight."""
    hour, minute = map(int, time_str.split(':'))
    return hour * 60 + minute


def minutes_to_duration(minutes: int) -> str:
    """Convert minutes to readable duration format."""
    hours = minutes // 60
    mins = minutes % 60
    if hours == 0:
        return f"{mins}m"
    elif mins == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {mins}m"


def parse_time_tracking_file(file_path: Path) -> Dict[str, Dict[str, any]]:
    """Parse a time tracking markdown file and return grouped task data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all day sections
    day_pattern = r'#### (\d{4}-\d{2}-\d{2})'  # \([^)]+\)'
    day_matches = list(re.finditer(day_pattern, content))

    results = {}

    for i, day_match in enumerate(day_matches):
        date_str = day_match.group(1)
        day_start = day_match.end()

        # Find the end of this day's section
        if i + 1 < len(day_matches):
            day_end = day_matches[i + 1].start()
        else:
            # Look for next section header or end of file
            next_section = re.search(r'\n##[^#]', content[day_start:])
            day_end = day_start + next_section.start() \
                if next_section else len(content)

        day_content = content[day_start:day_end]

        # Parse tasks for this day
        task_data = parse_day_tasks(day_content)
        if task_data:
            results[date_str] = task_data

    return results


def parse_day_tasks(day_content: str) -> Dict[str, any]:
    """Parse tasks for a single day."""
    lines = day_content.strip().split('\n')
    tasks = []
    current_task = None

    for line in lines:
        if not line:
            continue

        # Main task line (starts with -)
        if line.startswith('- ') and re.search(r'\d{2}:\d{2}', line):
            if current_task:
                tasks.append(current_task)

            # Extract time and task name
            time_match = re.search(r'(\d{2}:\d{2})', line)
            if time_match:
                time_str = time_match.group(1)
                task_name = line[line.find(time_str) + 5:].strip()
                if task_name.startswith('- '):
                    task_name = task_name[2:]

                current_task = {
                    'time': time_str,
                    'name': task_name,
                    'notes': []
                }

        # TODO: think how to change bullet points
        # Sub-bullet point (notes)
        elif line.strip().startswith('- ') and current_task:
            current_task['notes'].append(line)

    # Add the last task
    if current_task:
        tasks.append(current_task)

    # Calculate durations and group by task label
    grouped_tasks = {}

    for i, task in enumerate(tasks):
        start_time = parse_time(task['time'])

        # Calculate end time (start of next task or end of day)
        if i + 1 < len(tasks):
            end_time = parse_time(tasks[i + 1]['time'])
        else:
            # Last 'task' should be "Bye"
            # and only signals end time to finish previous calcuation
            continue

        duration = end_time - start_time
        if duration < 0:  # Handle day boundary crossing
            duration += 24 * 60

        # Group by task name
        task_name = task['name']
        if task_name not in grouped_tasks:
            grouped_tasks[task_name] = {
                'total_duration': 0,
                'notes': [],
                'occurrences': []
            }

        grouped_tasks[task_name]['total_duration'] += duration
        grouped_tasks[task_name]['notes'].extend(task['notes'])
        grouped_tasks[task_name]['occurrences'].append({
            'time': task['time'],
            'duration': duration,
            'notes': task['notes']
        })

    return grouped_tasks


# TODO: add info to document
def print_summary(results: Dict[str, Dict[str, any]]):
    """Print a summary of the parsed time tracking data."""
    for date, tasks in results.items():
        print(f"\n📅 {date}")
        print("=" * 50)

        # Sort tasks by total duration (descending)
        sorted_tasks = sorted(
            tasks.items(), key=lambda x: x[1]['total_duration'], reverse=True)

        for task_name, task_data in sorted_tasks:
            duration_str = minutes_to_duration(task_data['total_duration'])
            print(f"\n🔸 {task_name}: {duration_str}")

            if task_data['notes']:
                print("   Notes:")
                for note in task_data['notes']:
                    print(f"   • {note}")

        # Show total time tracked for the day
        total_minutes = sum(task['total_duration'] for task in tasks.values())
        total_duration_str = minutes_to_duration(total_minutes)
        print(f"\n⏱️  Total time tracked: {total_duration_str}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse time tracking markdown files')
    parser.add_argument('files', nargs='+', help='Markdown files to parse')
    parser.add_argument('--summary', action='store_true',
                        help='Show summary across all files')

    args = parser.parse_args()

    all_results = {}

    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            continue

        print(f"📄 Processing: {file_path}")
        results = parse_time_tracking_file(path)
        all_results.update(results)

    if all_results:
        print_summary(all_results)

        if args.summary and len(all_results) > 1:
            print("\n" + "=" * 60)
            print("📊 OVERALL SUMMARY")
            print("=" * 60)

            # Aggregate all tasks across all days
            overall_tasks = {}
            for date, tasks in all_results.items():
                for task_name, task_data in tasks.items():
                    if task_name not in overall_tasks:
                        overall_tasks[task_name] = {
                            'total_duration': 0,
                            'notes': [],
                            'days': 0
                        }

                    overall_tasks[task_name]['total_duration'] += task_data['total_duration']
                    overall_tasks[task_name]['notes'].extend(
                        task_data['notes'])
                    overall_tasks[task_name]['days'] += 1

            # Sort by total duration
            sorted_overall = sorted(overall_tasks.items(
            ), key=lambda x: x[1]['total_duration'], reverse=True)

            for task_name, task_data in sorted_overall:
                duration_str = minutes_to_duration(task_data['total_duration'])
                days_str = f"({task_data['days']} day{
                    's' if task_data['days'] > 1 else ''})"
                print(f"\n🔸 {task_name}: {duration_str} {days_str}")
    else:
        print("❌ No time tracking data found in the specified files.")


if __name__ == '__main__':
    main()
