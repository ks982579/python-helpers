import argparse
from pathlib import Path


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
