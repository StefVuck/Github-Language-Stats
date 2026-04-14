#!/usr/bin/env python3
import json
import os
import sys
import argparse
from github_client import GitHubClient
from language_analyzer import LanguageAnalyzer
from visualizer import Visualizer


def parse_args():
    parser = argparse.ArgumentParser(
        description=('GitHub Profile Language Analytics - '
                    'Generate beautiful visualizations of your language usage')
    )
    parser.add_argument(
        '--types',
        nargs='+',
        choices=['leaderboard', 'bar', 'horizontal-bar', 'pie', 'donut'],
        default=['leaderboard'],
        help='Visualization types to generate (default: leaderboard)'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to config file (default: config.json)'
    )
    parser.add_argument(
        '--output',
        default='output',
        help='Output directory for visualizations (default: output)'
    )
    parser.add_argument(
        '--top-repos',
        type=int,
        default=5,
        help='Number of top contributing repos to show in leaderboard breakdown (default: 5)'
    )
    parser.add_argument(
        '--dark-mode',
        action='store_true',
        help='Enable dark mode theme for visualizations'
    )
    parser.add_argument(
        '--loc',
        action='store_true',
        help='Count actual lines of code by shallow cloning repos (slower but accurate)'
    )
    return parser.parse_args()

def load_config(config_path: str = 'config.json'):
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        print("Please copy config.example.json to config.json and add your GitHub token.")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    args = parse_args()

    print("GitHub Profile Language Analytics")
    print("=" * 50)

    config = load_config(args.config)
    token = config.get('github_token')
    excluded_repos = config.get('excluded_repos', [])
    include_forks = config.get('include_forks', False)
    excluded_languages = config.get('excluded_languages', ['HTML', 'CSS'])
    hide_private_repo_names = config.get('hide_private_repo_names', False)

    if not token or token == 'your_github_personal_access_token_here':
        print("Error: Please set your GitHub token in config.json")
        sys.exit(1)

    print("\nInitializing GitHub client...")
    client = GitHubClient(token)
    username = client.get_username()
    print(f"Authenticated as: {username}")

    filter_msg = f"excluding: {excluded_repos}" if excluded_repos else "no exclusions"
    fork_msg = "including forks" if include_forks else "excluding forks"
    print(f"\nFetching repositories ({filter_msg}, {fork_msg})...")
    repos = client.get_all_repos(excluded_repos, include_forks)
    print(f"Found {len(repos)} repositories")

    lang_list = ', '.join(excluded_languages) if excluded_languages else None
    lang_msg = f"excluding languages: {lang_list}" if lang_list else "all languages"
    privacy_msg = " (hiding private repo names)" if hide_private_repo_names else ""
    print(f"\nAnalyzing language statistics ({lang_msg}{privacy_msg})...")
    analyzer = LanguageAnalyzer(excluded_languages, hide_private_repo_names)

    get_stats = client.get_loc_stats if args.loc else client.get_language_stats
    stat_label = "lines of code" if args.loc else "bytes"
    print(f"  (counting {stat_label})")

    for i, repo in enumerate(repos, 1):
        privacy_indicator = " [Private]" if client.is_repo_private(repo) else ""
        print(f"  [{i}/{len(repos)}] Processing: {repo.name}{privacy_indicator}")
        languages = get_stats(repo, set(excluded_languages)) if args.loc else get_stats(repo)
        if args.loc and not languages:
            print(f"    Warning: LOC count failed for {repo.name}, falling back to bytes")
            languages = client.get_language_stats(repo)
        is_private = client.is_repo_private(repo)
        analyzer.add_repo_languages(repo.name, languages, is_private)

    print("\nGenerating leaderboards...")
    by_repos = analyzer.get_by_repos()
    by_bytes = analyzer.get_by_bytes()
    by_weighted = analyzer.get_by_weighted()

    print("\nLanguage Statistics:")
    print(f"  Total languages: {len(analyzer.get_all_languages())}")
    top_by_repos = by_repos[0][0] if by_repos else 'N/A'
    top_by_bytes = by_bytes[0][0] if by_bytes else 'N/A'
    top_by_weighted = by_weighted[0][0] if by_weighted else 'N/A'
    print(f"  Top language by repos: {top_by_repos}")
    print(f"  Top language by bytes: {top_by_bytes}")
    print(f"  Top language by weighted: {top_by_weighted}")

    print(f"\nCreating visualizations (types: {', '.join(args.types)})...")
    visualizer = Visualizer(args.output, dark_mode=args.dark_mode, use_loc=args.loc)

    for viz_type in args.types:
        if viz_type == 'leaderboard':
            visualizer.create_all_leaderboards(
                username, by_repos, by_bytes, by_weighted,
                get_breakdown_fn=analyzer.get_top_contributing_repos,
                top_repos_count=args.top_repos
            )
        elif viz_type == 'bar':
            visualizer.create_bar_charts(
                username, by_repos, by_bytes, by_weighted
            )
        elif viz_type == 'horizontal-bar':
            visualizer.create_horizontal_bar_charts(
                username, by_repos, by_bytes, by_weighted
            )
        elif viz_type in ['pie', 'donut']:
            is_donut = viz_type == 'donut'
            visualizer.create_pie_charts(
                username, by_repos, by_bytes, by_weighted, donut=is_donut
            )

    print("\n" + "=" * 50)
    print("Analysis complete!")
    print(f"Check the '{args.output}' directory for your visualizations.")

if __name__ == '__main__':
    main()
