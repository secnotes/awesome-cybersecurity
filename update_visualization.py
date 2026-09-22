'''
Author: Security Notes (github.com/secnotes)
Version: 1.0
Date: 2026-09-21
Description: Regenerate the two README data-visualization charts from awesome_security_repo.csv
描述: 根据 awesome_security_repo.csv 重新生成 README 中引用的两张数据可视化图
输出:
  - images/top_repositories.png   按 star 统计的 Top 20 仓库占比饼图
  - images/trend_repositories.png  按创建年份统计的仓库数量趋势
用法: python3 update_visualization.py
'''

import os
import sys

import pandas as pd
import matplotlib

matplotlib.use('Agg')  # 非交互后端，无需显示器
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# 统一配色
BAR_COLOR = '#3b82f6'
TEXT_COLOR = '#1f2937'
MUTED_COLOR = '#6b7280'
GRID_COLOR = '#e5e7eb'

# 饼图: 蓝色有序色阶 (浅->深, 已经官方调色板校验 --ordinal 通过),
# 名次越靠前颜色越深; Other 切片用中性灰
PIE_RAMP = ['#86b6ef', '#61a0ea', '#3987e5', '#2871ca',
            '#1c5cab', '#14488b', '#0d366b']
OTHER_COLOR = MUTED_COLOR
NAMED_SLICES = 7  # Top 20 中前 N 名单独成切片，其余合并为 Other

# 仓库根目录 (脚本可在任意 cwd 下运行)
ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(ROOT, 'awesome_security_repo.csv')
IMAGES_DIR = os.path.join(ROOT, 'images')
TOP_IMG = os.path.join(IMAGES_DIR, 'top_repositories.png')
TREND_IMG = os.path.join(IMAGES_DIR, 'trend_repositories.png')

TOP_N = 20


def load_data():
    '''读取 CSV (utf-8-sig 以处理 BOM) 并做基本清洗'''
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')

    # 数值化关键列
    df['star'] = pd.to_numeric(df['star'], errors='coerce')
    df['created_time'] = pd.to_numeric(df['created_time'], errors='coerce')

    # 丢弃关键字段缺失的行
    df = df.dropna(subset=['star', 'created_time'])
    df['created_year'] = df['created_time'].astype(int)

    return df


def plot_top_repositories(df):
    '''Top N 仓库按 star 占比画环形饼图: 前几名独立切片，尾部合并 Other'''
    top = df.sort_values('star', ascending=False).head(TOP_N)
    labels = (top['user'] + '/' + top['name']).tolist()
    stars = top['star'].astype(int).tolist()

    # 聚合: 前 NAMED_SLICES 名 + Other
    named_labels = labels[:NAMED_SLICES]
    named_stars = stars[:NAMED_SLICES]
    tail_labels = labels[NAMED_SLICES:]
    tail_stars = stars[NAMED_SLICES:]
    other_stars = sum(tail_stars)

    values = named_stars + [other_stars]
    # 名次越靠前颜色越深; Other 用灰色
    colors = PIE_RAMP[:NAMED_SLICES][::-1] + [OTHER_COLOR]

    fig, ax = plt.subplots(figsize=(14, 8), dpi=150)

    _, _, autotexts = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        autopct=lambda p: f'{p:.1f}%',
        pctdistance=0.79,
        wedgeprops={'width': 0.42, 'edgecolor': 'white', 'linewidth': 2},
        textprops={'color': TEXT_COLOR, 'fontsize': 10},
    )
    # 百分比文字: 浅色切片用深字、深色切片用白字, 保证可读
    light_slices = {'#86b6ef', '#61a0ea', '#3987e5'}
    for text, color in zip(autotexts, colors):
        text.set_color(TEXT_COLOR if color in light_slices else 'white')
        text.set_fontsize(10)
        text.set_fontweight('bold')

    # 环心: Top N 总 star 数
    total = sum(values)
    ax.text(0, 0.06, f'Top {TOP_N}', ha='center', va='center',
            fontsize=14, color=TEXT_COLOR, fontweight='bold')
    ax.text(0, -0.09, f'{total:,} stars', ha='center', va='center',
            fontsize=12, color=MUTED_COLOR)

    fig.suptitle(f'Top {TOP_N} Awesome Cybersecurity Repositories by Stars',
                 fontsize=16, color=TEXT_COLOR, y=0.97, fontweight='bold')

    # 图例: 独立切片 + Other + 尾部全部仓库 (无色块, 弱化缩进显示)
    n_tail = len(tail_labels)
    handles = [
        Patch(facecolor=c, edgecolor='white',
              label=f'{lab}  {s:,}')
        for c, lab, s in zip(colors[:NAMED_SLICES], named_labels, named_stars)
    ]
    handles.append(Patch(facecolor=OTHER_COLOR, edgecolor='white',
                         label=f'Other ({n_tail} repositories)  {other_stars:,}'))
    handles.extend(
        Line2D([0], [0], marker='', linestyle='',
               label=f'   {lab}  {s:,}')
        for lab, s in zip(tail_labels, tail_stars)
    )
    legend = fig.legend(
        handles=handles,
        loc='center left',
        bbox_to_anchor=(0.72, 0.5),
        fontsize=9,
        frameon=False,
        handlelength=1.4,
        handleheight=1.1,
    )
    # 尾部条目弱化
    for text in legend.get_texts()[-n_tail:]:
        text.set_color(MUTED_COLOR)
        text.set_fontsize(8.5)

    ax.axis('equal')
    fig.tight_layout(rect=[0, 0, 0.7, 0.95])
    fig.savefig(TOP_IMG)
    plt.close(fig)
    print(f'✅ 已生成 {TOP_IMG} ({NAMED_SLICES} 个独立切片 + '
          f'Other/{n_tail}, 共 {TOP_N} 个仓库)')


def plot_trend(df):
    '''按创建年份统计仓库数量趋势'''
    counts = df['created_year'].value_counts().sort_index()
    years = counts.index.tolist()
    values = counts.values.tolist()

    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

    bars = ax.bar([str(y) for y in years], values,
                  color=BAR_COLOR, edgecolor='white', width=0.7)

    ax.set_xlabel('Created Year', fontsize=12, color=TEXT_COLOR)
    ax.set_ylabel('Number of Repositories', fontsize=12, color=TEXT_COLOR)
    ax.set_title('Awesome Cybersecurity Repositories Created per Year',
                 fontsize=16, color=TEXT_COLOR, pad=15, fontweight='bold')

    ymax = max(values)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + ymax * 0.015,
                str(value),
                ha='center', va='bottom', fontsize=10, color=TEXT_COLOR)

    ax.set_ylim(0, ymax * 1.15)
    ax.grid(axis='y', color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='both', labelsize=10, colors=TEXT_COLOR)

    fig.tight_layout()
    fig.savefig(TREND_IMG)
    plt.close(fig)
    print(f'✅ 已生成 {TREND_IMG} ({len(years)} 个年份, '
          f'{sum(values)} 个仓库)')


def main():
    if not os.path.exists(CSV_PATH):
        print(f'❌ 找不到 CSV: {CSV_PATH}', file=sys.stderr)
        sys.exit(1)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    print('=' * 50)
    print('Awesome Cybersecurity Visualization Updater v1.0')
    print('=' * 50)

    df = load_data()
    print(f'📊 已加载 {len(df)} 个仓库记录')

    plot_top_repositories(df)
    plot_trend(df)

    print('\n完成。README 中的数据可视化图已更新。')


if __name__ == '__main__':
    main()
