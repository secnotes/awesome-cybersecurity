'''
Author: Security Notes (github.com/secnotes)
Version: 2.0
Date: 2026-09-21
Description: Fetch repository data directly via the GitHub Search API
描述: 使用 GitHub Search API 直接获取仓库信息
优化点:
1. 直接使用 GitHub Search API，一次请求获取完整信息
2. 无需额外请求获取创建时间
3. 添加进度显示
4. 支持可选的 GitHub Token
5. 如需代理，设置 HTTPS_PROXY 环境变量即可（requests 原生支持）
6. 保留中文描述的项目，仅过滤描述超过300字的项目
Rate Limits:
- 未认证: 10 requests/minute, 60 requests/hour
- 认证: 30 requests/minute, 5000 requests/hour
Reference:
https://docs.github.com/en/rest/search/search
'''

import requests
import csv
import time
import sys
import random
import os

class GitHubRepoCrawler:
    def __init__(self, token=None):
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'

        self.base_url = 'https://api.github.com/search/repositories'

    def _do_request(self, params):
        """
        执行请求
        :param params: 请求参数
        :return: response 或 None
        """
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            return response
        except requests.exceptions.ProxyError:
            raise Exception("代理连接失败")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接失败")
        except requests.exceptions.Timeout:
            raise Exception("请求超时")
        except Exception as e:
            raise Exception(f"请求异常: {e}")

    def search(self, keyword, page=1, per_page=100, min_stars=10):
        """
        搜索仓库
        :param keyword: 搜索关键词
        :param page: 页码 (1-10 for authenticated, 1-1 for unauthenticated)
        :param per_page: 每页数量 (max 100)
        :param min_stars: 最小 star 数
        :return: 仓库列表
        """
        # 构建查询: 关键词 + star 数筛选
        query = f'{keyword} stars:>={min_stars}'

        params = {
            'q': query,
            'sort': 'stars',  # 按 star 排序
            'order': 'desc',
            'per_page': per_page,
            'page': page,
        }

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self._do_request(params)

                # 检查速率限制
                if response.status_code == 403:
                    reset_time = response.headers.get('X-RateLimit-Reset', 0)
                    wait_time = max(int(reset_time) - int(time.time()), 60)
                    print(f"  ⚠️ 速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time + 5)
                    continue

                if response.status_code == 429:
                    print(f"  ⚠️ 请求过多，等待 60 秒...")
                    time.sleep(60)
                    continue

                if response.status_code != 200:
                    print(f"  ❌ 错误: HTTP {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(random.randint(5, 10))
                        continue
                    return None

                data = response.json()
                return data.get('items', [])

            except Exception as e:
                error_msg = str(e)
                print(f"  ⚠️ {error_msg}")

                # 请求失败，进行重试
                if attempt < max_retries - 1:
                    wait_time = random.randint(3, 8)
                    print(f"  💤 等待 {wait_time} 秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                return None

        return None

    def crawl_all(self, keywords, max_pages=10, per_page=100, min_stars=10):
        """
        爬取所有关键词的仓库
        """
        all_repos = []
        seen_ids = set()

        for keyword in keywords:
            print(f"\n🔍 搜索关键词: '{keyword}'")

            for page in range(1, max_pages + 1):
                print(f"  📄 第 {page}/{max_pages} 页...", end=' ')

                repos = self.search(keyword, page=page, per_page=per_page, min_stars=min_stars)

                if repos is None:
                    print("失败")
                    continue

                if len(repos) == 0:
                    print("无结果，停止此关键词")
                    break

                new_count = 0
                filtered_count = 0
                for repo in repos:
                    repo_id = repo['id']

                    if repo_id not in seen_ids:
                        seen_ids.add(repo_id)

                        # 处理描述
                        description = (repo['description'] or '').replace('\n', ' ').replace('\r', '').strip()

                        # 过滤条件：描述超过300字（中文项目正常保留）
                        if len(description) > 300:
                            filtered_count += 1
                            continue

                        new_count += 1

                        all_repos.append({
                            'id': repo_id,
                            'name': repo['name'],
                            'user': repo['owner']['login'],
                            'description': description,
                            'star': repo['stargazers_count'],
                            'update time': repo['updated_at'],
                            'url': repo['html_url'],
                            'created_time': float(repo['created_at'][:4]),
                        })

                print(f"获取 {len(repos)} 个仓库, 新增 {new_count} 个, 过滤 {filtered_count} 个")

                # 未认证模式下，每页请求后等待避免速率限制
                if not self.token:
                    wait = random.randint(8, 12)
                    print(f"  💤 等待 {wait} 秒 (未认证模式限制)")
                    time.sleep(wait)
                else:
                    # 认证模式也需要适度等待
                    time.sleep(random.randint(1, 3))

        # 按 star 排序
        all_repos.sort(key=lambda x: x['star'], reverse=True)

        return all_repos

    def save_to_csv(self, repos, filename):
        """
        保存到 CSV 文件
        """
        headers = ['id', 'name', 'user', 'description', 'star', 'update time', 'url', 'created_time']

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, headers)
            writer.writeheader()
            writer.writerows(repos)

        print(f"\n✅ 已保存 {len(repos)} 个仓库到 {filename}")


def main():
    if len(sys.argv) <= 1:
        print('<usage>: python reptile_security.py [output.csv]')
        sys.exit(1)

    # 配置
    # 优先从环境变量读取 (CI 会自动注入 GITHUB_TOKEN)，本地可留空走未认证模式
    token = os.environ.get('GITHUB_TOKEN', '').strip()  # 可选: 也可在这里硬编码 GitHub Token
    keywords = ['awesome-security', 'awesome_cybersecurity']
    max_pages = 5   # 每个关键词最多爬取页数 (每页100条)
    per_page = 100
    min_stars = 10

    print("=" * 50)
    print("GitHub Security Repositories Crawler v2.0")
    print("=" * 50)
    print(f"关键词: {keywords}")
    print(f"最小 stars: {min_stars}")
    print(f"每页数量: {per_page}")
    print(f"最大页数: {max_pages}")
    print(f"认证: {'是' if token else '否 (60次/小时限制)'}")
    print("=" * 50)

    crawler = GitHubRepoCrawler(token=token)
    repos = crawler.crawl_all(
        keywords=keywords,
        max_pages=max_pages,
        per_page=per_page,
        min_stars=min_stars,
    )

    if repos:
        crawler.save_to_csv(repos, sys.argv[1])

        # 统计信息
        print("\n📊 统计信息:")
        print(f"  总仓库数: {len(repos)}")
        print(f"  最高 star: {repos[0]['name']} ({repos[0]['star']} stars)")
        print(f"  最新更新: {repos[0]['update time'][:10]}")
    else:
        print("\n❌ 未获取到数据")


if __name__ == '__main__':
    main()