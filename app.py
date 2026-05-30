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
st.write("Štiklirajte putnike i statuse. Unos za isti datum će automatski ažurirati (prepisati) stari red.")

# Inicijalizacija tabele u sesiji (da aplikacija pamti podatke tokom rada)
if "podaci_o_putovanjima" not in st.session_state:
    st.session_state.podaci_o_putovanjima = pd.DataFrame(
        columns=["Datum", "Imena putnika", "Polazak", "Odlazak"]
    )

# Lista tvojih putnika
lista_putnika = ["Ksenija", "Radislav", "Nikola", "Stefan", "Ivan", "Miroslav", "Branko", "Milica"]

st.subheader("📝 Unos novih ili izmena postojećih podataka")

# Podela ekrana na dve kolone radi boljeg izgleda
kolona_levo, kolona_desno = st.columns([1, 2])

# LEVA KOLONA: Izbor putnika preko checkbox-a
with kolona_levo:
    st.write("**Izaberite putnike:**")
    selektovani_putnici = []
    for putnik in lista_putnika:
        if st.checkbox(putnik, key=f"cb_{putnik}"):
            selektovani_putnici.append(putnik)

# DESNA KOLONA: Izbor datuma i statusa (Da/Ne)
with kolona_desno:
    st.write("**Detalji putovanja:**")
    datum = st.date_input("Datum putovanja")
    
    st.write("") 
    st.write("**Status putovanja (Štiklirajte za DA):**")
    
    # Checkbox-ovi za status polaska i odlaska
    polazak_cb = st.checkbox("Polazak realizovan?")
    odlazak_cb = st.checkbox("Odlazak realizovan?")
    
    # Prebacivanje True/False stanja u tekst "Da" ili "Ne"
    polazak_status = "Da" if polazak_cb else "Ne"
    odlazak_status = "Da" if odlazak_cb else "Ne"
    
    st.write("") 
    
    # Dugme za čuvanje podataka
    if st.button("Dodaj / Izmeni u tabeli", type="primary"):
        if not selektovani_putnici:
            st.error("Morate štiklirati barem jednog putnika!")
        else:
            # Formatiranje datuma i spajanje imena zarezom
            datum_str = datum.strftime("%d.%m.%Y")
            spojena_imena = ", ".join(selektovani_putnici)
            
            # Kreiranje novog reda podataka
            novi_red = pd.DataFrame([{
                "Datum": datum_str,
                "Imena putnika": spojena_imena,
                "Polazak": polazak_status,
                "Odlazak": odlazak_status
            }])
            
            postojeca_tabela = st.session_state.podaci_o_putovanjima
            
            # LOGIKA ZA PREPISIVANJE GRESKE: Ako datum već postoji u tabeli
            if datum_str in postojeca_tabela["Datum"].values:
                # Brišemo staru verziju za taj dan
                tabela_bez_starog_dana = postojeca_tabela[postojeca_tabela["Datum"] != datum_str]
                # Dodajemo novu verziju u tabelu
                st.session_state.podaci_o_putovanjima = pd.concat([tabela_bez_starog_dana, novi_red], ignore_index=True)
                st.warning(f"Podaci za datum {datum_str} su ažurirani! Stari red je zamenjen novim.")
            else:
                # Ako je datum nov, samo ga regularno dodajemo
                st.session_state.podaci_o_putovanjima = pd.concat([postojeca_tabela, novi_red], ignore_index=True)
                st.success("Podaci uspešno dodati u tabelu!")
            
            # Automatsko sortiranje tabele po datumu radi preglednosti
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
    
    # 1) Excel Export
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
        
    # 2) PDF Export
    with col_exp2:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph("<b>Izveštaj o realizovanim putovanjima</b>", styles['Title']))
        elements.append(Spacer(1, 20))
        
        pdf_data = [df.columns.tolist()] + df.values.tolist()
        
        # Podešavanje širine kolona u PDF-u (ime dobija najviše prostora)
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