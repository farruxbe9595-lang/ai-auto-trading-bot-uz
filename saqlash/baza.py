import sqlite3
from datetime import datetime, date
from asosiy.sozlamalar import DB_PATH, BOSHLANGICH_KAPITAL


def ulanish():
    return sqlite3.connect(DB_PATH)


def _column_exists(cur, table, column):
    rows = cur.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def bazani_tayyorla():
    con = ulanish()
    cur = con.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS tavsiyalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vaqt TEXT,
        symbol TEXT,
        tavsiya TEXT,
        narx REAL,
        ishonch REAL,
        trend TEXT,
        rsi REAL,
        sabablar TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS savdolar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ochilish_vaqti TEXT,
        yopilish_vaqti TEXT,
        symbol TEXT,
        yonalish TEXT,
        kirish_narxi REAL,
        chiqish_narxi REAL,
        miqdor REAL,
        zarar_toxtatish REAL,
        foyda_olish REAL,
        foyda_zarar REAL,
        holat TEXT,
        izoh TEXT
    )''')

    # Eski bazaga yangi ustunlar qo‘shish
    if not _column_exists(cur, 'savdolar', 'savdo_hajmi_usd'):
        cur.execute("ALTER TABLE savdolar ADD COLUMN savdo_hajmi_usd REAL DEFAULT 0")

    if not _column_exists(cur, 'savdolar', 'eng_yaxshi_foiz'):
        cur.execute("ALTER TABLE savdolar ADD COLUMN eng_yaxshi_foiz REAL DEFAULT 0")

    con.commit()
    con.close()


def tavsiyani_saqlash(t):
    con = ulanish()
    cur = con.cursor()

    cur.execute(
        '''INSERT INTO tavsiyalar
        (vaqt, symbol, tavsiya, narx, ishonch, trend, rsi, sabablar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            datetime.now().isoformat(),
            t['symbol'],
            t['tavsiya'],
            t['narx'],
            t['ishonch_foizi'],
            t['trend'],
            t['rsi'],
            '; '.join(t['sabablar'])
        )
    )

    con.commit()
    con.close()


def savdo_ochish(symbol, yonalish, kirish, miqdor, sl, tp, izoh, savdo_hajmi_usd):
    con = ulanish()
    cur = con.cursor()

    cur.execute(
        '''INSERT INTO savdolar
        (ochilish_vaqti, symbol, yonalish, kirish_narxi, miqdor,
         zarar_toxtatish, foyda_olish, holat, izoh, savdo_hajmi_usd, eng_yaxshi_foiz)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            datetime.now().isoformat(),
            symbol,
            yonalish,
            kirish,
            miqdor,
            sl,
            tp,
            'OCHIQ',
            izoh,
            savdo_hajmi_usd,
            0
        )
    )

    con.commit()
    trade_id = cur.lastrowid
    con.close()
    return trade_id


def savdo_yopish(trade_id, chiqish, foyda_zarar, izoh=''):
    con = ulanish()
    cur = con.cursor()

    cur.execute(
        '''UPDATE savdolar
        SET yopilish_vaqti=?,
            chiqish_narxi=?,
            foyda_zarar=?,
            holat=?,
            izoh=COALESCE(izoh, '') || ?
        WHERE id=?''',
        (
            datetime.now().isoformat(),
            chiqish,
            foyda_zarar,
            'YOPILGAN',
            '\n' + izoh,
            trade_id
        )
    )

    con.commit()
    con.close()


def eng_yaxshi_foiz_yangilash(trade_id, eng_yaxshi_foiz):
    con = ulanish()
    cur = con.cursor()

    cur.execute(
        "UPDATE savdolar SET eng_yaxshi_foiz=? WHERE id=?",
        (eng_yaxshi_foiz, trade_id)
    )

    con.commit()
    con.close()


def ochiq_savdolar():
    con = ulanish()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    rows = cur.execute("SELECT * FROM savdolar WHERE holat='OCHIQ' ORDER BY id").fetchall()

    con.close()
    return [dict(r) for r in rows]


def bugungi_statistika():
    today = date.today().isoformat()
    con = ulanish()
    cur = con.cursor()

    rows = cur.execute(
        "SELECT foyda_zarar FROM savdolar WHERE holat='YOPILGAN' AND substr(yopilish_vaqti, 1, 10)=? ORDER BY id",
        (today,)
    ).fetchall()

    savdo_soni = len(rows)
    foyda_zarar = sum((r[0] or 0) for r in rows)

    ketma = 0
    for (fz,) in reversed(rows):
        if (fz or 0) < 0:
            ketma += 1
        else:
            break

    con.close()

    return {
        'savdo_soni': savdo_soni,
        'foyda_zarar': foyda_zarar,
        'ketma_ket_zarar': ketma
    }


def balans_holati():
    con = ulanish()
    cur = con.cursor()

    yopilgan = cur.execute(
        "SELECT COALESCE(SUM(foyda_zarar), 0) FROM savdolar WHERE holat='YOPILGAN'"
    ).fetchone()[0] or 0

    band = cur.execute(
        "SELECT COALESCE(SUM(savdo_hajmi_usd), 0) FROM savdolar WHERE holat='OCHIQ'"
    ).fetchone()[0] or 0

    con.close()

    umumiy = BOSHLANGICH_KAPITAL + yopilgan
    erkin = umumiy - band

    return {
        'boshlangich': BOSHLANGICH_KAPITAL,
        'umumiy': round(umumiy, 4),
        'band': round(band, 4),
        'erkin': round(erkin, 4),
        'yopilgan_foyda_zarar': round(yopilgan, 4)
    }


def barcha_savdolar():
    con = ulanish()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    rows = cur.execute('SELECT * FROM savdolar ORDER BY id').fetchall()

    con.close()
    return [dict(r) for r in rows]
