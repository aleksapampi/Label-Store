import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tvoj_tajni_kljuc_ovde'

# ----- Pomoćne funkcije -----

def init_baza():
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()

    # Tabela korisnici
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS korisnici (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            korisnicko_ime TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            lozinka TEXT NOT NULL,
            rola TEXT DEFAULT 'korisnik'
        )
    ''')

    # Tabela kupci
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kupci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            prezime TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            adresa TEXT NOT NULL,
            broj_telefona TEXT NOT NULL,
            artikal TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

init_baza()

# ----- Rute -----

@app.route('/')
def homepage():
    if 'korisnik_id' in session:
        return redirect(url_for('homepage2'))
    return render_template('login.html')

@app.route('/registracija', methods=['GET', 'POST'])
def registracija():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        rola = request.form['rola']  # Očekuje se da forma ima input za rolu

        if password != confirm_password:
            flash('Lozinke se ne poklapaju.', 'danger')
            return redirect(url_for('registracija'))

        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()

        # Provera da li postoji korisnik sa istim email-om ili korisničkim imenom
        cursor.execute("SELECT * FROM korisnici WHERE email = ? OR korisnicko_ime = ?", (email, username))
        if cursor.fetchone():
            flash('Email ili korisničko ime već postoji.', 'danger')
            conn.close()
            return redirect(url_for('registracija'))

        # Hashovanje lozinke
        hashed_password = generate_password_hash(password)

        # Ubacivanje korisnika u bazu
        cursor.execute(
            "INSERT INTO korisnici (email, korisnicko_ime, lozinka, rola) VALUES (?, ?, ?, ?)",
            (email, username, hashed_password, rola)
        )
        conn.commit()
        conn.close()

        flash('Uspešna registracija! Možete se prijaviti.', 'success')
        return redirect(url_for('homepage'))  # Možeš da preusmeriš i na login stranu ako želiš

    return render_template('registracija.html')



@app.route('/prijava', methods=['GET', 'POST'])
def prijava():
    if request.method == 'POST':
        email = request.form['loginEmail']
        lozinka = request.form['loginPassword']

        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()

        # Dohvati id, korisnicko_ime, lozinku i rolu korisnika sa unetim emailom
        cursor.execute("SELECT id, korisnicko_ime, lozinka, rola FROM korisnici WHERE email = ?", (email,))
        korisnik = cursor.fetchone()
        conn.close()

        if korisnik and check_password_hash(korisnik[2], lozinka):
            session['korisnik_id'] = korisnik[0]
            session['korisnicko_ime'] = korisnik[1]
            session['rola'] = korisnik[3]  # Čuvamo ulogu u sesiji
            session.pop('gost', None)
            flash('Uspešno ste se prijavili!', 'success')
            return redirect(url_for('homepage2'))
        else:
            flash('Pogrešni podaci za prijavu!', 'danger')
            return redirect(url_for('prijava'))

    return render_template('login.html')



@app.route('/nastavi-kao-gost')
def nastavi_kao_gost():
    session['gost'] = True
    session.pop('korisnik_id', None)
    session.pop('korisnicko_ime', None)
    flash('Nastavili ste kao gost. Neke funkcije nisu dostupne.', 'info')
    return redirect(url_for('homepage2'))

@app.route('/homepage2')
def homepage2():
    if 'korisnik_id' in session:
        return render_template('homepage2.html', korisnik=session.get('korisnicko_ime'), gost=False)
    elif session.get('gost'):
        return render_template('homepage2.html', gost=True, korisnik=None)
    else:
        flash('Morate biti ulogovani ili nastaviti kao gost!', 'warning')
        return redirect(url_for('prijava'))

@app.route('/izloguj_se')
def izloguj_se():
    session.clear()
    flash('Uspešno ste se izlogovali!', 'success')
    return redirect(url_for('prijava'))

@app.route('/profil')
def profil():
    if 'korisnik_id' not in session:
        flash('Morate biti ulogovani da biste pristupili ovoj stranici!', 'warning')
        return redirect(url_for('prijava'))
    return render_template('profil.html', korisnik=session.get('korisnicko_ime'))

# ----- Kupci -----

@app.route('/dodaj_kupca', methods=['GET', 'POST'])
def dodaj_kupca():
    if 'korisnik_id' not in session and not session.get('gost'):
        flash('Morate biti ulogovani da biste dodali kupca!', 'warning')
        return redirect(url_for('prijava'))
    
    if request.method == 'POST':
        email = request.form['email']
        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kupci WHERE email = ?", (email,))
        if cursor.fetchone():
            flash("Kupac sa ovim email-om već postoji!", "danger")
            conn.close()
            return redirect(url_for('dodaj_kupca'))

        try:
            cursor.execute('''INSERT INTO kupci (ime, prezime, email, adresa, broj_telefona, artikal)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (request.form['ime'], request.form['prezime'], email,
                            request.form['adresa'], request.form['broj_telefona'], request.form['artikal']))
            conn.commit()
            flash("Kupac je uspešno dodat!", "success")
        except:
            flash("Greška pri dodavanju kupca!", "danger")
        conn.close()
        return redirect(url_for('pregled_kupaca'))
    return render_template('dodaj_kupca.html')

from flask import session, redirect, url_for, flash

def proveri_admina():
    if 'korisnik_id' not in session or session.get('rola') != 'administrator':
        flash('Nemate dozvolu za pristup ovoj stranici.', 'danger')
        return redirect(url_for('prijava'))
    return None

@app.route('/pregled_kupaca')
def pregled_kupaca():
    provera = proveri_admina()
    if provera:
        return provera  # ako nije admin, preusmeri

    conn = sqlite3.connect('baza.db')
    conn.row_factory = sqlite3.Row  # dodaj ovo da vrati dict-like objekte
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kupci")
    kupci = cursor.fetchall()
    conn.close()

    return render_template('pregled_kupaca.html', kupci=kupci)


@app.route('/izmena_kupca/<int:id>', methods=['GET', 'POST'])
def izmena_kupca(id):
    provera = proveri_admina()
    if provera:
        return provera

    conn = sqlite3.connect('baza.db')
    conn.row_factory = sqlite3.Row  # omogućava pristup kolona po imenu
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute('''UPDATE kupci SET ime=?, prezime=?, email=?, adresa=?, broj_telefona=?, artikal=?
                          WHERE id=?''',
                       (request.form['ime'], request.form['prezime'], request.form['email'],
                        request.form['adresa'], request.form['broj_telefona'], request.form['artikal'], id))
        conn.commit()
        conn.close()
        flash("Kupac uspešno izmenjen!", "success")
        return redirect(url_for('pregled_kupaca'))

    cursor.execute("SELECT * FROM kupci WHERE id = ?", (id,))
    kupac = cursor.fetchone()
    conn.close()
    return render_template('izmena_kupca.html', kupac=kupac)

@app.route('/brisanje_kupca/<int:id>', methods=['POST'])
def brisanje_kupca(id):
    provera = proveri_admina()
    if provera:
        return provera

    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kupci WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Kupac uspešno obrisan!", "success")
    return redirect(url_for('pregled_kupaca'))


# ----- Artikli i korpa -----

artikli = []

@app.route('/artikli', methods=['GET', 'POST'])
def artikli_stranica():
    if request.method == 'POST':
        novi_artikal = {
            "id": len(artikli) + 1,
            "naziv": request.form['naziv'],
            "opis": request.form['opis'],
            "cena": request.form['cena'],
            "kolicina": request.form['kolicina']
        }
        artikli.append(novi_artikal)
        flash("Artikal dodat!", "success")
        return redirect(url_for('artikli_stranica'))
    return render_template('artikli.html', artikli=artikli)

@app.route('/nike_duks')
def nike_duks():
    return render_template('nike_duks.html')

@app.route('/dodaj_u_korpu/<naziv>', methods=['POST'])
def dodaj_u_korpu(naziv):
    if 'korpa' not in session:
        session['korpa'] = []
    session['korpa'].append(naziv)
    session.modified = True
    flash(f'Artikal "{naziv}" dodat u korpu.', 'success')
    return redirect(url_for('pregled_korpe'))

@app.route('/pregled_korpe')
def pregled_korpe():
    return render_template('korpa.html', korpa=session.get('korpa', []))

@app.route('/ukloni_iz_korpe/<string:naziv>', methods=['POST'])
def ukloni_iz_korpe(naziv):
    if 'korpa' in session and naziv in session['korpa']:
        session['korpa'].remove(naziv)
        session.modified = True
        flash(f'Artikal "{naziv}" uklonjen iz korpe.', 'success')
    return redirect(url_for('pregled_korpe'))

# ----- Pokretanje aplikacije -----

if __name__ == "__main__":
    app.run(debug=True)
