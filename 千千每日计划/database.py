# database.py
# 负责所有数据库操作 (已更新)

import sqlite3
from PyQt6.QtCore import QTime


class DatabaseManager:
    """
    管理SQLite数据库的连接和操作。
    """

    def __init__(self, db_name="daily_planner.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS time_slots
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                week_start_date
                                TEXT
                                NOT
                                NULL,
                                start_time
                                TEXT
                                NOT
                                NULL,
                                end_time
                                TEXT
                                NOT
                                NULL,
                                row_span
                                INTEGER
                                NOT
                                NULL
                                DEFAULT
                                1
                            )
                            """)
        self.cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_time_slot ON time_slots(week_start_date, start_time)")

        # 增加 plan_type 字段: normal, rest, empty
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS plans
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                plan_date
                                TEXT
                                NOT
                                NULL,
                                time_slot_id
                                INTEGER
                                NOT
                                NULL,
                                plan_text
                                TEXT,
                                status
                                INTEGER
                                NOT
                                NULL
                                DEFAULT
                                0,
                                row_span
                                INTEGER
                                NOT
                                NULL
                                DEFAULT
                                1,
                                plan_type
                                TEXT
                                NOT
                                NULL
                                DEFAULT
                                'normal',
                                FOREIGN
                                KEY
                            (
                                time_slot_id
                            ) REFERENCES time_slots
                            (
                                id
                            ) ON DELETE CASCADE,
                                UNIQUE
                            (
                                plan_date,
                                time_slot_id
                            )
                                )
                            """)

        # 新增：用于存储每日特定时间段合并信息的表
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS day_specific_merges
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                plan_date
                                TEXT
                                NOT
                                NULL,
                                start_slot_id
                                INTEGER
                                NOT
                                NULL,
                                row_span
                                INTEGER
                                NOT
                                NULL,
                                UNIQUE
                            (
                                plan_date,
                                start_slot_id
                            )
                                )
                            """)

        self.conn.commit()

    def add_time_slot(self, start_time, end_time, week_start_date):
        try:
            self.cursor.execute("INSERT INTO time_slots (start_time, end_time, week_start_date) VALUES (?, ?, ?)",
                                (start_time, end_time, week_start_date))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"周 {week_start_date} 的时间段 {start_time}-{end_time} 已存在。")

    def get_time_slots(self, week_start_date, include_hidden=False):
        query = "SELECT id, start_time, end_time, row_span FROM time_slots WHERE week_start_date = ?"
        if not include_hidden:
            query += " AND row_span > 0"
        query += " ORDER BY start_time"

        self.cursor.execute(query, (week_start_date,))
        return self.cursor.fetchall()

    def delete_time_slot(self, slot_id):
        self.cursor.execute("DELETE FROM time_slots WHERE id = ?", (slot_id,))
        self.conn.commit()

    def add_plan(self, date, time_slot_id, text, status, plan_type='normal'):
        try:
            self.cursor.execute("""
                                INSERT INTO plans (plan_date, time_slot_id, plan_text, status, plan_type)
                                VALUES (?, ?, ?, ?, ?)
                                """, (date, time_slot_id, text, status, plan_type))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_plan(self, date, time_slot_id):
        self.cursor.execute("""
                            SELECT id, plan_text, status, row_span, plan_type
                            FROM plans
                            WHERE plan_date = ?
                              AND time_slot_id = ?
                            """, (date, time_slot_id))
        return self.cursor.fetchone()

    def get_plans_for_date(self, date):
        self.cursor.execute("""
                            SELECT p.id, ts.start_time, p.plan_text, p.status
                            FROM plans p
                                     JOIN time_slots ts ON p.time_slot_id = ts.id
                            WHERE p.plan_date = ?
                            ORDER BY ts.start_time
                            """, (date,))
        return self.cursor.fetchall()

    def get_plans_for_export(self, start_date, end_date):
        self.cursor.execute("""
                            SELECT p.plan_date,
                                   p.plan_text,
                                   p.row_span,
                                   p.time_slot_id,
                                   ts.week_start_date
                            FROM plans p
                                     JOIN time_slots ts ON p.time_slot_id = ts.id
                            WHERE p.plan_date BETWEEN ? AND ?
                              AND p.plan_type = 'normal'
                              AND p.plan_text IS NOT NULL
                              AND p.plan_text != ''
                            ORDER BY p.plan_date, ts.start_time
                            """, (start_date, end_date))
        plans_to_process = self.cursor.fetchall()

        week_slots_cache = {}
        self.cursor.execute("SELECT id, week_start_date, start_time, end_time FROM time_slots ORDER BY start_time")
        for slot_id, week_start, start_t, end_t in self.cursor.fetchall():
            if week_start not in week_slots_cache:
                week_slots_cache[week_start] = []
            week_slots_cache[week_start].append({'id': slot_id, 'start_time': start_t, 'end_time': end_t})

        results = []
        for plan_date, plan_text, row_span, time_slot_id, week_start_date in plans_to_process:
            if week_start_date not in week_slots_cache:
                continue

            week_slots = week_slots_cache[week_start_date]

            start_index = -1
            for i, slot in enumerate(week_slots):
                if slot['id'] == time_slot_id:
                    start_index = i
                    break

            if start_index == -1:
                continue

            start_time = week_slots[start_index]['start_time']

            end_index = start_index + row_span - 1

            if end_index < len(week_slots):
                end_time = week_slots[end_index]['end_time']
                results.append((plan_date, start_time, end_time, plan_text))
            else:
                end_time = week_slots[-1]['end_time']
                results.append((plan_date, start_time, end_time, plan_text))
                print(f"警告: 日期 {plan_date} 的计划合并跨度超出了范围。")

        return results

    def update_plan_content(self, plan_id, text, status):
        self.cursor.execute("UPDATE plans SET plan_text = ?, status = ? WHERE id = ?", (text, status, plan_id))
        self.conn.commit()

    def update_plan_type(self, plan_id, plan_type):
        self.cursor.execute("UPDATE plans SET plan_type = ? WHERE id = ?", (plan_type, plan_id))
        self.conn.commit()

    def create_default_time_slots(self, week_start_date):
        default_slots = []
        for hour in range(6, 20):
            start_time = f"{hour:02d}:00"
            end_time = f"{hour + 1:02d}:00"
            default_slots.append((week_start_date, start_time, end_time))

        try:
            self.cursor.executemany(
                "INSERT OR IGNORE INTO time_slots (week_start_date, start_time, end_time) VALUES (?, ?, ?)",
                default_slots)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"创建默认时间段时出错: {e}")

    def get_time_slot_by_id(self, slot_id):
        self.cursor.execute("SELECT start_time, end_time, row_span FROM time_slots WHERE id = ?", (slot_id,))
        return self.cursor.fetchone()

    def update_time_slot(self, slot_id, start_time, end_time):
        try:
            self.cursor.execute("UPDATE time_slots SET start_time = ?, end_time = ? WHERE id = ?",
                                (start_time, end_time, slot_id))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"更新时间段时出错: {e} - 可能是时间冲突。")

    def update_plan_after_merge(self, plan_id, new_text, new_span):
        self.cursor.execute("UPDATE plans SET plan_text = ?, row_span = ? WHERE id = ?", (new_text, new_span, plan_id))
        self.conn.commit()

    def delete_plan_by_id(self, plan_id):
        self.cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        self.conn.commit()

    def update_plan_span(self, plan_id, span):
        self.cursor.execute("UPDATE plans SET row_span = ? WHERE id = ?", (span, plan_id))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def merge_time_slots_down(self, source_id, target_id):
        try:
            source_info = self.get_time_slot_by_id(source_id)
            target_info = self.get_time_slot_by_id(target_id)
            if not source_info or not target_info: return False

            new_span = source_info[2] + target_info[2]

            self.conn.execute("BEGIN TRANSACTION")
            self.cursor.execute("UPDATE time_slots SET row_span = ? WHERE id = ?", (new_span, source_id))
            self.cursor.execute("UPDATE time_slots SET row_span = 0 WHERE id = ?", (target_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Database error during time slot merge down: {e}")
            return False

    def merge_time_slots_up(self, target_id, source_id):
        try:
            source_info = self.get_time_slot_by_id(source_id)
            target_info = self.get_time_slot_by_id(target_id)
            if not source_info or not target_info: return False

            new_span = source_info[2] + target_info[2]

            self.conn.execute("BEGIN TRANSACTION")
            self.cursor.execute("UPDATE time_slots SET row_span = ? WHERE id = ?", (new_span, target_id))
            self.cursor.execute("UPDATE time_slots SET row_span = 0 WHERE id = ?", (source_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Database error during time slot merge up: {e}")
            return False

    def split_time_slot(self, slot_ids_to_reset):
        try:
            self.conn.execute("BEGIN TRANSACTION")
            for slot_id in slot_ids_to_reset:
                self.cursor.execute("UPDATE time_slots SET row_span = 1 WHERE id = ?", (slot_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Database error during time slot split: {e}")
            return False

    # --- 新增：每日特定合并的方法 ---
    def get_day_specific_merges(self, plan_date):
        """获取某一天特定的时间段合并信息。返回一个字典 {start_slot_id: row_span}"""
        self.cursor.execute("""
                            SELECT start_slot_id, row_span
                            FROM day_specific_merges
                            WHERE plan_date = ?
                            """, (plan_date,))
        return dict(self.cursor.fetchall())

    def update_day_specific_merge(self, plan_date, start_slot_id, row_span):
        """更新或插入一天的特定合并信息。"""
        self.cursor.execute("""
                            INSERT INTO day_specific_merges (plan_date, start_slot_id, row_span)
                            VALUES (?, ?, ?) ON CONFLICT(plan_date, start_slot_id) DO
                            UPDATE SET
                                row_span = excluded.row_span
                            """, (plan_date, start_slot_id, row_span))
        self.conn.commit()

    def split_day_specific_merge(self, plan_date, start_slot_id):
        """为拆分操作删除特定的单日合并条目。"""
        self.cursor.execute("""
                            DELETE
                            FROM day_specific_merges
                            WHERE plan_date = ?
                              AND start_slot_id = ?
                            """, (plan_date, start_slot_id))
        self.conn.commit()
