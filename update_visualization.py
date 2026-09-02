'''
Author: Sec Notes
Version: 1.0
Date: 2026-09-01
Description: 根据 awesome_security_repo.csv 重新生成 README 中引用的两张数据可视化图
输出:
  - images/top_repositories.png   按 star 排序的 Top 20 仓库
  - images/trend_repositories.png  按创建年份统计的仓库数量趋势
用法: python3 update_visualization.py
'''

import os
import sys

import pandas as pd
import matplotlib

matplotlib.use('Agg')  # 非交互后端，无需显示器
import matplotlib.pyplot as plt

# 统一配色
BAR_COLOR = '#3b82f6'
ACCENT_COLOR = '#1d4ed8'
TEXT_COLOR = '#1f2937'
GRID_COLOR = '#e5e7eb'

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
    '''Top N 仓库按 star 横向条形图'''
    top = df.sort_values('star', ascending=False).head(TOP_N).iloc[::-1]
    labels = (top['user'] + '/' + top['name']).tolist()
    stars = top['star'].astype(int).tolist()

    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)

    bars = ax.barh(labels, stars, color=BAR_COLOR, edgecolor='white', height=0.7)

    ax.set_xlabel('Stars', fontsize=12, color=TEXT_COLOR)
    # 标题相对整张图居中 (set_title 居中于绘图区, 长标签会使其偏左)
    fig.suptitle(f'Top {TOP_N} Awesome Cybersecurity Repositories by Stars',
                 fontsize=16, color=TEXT_COLOR, y=0.98, fontweight='bold')

    # 数值标注
    xmax = max(stars)
    for bar, value in zip(bars, stars):
        ax.text(bar.get_width() + xmax * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'{value:,}',
                va='center', ha='left', fontsize=9, color=TEXT_COLOR)

    ax.set_xlim(0, xmax * 1.12)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.grid(axis='x', color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='y', labelsize=9, colors=TEXT_COLOR)
    ax.tick_params(axis='x', labelsize=10, colors=TEXT_COLOR)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(TOP_IMG)
    plt.close(fig)
    print(f'✅ 已生成 {TOP_IMG} ({len(top)} 个仓库)')


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
