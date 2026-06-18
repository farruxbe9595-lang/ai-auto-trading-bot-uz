"""
Real (Binance) savdolar uchun ALOHIDA jadval. Mavjud `saqlash/baza.py`dagi
`savdolar` jadvali (sinov savdosi va hisobotlar shu yerdan o'qiydi) BUTUNLAY
tegilmagan qoldi — bu ataylab qilingan: real va sinov savdolarni aralashtirib
yubormaslik uchun.
"""

import sqlite3
from datetime import datetime, date

from asosiy.sozlamalar import DATA_DIR
import os

REAL_DB_PATH = os.path.join(DATA_DIR, "real_savdolar.db")


def ulanish():
    return sqlite3.connect(REAL_DB_PATH)


def real_bazani_tayyorla():
    con = ulanish()
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS real_savdolar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ochilish_vaqti TEXT,
        yopilish_vaqti TEXT,
        symbol TEXT,
        miqdor REAL,
        kirish_narxi REAL,
        kirish_buyurtma_id TEXT,
        oco_order_list_id INTEGER,
        sl_narx REAL,
        tp_narx REAL,
        chiqish_narxi REAL,
        foyda_zarar REAL,
        holat TEXT,
        sabab TEXT
    )''')
    con.commit()
    con.close()


def real_savdo_ochish(symbol, miqdor, kirish_narxi, kirish_buyurtma_id, oco_order_list_id, sl_narx, tp_narx):
    con = ulanish()
    cur = con.cursor()
    cur.execute(
        '''INSERT INTO real_savdolar
        (ochilish_vaqti, symbol, miqdor, kirish_narxi, kirish_buyurtma_id,
         oco_order_list_id, sl_narx, tp_narx, holat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OCHIQ')''',
        (datetime.now().isoformat(), symbol, miqdor, kirish_narxi,
         kirish_buyurtma_id, oco_order_list_id, sl_narx, tp_narx)
    )
    con.commit()
    trade_id = cur.lastrowid
    con.close()
    return trade_id


def real_savdo_yopish(trade_id, chiqish_narxi, foyda_zarar, sabab):
    con = ulanish()
    cur = con.cursor()
    cur.execute(
        '''UPDATE real_savdolar
        SET yopilish_vaqti=?, chiqish_narxi=?, foyda_zarar=?, holat='YOPILGAN', sabab=?
        WHERE id=?''',
        (datetime.now().isoformat(), chiqish_narxi, foyda_zarar, sabab, trade_id)
    )
    con.commit()
    con.close()


def real_ochiq_savdolar():
    con = ulanish()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute("SELECT * FROM real_savdolar WHERE holat='OCHIQ' ORDER BY id").fetchall()
    con.close()
    return [dict(r) for r in rows]


def real_bugungi_statistika():
    today = date.today().isoformat()
    con = ulanish()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT foyda_zarar FROM real_savdolar WHERE holat='YOPILGAN' AND substr(yopilish_vaqti,1,10)=? ORDER BY id",
        (today,)
    ).fetchall()
    con.close()
    savdo_soni = len(rows)
    foyda_zarar = sum((r[0] or 0) for r in rows)

    ketma = 0
    for (fz,) in reversed(rows):
        if (fz or 0) < 0:
            ketma += 1
        else:
            break

    return {"savdo_soni": savdo_soni, "foyda_zarar": foyda_zarar, "ketma_ket_zarar": ketma}


def real_barcha_savdolar():
    con = ulanish()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute("SELECT * FROM real_savdolar ORDER BY id").fetchall()
    con.close()
    return [dict(r) for r in rows]
