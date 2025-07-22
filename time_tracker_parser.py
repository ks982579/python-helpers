#!/usr/bin/env python3

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import yaml
import os
from markflow.models.yaml_config import YamlConfig
from markflow.models.markdown_files import MarkdownFile


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


# TODO: add in markdown under the times.
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
            print(f"- {task_name}: {duration_str}")

            if task_data['notes']:
                print("\t- Notes:")
                for note in task_data['notes']:
                    # Note should already have the hyphen
                    print(f"\t\t{note}")

        # Show total time tracked for the day
        total_minutes = sum(task['total_duration'] for task in tasks.values())
        total_duration_str = minutes_to_duration(total_minutes)
        print(f"\n⏱️  Total time tracked: {total_duration_str}")


def get_latest_sprint(sprint_path: Path) -> Path:
    """
    From the path provided, the assumptions are the paths are
    sorted ascending.
    This will return the latest spring day.
    """
    # print(f"Sprints Root: {str(sprint_path)}")
    last_year = [x for x in sprint_path.iterdir() if x.is_dir()][-1]
    last_month = [x for x in last_year.iterdir() if x.is_dir()][-1]
    last_sprint = [x for x in last_month.iterdir() if x.is_dir()][-1]
    return [x for x in last_sprint.iterdir() if x.is_file() and '.md' in x.suffix][-1]


def main():
    parser = argparse.ArgumentParser(
        description='Parse time tracking markdown files')
    parser.add_argument('--file', action='append',
                        help='Markdown files to parse')
    parser.add_argument('--aggregate-time', action='store_true',
                        help='aggregates time in the latest sprint-day file')
    parser.add_argument('--new-day', action='store_true',
                        help='creates a new sprint day')
    parser.add_argument('--summary', action='store_true',
                        help='Show summary across all files')
    parser.add_argument('--config', action='store_true',
                        help='Set up or reconfigure the tracking root directory to the top of sprints')
    # parser.add_argument('--help', action='store_true',
    #                     help='prints the help text for this tool')

    args = parser.parse_args()

    # if specific file not specified use config
    # if args.help:
    #     parser.print_help()
    #     return

    # Handle config setup
    if args.config:
        YamlConfig.create_config()
        return

    all_results = {}

    # to hold files if needed.
    files: List[MarkdownFile] = []

    # What file(s) are we parsing
    # put file into 'files' either way.
    # TODO: Encapsulate logic
    if args.file is not None and len(args.file) > 0:
        for file_path in args.file:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ File not found: {file_path}")
                continue
            else:
                files.append(MarkdownFile(file_path))
    elif not args.new_day:
        config: YamlConfig = YamlConfig.load_config()
        file_path = get_latest_sprint(config.root_path)
        files.append(MarkdownFile(file_path))

    # TODO: need groupings to avoid the issue with no files
    if args.aggregate_time:
        if len(files) < 1:
            print("No files found to aggregate?")

        for mdfile in files:
            print(f"📄 Processing: {mdfile.file_path}")
            # TODO: parsing doesn't need to reopen file now
            results = parse_time_tracking_file(mdfile.file_path)
            all_results.update(results)

    if args.new_day:
        print("Starting a new day!")
        config: YamlConfig = YamlConfig.load_config()
        latest_sprint_path = get_latest_sprint(config.root_path)
        # get date from file name
        # will have to determine which week of the year it is
        mdfile = MarkdownFile(latest_sprint_path)

        # WARN: There will come a time in 2026 where week will be 00...
        latest_parent_path = latest_sprint_path.parent.absolute()

        # Default values
        rn = datetime.now()  # right_now
        new_file_name = f"{rn.strftime("%Y%m%d")}.md"
        sprint = rn.strftime("%U")

        # Check if in the same week
        # Week switches to 00 for new year
        if latest_sprint_path.parts[-2] == sprint or int(sprint) == 0:
            # Adding to same sprint
            new_file_path = latest_parent_path / new_file_name
        else:
            print("🔥 New Sprint - Good Luck!")
            year = rn.strftime("%Y")
            month = rn.strftime("%m")
            # create directory first
            new_file_path = config.root_path / year / month / sprint
            new_file_path.mkdir(parents=True, exist_ok=True)
            # full path
            new_file_path = new_file_path / new_file_name

        # Update the date header in the content
        updated_content = mdfile.content
        new_date = rn.strftime("%Y-%m-%d")

        # Replace the first line with the new date
        lines = updated_content.split('\n')
        if lines:
            lines[0] = f'# Today {new_date}'
        
        # Find the Daily Tracker section and add new day entry
        daily_tracker_index = -1
        for i, line in enumerate(lines):
            if line.strip() == "### Daily Tracker":
                daily_tracker_index = i
                break
        
        if daily_tracker_index != -1:
            # Get current time for the initial entry
            current_time = rn.strftime("%H:%M")
            day_abbrev = rn.strftime("%a")  # Mon, Tue, Wed, etc.
            
            # Create the new day section
            new_day_section = [
                "",  # Empty line before
                f"#### {new_date} ({day_abbrev})",
                "",  # Empty line after
                f"- {current_time} - Admin"
            ]
            
            # Insert after the Daily Tracker heading
            # Find where to insert (after any existing content under Daily Tracker)
            insert_index = daily_tracker_index + 1
            
            # Skip any existing content until we find a good insertion point
            while (insert_index < len(lines) and 
                   lines[insert_index].strip() != "" and 
                   not lines[insert_index].startswith("####")):
                insert_index += 1
            
            # Insert the new day section
            for i, section_line in enumerate(new_day_section):
                lines.insert(insert_index + i, section_line)
        
        updated_content = '\n'.join(lines)

        # TODO: Eventually load in the Markdown class
        with open(new_file_path, 'w', encoding="UTF-8") as file:
            # Can read-to-write update later
            file.write(updated_content)
        print(f"📊 Created: {new_file_path}")

    if all_results:
        print_summary(all_results)

        # TODO: Summary will need updates
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
