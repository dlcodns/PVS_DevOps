import time
import sys
import os
import pandas as pd
import pymysql
from datetime import datetime

CSV_PATH = "/home/chaeun/pvs/data/dataset_gps_mpu_left.csv"
LOG_PATH = "/home/chaeun/pvs/logs/app.log"

DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "1234"
DB_NAME = "PVS"

SLEEP_SEC = 0.2
RETRY_MAX = 3


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def connect_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=False
    )


def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def parse_epoch_to_dt(x):
    if pd.isna(x):
        return None
    fx = float(x)
    unit = "ms" if fx > 1e11 else "s"
    return pd.to_datetime(fx, unit=unit).to_pydatetime()


def load_and_prepare_dataframe(csv_path: str) -> pd.DataFrame:
    
    df = pd.read_csv(csv_path)

    if "timestamp" not in df.columns:
        raise ValueError(f"CSV에 timestamp 컬럼이 없습니다. columns={list(df.columns)}")

    df["sensor_time"] = df["timestamp"].apply(parse_epoch_to_dt)
    df = df.dropna(subset=["sensor_time"]).copy()

    # 숫자 변환(실패 시 None)
    for col in ["speed", "acc_x", "acc_y", "acc_z"]:
        if col not in df.columns:
            df[col] = None
        df[col] = df[col].apply(safe_float)

    df = df.sort_values("sensor_time").reset_index(drop=True)
    return df


def ensure_process_state_row(conn, cur):
    cur.execute(
        "INSERT INTO process_state (id, last_sensor_time) VALUES (1, NULL) "
        "ON DUPLICATE KEY UPDATE id=id"
    )
    conn.commit()


def get_last_sensor_time(cur):
    cur.execute("SELECT last_sensor_time FROM process_state WHERE id=1")
    row = cur.fetchone()
    return row[0] if row else None


def update_process_state(cur, sensor_time: datetime):
    cur.execute(
        "UPDATE process_state SET last_sensor_time=%s, updated_time=NOW() WHERE id=1",
        (sensor_time,)
    )


def insert_sensor_log(cur, sensor_time: datetime, speed, ax, ay, az):
    cur.execute(
        """
        INSERT INTO sensor_logs (sensor_time, speed, acc_x, acc_y, acc_z)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          speed=VALUES(speed),
          acc_x=VALUES(acc_x),
          acc_y=VALUES(acc_y),
          acc_z=VALUES(acc_z)
        """,
        (sensor_time, speed, ax, ay, az)
    )


# ✅ [추가] datetime 예쁘게 출력하기 위한 포맷터(기존 출력만 개선)
def fmt_dt(v):
    if v is None:
        return "NULL"
    return v.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # ms 단위까지


# ✅ [추가] row 튜플의 datetime만 깔끔하게 바꿔 출력(스키마 몰라도 동작)
def pretty_row(row):
    out = []
    for v in row:
        if isinstance(v, datetime):
            out.append(fmt_dt(v))
        else:
            out.append(v)
    return tuple(out)


def reset_all(cur):
    """
    ✅ [수정] 두 테이블 다 리셋
      - sensor_logs 전체 삭제 (TRUNCATE 우선, 실패 시 DELETE fallback)
      - process_state 초기화
    """
    try:
        cur.execute("TRUNCATE TABLE sensor_logs")
    except Exception as e:
        log(f"[WARN] TRUNCATE failed: {e} -> fallback DELETE")
        cur.execute("DELETE FROM sensor_logs")

    cur.execute(
        "UPDATE process_state SET last_sensor_time=NULL, updated_time=NOW() WHERE id=1"
    )


def main():
    print("[INFO] Starting PVS mini project loader...")

    conn = connect_db()
    cur = conn.cursor()

    ensure_process_state_row(conn, cur)

    while True:
        print("\n==============================")
        print("1: continue (process data)")
        print("2: reset ALL (process_state + sensor_logs)")
        print("3: show sensor_logs (ALL)")
        print("4: show process_state")
        print("0: exit")
        print("==============================")

        try:
            choice = int(input("Select: "))
        except ValueError:
            print("[ERROR] 숫자를 입력하세요.")
            continue

        # ------------------------------
        # 0. exit
        # ------------------------------
        if choice == 0:
            print("[INFO] Exit program.")
            break

        # ------------------------------
        # 1. process CSV -> DB (resume)
        # ------------------------------
        elif choice == 1:
                print("[INFO] Start / Resume processing...")

                df = load_and_prepare_dataframe(CSV_PATH)

                last_time = get_last_sensor_time(cur)

                if last_time is None:
                        print("[INFO] First run: no last_sensor_time")
                        work_df = df
                else:
                        print(f"[INFO] Resume mode: last_sensor_time={last_time}")
                        work_df = df[df["sensor_time"] > last_time]

                total = len(work_df)
                print(f"[INFO] Rows to process: {total}")

                prev_time = None

                for idx, row in enumerate(work_df.itertuples(index=False), start=1):
                        try:
                                # 이전 sensor_time과의 차이를 그대로 sleep (ms 단위 재현)
                                if prev_time is not None:
                                        delta = (row.sensor_time - prev_time).total_seconds()
                                        if delta > 0:
                                                time.sleep(delta)

                                insert_sensor_log(
                                        cur,
                                        row.sensor_time,
                                        row.speed,
                                        row.acc_x,
                                        row.acc_y,
                                        row.acc_z
                                )

                                update_process_state(cur, row.sensor_time)
                                conn.commit()

                                print(
                                        f"[OK] {idx}/{total} "
                                        f"sensor_time={row.sensor_time} speed={row.speed}"
                                )

                                prev_time = row.sensor_time

                        except Exception as e:
                                conn.rollback()
                                print(f"[ERROR] DB error: {e}")
                                print("[INFO] Safe stop. Resume possible.")
                                break

        # ------------------------------
        # 2. reset ALL (process_state + sensor_logs)
        # ------------------------------
        elif choice == 2:
            confirm = input("Really reset ALL? (y/n): ").strip().lower()
            if confirm == "y":
                try:
                    reset_all(cur)
                    conn.commit()
                    print("[INFO] process_state + sensor_logs reset.")
                except Exception as e:
                    conn.rollback()
                    print(f"[ERROR] reset failed: {e}")
            else:
                print("[INFO] reset canceled.")

        # ------------------------------
        # 3. sensor_logs 전체 출력 (datetime 보기 좋게)
        # ------------------------------
        elif choice == 3:
            cur.execute("SELECT * FROM sensor_logs")
            rows = cur.fetchall()
            print("[INFO] sensor_logs:")
            for row in rows:
                print(pretty_row(row))

        # ------------------------------
        # 4. process_state 출력 (datetime 보기 좋게)
        # ------------------------------
        elif choice == 4:
            cur.execute("SELECT * FROM process_state")
            row = cur.fetchone()
            print("[INFO] process_state:")
            if row:
                print(pretty_row(row))
            else:
                print("(empty)")

        else:
            print("[ERROR] 잘못된 선택입니다.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()