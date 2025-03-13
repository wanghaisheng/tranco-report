import logging
import sqlite3
import re
import requests
from bs4 import BeautifulSoup
from collections import Counter
import os
from datetime import datetime, timedelta

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_FILE = 'domain_rank.db'

def get_new_domains(time_period='week'):
    """获取指定时间段内新出现的域名."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if time_period == 'week':
        sql = """
            SELECT domain FROM domains WHERE first_seen >= DATE('now', 'weekday 0', '-7 days')
        """
    elif time_period == 'month':
        sql = """
            SELECT domain FROM domains WHERE first_seen >= DATE('now', 'start of month')
        """
    else:
        logging.error("Invalid time_period. Must be 'week' or 'month'.")
        return []

    cursor.execute(sql)
    new_domains = [row[0] for row in cursor.fetchall()]
    conn.close()
    return new_domains

def extract_domain_keywords(domains):
    """提取域名关键词."""
    keywords = []
    for domain in domains:
        try:
            domain_name = domain.split('.')[0]
            words = re.findall(r"[a-zA-Z0-9-]+", domain_name)
            keywords.extend(words)
        except Exception as e:
            logging.warning(f"Could not extract keywords from domain {domain}: {e}")
    return Counter(keywords)

def get_website_title(domain):
    """获取网站标题."""
    try:
        url = f"http://{domain}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)  # 设置超时
        response.raise_for_status()  # 检查是否有 HTTP 错误
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title').text
        return title
    except requests.exceptions.RequestException as e:
        logging.warning(f"Could not retrieve title for {domain}: {e}")
        return None
    except AttributeError:
        logging.warning(f"Could not find title tag for {domain}")
        return None

def extract_title_keywords(titles):
    """提取网站标题关键词."""
    # TODO: 使用 NLP 技术进行关键词提取 (例如 NLTK 或 spaCy)
    # 这里只做简单的空格分割
    keywords = []
    for title in titles:
        if title:
            keywords.extend(title.split())
    return Counter(keywords)

def analyze_domain_patterns(domains):
    """分析域名模式."""
    tlds = [domain.split('.')[-1] for domain in domains]
    return Counter(tlds)

def generate_report(time_period='week'):
    """生成报告."""
    logging.info(f"Generating {time_period}ly report...")

    # 获取新域名
    new_domains = get_new_domains(time_period=time_period)
    logging.info(f"New domains this {time_period}: {len(new_domains)}")

    # 提取域名关键词
    domain_keywords = extract_domain_keywords(new_domains)
    logging.info(f"Top domain keywords: {domain_keywords.most_common(10)}")

    # 获取网站标题
    titles = []
    for domain in new_domains[:10]:  # 只获取前 10 个域名以避免请求过多
        title = get_website_title(domain)
        titles.append(title)
        print(f"Title for {domain}: {title}")

    # 提取标题关键词
    title_keywords = extract_title_keywords(titles)
    logging.info(f"Top title keywords: {title_keywords.most_common(10)}")

    # 分析域名模式
    domain_patterns = analyze_domain_patterns(new_domains)
    logging.info(f"Domain patterns: {domain_patterns.most_common(5)}")

    logging.info(f"{time_period}ly report generated.")

if __name__ == "__main__":
    # 设置报告类型（'day', 'week', 'month'）
    report_type = 'week'

    # 根据报告类型生成不同的报告
    if report_type == 'day':
        generate_report(time_period = 'day') # 无法生成日报告，因为没有day的数据
    elif report_type == 'week':
        generate_report(time_period='week')
    elif report_type == 'month':
        generate_report(time_period='month')
    else:
        logging.error("Invalid report type. Must be 'day', 'week', or 'month'.")
