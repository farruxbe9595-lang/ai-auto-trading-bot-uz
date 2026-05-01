import sqlite3
from datetime import datetime, date
from asosiy.sozlamalar import DB_PATH


def ulanish():
    return sqlite3.connect(DB_PATH)


def bazani_tayyorla():
    con = ulanish()
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS tavsiyalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vaqt TEXT, symbol TEXT, tavsiya TEXT, narx REAL, ishonch REAL,
        trend TEXT, rsi REAL, sabablar TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS savdolar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ochilish_vaqti TEXT, yopilish_vaqti TEXT, symbol TEXT,
        yonalish TEXT, kirish_narxi REAL, chiqish_narxi REAL,
        miqdor REAL, zarar_toxtatish REAL, foyda_olish REAL,
        foyda_zarar REAL, holat TEXT, izoh TEXT
    )''')
    con.commit(); con.close()


def tavsiyani_saqlash(t):
    con = ulanish(); cur = con.cursor()
    cur.execute('INSERT INTO tavsiyalar (vaqt,symbol,tavsiya,narx,ishonch,trend,rsi,sabablar) VALUES (?,?,?,?,?,?,?,?)',
        (datetime.now().isoformat(), t['symbol'], t['tavsiya'], t['narx'], t['ishonch_foizi'], t['trend'], t['rsi'], '; '.join(t['sabablar'])))
    con.commit(); con.close()


def savdo_ochish(symbol, yonalish, kirish, miqdor, sl, tp, izoh):
    con = ulanish(); cur = con.cursor()
    cur.execute('''INSERT INTO savdolar
        (ochilish_vaqti, symbol, yonalish, kirish_narxi, miqdor, zarar_toxtatish, foyda_olish, holat, izoh)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (datetime.now().isoformat(), symbol, yonalish, kirish, miqdor, sl, tp, 'OCHIQ', izoh))
    con.commit(); trade_id = cur.lastrowid; con.close(); return trade_id


def savdo_yopish(trade_id, chiqish, foyda_zarar, izoh=''):
    con = ulanish(); cur = con.cursor()
    cur.execute('UPDATE savdolar SET yopilish_vaqti=?, chiqish_narxi=?, foyda_zarar=?, holat=?, izoh=izoh || ? WHERE id=?',
        (datetime.now().isoformat(), chiqish, foyda_zarar, 'YOPILGAN', '\n' + izoh, trade_id))
    con.commit(); con.close()


def ochiq_savdolar():
    con = ulanish(); con.row_factory = sqlite3.Row; cur = con.cursor()
    rows = cur.execute("SELECT * FROM savdolar WHERE holat='OCHIQ'").fetchall()
    con.close(); return [dict(r) for r in rows]


def bugungi_statistika():
    today = date.today().isoformat()
    con = ulanish(); cur = con.cursor()
    rows = cur.execute("SELECT foyda_zarar FROM savdolar WHERE holat='YOPILGAN' AND substr(yopilish_vaqti,1,10)=?", (today,)).fetchall()
    savdo_soni = len(rows)
    foyda_zarar = sum((r[0] or 0) for r in rows)
    ketma = 0
    for (fz,) in reversed(rows):
        if (fz or 0) < 0: ketma += 1
        else: break
    con.close()
    return {'savdo_soni': savdo_soni, 'foyda_zarar': foyda_zarar, 'ketma_ket_zarar': ketma}


def barcha_savdolar():
    con = ulanish(); con.row_factory = sqlite3.Row; cur = con.cursor()
    rows = cur.execute('SELECT * FROM savdolar ORDER BY id').fetchall()
    con.close(); return [dict(r) for r in rows]
