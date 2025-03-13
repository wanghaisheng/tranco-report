import csv
import logging
import os
from datetime import datetime
import sqlite3
import zipfile
import codecs

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_FILE = 'domain_rank.db'
ZIP_FILE = 'tranco.zip'
CSV_FILE_NAME = 'top-1m.csv'

def create_database():
    """创建数据库和表."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 创建 domains 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            domain TEXT PRIMARY KEY,
            first_seen DATE,
            last_seen DATE,
            total_rank_sum INTEGER DEFAULT 0,
            rank_count INTEGER DEFAULT 0
        )
    """)

    # 创建 daily_ranks 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_ranks (
            domain TEXT,
            date DATE,
            rank INTEGER,
            FOREIGN KEY (domain) REFERENCES domains(domain),
            PRIMARY KEY (domain, date)
        )
    """)

    conn.commit()
    conn.close()
    logging.info("Database and tables created/verified.")

def update_database(zip_file):
    """更新数据库."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            with z.open(CSV_FILE_NAME, 'r') as csvfile:
                reader = csv.reader(codecs.getreader("utf-8")(csvfile))
                data = list(reader)

        for row in data[1:]:  # skip header
            if len(row) == 2:
                try:
                    rank = int(row[0].strip())
                    domain = row[1].strip()

                    # 更新或插入域名
                    cursor.execute("""
                        INSERT INTO domains (domain, first_seen, last_seen, total_rank_sum, rank_count)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(domain) DO UPDATE SET
                            last_seen = ?,
                            total_rank_sum = total_rank_sum + ?,
                            rank_count = rank_count + 1
                    """, (domain, today, today, rank, 1, today, rank))

                    # 插入每日排名
                    cursor.execute("""
                        INSERT OR REPLACE INTO daily_ranks (domain, date, rank)
                        VALUES (?, ?, ?)
                    """, (domain, today, rank))

                except (ValueError, IndexError) as e:
                    logging.warning(f"Could not process row {row}: {e}")

        conn.commit()
        logging.info("Database updated successfully.")

    except FileNotFoundError:
        logging.error(f"Zip file not found: {zip_file}")
    except Exception as e:
        logging.error(f"Error processing zip file: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    """主函数."""
    # 确保 data 目录存在
    if not os.path.exists("data"):
        os.makedirs("data")

    # 下载 zip 文件
    zip_file_path = os.path.join("data", ZIP_FILE)

    if not os.path.exists(zip_file_path):
        logging.info(f"Downloading {ZIP_FILE}...")
        os.system(f"wget https://tranco-list.eu/top-1m.csv.zip -O {zip_file_path}")
        logging.info(f"{ZIP_FILE} downloaded successfully.")

    # 创建数据库
    create_database()

    # 更新数据库
    update_database(zip_file_path)
