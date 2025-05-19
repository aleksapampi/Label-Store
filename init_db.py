import sqlite3

# Povezivanje na bazu (ako ne postoji, napraviće se)
conn = sqlite3.connect('korisnici.db')
cursor = conn.cursor()

# Kreiranje tabele korisnici ako ne postoji
cursor.execute('''
CREATE TABLE IF NOT EXISTS korisnici (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    rola TEXT NOT NULL
)
''')

conn.commit()
conn.close()

print("Baza i tabela korisnici su uspešno kreirani (ili već postoje).")
