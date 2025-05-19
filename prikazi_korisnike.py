import sqlite3

try:
    conn = sqlite3.connect('korisnici.db')  # Ako je fajl u istom folderu
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM korisnici')
    korisnici = cursor.fetchall()

    if not korisnici:
        print("Nema korisnika u bazi.")
    else:
        for korisnik in korisnici:
            print(korisnik)

    conn.close()
except Exception as e:
    print("Greška:", e)
