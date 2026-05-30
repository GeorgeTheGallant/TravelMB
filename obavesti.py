import os
import smtplib
from email.mime.text import MIMEText

def posalji_email_petkom():
    try:
        # GitHub Actions će ove podatke bezbjedno povući iz svojih Secrets podešavanja
        sender = os.environ["EMAIL_SENDER"]
        password = os.environ["EMAIL_PASSWORD"]
        primaoci = [m.strip() for m in os.environ["EMAIL_PRIMAOCI"].split(",")]
        
        tekst_petak = (
            "Dobar dan!\n\n"
            "Da li ste popunili tabelu putovanja za ovu sedmicu?\n\n"
            "Molimo vas da unesete podatke na vreme kako bismo imali tačnu evidenciju.\n\n"
            "Link aplikacije: https://travelmb.streamlit.app"
        )
        
        msg = MIMEText(tekst_petak)
        msg['Subject'] = "📅 Podsetnik: Popunjavanje tabele za ovu sedmicu"
        msg['From'] = sender
        msg['To'] = ", ".join(primaoci)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, primaoci, msg.as_string())
        print("Email podsetnik za petak je uspešno poslat!")
        return True
    except Exception as e:
        print(f"Greška prilikom slanja email-a: {e}")
        return False

if __name__ == "__main__":
     posalji_email_petkom()