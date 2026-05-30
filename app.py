import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Podešavanje stranice i naslova aplikacije
st.set_page_config(page_title="Evidencija Putnika", layout="wide")

st.title("🧳 Pametna Aplikacija za Evidenciju Putovanja")
st.write("Štiklirajte putnike i statuse. Upravljajte listom putnika direktno sa desne strane (maksimalno 15).")

# 1) Inicijalizacija baze podataka (tabela putovanja)
if "podaci_o_putovanjima" not in st.session_state:
    st.session_state.podaci_o_putovanjima = pd.DataFrame(
        columns=["Datum", "Imena putnika", "Polazak", "Odlazak"]
    )

# 2) Inicijalizacija LISTE PUTNIKA u sesiji (da bi bila promenljiva)
if "lista_putnika" not in st.session_state:
    st.session_state.lista_putnika = ["Ksenija", "Radislav", "Nikola", "Stefan", "Ivan", "Miroslav", "Branko", "Milica"]

# --- GLAVNI INTERFEJS: UPRAVLJANJE PUTNICIMA I UNOS ---
st.subheader("📝 Unos podataka i upravljanje listom putnika")

# Delimo ekran na dve glavne kolone (Levo: Checkbox lista, Desno: Kontrole i detalji rute)
kolona_levo, kolona_desno = st.columns([1, 2])

# LEVA KOLONA: Dinamički prikaz checkbox-ova iz session_state-a
with kolona_levo:
    st.write("**Izaberite putnike:**")
    selektovani_putnici = []
    for putnik in st.session_state.lista_putnika:
        if st.checkbox(putnik, key=f"cb_{putnik}"):
            selektovani_putnici.append(putnik)

# DESNA KOLONA: Podeljena na upravljanje ljudima (gore) i unos rute (dole)
with kolona_desno:
    # Iskorišćavanje desnog prostora za Dodavanje/Brisanje
    st.write("**⚙️ Upravljanje listom putnika (Trenutno: {}/15):**".format(len(st.session_state.lista_putnika)))
    
    kolona_dodaj, kolona_obrisi = st.columns(2)
    
    with kolona_dodaj:
        novo_ime = st.text_input("➕ Dodaj novog putnika:", placeholder="Upiši ime", key="txt_novo_ime")
        if st.button("Potvrdi dodavanje"):
            if not novo_ime.strip():
                st.error("Ime ne može biti prazno!")
            elif len(st.session_state.lista_putnika) >= 15:
                st.error("Dostignut je maksimalan broj od 15 putnika!")
            elif novo_ime.strip() in st.session_state.lista_putnika:
                st.warning(f"Putnik {novo_ime} već postoji na listi.")
            else:
                st.session_state.lista_putnika.append(novo_ime.strip())
                st.success(f"Putnik {novo_ime} je dodat na listu!")
                st.rerun()
                
    with kolona_obrisi:
        # Padajući meni za izbor putnika kojeg brišemo iz sistema
        putnik_za_brisanje = st.selectbox("❌ Ukloni putnika sa liste:", ["-- Izaberi --"] + st.session_state.lista_putnika)
        if st.button("Potvrdi brisanje"):
            if putnik_za_brisanje != "-- Izaberi --":
                st.session_state.lista_putnika.remove(putnik_za_brisanje)
                st.success(f"Putnik {putnik_za_brisanje} je uspešno uklonjen sa liste!")
                st.rerun()
            else:
                st.error("Izaberite putnika kojeg želite da obrišete.")

    st.write("---") # Razdelnik unutar desne kolone
    
    # DETALJI PUTOVANJA
    st.write("**📅 Detalji putovanja:**")
    datum = st.date_input("Datum putovanja")
    
    st.write("**Status putovanja (Štiklirajte za DA):**")
    polazak_cb = st.checkbox("Polazak realizovan?")
    odlazak_cb = st.checkbox("Odlazak realizovan?")
    
    polazak_status = "Da" if polazak_cb else "Ne"
    odlazak_status = "Da" if odlazak_cb else "Ne"
    
    st.write("") 
    
    # Dugme za čuvanje u tabelu
    if st.button("Dodaj / Izmeni u tabeli", type="primary"):
        if not selektovani_putnici:
            st.error("Morate štiklirati barem jednog putnika na levoj strani!")
        else:
            datum_str = datum.strftime("%d.%m.%Y")
            spojena_imena = ", ".join(selektovani_putnici)
            
            novi_red = pd.DataFrame([{
                "Datum": datum_str,
                "Imena putnika": spojena_imena,
                "Polazak": polazak_status,
                "Odlazak": odlazak_status
            }])
            
            postojeca_tabela = st.session_state.podaci_o_putovanjima
            
            # Logika prepisivanja ako datum postoji
            if datum_str in postojeca_tabela["Datum"].values:
                tabela_bez_starog_dana = postojeca_tabela[postojeca_tabela["Datum"] != datum_str]
                st.session_state.podaci_o_putovanjima = pd.concat([tabela_bez_starog_dana, novi_red], ignore_index=True)
                st.warning(f"Podaci za datum {datum_str} su ažurirani! Stari red je zamenjen novim.")
            else:
                st.session_state.podaci_o_putovanjima = pd.concat([postojeca_tabela, novi_red], ignore_index=True)
                st.success("Podaci uspešno dodati u tabelu!")
            
            st.session_state.podaci_o_putovanjima = st.session_state.podaci_o_putovanjima.sort_values(by="Datum").reset_index(drop=True)

# --- INTERAKTIVNI PRIKAZ TABELE ---
st.subheader("📊 Tabela putovanja")
df = st.session_state.podaci_o_putovanjima

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    if st.button("Isprazni celu tabelu"):
        st.session_state.podaci_o_putovanjima = pd.DataFrame(
            columns=["Datum", "Imena putnika", "Polazak", "Odlazak"]
        )
        st.rerun()

    # --- EKSPORTOVANJE (EXCEL I PDF) ---
    st.subheader("📥 Preuzimanje fajlova")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Putovanja')
        st.download_button(
            label="Preuzmi kao EXCEL (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="evidencija_putovanja.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_exp2:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph("<b>Izveštaj o realizovanim putovanjima</b>", styles['Title']))
        elements.append(Spacer(1, 20))
        
        pdf_data = [df.columns.tolist()] + df.values.tolist()
        
        t = Table(pdf_data, colWidths=[80, 260, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t)
        doc.build(elements)
        
        st.download_button(
            label="Preuzmi kao PDF (.pdf)",
            data=pdf_buffer.getvalue(),
            file_name="evidencija_putovanja.pdf",
            mime="application/pdf",
            use_container_width=True
        )
else:
    st.info("Tabela je trenutno prazna. Selektujte podatke iznad da biste započeli evidenciju.")