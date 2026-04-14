import json
import os
from io import BytesIO
from typing import List, Tuple, Union, Dict, Callable

import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import requests
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image


class Visualizer:
    def __init__(self, output_dir: str = 'output', dark_mode: bool = False, use_loc: bool = False,
                 badge_cache_dir: str = None):
        self.output_dir = output_dir
        self.badge_cache_dir = badge_cache_dir or os.path.join(output_dir, '.badge_cache')
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.badge_cache_dir, exist_ok=True)
        self.badge_cache = {}
        self.languages = self._load_languages()
        self.dark_mode = dark_mode
        self.volume_label = 'Lines of Code' if use_loc else 'Bytes of Code'
        self.volume_suffix = 'lines' if use_loc else 'bytes'
        self._setup_modern_style()

    def _setup_modern_style(self):
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Inter', 'Segoe UI', 'Arial', 'DejaVu Sans']
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.titleweight'] = 'bold'
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9

        if self.dark_mode:
            plt.rcParams['figure.facecolor'] = '#0d1117'
            plt.rcParams['axes.facecolor'] = '#161b22'
            plt.rcParams['axes.edgecolor'] = '#30363d'
            plt.rcParams['axes.labelcolor'] = '#e6edf3'
            plt.rcParams['text.color'] = '#e6edf3'
            plt.rcParams['xtick.color'] = '#e6edf3'
            plt.rcParams['ytick.color'] = '#e6edf3'
            plt.rcParams['grid.color'] = '#30363d'
        else:
            plt.rcParams['figure.facecolor'] = 'white'
            plt.rcParams['axes.facecolor'] = '#fafafa'
            plt.rcParams['axes.edgecolor'] = '#e0e0e0'
            plt.rcParams['grid.color'] = '#e0e0e0'

        plt.rcParams['axes.linewidth'] = 1.2
        plt.rcParams['grid.linestyle'] = '-'
        plt.rcParams['grid.linewidth'] = 0.8
        plt.rcParams['grid.alpha'] = 0.3

    @property
    def text_color(self) -> str:
        return '#e6edf3' if self.dark_mode else '#333333'

    @property
    def stroke_color(self) -> str:
        return '#0d1117' if self.dark_mode else 'white'

    @property
    def spine_color(self) -> str:
        return '#30363d' if self.dark_mode else '#d0d0d0'

    @property
    def figure_facecolor(self) -> str:
        return '#0d1117' if self.dark_mode else 'white'

    @property
    def donut_center_color(self) -> str:
        return '#161b22' if self.dark_mode else '#fafafa'

    @property
    def donut_edge_color(self) -> str:
        return '#30363d' if self.dark_mode else '#e0e0e0'

    def _load_languages(self) -> Dict:
        languages_path = os.path.join(os.path.dirname(__file__), 'languages.json')
        try:
            with open(languages_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            print(f"Warning: Could not load languages.json: {e}")
            return {}

    def _get_color(self, language: str) -> str:
        lang_config = self.languages.get(language, {})
        return lang_config.get('color', '#888888')

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

    def _get_badge_url(self, language: str) -> str:
        lang_config = self.languages.get(language, {})
        lang_name = language.replace(' ', '_')

        if lang_config and lang_config.get('badge_color'):
            color = lang_config['badge_color']
            logo = lang_config.get('logo')

            if logo:
                return (
                    f"https://img.shields.io/badge/{lang_name}-{color}.png"
                    f"?style=for-the-badge&logo={logo}&logoColor=white"
                )
            return (
                f"https://img.shields.io/badge/{lang_name}-{color}.png"
                f"?style=for-the-badge"
            )

        default_color = '888888'
        return (
            f"https://img.shields.io/badge/{lang_name}-{default_color}.png"
            f"?style=for-the-badge"
        )

    def _download_badge(self, language: str) -> Image.Image:
        if language in self.badge_cache:
            return self.badge_cache[language]

        safe_name = language.replace(' ', '_').replace('/', '_')
        badge_path = os.path.join(self.badge_cache_dir, f"{safe_name}.png")

        if os.path.exists(badge_path):
            try:
                img = Image.open(badge_path)
                self.badge_cache[language] = img
                return img
            except (OSError, ValueError):
                pass

        url = self._get_badge_url(language)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            img.save(badge_path)
            self.badge_cache[language] = img
            return img
        except (requests.RequestException, OSError, ValueError) as e:
            print(f"Warning: Could not download badge for {language}: {e}")
            return None

    def _format_number(self, num: Union[int, float]) -> str:
        if isinstance(num, float):
            return f'{num:.3f}'
        if num >= 1_000_000:
            return f'{num/1_000_000:.1f}M'
        if num >= 1_000:
            return f'{num/1_000:.1f}K'
        return str(num)

    def create_leaderboard(self, data: List[Tuple[str, Union[int, float]]],
                          title: str, filename: str, value_label: str):
        if not data:
            print(f"No data to visualize for {title}")
            return

        fig, ax = plt.subplots(figsize=(11, max(6, len(data) * 0.4)))

        languages = [item[0] for item in data]
        values = [item[1] for item in data]
        colors = [self._get_color(lang) for lang in languages]

        y_pos = range(len(languages))
        bars = ax.barh(y_pos, values, color=colors, edgecolor='white', linewidth=1,
                      alpha=0.9, height=0.7)

        for bar in bars:
            bar.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                 shadow_rgbFace='#00000015', alpha=0.3),
                                 path_effects.Normal()])

        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            label = self._format_number(value)
            text = ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {label}',
                   ha='left', va='center', fontweight='bold', fontsize=10, color=self.text_color)
            text.set_path_effects([path_effects.withStroke(linewidth=3, foreground=self.stroke_color)])

        for i, language in enumerate(languages):
            badge_img = self._download_badge(language)
            if badge_img:
                imagebox = OffsetImage(badge_img, zoom=0.35)
                ab = AnnotationBbox(imagebox, (-0.02, i), xycoords=('axes fraction', 'data'),
                                   box_alignment=(1, 0.5), frameon=False)
                ax.add_artist(ab)
            else:
                ax.text(-0.02, i, language, ha='right', va='center',
                       transform=ax.get_yaxis_transform(), fontsize=10, fontweight='bold')

        ax.set_yticks(y_pos)
        ax.set_yticklabels([''] * len(languages))
        ax.invert_yaxis()
        ax.set_xlabel(value_label, fontsize=13, fontweight='bold', color=self.text_color)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(self.spine_color)
        ax.grid(axis='x', alpha=0.25, linestyle='-', zorder=0)
        ax.set_axisbelow(True)

        plt.tight_layout()
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.figure_facecolor)
        plt.close()

        print(f"Saved: {output_path}")

    def create_leaderboard_with_breakdown(self, data: List[Tuple[str, Union[int, float]]],
                                          title: str, filename: str, value_label: str,
                                          get_breakdown: Callable[[str], List[Tuple[str, int]]],
                                          top_repos_count: int = 5):
        if not data:
            print(f"No data to visualize for {title}")
            return

        fig, ax = plt.subplots(figsize=(11, max(6, len(data) * 0.4)))

        languages = [item[0] for item in data]
        values = [item[1] for item in data]
        base_colors = [self._get_color(lang) for lang in languages]

        y_pos = range(len(languages))

        for i, language in enumerate(languages):
            top_repos = get_breakdown(language, top_repos_count)

            if top_repos:
                left = 0
                base_color = base_colors[i]

                for j, (repo, lines) in enumerate(top_repos):
                    alpha = 1.0 - (j * 0.15)
                    alpha = max(alpha, 0.4)

                    bar = ax.barh(i, lines, left=left, height=0.7,
                                color=base_color, alpha=alpha,
                                edgecolor='white', linewidth=0.8)

                    for patch in bar:
                        patch.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                               shadow_rgbFace='#00000015', alpha=0.3),
                                               path_effects.Normal()])

                    left += lines

                if left < values[i]:
                    remaining = values[i] - left
                    bar = ax.barh(i, remaining, left=left, height=0.7,
                                color=base_color, alpha=0.25,
                                edgecolor='white', linewidth=0.8)

                    for patch in bar:
                        patch.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                               shadow_rgbFace='#00000015', alpha=0.3),
                                               path_effects.Normal()])
            else:
                bar = ax.barh(i, values[i], height=0.7,
                            color=base_colors[i], alpha=0.9,
                            edgecolor='white', linewidth=1)

                for patch in bar:
                    patch.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                           shadow_rgbFace='#00000015', alpha=0.3),
                                           path_effects.Normal()])

        for i, value in enumerate(values):
            label = self._format_number(value)
            text = ax.text(value, i,
                   f' {label}',
                   ha='left', va='center', fontweight='bold', fontsize=10, color=self.text_color)
            text.set_path_effects([path_effects.withStroke(linewidth=3, foreground=self.stroke_color)])

        for i, language in enumerate(languages):
            badge_img = self._download_badge(language)
            if badge_img:
                imagebox = OffsetImage(badge_img, zoom=0.35)
                ab = AnnotationBbox(imagebox, (-0.02, i), xycoords=('axes fraction', 'data'),
                                   box_alignment=(1, 0.5), frameon=False)
                ax.add_artist(ab)
            else:
                ax.text(-0.02, i, language, ha='right', va='center',
                       transform=ax.get_yaxis_transform(), fontsize=10, fontweight='bold')

        ax.set_yticks(y_pos)
        ax.set_yticklabels([''] * len(languages))
        ax.invert_yaxis()
        ax.set_xlabel(value_label, fontsize=13, fontweight='bold', color=self.text_color)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(self.spine_color)
        ax.grid(axis='x', alpha=0.25, linestyle='-', zorder=0)
        ax.set_axisbelow(True)

        plt.tight_layout()
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.figure_facecolor)
        plt.close()

        print(f"Saved: {output_path}")

    def create_all_leaderboards(self, username: str, by_repos: List[Tuple[str, int]],
                               by_bytes: List[Tuple[str, int]],
                               by_weighted: List[Tuple[str, float]],
                               get_breakdown_fn: Callable[[str], List[Tuple[str, int]]] = None,
                               top_repos_count: int = 5):
        self.create_leaderboard(
            by_repos,
            f'{username} - Language Leaderboard by Repository Count',
            'leaderboard_by_repos.png',
            'Number of Repositories'
        )

        if get_breakdown_fn:
            self.create_leaderboard_with_breakdown(
                by_bytes,
                f'{username} - Language Leaderboard by {self.volume_label} (with Top Contributing Repos)',
                f'leaderboard_by_{self.volume_suffix}.png',
                self.volume_label,
                get_breakdown_fn,
                top_repos_count
            )
        else:
            self.create_leaderboard(
                by_bytes,
                f'{username} - Language Leaderboard by {self.volume_label}',
                f'leaderboard_by_{self.volume_suffix}.png',
                self.volume_label
            )

        self.create_leaderboard(
            by_weighted,
            f'{username} - Language Leaderboard by Weighted Score',
            'leaderboard_by_weighted.png',
            'Weighted Score (Normalized)'
        )

    def create_bar_charts(self, username: str, by_repos: List[Tuple[str, int]],
                         by_bytes: List[Tuple[str, int]],
                         by_weighted: List[Tuple[str, float]]):
        self._create_vertical_bar(
            by_repos,
            f'{username} - Languages by Repository Count',
            'bar_by_repos.png',
            'Repository Count'
        )
        self._create_vertical_bar(
            by_bytes,
            f'{username} - Languages by {self.volume_label}',
            f'bar_by_{self.volume_suffix}.png',
            self.volume_label
        )
        self._create_vertical_bar(
            by_weighted,
            f'{username} - Languages by Weighted Score',
            'bar_by_weighted.png',
            'Weighted Score'
        )

    def _create_vertical_bar(self, data: List[Tuple[str, Union[int, float]]],
                            title: str, filename: str, value_label: str):
        if not data:
            print(f"No data to visualize for {title}")
            return

        top_n = min(12, len(data))
        data = data[:top_n]

        fig, ax = plt.subplots(figsize=(10, 6))

        languages = [item[0] for item in data]
        values = [item[1] for item in data]
        colors = [self._get_color(lang) for lang in languages]

        x_pos = range(len(languages))
        bars = ax.bar(x_pos, values, color=colors, edgecolor='white', linewidth=1,
                     alpha=0.9, width=0.7)

        for bar in bars:
            bar.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                 shadow_rgbFace='#00000015', alpha=0.3),
                                 path_effects.Normal()])

        for bar, value in zip(bars, values):
            height = bar.get_height()
            label = self._format_number(value)
            text = ax.text(bar.get_x() + bar.get_width()/2, height,
                   label, ha='center', va='bottom', fontweight='bold', fontsize=9,
                   color=self.text_color)
            text.set_path_effects([path_effects.withStroke(linewidth=2, foreground=self.stroke_color)])

        ax.set_xticks(x_pos)
        ax.set_xticklabels(languages, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel(value_label, fontsize=11, fontweight='bold', color=self.text_color)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.spine_color)
        ax.spines['bottom'].set_color(self.spine_color)
        ax.grid(axis='y', alpha=0.25, linestyle='-', zorder=0)
        ax.set_axisbelow(True)

        plt.tight_layout()
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.figure_facecolor)
        plt.close()

        print(f"Saved: {output_path}")

    def create_horizontal_bar_charts(self, username: str, by_repos: List[Tuple[str, int]],
                                     by_bytes: List[Tuple[str, int]],
                                     by_weighted: List[Tuple[str, float]]):
        self._create_simple_horizontal_bar(
            by_repos,
            f'{username} - Languages by Repository Count',
            'horizontal_bar_by_repos.png',
            'Repository Count'
        )
        self._create_simple_horizontal_bar(
            by_bytes,
            f'{username} - Languages by {self.volume_label}',
            f'horizontal_bar_by_{self.volume_suffix}.png',
            self.volume_label
        )
        self._create_simple_horizontal_bar(
            by_weighted,
            f'{username} - Languages by Weighted Score',
            'horizontal_bar_by_weighted.png',
            'Weighted Score'
        )

    def _create_simple_horizontal_bar(self, data: List[Tuple[str, Union[int, float]]],
                                      title: str, filename: str, value_label: str):
        if not data:
            print(f"No data to visualize for {title}")
            return

        top_n = min(15, len(data))
        data = data[:top_n]

        fig, ax = plt.subplots(figsize=(10, max(6, len(data) * 0.35)))

        languages = [item[0] for item in data]
        values = [item[1] for item in data]
        colors = [self._get_color(lang) for lang in languages]

        y_pos = range(len(languages))
        bars = ax.barh(y_pos, values, color=colors, edgecolor='white', linewidth=1,
                      alpha=0.9, height=0.65)

        for bar in bars:
            bar.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                 shadow_rgbFace='#00000015', alpha=0.3),
                                 path_effects.Normal()])

        for bar, value in zip(bars, values):
            width = bar.get_width()
            label = self._format_number(value)
            text = ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {label}', ha='left', va='center', fontweight='bold',
                   fontsize=9, color=self.text_color)
            text.set_path_effects([path_effects.withStroke(linewidth=2, foreground=self.stroke_color)])

        for i, language in enumerate(languages):
            badge_img = self._download_badge(language)
            if badge_img:
                imagebox = OffsetImage(badge_img, zoom=0.3)
                ab = AnnotationBbox(imagebox, (-0.02, i), xycoords=('axes fraction', 'data'),
                                   box_alignment=(1, 0.5), frameon=False)
                ax.add_artist(ab)
            else:
                ax.text(-0.02, i, language, ha='right', va='center',
                       transform=ax.get_yaxis_transform(), fontsize=9,
                       fontweight='bold', color=self.text_color)

        ax.set_yticks(y_pos)
        ax.set_yticklabels([''] * len(languages))
        ax.invert_yaxis()
        ax.set_xlabel(value_label, fontsize=11, fontweight='bold', color=self.text_color)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(self.spine_color)
        ax.grid(axis='x', alpha=0.25, linestyle='-', zorder=0)
        ax.set_axisbelow(True)

        plt.tight_layout()
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.figure_facecolor)
        plt.close()

        print(f"Saved: {output_path}")

    def create_pie_charts(self, username: str, by_repos: List[Tuple[str, int]],
                         by_bytes: List[Tuple[str, int]],
                         by_weighted: List[Tuple[str, float]],
                         donut: bool = False):
        chart_type = 'donut' if donut else 'pie'
        self._create_pie_chart(
            by_repos,
            f'{username} - Languages by Repository Count',
            f'{chart_type}_by_repos.png',
            donut
        )
        self._create_pie_chart(
            by_bytes,
            f'{username} - Languages by {self.volume_label}',
            f'{chart_type}_by_{self.volume_suffix}.png',
            donut
        )
        self._create_pie_chart(
            by_weighted,
            f'{username} - Languages by Weighted Score',
            f'{chart_type}_by_weighted.png',
            donut
        )

    def _create_pie_chart(self, data: List[Tuple[str, Union[int, float]]],
                         title: str, filename: str, donut: bool = False):
        if not data:
            print(f"No data to visualize for {title}")
            return

        top_n = min(8, len(data))
        top_data = data[:top_n]

        if len(data) > top_n:
            other_value = sum(item[1] for item in data[top_n:])
            top_data.append(('Other', other_value))

        fig, ax = plt.subplots(figsize=(9, 7))

        languages = [item[0] for item in top_data]
        values = [item[1] for item in top_data]
        colors = [self._get_color(lang) if lang != 'Other' else '#d0d0d0' for lang in languages]

        def autopct_format(pct):
            return f'{pct:.1f}%' if pct > 3 else ''

        wedges, texts, autotexts = ax.pie(
            values,
            labels=languages,
            colors=colors,
            autopct=autopct_format,
            startangle=90,
            pctdistance=0.82 if donut else 0.65,
            wedgeprops={'width': 0.4 if donut else 1, 'edgecolor': 'white',
                       'linewidth': 1, 'alpha': 0.9},
            textprops={'fontweight': 'bold', 'fontsize': 9}
        )

        for wedge in wedges:
            wedge.set_path_effects([path_effects.SimplePatchShadow(offset=(1, -1),
                                   shadow_rgbFace='#00000020', alpha=0.3),
                                   path_effects.Normal()])

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
            autotext.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#00000050')])

        if donut:
            centre_circle = plt.Circle((0, 0), 0.60, fc=self.donut_center_color,
                                      ec=self.donut_edge_color, linewidth=1)
            fig.gca().add_artist(centre_circle)

        plt.tight_layout()
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=self.figure_facecolor)
        plt.close()

        print(f"Saved: {output_path}")
