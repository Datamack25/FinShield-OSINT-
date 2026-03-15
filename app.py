import streamlit as st
import requests
import json
import re
import time
import os
import sqlite3
import csv
import io
from datetime import datetime
from io import BytesIO
from urllib.parse import quote_plus, urlparse
# anthropic not required — using free local engine
import pandas as pd

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinShield OSINT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
:root {
  --bg:#0a0d14; --surface:#111520; --border:#1e2535;
  --accent:#00d4ff; --accent2:#ff6b35; --green:#00ff88;
  --red:#ff3366; --yellow:#ffcc00; --text:#c8d6e5; --muted:#5a6a7a;
}
html,body,[data-testid="stApp"]{background:var(--bg)!important;color:var(--text);font-family:'IBM Plex Sans',sans-serif;}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border);}
[data-testid="stSidebar"] *{color:var(--text)!important;}
h1,h2,h3{font-family:'IBM Plex Mono',monospace!important;}
h1{color:var(--accent)!important;letter-spacing:-0.5px;}
h2{color:var(--text)!important;border-bottom:1px solid var(--border);padding-bottom:8px;}
h3{color:var(--accent)!important;font-size:0.95rem!important;}
input,textarea,[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
  background:var(--surface)!important;color:var(--text)!important;
  border:1px solid var(--border)!important;border-radius:4px!important;
  font-family:'IBM Plex Mono',monospace!important;}
input:focus,textarea:focus{border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(0,212,255,0.1)!important;}
.stButton>button{background:transparent!important;color:var(--accent)!important;
  border:1px solid var(--accent)!important;border-radius:3px!important;
  font-family:'IBM Plex Mono',monospace!important;font-size:0.85rem!important;
  letter-spacing:1px!important;transition:all 0.15s!important;}
.stButton>button:hover{background:var(--accent)!important;color:var(--bg)!important;}
.metric-card{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:16px 20px;margin:8px 0;}
.metric-card .label{font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:2px;}
.metric-card .value{font-family:'IBM Plex Mono',monospace;font-size:1.4rem;color:var(--accent);margin-top:4px;}
.metric-card .sub{font-size:0.8rem;color:var(--text);margin-top:2px;}
.badge-low{background:rgba(0,255,136,0.1);color:var(--green);border:1px solid rgba(0,255,136,0.3);padding:2px 10px;border-radius:12px;font-size:0.75rem;font-family:'IBM Plex Mono',monospace;}
.badge-medium{background:rgba(255,204,0,0.1);color:var(--yellow);border:1px solid rgba(255,204,0,0.3);padding:2px 10px;border-radius:12px;font-size:0.75rem;font-family:'IBM Plex Mono',monospace;}
.badge-high{background:rgba(255,51,102,0.1);color:var(--red);border:1px solid rgba(255,51,102,0.3);padding:2px 10px;border-radius:12px;font-size:0.75rem;font-family:'IBM Plex Mono',monospace;}
.info-box{background:rgba(0,212,255,0.05);border-left:3px solid var(--accent);padding:12px 16px;margin:8px 0;border-radius:0 4px 4px 0;font-size:0.88rem;}
.warn-box{background:rgba(255,204,0,0.05);border-left:3px solid var(--yellow);padding:12px 16px;margin:8px 0;border-radius:0 4px 4px 0;font-size:0.88rem;}
.danger-box{background:rgba(255,51,102,0.07);border-left:3px solid var(--red);padding:12px 16px;margin:8px 0;border-radius:0 4px 4px 0;font-size:0.88rem;}
.ok-box{background:rgba(0,255,136,0.05);border-left:3px solid var(--green);padding:12px 16px;margin:8px 0;border-radius:0 4px 4px 0;font-size:0.88rem;}
.result-row{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:12px 16px;margin:6px 0;font-size:0.85rem;}
.result-row:hover{border-color:var(--accent);}
[data-testid="stTabs"] [role="tablist"]{border-bottom:1px solid var(--border)!important;gap:0!important;}
[data-testid="stTabs"] button{background:transparent!important;color:var(--muted)!important;border-radius:0!important;
  border-bottom:2px solid transparent!important;font-family:'IBM Plex Mono',monospace!important;
  font-size:0.8rem!important;letter-spacing:1px!important;padding:8px 18px!important;}
[data-testid="stTabs"] button[aria-selected="true"]{color:var(--accent)!important;border-bottom-color:var(--accent)!important;background:rgba(0,212,255,0.05)!important;}
[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:4px!important;}
[data-testid="stExpander"] summary{color:var(--text)!important;}
[data-testid="stSelectbox"] div,[data-testid="stMultiSelect"] div{background:var(--surface)!important;color:var(--text)!important;border-color:var(--border)!important;}
hr{border-color:var(--border)!important;}
.stProgress>div>div{background:var(--accent)!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}
.header-strip{display:flex;align-items:center;gap:16px;padding:20px 0 12px;border-bottom:1px solid var(--border);margin-bottom:24px;}
.shield-icon{font-size:2.5rem;}
.app-title{font-family:'IBM Plex Mono',monospace;font-size:1.8rem;color:var(--accent);letter-spacing:-1px;}
.app-sub{font-size:0.8rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-top:2px;}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:1rem;color:var(--accent);text-transform:uppercase;letter-spacing:2px;margin:20px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border);}
table{width:100%!important;}
[data-testid="stDataFrame"]{background:var(--surface)!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# DATABASE LAYER — SQLite persistence
# ══════════════════════════════════════════════════════════════════
DB_PATH = "finshield.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Banks table
    c.execute("""CREATE TABLE IF NOT EXISTS banks (
        code        TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        address     TEXT DEFAULT '',
        city        TEXT DEFAULT '',
        postal_code TEXT DEFAULT '',
        country     TEXT DEFAULT 'FR',
        bic         TEXT DEFAULT '',
        type        TEXT DEFAULT '',
        regafi_url  TEXT DEFAULT '',
        notes       TEXT DEFAULT '',
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # IBAN country structures table
    c.execute("""CREATE TABLE IF NOT EXISTS iban_countries (
        code        TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        length      INTEGER NOT NULL,
        structure   TEXT DEFAULT '',
        example     TEXT DEFAULT '',
        bban_format TEXT DEFAULT '',
        notes       TEXT DEFAULT ''
    )""")

    # OSINT reports history
    c.execute("""CREATE TABLE IF NOT EXISTS osint_reports (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        entity      TEXT NOT NULL,
        entity_type TEXT DEFAULT '',
        iban        TEXT DEFAULT '',
        score       INTEGER DEFAULT 0,
        niveau      TEXT DEFAULT '',
        recommandation TEXT DEFAULT '',
        resume      TEXT DEFAULT '',
        full_json   TEXT DEFAULT '',
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Watchlist
    c.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        entity      TEXT NOT NULL,
        entity_type TEXT DEFAULT '',
        reason      TEXT DEFAULT '',
        risk_level  TEXT DEFAULT '',
        added_by    TEXT DEFAULT '',
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

def seed_banks():
    """Seed the banks table with initial data if empty."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM banks")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    banks = [
        ("30004","BNP Paribas","16 BOULEVARD DES ITALIENS","PARIS","75009","FR","BNPAFRPP","Etablissement de crédit","",""),
        ("30003","Société générale","189 RUE D AUBERVILLIERS","PARIS CEDEX 18","75886","FR","SOGEFRPP","Etablissement de crédit","",""),
        ("30006","Crédit Agricole S.A.","12 PLACE DES ETATS UNIS","MONTROUGE","92120","FR","AGRIFRPP","Etablissement de crédit","",""),
        ("30002","CREDIT LYONNAIS (LCL)","18 rue de la République","LYON","69002","FR","CRLYFRPP","Etablissement de crédit","",""),
        ("30007","Natixis","30 AVENUE PIERRE MENDES FRANCE","PARIS 13","75013","FR","NATXFRPP","Etablissement de crédit","",""),
        ("20041","La Banque Postale","115 RUE DE SÈVRES","PARIS CEDEX 06","75275","FR","PSSTFRPP","Etablissement de crédit","",""),
        ("10107","BRED - Banque populaire","18 QUAI DE LA RAPEE","PARIS 12","75012","FR","BREDFRPP","Etablissement de crédit","",""),
        ("40618","Boursorama","18 QUAI DU POINT DU JOUR","BOULOGNE BILLANCOURT","92100","FR","BOUSFRPP","Etablissement de crédit","",""),
        ("30056","HSBC Continental Europe","38 AVENUE KLEBER","PARIS","75116","FR","CCFRFRPP","Etablissement de crédit","",""),
        ("30438","ING Bank NV","40 AVENUE DES TERROIRS DE FRANCE","PARIS 12","75012","FR","INGBFRPP","Etablissement de crédit","",""),
        ("30066","CIC","6 AVENUE DE PROVENCE","PARIS 09","75009","FR","CMCIFRPP","Etablissement de crédit","",""),
        ("30076","Crédit du Nord","28 PLACE RIHOUR","LILLE CEDEX","59023","FR","NORDFRPP","Etablissement de crédit","",""),
        ("16188","BPCE","50 AVENUE PIERRE MENDES FRANCE","PARIS 13","75013","FR","BPCEFRPP","Etablissement de crédit","",""),
        ("18359","Bpifrance","27-31 AVENUE DU GÉNÉRAL LECLERC","MAISONS - ALFORT","94710","FR","","Etablissement de crédit","",""),
        ("42559","Crédit coopératif","12 BOULEVARD PESARO","NANTERRE CEDEX","92024","FR","CCOPFRPP","Etablissement de crédit","",""),
        ("30788","Banque Neuflize OBC","3 AVENUE HOCHE","PARIS 08","75008","FR","NEIOFR22","Etablissement de crédit","",""),
        ("40978","Banque Palatine","42 RUE D'ANJOU","PARIS CEDEX 08","75382","FR","PALFFR22","Etablissement de crédit","",""),
        ("18370","ORANGE BANK","67 RUE ROBESPIERRE","MONTREUIL","93100","FR","","Etablissement de crédit","",""),
        ("28233","REVOLUT PAYMENTS UAB","3 RUE DE STOCKHOLM","PARIS","75008","FR","REVOLT21","Autre institution","",""),
        ("20433","N26 BANK GMBH","","","","DE","NTSBDEB1","Etablissement de crédit","",""),
        ("28033","KLARNA BANK AB","","","","SE","KLNOSE22","Etablissement de crédit","",""),
        ("19870","Carrefour banque","9-13 AVENUE DU LAC","EVRY-COURCOURONNES","91000","FR","","Etablissement de crédit","",""),
        ("12869","ONEY BANK","40 AVENUE DE FLANDRE","CROIX CEDEX","59964","FR","ONEYFRPP","Etablissement de crédit","",""),
        ("14940","Cofidis","61 AVENUE HALLEY","VILLENEUVE D'ASCQ CEDEX","59866","FR","","Etablissement de crédit","",""),
        ("16218","Bforbank","20 AVENUE ANDRÉ PROTHIN","PARIS LA DEFENSE CEDEX","92927","FR","","Etablissement de crédit","",""),
        ("31489","Crédit agricole CIB","12 PLACE DES ETATS-UNIS","Montrouge Cedex","92547","FR","BSUIFRPP","Etablissement de crédit","",""),
        ("43199","Crédit Foncier de France","19 RUE DES CAPUCINES","PARIS 01","75001","FR","","Etablissement de crédit","",""),
        ("25533","Goldman Sachs Bank Europe SE","5 Avenue Kléber","PARIS","75116","FR","GOLDFRPP","Etablissement de crédit","",""),
        ("30748","Lazard Frères Banque","121 BOULEVARD HAUSSMANN","PARIS 08","75008","FR","LAZAFRPP","Etablissement de crédit","",""),
        ("30758","UBS (France) S.A.","69 BOULEVARD HAUSSMANN","PARIS 08","75008","FR","UBSWFRPP","Etablissement de crédit","",""),
        ("11833","ICBC (Europe) SA","73 BOULEVARD HAUSSMANN","PARIS 08","75008","FR","ICBKFRPP","Etablissement de crédit","",""),
        ("30628","JPMorgan Chase bank","14 PLACE VENDOME","PARIS 01","75001","FR","CHASFRPP","Etablissement de crédit","",""),
        ("17789","Deutsche bank AG","3-5 avenue de Friedland","PARIS CEDEX 08","","FR","DEUTFRPP","Etablissement de crédit","",""),
        ("18769","Bank of China limited","23 AVENUE DE LA GRANDE ARMEE","PARIS 16","75116","FR","BKCHFRPP","Etablissement de crédit","",""),
        ("41189","BBVA","29 AVENUE DE L OPERA","PARIS 01","75001","FR","BBVAFRPP","Etablissement de crédit","",""),
        ("44729","Banco Santander SA","40 RUE DE COURCELLES","PARIS 08","75008","FR","BSCHFRPP","Etablissement de crédit","",""),
        ("30001","BANQUE DE FRANCE","1 RUE LA VRILLIERE","PARIS 01","75001","FR","BDFEFRPP","Banque centrale","",""),
        ("15208","Crédit municipal de Paris","55 RUE DES FRANCS-BOURGEOIS","PARIS CEDEX 04","75181","FR","","Etablissement de crédit","",""),
        ("12548","Axa banque","203-205 RUE CARNOT","FONTENAY-SOUS-BOIS CEDEX","94138","FR","AXABFRPP","Etablissement de crédit","",""),
        ("12240","Allianz banque","TOUR ALLIANZ ONE 1 COURS MICHELET","Paris La défense Cedex","92076","FR","","Etablissement de crédit","",""),
        ("13507","Banque populaire du Nord","847 AVENUE DE LA REPUBLIQUE","MARCQ EN BAROEUL","59700","FR","CCBPFRPP","Etablissement de crédit","",""),
        ("16807","BP Auvergne Rhône Alpes","4 BOULEVARD EUGENE DERUELLE","Lyon","69003","FR","CCBPFRPP","Etablissement de crédit","",""),
        ("17515","CE Ile-de-France","19 RUE DU LOUVRE","PARIS CEDEX 1","75021","FR","CEPAFRPP","Etablissement de crédit","",""),
        ("11315","Caisse d'Epargne CEPAC","PLACE ESTRANGIN PASTRÉ","MARSEILLE CEDEX 6","13254","FR","CEPAFRPP","Etablissement de crédit","",""),
        ("11188","RCI Banque","15 RUE D UZES","PARIS","75002","FR","RCIEFR22","Etablissement de crédit","",""),
        ("24599","Milleis Banque","32 AVENUE GEORGE V","PARIS 08","75008","FR","MILLFRPP","Etablissement de crédit","",""),
        ("19530","Amundi","91-93 BOULEVARD PASTEUR","PARIS CEDEX 15","75730","FR","","Etablissement de crédit","",""),
        ("45129","AFD","5 RUE ROLAND BARTHES","PARIS 12","75012","FR","","Autre institution","",""),
        ("18059","HSBC Bank Plc Paris Branch","38 AVENUE KLEBER","PARIS","75116","FR","CCFRFRPP","Etablissement de crédit","",""),
        ("14690","Monabanq.","61 AVENUE HALLEY","VILLENEUVE D ASCQ","59650","FR","","Etablissement de crédit","",""),
    ]
    c.executemany("""INSERT OR IGNORE INTO banks
        (code,name,address,city,postal_code,country,bic,type,regafi_url,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", banks)
    conn.commit()
    conn.close()

def seed_iban_countries():
    """Seed IBAN country structures from BCEE document + ISO standard."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM iban_countries")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    countries = [
        ("AL","Albanie",28,"ALkk bbbs sssx cccc cccc cccc cccc","AL47212110090000000235698741","8n,16c",""),
        ("AD","Andorre",24,"ADkk bbbb ssss cccc cccc cccc","AD1200012030200359100100","4n,4n,12c",""),
        ("AT","Autriche",20,"ATkk bbbb bccc cccc cccc","AT611904300234573201","5n,11n","AT61 1904 3002 3457 3201"),
        ("BE","Belgique",16,"BEkk bbbc cccc ccxx","BE62510007547061","3n,7n,2n","BE62 5100 0754 7061"),
        ("BG","Bulgarie",22,"BGkk bbbb ssss ttcc cccc cc","BG80BNBG96611020345678","4a,4n,2n,8c","BG80 BNBG 9661 1020 3456 78"),
        ("CH","Suisse",21,"CHkk bbbb bccc cccc cccc c","CH9300762011623852977","5n,12c","CH93 0076 2011 6238 5297 7"),
        ("CY","Chypre",28,"CYkk bbbs ssss cccc cccc cccc cccc","CY17002001280000001200527600","3n,5n,16c","CY17 0020 0128 0000 0012 0052 7600"),
        ("CZ","Rép. Tchèque",24,"CZkk bbbb ssss sscc cccc cccc","CZ6508000000192000145399","4n,6n,10n","CZ12 AAAA 2222 2222 2222 2222"),
        ("DE","Allemagne",22,"DEkk bbbb bbbb cccc cccc cc","DE89370400440532013000","8n,10n","DE89 3704 0044 0532 0130 00"),
        ("DK","Danemark",18,"DKkk bbbb cccc cccc cc","DK5000400440116243","4n,9n,1n","DK50 0040 0440 1162 43"),
        ("EE","Estonie",20,"EEkk bbss cccc cccc cccx","EE382200221020145399","2n,2n,11n,1n","EE38 2200 2210 2014 5399"),
        ("ES","Espagne",24,"ESkk bbbb gggg xxcc cccc cccc","ES9121000418450200051332","4n,4n,1n,1n,10n","ES07 0012 0345 0300 0006 7890"),
        ("FI","Finlande",18,"FIkk bbbb bbcc cccc cx","FI2112345600000785","6n,7n,1n","FI21 1234 5600 0007 85"),
        ("FR","France",27,"FRkk bbbb bggg ggcc cccc cccc cxx","FR7630006000011234567890189","5n,5n,11c,2n","FR14 2004 1010 0505 0001 3M02 606"),
        ("GB","Grande-Bretagne",22,"GBkk bbbb ssss sscc cccc cc","GB29NWBK60161331926819","4a,6n,8n","GB19 LOYD 3096 1700 7099 43"),
        ("GR","Grèce",27,"GRkk bbbs sssc cccc cccc cccc ccc","GR1601101250000000012300695","3n,4n,16n","GR11 0172 0500 0050 5000 8582 675"),
        ("HR","Croatie",21,"HRkk bbbb bbbc cccc cccc c","HR1210010051863000160","7n,10n","HR12 1001 0051 8630 0016 0"),
        ("HU","Hongrie",28,"HUkk bbbs sssk cccc cccc cccc cccx","HU42117730161111101800000000","3n,4n,1n,15n,1n","HU42 1177 3016 1111 1018 0000 0000"),
        ("IE","Irlande",22,"IEkk aaaa bbbb bbcc cccc cc","IE29AIBK93115212345678","4a,6n,8n","IE29 AIBK 931 1521 2345 678"),
        ("IS","Islande",26,"ISkk bbbb sscc cccc iiii iiii ii","IS140159260076545510730339","4n,2n,6n,10n","IS14 0159 2600 7654 5510 7303 39"),
        ("IT","Italie",27,"ITkk xbbb bbss sssc cccc cccc ccc","IT60X0542811101000000123456","1a,5n,5n,12c","IT40 S054 2811 1010 0000 0123 456"),
        ("LI","Liechtenstein",21,"LIkk bbbb bccc cccc cccc c","LI21088100002324013AA","5n,12c",""),
        ("LT","Lituanie",20,"LTkk bbbb bccc cccc cccc","LT121000011101001000","5n,11n","LT12 1000 0111 0100 1000"),
        ("LU","Luxembourg",20,"LUkk bbbc cccc cccc cccc","LU280019400644750000","3n,13c","LU28 0019 4006 4475 0000"),
        ("LV","Lettonie",21,"LVkk bbbb cccc cccc cccc c","LV80BANK0000435195001","4a,13c","LV80 BANK 0000 4351 9500 1"),
        ("MC","Monaco",27,"MCkk bbbb bggg ggcc cccc cccc cxx","MC5811222000010123456789030","5n,5n,11c,2n",""),
        ("MT","Malte",31,"MTkk bbbb ssss sccc cccc cccc cccc ccc","MT84MALT011000012345MTLCAST001S","4a,5n,18c","MT84 MALT 0110 0001 2345 MTLC AST0 01S"),
        ("NL","Pays-Bas",18,"NLkk bbbb cccc cccc cc","NL39RABO0300065264","4a,10n","NL39 RABO 0300 0652 64"),
        ("NO","Norvège",15,"NOkk bbbb cccc ccx","NO9386011117947","4n,6n,1n","NO93 8601 1117 947"),
        ("PL","Pologne",28,"PLkk bbbs sssx cccc cccc cccc cccc","PL27114020040000300201355387","8n,16n","PL27 1140 2004 0000 3002 0135 5387"),
        ("PT","Portugal",25,"PTkk bbbb ssss cccc cccc cccx x","PT50000201231234567890154","4n,4n,11n,2n","PT50 0002 0123 1234 5678 9015 4"),
        ("RO","Roumanie",24,"ROkk bbbb cccc cccc cccc cccc","RO49AAAA1B31007593840000","4a,16c","RO49 AAAA 1B31 0075 9384 0000"),
        ("SE","Suède",24,"SEkk bbbc cccc cccc cccc cccc","SE3550000000054910000003","3n,16n,1n","SE35 5000 0000 0549 1000 0003"),
        ("SI","Slovénie",19,"SIkk bbss sccc cccc cxx","SI56191000000123438","5n,8n,2n","SI56 6191 0000 0123 438"),
        ("SK","Slovaquie",24,"SKkk bbbb ssss sscc cccc cccc","SK3112000000198742637341","4n,6n,10n","SK31 1200 0000 1987 4263 7341"),
        ("SM","Saint-Marin",27,"SMkk xbbb bbss sssc cccc cccc ccc","SM86U0322509800000000270100","1a,5n,5n,12c",""),
        ("TR","Turquie",26,"TRkk bbbb bxcc cccc cccc cccc cc","TR330006100519786457841326","5n,1c,16c",""),
        ("MA","Maroc",28,"MAkk bbbb bsss sscc cccc cccc cccc","","3n,3n,2n,16n",""),
        ("TN","Tunisie",24,"TNkk bbss sccc cccc cccc cccc","","2n,3n,13n,2n",""),
        ("DZ","Algérie",26,"DZkk bbbb bsss sscc cccc cccc cc","","5n,5n,10n,2n",""),
        ("AE","Émirats Arabes Unis",23,"AEkk bbbc cccc cccc cccc ccc","","3n,16n",""),
        ("SA","Arabie Saoudite",24,"SAkk bbcc cccc cccc cccc cccc","","2n,18c",""),
        ("MU","Maurice",30,"MUkk bbbb bbss cccc cccc cccc cccc cc","","4a,2n,2n,12n,3n,3a",""),
    ]
    c.executemany("""INSERT OR IGNORE INTO iban_countries
        (code,name,length,bban_format,example,structure,notes) VALUES (?,?,?,?,?,?,?)""", countries)
    conn.commit()
    conn.close()

# Init DB on startup
init_db()
seed_banks()
seed_iban_countries()

# ══════════════════════════════════════════════════════════════════
# DB CRUD helpers
# ══════════════════════════════════════════════════════════════════
def db_get_banks(search=""):
    conn = get_db()
    if search:
        q = f"%{search.lower()}%"
        rows = conn.execute(
            "SELECT * FROM banks WHERE lower(name) LIKE ? OR code LIKE ? OR bic LIKE ? ORDER BY name",
            (q, q, q)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM banks ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_bank_by_code(code):
    conn = get_db()
    code_clean = code.lstrip("0")
    row = conn.execute("SELECT * FROM banks WHERE code=? OR code=?", (code, code_clean)).fetchone()
    if not row:
        # Try prefix match
        row = conn.execute("SELECT * FROM banks WHERE code LIKE ? LIMIT 1", (code[:4]+"%",)).fetchone()
    conn.close()
    return dict(row) if row else None

def db_upsert_bank(code, name, address, city, postal_code, country, bic, btype, notes):
    conn = get_db()
    conn.execute("""INSERT INTO banks (code,name,address,city,postal_code,country,bic,type,notes,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(code) DO UPDATE SET
        name=excluded.name, address=excluded.address, city=excluded.city,
        postal_code=excluded.postal_code, country=excluded.country, bic=excluded.bic,
        type=excluded.type, notes=excluded.notes, updated_at=CURRENT_TIMESTAMP""",
        (code, name, address, city, postal_code, country, bic, btype, notes))
    conn.commit()
    conn.close()

def db_delete_bank(code):
    conn = get_db()
    conn.execute("DELETE FROM banks WHERE code=?", (code,))
    conn.commit()
    conn.close()

def db_get_iban_country(code):
    conn = get_db()
    row = conn.execute("SELECT * FROM iban_countries WHERE code=?", (code.upper(),)).fetchone()
    conn.close()
    return dict(row) if row else None

def db_get_all_iban_countries():
    conn = get_db()
    rows = conn.execute("SELECT * FROM iban_countries ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_upsert_iban_country(code, name, length, bban_format, example, structure, notes):
    conn = get_db()
    conn.execute("""INSERT INTO iban_countries (code,name,length,bban_format,example,structure,notes)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(code) DO UPDATE SET
        name=excluded.name, length=excluded.length, bban_format=excluded.bban_format,
        example=excluded.example, structure=excluded.structure, notes=excluded.notes""",
        (code.upper(), name, length, bban_format, example, structure, notes))
    conn.commit()
    conn.close()

def db_save_report(entity, entity_type, iban, score, niveau, reco, resume, full_json):
    conn = get_db()
    conn.execute("""INSERT INTO osint_reports
        (entity,entity_type,iban,score,niveau,recommandation,resume,full_json)
        VALUES (?,?,?,?,?,?,?,?)""",
        (entity, entity_type, iban, score, niveau, reco, resume, full_json))
    conn.commit()
    conn.close()

def db_get_reports(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM osint_reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_watchlist():
    conn = get_db()
    rows = conn.execute("SELECT * FROM watchlist ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_add_watchlist(entity, entity_type, reason, risk_level, added_by):
    conn = get_db()
    conn.execute("INSERT INTO watchlist (entity,entity_type,reason,risk_level,added_by) VALUES (?,?,?,?,?)",
                 (entity, entity_type, reason, risk_level, added_by))
    conn.commit()
    conn.close()

def db_delete_watchlist(wid):
    conn = get_db()
    conn.execute("DELETE FROM watchlist WHERE id=?", (wid,))
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════════════════
# IBAN VALIDATION
# ══════════════════════════════════════════════════════════════════
def validate_iban(iban_raw: str) -> dict:
    iban = iban_raw.replace(" ", "").replace("-", "").upper()
    result = {
        "raw": iban, "formatted": " ".join(iban[i:i+4] for i in range(0, len(iban), 4)),
        "valid": False, "country": "", "bank_code": "",
        "branch_code": "", "account_no": "", "rib_key": "", "message": ""
    }
    if len(iban) < 5:
        result["message"] = "IBAN trop court"
        return result

    country = iban[:2]
    result["country"] = country

    # Check country exists
    country_info = db_get_iban_country(country)
    if country_info:
        expected_len = country_info["length"]
        if len(iban) != expected_len:
            result["message"] = f"Longueur incorrecte : {len(iban)} chars (attendu {expected_len} pour {country_info['name']})"
            return result

    # Mod-97 check
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        elif ch.isalpha():
            numeric += str(ord(ch) - 55)
        else:
            result["message"] = f"Caractère invalide : '{ch}'"
            return result

    if int(numeric) % 97 != 1:
        result["message"] = "❌ Clé de contrôle invalide (mod97 échoué)"
        return result

    result["valid"] = True
    result["message"] = "✅ IBAN valide"

    # Extract fields for FR (27) and MC (27)
    if country in ("FR", "MC") and len(iban) == 27:
        result["bank_code"]   = iban[4:9]
        result["branch_code"] = iban[9:14]
        result["account_no"]  = iban[14:25]
        result["rib_key"]     = iban[25:27]
    elif country == "LU" and len(iban) == 20:
        result["bank_code"] = iban[4:7]
    elif country == "BE" and len(iban) == 16:
        result["bank_code"] = iban[4:7]
    elif country == "DE" and len(iban) == 22:
        result["bank_code"] = iban[4:12]
    elif country == "GB" and len(iban) == 22:
        result["bank_code"] = iban[4:8]   # BIC prefix (4 chars)
    elif country == "NL" and len(iban) == 18:
        result["bank_code"] = iban[4:8]
    elif country == "ES" and len(iban) == 24:
        result["bank_code"] = iban[4:8]
    elif country == "IT" and len(iban) == 27:
        result["bank_code"] = iban[5:10]
    elif country == "CH" and len(iban) == 21:
        result["bank_code"] = iban[4:9]
    else:
        # Generic: take first 4-8 chars after check digits as bank code
        result["bank_code"] = iban[4:8]

    return result

# ══════════════════════════════════════════════════════════════════
# WEB / OSINT FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def check_opensanctions(name: str) -> dict:
    try:
        r = requests.get(
            f"https://api.opensanctions.org/search/default?q={quote_plus(name)}&limit=5",
            timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {"found": d.get("total", 0) > 0, "count": d.get("total", 0),
                    "results": d.get("results", [])[:5]}
    except:
        pass
    return {"found": False, "count": 0, "results": [], "error": "Non disponible"}

def search_web(query: str, num: int = 8) -> list:
    results = []
    # DuckDuckGo
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
                         headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select(".result")[:num]:
            a = item.find("a", class_="result__a")
            snip = item.find("a", class_="result__snippet")
            if a:
                results.append({"title": a.get_text(strip=True),
                                 "url": a.get("href",""),
                                 "snippet": snip.get_text(strip=True) if snip else ""})
    except:
        pass
    # Bing fallback
    if not results:
        try:
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(f"https://www.bing.com/search?q={quote_plus(query)}&count={num}",
                              headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for li in soup.select("li.b_algo")[:num]:
                h2 = li.find("h2")
                a  = h2.find("a") if h2 else None
                p  = li.find("p")
                if a:
                    results.append({"title": a.get_text(strip=True),
                                     "url": a.get("href",""),
                                     "snippet": p.get_text(strip=True) if p else ""})
        except:
            pass
    return results

def scrape_page(url: str, max_chars=3000) -> str:
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header","aside"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)[:max_chars]
    except:
        return ""

# ══════════════════════════════════════════════════════════════════
# KEYWORD-BASED RISK ENGINE  (100% gratuit, zéro API)
# ══════════════════════════════════════════════════════════════════

# Chaque catégorie : {mot: poids}  (poids 1–5, 5 = très grave)
RISK_KEYWORDS = {
    "sanctions": {
        # FR
        "sanction":5,"sanctionné":5,"sanctions":5,"ofac":5,"gel des avoirs":5,
        "liste noire":5,"blacklist":5,"embargo":4,"liste ue":4,"liste onu":4,
        "seco":4,"trésor américain":4,"amf sanction":5,"acpr sanction":5,
        "interdiction bancaire":5,"interdit bancaire":4,
        # EN
        "sanctioned":5,"blacklisted":5,"ofac list":5,"eu sanctions":4,
        "un sanctions":4,"asset freeze":5,"travel ban":4,
    },
    "fraud": {
        # FR
        "fraude":5,"frauduleux":5,"escroquerie":5,"arnaque":4,"abus de confiance":5,
        "détournement":5,"malversation":5,"falsification":4,"faux et usage de faux":5,
        "corruption":5,"corruptions":5,"pot-de-vin":5,"blanchiment":5,
        "blanchiment d'argent":5,"financement du terrorisme":5,"financement terrorisme":5,
        "abus de biens sociaux":4,"abus de position dominante":3,"tromperie":3,
        "publicité mensongère":2,"pratiques commerciales trompeuses":3,
        # EN
        "fraud":5,"fraudulent":5,"scam":4,"embezzlement":5,"money laundering":5,
        "bribery":5,"corruption":5,"forgery":4,"misappropriation":5,
        "terrorist financing":5,"ponzi":5,
    },
    "judicial": {
        # FR
        "condamné":5,"condamnation":5,"mis en examen":4,"garde à vue":3,
        "perquisition":3,"liquidation judiciaire":4,"redressement judiciaire":4,
        "faillite":4,"procédure collective":4,"tribunal correctionnel":4,
        "tribunal de commerce":3,"arrêt de cour":3,"jugement":3,"plainte":3,
        "dépôt de bilan":4,"dissolution":3,"peine de prison":5,"incarcéré":5,
        "inculpé":4,"mise en cause":3,"assigné en justice":3,"procès":3,
        "appel en justice":3,"arrêté":3,"interpellé":3,
        # EN
        "convicted":5,"conviction":5,"indicted":4,"arrested":4,"imprisoned":5,
        "bankruptcy":4,"liquidation":4,"sued":3,"lawsuit":3,"court ruling":3,
        "criminal charges":5,"plea guilty":5,"sentenced":5,
    },
    "reputation": {
        # FR
        "arnaqueur":4,"escroc":4,"mauvais payeur":3,"litige client":2,
        "plainte client":3,"avis négatif":2,"très mauvais":2,"déconseillé":2,
        "méfiez-vous":3,"alerte":3,"avertissement":3,"mise en garde":3,
        "signalement":3,"dénonciation":3,
        # EN
        "scammer":4,"bad reviews":2,"complaint":2,"warning":3,"alert":3,
        "avoid":2,"do not trust":3,"rip off":3,"negative":2,
    },
    "pep": {
        # FR
        "personnalité politique":3,"personnage politiquement exposé":4,"pep":3,
        "ministre":3,"député":3,"sénateur":3,"préfet":3,"ambassadeur":3,
        "élu":2,"fonctionnaire":2,"haut fonctionnaire":3,"magistrat":3,
        "dirigeant":2,"président":2,"directeur général":1,
        # EN
        "politically exposed":4,"politician":3,"minister":3,"senator":3,
        "ambassador":3,"official":2,"government":2,"public figure":2,
    },
    "positive": {
        # FR — ces mots réduisent le score
        "agréé":2,"accrédité":2,"certifié":2,"récompensé":2,"fiable":2,
        "reconnu":1,"bien noté":2,"excellent":1,"recommandé":2,"sérieux":1,
        "régulé":2,"autorisation":2,"license":2,"conforme":2,
        # EN
        "accredited":2,"certified":2,"award":1,"trusted":2,"reliable":2,
        "regulated":2,"licensed":2,"compliant":2,"reputable":2,
    },
}

# Domaines sources connus et leur crédibilité (multiplicateur)
SOURCE_CREDIBILITY = {
    "lemonde.fr":1.5,"lefigaro.fr":1.5,"liberation.fr":1.3,"bfmtv.com":1.3,
    "franceinfo.fr":1.4,"latribune.fr":1.4,"lesechos.fr":1.5,"capital.fr":1.3,
    "challenges.fr":1.3,"reuters.com":1.6,"bloomberg.com":1.6,"ft.com":1.6,
    "theguardian.com":1.5,"nytimes.com":1.5,"bbc.com":1.4,"wsj.com":1.5,
    "opensanctions.org":2.0,"legifrance.gouv.fr":2.0,"justice.fr":2.0,
    "bodacc.fr":1.8,"infogreffe.fr":1.8,"amf-france.org":2.0,"acpr.banque-france.fr":2.0,
    "interpol.int":2.0,"europol.europa.eu":2.0,"tracfin.gouv.fr":2.0,
    "tribunal.fr":1.8,"tribunaux.fr":1.8,
    "trustpilot.com":1.0,"avis-verifies.com":0.9,"google.com":0.8,
}

def _text_lower(s): return s.lower() if s else ""

def analyze_local(entity: str, search_results: list, scraped_texts: list, os_result: dict) -> dict:
    """
    Moteur d'analyse de risque 100% local, sans API payante.
    Analyse les titres, snippets et textes scrapés par catégories de risque pondérées.
    """
    entity_low = entity.lower()
    scores_by_cat = {k: 0 for k in RISK_KEYWORDS}
    hits_by_cat   = {k: [] for k in RISK_KEYWORDS}
    negative_news = []
    all_text_sources = []

    # Combine all textual data
    for r in search_results:
        combined = f"{r.get('title','')} {r.get('snippet','')}"
        domain = urlparse(r.get("url","")).netloc.replace("www.","")
        cred = SOURCE_CREDIBILITY.get(domain, 1.0)
        all_text_sources.append({"text": combined, "title": r.get("title",""),
                                   "url": r.get("url",""), "domain": domain, "cred": cred})
    for t in scraped_texts:
        all_text_sources.append({"text": t, "title": "", "url": "", "domain": "", "cred": 1.0})

    # Score each source against each category
    for src in all_text_sources:
        txt = _text_lower(src["text"])
        for cat, kws in RISK_KEYWORDS.items():
            cat_hits = []
            for kw, weight in kws.items():
                if kw in txt:
                    # Check entity name proximity (bonus if entity name nearby)
                    idx = txt.find(kw)
                    context_window = txt[max(0,idx-120):idx+120]
                    proximity_bonus = 1.5 if entity_low[:6] in context_window else 1.0
                    effective_weight = weight * src["cred"] * proximity_bonus
                    cat_hits.append((kw, round(effective_weight, 1)))
                    scores_by_cat[cat] += effective_weight

            # If negative hits and has title → candidate for negative_news
            if cat not in ("positive",) and cat_hits and src.get("title"):
                neg_score = sum(w for _,w in cat_hits)
                if neg_score >= 3 and src.get("title"):
                    # Determine nature
                    nature_map = {"sanctions":"Sanction / Liste noire","fraud":"Fraude / Corruption",
                                  "judicial":"Litige judiciaire","reputation":"Réputation négative","pep":"PEP"}
                    gravite = "eleve" if neg_score >= 8 else ("moyen" if neg_score >= 4 else "faible")
                    negative_news.append({
                        "titre": src["title"][:100],
                        "source": src.get("domain",""),
                        "url": src.get("url",""),
                        "date": "",
                        "nature": nature_map.get(cat, cat),
                        "gravite": gravite,
                        "mots_cles": [kw for kw,_ in cat_hits[:4]],
                        "score_brut": round(neg_score, 1),
                    })

    # Deduplicate negative_news by title similarity
    seen_titles = set()
    neg_dedup = []
    for n in sorted(negative_news, key=lambda x: x["score_brut"], reverse=True):
        key = n["titre"][:40].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            neg_dedup.append(n)

    # OpenSanctions adds to sanctions score heavily
    if os_result.get("found"):
        scores_by_cat["sanctions"] += os_result["count"] * 15

    # Compute final risk score
    raw_neg = (scores_by_cat["sanctions"] * 2.5 +
               scores_by_cat["fraud"]     * 2.0 +
               scores_by_cat["judicial"]  * 1.8 +
               scores_by_cat["reputation"]* 1.0 +
               scores_by_cat["pep"]       * 0.8)
    positive_offset = scores_by_cat["positive"] * 3

    # Normalize to 0-100
    score = min(100, max(0, int(raw_neg * 2.5 - positive_offset)))

    # Determine niveau
    if score >= 70:   niveau = "CRITIQUE"
    elif score >= 45: niveau = "ELEVE"
    elif score >= 20: niveau = "MODERE"
    else:             niveau = "FAIBLE"

    # Recommandation
    if score >= 60 or os_result.get("found") or scores_by_cat["sanctions"] > 5:
        reco = "REFUSER"
    elif score >= 25 or len(neg_dedup) >= 3:
        reco = "VIGILANCE_RENFORCEE"
    else:
        reco = "ACCEPTER"

    # Sanctions flag
    sanctions_trouve = os_result.get("found", False) or scores_by_cat["sanctions"] > 3
    sanctions_details = ""
    if os_result.get("found"):
        sanctions_details = f"{os_result['count']} résultat(s) OpenSanctions : " + \
            ", ".join(r.get("caption","") for r in os_result.get("results",[])[:2])
    elif scores_by_cat["sanctions"] > 3:
        all_sanc_kws = [kw for src in all_text_sources
                        for kw in RISK_KEYWORDS["sanctions"] if kw in _text_lower(src["text"])]
        sanctions_details = "Mots-clés détectés : " + ", ".join(set(all_sanc_kws[:5]))

    # Litiges flag
    litiges_trouve = scores_by_cat["judicial"] > 4
    litiges_details = ""
    if litiges_trouve:
        jud_kws = set()
        for src in all_text_sources:
            for kw in RISK_KEYWORDS["judicial"]:
                if kw in _text_lower(src["text"]):
                    jud_kws.add(kw)
        litiges_details = "Indicateurs : " + ", ".join(list(jud_kws)[:6])

    # PEP flag
    pep_trouve = scores_by_cat["pep"] > 3
    pep_details = "Exposition à des personnes politiquement exposées détectée." if pep_trouve else ""

    # Reputation summary
    rep_score = scores_by_cat["reputation"]
    pos_score = scores_by_cat["positive"]
    if rep_score > pos_score * 2:
        rep_notations = f"Réputation dégradée (score négatif : {round(rep_score,1)}, positif : {round(pos_score,1)})"
    elif pos_score > rep_score:
        rep_notations = f"Réputation globalement positive (score positif : {round(pos_score,1)})"
    else:
        rep_notations = "Réputation neutre ou insuffisamment documentée."

    # Build resume
    nb_neg = len(neg_dedup)
    sources_count = len([s for s in all_text_sources if s.get("domain")])
    resume_parts = [f"Analyse basée sur {sources_count} sources web et {len(scraped_texts)} pages lues."]
    if nb_neg:
        resume_parts.append(f"{nb_neg} signal(aux) négatif(s) détecté(s) (fraude, litiges, réputation).")
    else:
        resume_parts.append("Aucun signal négatif significatif identifié dans les sources consultées.")
    if sanctions_trouve:
        resume_parts.append("⚠️ Des indicateurs de sanctions ou listes de restriction ont été détectés.")
    elif score < 20:
        resume_parts.append("Profil de risque faible — aucune alerte majeure.")

    # Facteurs aggravants / atténuants
    aggravants = []
    attenuants = []
    if os_result.get("found"):
        aggravants.append(f"{os_result['count']} entrée(s) dans les bases de sanctions internationales (OpenSanctions)")
    if scores_by_cat["fraud"] > 5:
        aggravants.append(f"Mots-clés de fraude/corruption fortement représentés (score : {round(scores_by_cat['fraud'],1)})")
    if scores_by_cat["judicial"] > 4:
        aggravants.append(f"Indicateurs de procédures judiciaires détectés (score : {round(scores_by_cat['judicial'],1)})")
    if nb_neg >= 5:
        aggravants.append(f"{nb_neg} actualités négatives distinctes dans les résultats")
    if scores_by_cat["pep"] > 3:
        aggravants.append("Exposition potentielle à des PEP (personnes politiquement exposées)")
    if pos_score > 5:
        attenuants.append(f"Indicateurs de conformité/certification présents (score positif : {round(pos_score,1)})")
    if nb_neg == 0:
        attenuants.append("Aucune actualité négative directement identifiable")
    if not os_result.get("found"):
        attenuants.append("Absent des listes de sanctions OpenSanctions consultées")
    if scores_by_cat["sanctions"] == 0:
        attenuants.append("Aucun mot-clé de sanction détecté dans les sources")

    # Confidence: based on number of results
    if sources_count >= 15:
        confidence = "ELEVEE"
    elif sources_count >= 6:
        confidence = "MOYENNE"
    else:
        confidence = "FAIBLE"

    return {
        "score_risque": score,
        "niveau_risque": niveau,
        "resume_executif": " ".join(resume_parts),
        "negative_news": neg_dedup[:15],
        "sanctions": {"trouve": sanctions_trouve, "details": sanctions_details},
        "litiges_judiciaires": {"trouve": litiges_trouve, "details": litiges_details},
        "pep_exposure": {"trouve": pep_trouve, "details": pep_details},
        "reputation_notations": rep_notations,
        "facteurs_aggravants": aggravants,
        "facteurs_attenuants": attenuants,
        "recommandation": reco,
        "sources_consultees": list(set(s["domain"] for s in all_text_sources if s.get("domain")))[:15],
        "confiance_analyse": confidence,
        "scores_categories": {k: round(v,1) for k,v in scores_by_cat.items()},
        "moteur": "local_keywords",
    }


def analyze_with_groq(entity, search_results, scraped_texts, groq_key) -> dict:
    """
    Option gratuite : Groq API (llama-3.1-8b-instant, gratuit jusqu'à 14 400 req/jour).
    Clé gratuite sur console.groq.com
    """
    ctx = []
    for i, sr in enumerate(search_results[:12]):
        ctx.append(f"[S{i+1}] {sr.get('title','')} | {sr.get('snippet','')[:180]}")
    for i, t in enumerate(scraped_texts[:3]):
        if t.strip():
            ctx.append(f"[P{i+1}] {t[:600]}")

    prompt = f"""Tu es un analyste KYC/AML expert. Entité: «{entity}»

Sources OSINT:
{chr(10).join(ctx)}

Réponds UNIQUEMENT avec ce JSON (aucun texte autour):
{{"score_risque":0,"niveau_risque":"FAIBLE","resume_executif":"","negative_news":[{{"titre":"","source":"","date":"","nature":"","gravite":"faible","url":""}}],"sanctions":{{"trouve":false,"details":""}},"litiges_judiciaires":{{"trouve":false,"details":""}},"pep_exposure":{{"trouve":false,"details":""}},"reputation_notations":"","facteurs_aggravants":[],"facteurs_attenuants":[],"recommandation":"ACCEPTER","sources_consultees":[],"confiance_analyse":"MOYENNE"}}"""

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": [{"role":"user","content":prompt}],
                  "max_tokens": 1800, "temperature": 0.1},
            timeout=30)
        if r.status_code == 200:
            raw = r.json()["choices"][0]["message"]["content"].strip()
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            result = json.loads(raw)
            result["moteur"] = "groq_llama3"
            return result
    except Exception as e:
        pass
    return None


def analyze_with_ollama(entity, search_results, scraped_texts) -> dict:
    """
    Option 100% locale et gratuite : Ollama (llama3, mistral, etc.)
    Requiert Ollama installé localement : https://ollama.com
    """
    ctx = []
    for i, sr in enumerate(search_results[:10]):
        ctx.append(f"[S{i+1}] {sr.get('title','')} | {sr.get('snippet','')[:150]}")

    prompt = f"""Analyste KYC. Entité: «{entity}»
Sources: {chr(10).join(ctx)}
Réponds UNIQUEMENT en JSON: {{"score_risque":0,"niveau_risque":"FAIBLE","resume_executif":"","negative_news":[],"sanctions":{{"trouve":false,"details":""}},"litiges_judiciaires":{{"trouve":false,"details":""}},"pep_exposure":{{"trouve":false,"details":""}},"reputation_notations":"","facteurs_aggravants":[],"facteurs_attenuants":[],"recommandation":"ACCEPTER","confiance_analyse":"MOYENNE"}}"""

    try:
        r = requests.post("http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=60)
        if r.status_code == 200:
            raw = r.json().get("response","").strip()
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            result = json.loads(raw)
            result["moteur"] = "ollama_local"
            return result
    except:
        pass
    return None

# ══════════════════════════════════════════════════════════════════
# PDF GENERATION
# ══════════════════════════════════════════════════════════════════
def generate_pdf_report(entity, iban_result, bank_info, os_result, analysis):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=18*mm, rightMargin=18*mm,
                             topMargin=16*mm, bottomMargin=16*mm)

    BG    = HexColor("#0a0d14"); SURF  = HexColor("#111520")
    BORD  = HexColor("#1e2535"); ACC   = HexColor("#00d4ff")
    GREEN = HexColor("#00cc66"); RED   = HexColor("#ff3366")
    YEL   = HexColor("#ffcc00"); TEXT  = HexColor("#c8d6e5")
    MUTED = HexColor("#5a6a7a"); ACC2  = HexColor("#ff6b35")

    styles = getSampleStyleSheet()
    def S(nm, **kw):
        return ParagraphStyle(nm, parent=styles["Normal"], **kw)

    sTitle = S("T", fontSize=18, textColor=ACC,  fontName="Helvetica-Bold")
    sH1    = S("H1",fontSize=11, textColor=ACC,  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=5)
    sH2    = S("H2",fontSize=9,  textColor=TEXT, fontName="Helvetica-Bold", spaceBefore=8,  spaceAfter=3)
    sBody  = S("B", fontSize=8.5,textColor=TEXT, fontName="Helvetica",     spaceAfter=3,  leading=13)
    sSmall = S("Sm",fontSize=7.5,textColor=MUTED,fontName="Helvetica",     spaceAfter=2)
    sMono  = S("Mo",fontSize=8,  textColor=ACC2, fontName="Courier",       spaceAfter=2)

    niveau = analysis.get("niveau_risque","N/A")
    score  = analysis.get("score_risque","N/A")
    reco   = analysis.get("recommandation","N/A")
    rcolor = {"FAIBLE":GREEN,"MODERE":YEL,"ELEVE":ACC2,"CRITIQUE":RED}.get(niveau,MUTED)
    rccolor= {"ACCEPTER":GREEN,"VIGILANCE_RENFORCEE":YEL,"REFUSER":RED}.get(reco,MUTED)

    story = []

    # Header
    story.append(Table([["🛡️  FinShield OSINT — Rapport de Conformité",
                          f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}"]],
        colWidths=[120*mm, 52*mm],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BG),
            ("TEXTCOLOR",(0,0),(0,0),ACC), ("TEXTCOLOR",(1,0),(1,0),MUTED),
            ("FONTNAME",(0,0),(0,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(0,0),14),
            ("FONTSIZE",(1,0),(1,0),8),("ALIGN",(1,0),(1,0),"RIGHT"),
            ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ])))
    story.append(HRFlowable(width="100%",thickness=1.5,color=ACC,spaceAfter=14))

    # Entity + score box
    story.append(Paragraph(f"Entité analysée : <b>{entity}</b>", sH1))
    story.append(Table(
        [[f"Score : {score}/100", f"Niveau : {niveau}", f"Recommandation : {reco}",
          f"Confiance : {analysis.get('confiance_analyse','N/A')}"]],
        colWidths=[38*mm,38*mm,60*mm,36*mm],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),SURF),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("TEXTCOLOR",(0,0),(0,0),TEXT),
            ("TEXTCOLOR",(1,0),(1,0),rcolor), ("FONTNAME",(1,0),(1,0),"Helvetica-Bold"),
            ("TEXTCOLOR",(2,0),(2,0),rccolor),("FONTNAME",(2,0),(2,0),"Helvetica-Bold"),
            ("TEXTCOLOR",(3,0),(3,0),MUTED),
            ("BOX",(0,0),(-1,-1),0.5,BORD),("GRID",(0,0),(-1,-1),0.5,BORD),
        ])))
    story.append(Spacer(1,8))

    # Summary
    story.append(Paragraph("Résumé exécutif", sH1))
    story.append(Paragraph(analysis.get("resume_executif","Non disponible."), sBody))
    story.append(HRFlowable(width="100%",thickness=0.5,color=BORD,spaceAfter=6))

    # IBAN section
    if iban_result and iban_result.get("raw"):
        story.append(Paragraph("Vérification IBAN", sH1))
        rows = [["Champ","Valeur"]]
        fields = [("IBAN formaté",iban_result.get("formatted","")),
                  ("Statut",iban_result.get("message","")),
                  ("Pays",iban_result.get("country","")),
                  ("Code banque",iban_result.get("bank_code","")),
                  ("Code guichet",iban_result.get("branch_code","")),
                  ("N° de compte",iban_result.get("account_no","")),
                  ("Clé RIB",iban_result.get("rib_key",""))]
        for f,v in fields:
            if v:
                rows.append([f,v])
        if bank_info:
            rows += [("Banque",bank_info.get("name","")),
                     ("Adresse",f"{bank_info.get('address','')} {bank_info.get('city','')} {bank_info.get('postal_code','')}".strip()),
                     ("BIC",bank_info.get("bic","")),
                     ("Type",bank_info.get("type",""))]
        t = Table(rows, colWidths=[48*mm,124*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),
            ("TEXTCOLOR",(0,1),(0,-1),MUTED),("TEXTCOLOR",(1,1),(-1,-1),TEXT),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),
            ("GRID",(0,0),(-1,-1),0.3,BORD),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(t)
        story.append(Spacer(1,8))

    # Regulatory checks
    story.append(Paragraph("Vérifications Réglementaires (KYC/AML)", sH1))
    san = analysis.get("sanctions",{})
    lit = analysis.get("litiges_judiciaires",{})
    pep = analysis.get("pep_exposure",{})
    rcheck = [["Catégorie","Résultat","Détails"],
              ["Sanctions intl","TROUVÉ" if san.get("trouve") else "Non trouvé", san.get("details","")[:90]],
              ["OpenSanctions",f"{os_result.get('count',0)} résultat(s)",
               ", ".join(r.get("caption","") for r in os_result.get("results",[])[:2])[:90]],
              ["Litiges judiciaires","TROUVÉ" if lit.get("trouve") else "Non trouvé", lit.get("details","")[:90]],
              ["Exposition PEP","TROUVÉ" if pep.get("trouve") else "Non trouvé", pep.get("details","")[:90]]]
    t = Table(rcheck, colWidths=[42*mm,30*mm,100*mm])
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),
        ("TEXTCOLOR",(0,1),(-1,-1),TEXT),
        ("GRID",(0,0),(-1,-1),0.3,BORD),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ])
    for i in range(1,5):
        val = rcheck[i][1]
        col = RED if val == "TROUVÉ" or (i==2 and os_result.get("count",0)>0) else GREEN
        ts.add("TEXTCOLOR",(1,i),(1,i),col)
        ts.add("FONTNAME",(1,i),(1,i),"Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1,8))

    # Negative news
    neg = analysis.get("negative_news",[])
    story.append(Paragraph("Actualités Négatives Détectées", sH1))
    if neg:
        nh = [["Titre","Source","Nature","Gravité"]]
        for n in neg[:10]:
            nh.append([n.get("titre","")[:70], n.get("source","")[:25],
                       n.get("nature","")[:30], n.get("gravite","").upper()])
        t = Table(nh, colWidths=[80*mm,30*mm,40*mm,22*mm])
        gmap = {"FAIBLE":GREEN,"MOYEN":YEL,"ELEVE":RED}
        ts2 = TableStyle([
            ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),7.5),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),("TEXTCOLOR",(0,1),(-1,-1),TEXT),
            ("GRID",(0,0),(-1,-1),0.3,BORD),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ])
        for i,n in enumerate(neg[:10],1):
            c = gmap.get(n.get("gravite","").upper(),MUTED)
            ts2.add("TEXTCOLOR",(3,i),(3,i),c)
            ts2.add("FONTNAME",(3,i),(3,i),"Helvetica-Bold")
        t.setStyle(ts2)
        story.append(t)
    else:
        story.append(Paragraph("Aucune actualité négative identifiée dans les sources consultées.", sBody))
    story.append(Spacer(1,6))

    # Factors
    fa = analysis.get("facteurs_aggravants",[])
    fat = analysis.get("facteurs_attenuants",[])
    if fa or fat:
        story.append(Paragraph("Analyse des Facteurs de Risque", sH1))
        col1 = [Paragraph("⚠ Facteurs aggravants", S("fah",fontSize=8.5,textColor=RED,fontName="Helvetica-Bold"))]
        for f in fa: col1.append(Paragraph(f"• {f}", sBody))
        col2 = [Paragraph("✓ Facteurs atténuants", S("fat",fontSize=8.5,textColor=GREEN,fontName="Helvetica-Bold"))]
        for f in fat: col2.append(Paragraph(f"• {f}", sBody))
        story.append(Table([[col1,col2]], colWidths=[87*mm,87*mm],
            style=TableStyle([
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("BACKGROUND",(0,0),(-1,-1),BG),
                ("GRID",(0,0),(-1,-1),0.3,BORD),
                ("TOPPADDING",(0,0),(-1,-1),8),("LEFTPADDING",(0,0),(-1,-1),8),
            ])))
        story.append(Spacer(1,8))

    # Footer
    story.append(HRFlowable(width="100%",thickness=0.5,color=BORD,spaceAfter=4))
    story.append(Paragraph(
        f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} · FinShield OSINT v2 · "
        f"CONFIDENTIEL — Usage interne uniquement · Ce rapport est informatif et ne constitue pas un avis juridique.",
        sSmall))

    doc.build(story)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='font-family:IBM Plex Mono,monospace;color:#00d4ff;font-size:1.1rem;margin-bottom:4px;'>🛡️ FinShield OSINT</div>
    <div style='font-size:0.7rem;color:#5a6a7a;letter-spacing:2px;margin-bottom:20px;'>COMPLIANCE · INTELLIGENCE · v2.0</div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style='font-size:0.72rem;color:#5a6a7a;line-height:1.8;margin-bottom:8px;'>
    <b style='color:#00ff88;'>✅ Moteur local actif — aucune API requise</b><br>
    Analyse par mots-clés pondérés, scoring multi-catégories, 100% gratuit.
    </div>""", unsafe_allow_html=True)

    with st.expander("⚡ Booster avec un LLM gratuit (optionnel)"):
        st.markdown("""<div style='font-size:0.72rem;color:#5a6a7a;line-height:1.8;'>
        <b style='color:#ffcc00;'>Option A — Groq (cloud gratuit)</b><br>
        Clé gratuite sur <a href='https://console.groq.com' target='_blank' style='color:#00d4ff;'>console.groq.com</a><br>
        Modèle : llama-3.1-8b-instant · 14 400 req/jour offerts<br><br>
        <b style='color:#ffcc00;'>Option B — Ollama (100% local et privé)</b><br>
        Installer depuis <a href='https://ollama.com' target='_blank' style='color:#00d4ff;'>ollama.com</a> puis :<br>
        <code>ollama pull llama3.2</code><br>
        L app detecte automatiquement Ollama si actif sur localhost:11434.
        </div>""", unsafe_allow_html=True)
        api_key = st.text_input("Cle Groq (optionnelle)", type="password",
                                 placeholder="gsk_...", key="groq_key",
                                 help="Groq gratuit : 14 400 req/jour. Laissez vide pour moteur local.")
    st.markdown("---")

    # DB stats
    conn = get_db()
    nb_banks    = conn.execute("SELECT COUNT(*) FROM banks").fetchone()[0]
    nb_ibancountries = conn.execute("SELECT COUNT(*) FROM iban_countries").fetchone()[0]
    nb_reports  = conn.execute("SELECT COUNT(*) FROM osint_reports").fetchone()[0]
    nb_watch    = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
    conn.close()

    st.markdown(f"""
    <div style='font-size:0.72rem;color:#5a6a7a;line-height:2.0;'>
    <b style='color:#c8d6e5;'>Base de données</b><br>
    🏦 <span style='color:#00d4ff;'>{nb_banks}</span> banques indexées<br>
    🌍 <span style='color:#00d4ff;'>{nb_ibancountries}</span> pays IBAN supportés<br>
    📋 <span style='color:#00d4ff;'>{nb_reports}</span> rapports générés<br>
    👁 <span style='color:#00d4ff;'>{nb_watch}</span> entités sous surveillance<br>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.caption("SQLite local · Données persistantes")

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class='header-strip'>
  <span class='shield-icon'>🛡️</span>
  <div>
    <div class='app-title'>FinShield OSINT</div>
    <div class='app-sub'>Conformité · Due Diligence · Intelligence Financière</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏦  VÉRIFICATION IBAN",
    "🔍  ANALYSE OSINT",
    "📋  RECHERCHE BANQUE",
    "🗄️  GESTION BASE DE DONNÉES",
    "📁  HISTORIQUE & SURVEILLANCE",
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — IBAN VERIFICATION
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Vérification IBAN")
    st.markdown("<div class='info-box'>Supporte tous les pays IBAN (43 pays, norme ISO 13616). Validation mod-97, décomposition complète, identification banque via base locale.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        iban_input = st.text_input("IBAN", placeholder="FR76 3000 4000 0000 0000 0000 000  ·  LU28 0019 4006 4475 0000  ·  DE89 3704 0044 0532 0130 00")
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        check_btn = st.button("▶ VÉRIFIER", key="btn_iban")

    if check_btn and iban_input:
        res = validate_iban(iban_input)
        country_info = db_get_iban_country(res["country"]) if res["country"] else None

        # Status banner
        if res["valid"]:
            st.markdown(f"<div class='ok-box'>{res['message']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='danger-box'>{res['message']}</div>", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns([1.2, 1, 1])

        with col_a:
            st.markdown("#### Décomposition")
            fields = [
                ("IBAN formaté", res.get("formatted","")),
                ("Pays", f"{res.get('country','')} — {country_info['name'] if country_info else 'Inconnu'}"),
                ("Longueur", f"{len(res['raw'])} car. / {country_info['length'] if country_info else '?'} attendus"),
                ("Code banque", res.get("bank_code","")),
                ("Code guichet", res.get("branch_code","")),
                ("N° compte", res.get("account_no","")),
                ("Clé RIB", res.get("rib_key","")),
            ]
            for label, val in fields:
                if val and val.strip():
                    st.markdown(f"""
                    <div class='result-row'>
                    <span style='color:#5a6a7a;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;'>{label}</span><br>
                    <span style='font-family:IBM Plex Mono,monospace;font-size:0.88rem;'>{val}</span>
                    </div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown("#### Structure du pays")
            if country_info:
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='label'>Pays</div>
                  <div class='value' style='font-size:1rem;'>{country_info['name']} ({country_info['code']})</div>
                  <div class='sub'>Longueur : {country_info['length']} caractères</div>
                  <div class='sub' style='font-family:IBM Plex Mono,monospace;font-size:0.78rem;margin-top:6px;'>{country_info.get('bban_format','')[:50]}</div>
                </div>""", unsafe_allow_html=True)
                if country_info.get("example"):
                    st.markdown(f"<div class='info-box'>Exemple : <code>{country_info['example']}</code></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='warn-box'>Pays non référencé dans la base</div>", unsafe_allow_html=True)

        with col_c:
            st.markdown("#### Banque identifiée")
            if res.get("bank_code"):
                bank = db_get_bank_by_code(res["bank_code"])
                if bank:
                    bic_str = f" · BIC: {bank['bic']}" if bank.get("bic") else ""
                    st.markdown(f"""
                    <div class='metric-card'>
                      <div class='label'>Établissement</div>
                      <div class='value' style='font-size:0.9rem;line-height:1.4;'>{bank['name']}</div>
                      <div class='sub'>{bank.get('address','')} {bank.get('city','')}</div>
                      <div class='sub'>{bank.get('postal_code','')} {bank.get('country','')}</div>
                      <div style='margin-top:6px;font-size:0.75rem;color:#00d4ff;'>{bic_str}</div>
                      <div style='margin-top:6px;'><span class='badge-low'>{bank.get('type','')}</span></div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-box'>🔗 Vérifier sur <a href='https://www.regafi.fr' target='_blank' style='color:#00d4ff;'>REGAFI (ACPR)</a></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='warn-box'>⚠️ Code <b>{res['bank_code']}</b> non trouvé dans la base.<br><small>Ajoutez-la dans l'onglet <b>Gestion Base</b></small></div>", unsafe_allow_html=True)

        # Country reference table
        with st.expander("🌍 Référentiel IBAN — Tous les pays supportés"):
            all_countries = db_get_all_iban_countries()
            df_c = pd.DataFrame(all_countries)[["code","name","length","example"]]
            df_c.columns = ["Code","Pays","Longueur","Exemple"]
            st.dataframe(df_c, use_container_width=True, height=400)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — OSINT ANALYSIS
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Analyse OSINT & Due Diligence")
    st.markdown("""<div class='info-box'>
    Pipeline automatisé : OpenSanctions → web multi-requêtes (fraude, sanctions, litiges, réputation) →
    scraping → analyse IA Claude → score de risque + rapport PDF exportable.
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        entity_input = st.text_input("Entité à analyser", placeholder="Nom complet personne ou entreprise", key="entity_osint")
    with col2:
        entity_type = st.selectbox("Type", ["Entreprise","Personne physique","Groupe bancaire","Autre"])
    with col3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        launch_btn = st.button("▶ LANCER L'ANALYSE", key="btn_osint")

    with st.expander("🔗 Options avancées"):
        c1, c2 = st.columns(2)
        with c1:
            linked_iban = st.text_input("IBAN lié (optionnel)", key="linked_iban")
            add_to_watch = st.checkbox("Ajouter à la liste de surveillance après analyse")
        with c2:
            extra_context = st.text_area("Contexte additionnel (pays, secteur, notes…)", height=80, key="extra_ctx")

    if launch_btn and entity_input:
        if not api_key:
            st.markdown("<div class='danger-box'>❌ Clé API Anthropic requise. Renseignez-la dans la barre latérale.</div>", unsafe_allow_html=True)
        else:
            prog  = st.progress(0)
            stat  = st.empty()
            all_results, scraped = [], []

            # Step 1 — OpenSanctions
            stat.markdown("🔎 **[1/4]** Interrogation OpenSanctions…")
            os_result = check_opensanctions(entity_input)
            prog.progress(10)

            # Step 2 — Multi-query web search
            queries = [
                f'"{entity_input}" fraude arnaque escroquerie',
                f'"{entity_input}" condamné tribunal jugement peine',
                f'"{entity_input}" sanctions AMF ACPR autorité',
                f'"{entity_input}" liquidation judiciaire redressement faillite',
                f'"{entity_input}" blanchiment financement terrorisme',
                f'"{entity_input}" plainte client avis négatif',
                f'site:infogreffe.fr "{entity_input}"',
                f'site:bodacc.fr "{entity_input}"',
                f'"{entity_input}" Trustpilot avis',
                f'"{entity_input}" scandal corruption fraud',
            ]
            stat.markdown(f"🌐 **[2/4]** Recherche web ({len(queries)} requêtes ciblées)…")
            for i, q in enumerate(queries):
                r = search_web(q, num=5)
                all_results.extend(r)
                prog.progress(10 + int((i+1)/len(queries)*40))
                time.sleep(0.15)

            # Step 3 — Scraping
            stat.markdown("📄 **[3/4]** Lecture des pages pertinentes…")
            seen = set()
            for r in all_results[:20]:
                dom = urlparse(r.get("url","")).netloc
                if dom and dom not in seen and len(scraped) < 5:
                    seen.add(dom)
                    t = scrape_page(r["url"])
                    if t:
                        scraped.append(t)
            prog.progress(65)

            # IBAN
            iban_data, bank_data = {}, {}
            if linked_iban:
                iban_data = validate_iban(linked_iban)
                if iban_data.get("bank_code"):
                    b = db_get_bank_by_code(iban_data["bank_code"])
                    if b:
                        bank_data = b

            # Step 4 — Analysis (local engine + optional LLM boost)
            moteur_label = "🔍 Moteur local (mots-clés)"
            analysis = None

            # Try Ollama first if no Groq key (fully local)
            if not api_key:
                stat.markdown("🔍 **[4/4]** Analyse locale (mots-clés pondérés)…")
                try:
                    ollama_result = analyze_with_ollama(entity_input, all_results, scraped)
                    if ollama_result:
                        analysis = ollama_result
                        moteur_label = "🦙 Ollama local (llama3.2)"
                except:
                    pass

            # Try Groq if key provided
            if not analysis and api_key:
                stat.markdown("⚡ **[4/4]** Analyse Groq LLM (llama-3.1-8b)…")
                try:
                    groq_result = analyze_with_groq(entity_input, all_results, scraped, api_key)
                    if groq_result:
                        analysis = groq_result
                        moteur_label = "⚡ Groq — llama-3.1-8b"
                except:
                    pass

            # Always fallback to local engine
            if not analysis:
                stat.markdown("🔍 **[4/4]** Analyse locale (scoring par mots-clés)…")
                analysis = analyze_local(entity_input, all_results, scraped, os_result)
                moteur_label = "🔍 Moteur local (mots-clés pondérés — gratuit)"

            prog.progress(95)
            analysis["_moteur_label"] = moteur_label

            # Save to DB
            db_save_report(entity_input, entity_type,
                           linked_iban or "",
                           analysis.get("score_risque",0),
                           analysis.get("niveau_risque",""),
                           analysis.get("recommandation",""),
                           analysis.get("resume_executif",""),
                           json.dumps(analysis, ensure_ascii=False))

            if add_to_watch:
                db_add_watchlist(entity_input, entity_type,
                                 "Ajouté depuis analyse OSINT",
                                 analysis.get("niveau_risque",""),
                                 "Analyste")

            prog.progress(100)
            stat.empty()

            # ── Display results ────────────────────────────────────────
            st.markdown("---")
            niveau = analysis.get("niveau_risque","N/A")
            score  = analysis.get("score_risque","N/A")
            reco   = analysis.get("recommandation","N/A")
            conf   = analysis.get("confiance_analyse","N/A")

            badge_map = {"FAIBLE":"badge-low","MODERE":"badge-medium","ELEVE":"badge-high","CRITIQUE":"badge-high"}
            bmap = badge_map.get(niveau,"badge-medium")

            c1,c2,c3,c4,c5 = st.columns(5)
            with c1:
                st.markdown(f"<div class='metric-card'><div class='label'>Score risque</div><div class='value'>{score}<span style='font-size:0.8rem;color:#5a6a7a;'>/100</span></div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><div class='label'>Niveau</div><div class='value' style='font-size:1rem;margin-top:8px;'><span class='{bmap}'>{niveau}</span></div></div>", unsafe_allow_html=True)
            with c3:
                sc = "✓ OUI" if analysis.get("sanctions",{}).get("trouve") else "✗ NON"
                sc_col = "#ff3366" if analysis.get("sanctions",{}).get("trouve") else "#00ff88"
                st.markdown(f"<div class='metric-card'><div class='label'>Sanctions</div><div class='value' style='font-size:1rem;color:{sc_col};'>{sc}</div><div class='sub'>OS: {os_result.get('count',0)} hit(s)</div></div>", unsafe_allow_html=True)
            with c4:
                rc_col = {"ACCEPTER":"#00ff88","VIGILANCE_RENFORCEE":"#ffcc00","REFUSER":"#ff3366"}.get(reco,"#5a6a7a")
                st.markdown(f"<div class='metric-card'><div class='label'>Recommandation</div><div class='value' style='font-size:0.8rem;color:{rc_col};'>{reco}</div></div>", unsafe_allow_html=True)
            with c5:
                st.markdown(f"<div class='metric-card'><div class='label'>Sources web</div><div class='value' style='font-size:1rem;'>{len(all_results)}</div><div class='sub'>{len(scraped)} pages lues</div></div>", unsafe_allow_html=True)

            moteur_lbl = analysis.get("_moteur_label","🔍 Moteur local")
            # Show scores breakdown
            scores_cat = analysis.get("scores_categories",{})
            cat_display = " · ".join(f"{k}: {v}" for k,v in scores_cat.items()) if scores_cat else ""
            st.markdown(f"""
            <div style='background:rgba(0,212,255,0.04);border:1px solid #1e2535;border-radius:4px;padding:8px 14px;margin:6px 0;font-size:0.75rem;'>
              <span style='color:#5a6a7a;'>Moteur d analyse :</span>
              <span style='color:#00d4ff;font-family:IBM Plex Mono,monospace;'>{moteur_lbl}</span>
              {"<br><span style='color:#5a6a7a;'>Scores : "+cat_display+"</span>" if cat_display else ""}
            </div>""", unsafe_allow_html=True)
            st.markdown(f"<div class='info-box'><b>Résumé :</b> {analysis.get('resume_executif','')}</div>", unsafe_allow_html=True)

            cl, cr = st.columns(2)
            with cl:
                st.markdown("#### 📰 Actualités négatives")
                for n in analysis.get("negative_news",[]):
                    g = n.get("gravite","").lower()
                    cls = {"faible":"ok-box","moyen":"warn-box","eleve":"danger-box"}.get(g,"info-box")
                    st.markdown(f"<div class='{cls}'><b>{n.get('titre','')}</b><br><small>{n.get('source','')} · {n.get('date','')} · {n.get('nature','')}</small></div>", unsafe_allow_html=True)
                if not analysis.get("negative_news"):
                    st.markdown("<div class='ok-box'>✅ Aucune actualité négative détectée</div>", unsafe_allow_html=True)

                st.markdown("#### ⚖️ Litiges & procédures")
                lit = analysis.get("litiges_judiciaires",{})
                if lit.get("trouve"):
                    st.markdown(f"<div class='danger-box'>⚠️ {lit.get('details','')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucun litige identifié</div>", unsafe_allow_html=True)

            with cr:
                st.markdown("#### 🚨 Sanctions")
                if os_result.get("found"):
                    st.markdown(f"<div class='danger-box'>🔴 <b>{os_result['count']}</b> entrée(s) OpenSanctions</div>", unsafe_allow_html=True)
                    for r in os_result.get("results",[])[:3]:
                        st.markdown(f"<div class='result-row'><b>{r.get('caption','')}</b> · {', '.join(r.get('datasets',[]))}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucune sanction internationale</div>", unsafe_allow_html=True)

                st.markdown("#### 👤 PEP & Réputation")
                pep = analysis.get("pep_exposure",{})
                if pep.get("trouve"):
                    st.markdown(f"<div class='warn-box'>⚠️ {pep.get('details','')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucune exposition PEP</div>", unsafe_allow_html=True)
                rep = analysis.get("reputation_notations","")
                if rep:
                    st.markdown(f"<div class='info-box'>⭐ {rep}</div>", unsafe_allow_html=True)

            # Factors
            cf1, cf2 = st.columns(2)
            with cf1:
                st.markdown("#### 🔺 Facteurs aggravants")
                for f in analysis.get("facteurs_aggravants",[]):
                    st.markdown(f"<div class='danger-box'>• {f}</div>", unsafe_allow_html=True)
            with cf2:
                st.markdown("#### 🔻 Facteurs atténuants")
                for f in analysis.get("facteurs_attenuants",[]):
                    st.markdown(f"<div class='ok-box'>• {f}</div>", unsafe_allow_html=True)

            with st.expander(f"📋 Résultats bruts — {len(all_results)} sources collectées"):
                for r in all_results[:30]:
                    st.markdown(f"""
                    <div class='result-row'>
                      <a href='{r.get('url','')}' target='_blank' style='color:#00d4ff;text-decoration:none;'><b>{r.get('title','')}</b></a><br>
                      <small style='color:#5a6a7a;'>{r.get('url','')[:80]}</small><br>
                      <small>{r.get('snippet','')[:150]}</small>
                    </div>""", unsafe_allow_html=True)

            # PDF export
            st.markdown("---")
            if st.button("⬇ GÉNÉRER RAPPORT PDF", key="gen_pdf"):
                with st.spinner("Génération du rapport PDF…"):
                    try:
                        pdf = generate_pdf_report(entity_input, iban_data, bank_data, os_result, analysis)
                        fname = f"FinShield_{entity_input.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.download_button("📥 Télécharger le rapport PDF", data=pdf,
                                           file_name=fname, mime="application/pdf")
                        st.markdown("<div class='ok-box'>✅ Rapport PDF généré</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erreur PDF : {e}")

# ══════════════════════════════════════════════════════════════════
# TAB 3 — BANK SEARCH
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Recherche de Banque")
    st.markdown("<div class='info-box'>Recherche par code CIB, nom, BIC ou ville. Base persistante enrichissable depuis l'onglet Gestion.</div>", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3,1])
    with sc1:
        bq = st.text_input("Code CIB, nom, BIC…", placeholder="30004 · BNP · BNPAFRPP · Paris", key="bsearch")
    with sc2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        do_search = st.button("▶ RECHERCHER", key="btn_bsearch")

    if do_search and bq:
        hits = db_get_banks(bq)
        st.markdown(f"<div class='info-box'>{len(hits)} résultat(s)</div>", unsafe_allow_html=True)
        for b in hits[:20]:
            bic_str = f" · BIC : <code>{b['bic']}</code>" if b.get("bic") else ""
            st.markdown(f"""
            <div class='metric-card'>
              <div style='display:flex;justify-content:space-between;'>
                <div>
                  <span style='font-family:IBM Plex Mono,monospace;color:#00d4ff;font-size:1.1rem;'>{b['code']}</span>
                  {bic_str}
                </div>
                <span class='badge-low'>{b.get('type','')}</span>
              </div>
              <div style='font-size:0.95rem;color:#c8d6e5;margin-top:6px;'><b>{b['name']}</b></div>
              <div style='font-size:0.8rem;color:#5a6a7a;margin-top:2px;'>{b.get('address','')} · {b.get('city','')} {b.get('postal_code','')} · {b.get('country','')}</div>
              {'<div style="font-size:0.78rem;color:#5a6a7a;margin-top:4px;">'+b['notes']+'</div>' if b.get('notes') else ''}
            </div>""", unsafe_allow_html=True)

    # Full table
    with st.expander("📖 Table complète (toutes les banques)"):
        flt = st.text_input("Filtrer la table", key="full_bflt").lower()
        rows = db_get_banks(flt)
        if rows:
            df = pd.DataFrame(rows)[["code","name","bic","type","city","postal_code","country"]]
            df.columns = ["Code CIB","Banque","BIC","Type","Ville","CP","Pays"]
            st.dataframe(df, use_container_width=True, height=450)

# ══════════════════════════════════════════════════════════════════
# TAB 4 — DATABASE MANAGEMENT
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Gestion de la Base de Données")

    db_tab1, db_tab2, db_tab3 = st.tabs(["🏦 Banques", "🌍 Pays IBAN", "📤 Import / Export"])

    # ── Sub-tab: Banks ─────────────────────────────────────────────
    with db_tab1:
        st.markdown("### Ajouter / Modifier une banque")
        st.markdown("<div class='info-box'>Renseignez le code CIB à 5 chiffres. Si le code existe déjà, les données seront mises à jour.</div>", unsafe_allow_html=True)

        with st.form("form_bank"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                f_code = st.text_input("Code CIB *", placeholder="30004")
                f_name = st.text_input("Nom de la banque *", placeholder="BNP Paribas")
                f_bic  = st.text_input("Code BIC / SWIFT", placeholder="BNPAFRPP")
            with fc2:
                f_addr = st.text_input("Adresse", placeholder="16 Boulevard des Italiens")
                f_city = st.text_input("Ville", placeholder="Paris")
                f_cp   = st.text_input("Code postal", placeholder="75009")
            with fc3:
                f_country = st.selectbox("Pays", ["FR","BE","LU","MC","CH","DE","GB","ES","IT","NL","PT","AT","SE","NO","DK","FI","IE","PL","CZ","SK","HU","RO","BG","HR","GR","SI","LT","LV","EE","MT","CY","IS","LI","SM","TR","MA","TN","DZ","AE","SA","MU","AL","AD","Other"])
                f_type = st.selectbox("Type", ["Etablissement de crédit","Banque centrale","Autre institution","Fonds de marché monétaire","Organisme de paiement"])
                f_notes = st.text_area("Notes / Remarques", height=68)
            submitted = st.form_submit_button("💾 ENREGISTRER")
            if submitted:
                if f_code and f_name:
                    db_upsert_bank(f_code.strip(), f_name.strip(), f_addr.strip(),
                                   f_city.strip(), f_cp.strip(), f_country,
                                   f_bic.strip().upper(), f_type, f_notes.strip())
                    st.success(f"✅ Banque '{f_name}' (code {f_code}) enregistrée.")
                    st.rerun()
                else:
                    st.error("Le code CIB et le nom sont obligatoires.")

        st.markdown("### Banques enregistrées")
        filter_banks = st.text_input("Rechercher dans la liste", key="db_bank_flt")
        banks_list = db_get_banks(filter_banks)

        for b in banks_list[:100]:
            col_b1, col_b2 = st.columns([5,1])
            with col_b1:
                bic_d = f" · {b['bic']}" if b.get("bic") else ""
                st.markdown(f"""
                <div class='result-row'>
                  <b style='color:#00d4ff;'>{b['code']}</b>{bic_d} · {b['name']}
                  <span style='color:#5a6a7a;font-size:0.8rem;'> · {b.get('city','')} {b.get('postal_code','')} · {b.get('country','')}</span><br>
                  <small style='color:#5a6a7a;'>{b.get('type','')} {' · '+b['notes'] if b.get('notes') else ''}</small>
                </div>""", unsafe_allow_html=True)
            with col_b2:
                if st.button(f"🗑 Supprimer", key=f"del_bank_{b['code']}"):
                    db_delete_bank(b["code"])
                    st.rerun()

    # ── Sub-tab: IBAN Countries ────────────────────────────────────
    with db_tab2:
        st.markdown("### Ajouter / Modifier une structure IBAN par pays")
        st.markdown("<div class='info-box'>Basé sur la norme ISO 13616. Le document BCEE fourni couvre les principaux pays européens.</div>", unsafe_allow_html=True)

        with st.form("form_iban_country"):
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                ic_code   = st.text_input("Code ISO pays *", placeholder="FR", max_chars=2)
                ic_name   = st.text_input("Nom du pays *", placeholder="France")
                ic_length = st.number_input("Longueur IBAN *", min_value=15, max_value=34, value=27)
            with ic2:
                ic_bban   = st.text_input("Format BBAN", placeholder="5n,5n,11c,2n")
                ic_struct = st.text_input("Structure lisible", placeholder="FRkk bbbb bggg ggcc cccc cccc cxx")
            with ic3:
                ic_example = st.text_input("Exemple IBAN", placeholder="FR76 3000 4000 0000 0000 0000 000")
                ic_notes   = st.text_area("Notes", height=68)
            ic_sub = st.form_submit_button("💾 ENREGISTRER")
            if ic_sub:
                if ic_code and ic_name:
                    db_upsert_iban_country(ic_code.upper(), ic_name, ic_length,
                                           ic_struct, ic_example, ic_bban, ic_notes)
                    st.success(f"✅ Pays {ic_code.upper()} — {ic_name} enregistré.")
                    st.rerun()
                else:
                    st.error("Code et nom obligatoires.")

        st.markdown("### Référentiel IBAN actuel")
        all_ic = db_get_all_iban_countries()
        df_ic = pd.DataFrame(all_ic)[["code","name","length","bban_format","example"]]
        df_ic.columns = ["Code","Pays","Longueur","Format BBAN","Exemple"]
        st.dataframe(df_ic, use_container_width=True, height=500)

    # ── Sub-tab: Import / Export ────────────────────────────────────
    with db_tab3:
        st.markdown("### Export de la base")

        exp1, exp2 = st.columns(2)
        with exp1:
            st.markdown("#### 📤 Exporter les banques (CSV)")
            banks_all = db_get_banks()
            if banks_all:
                csv_buf = io.StringIO()
                writer = csv.DictWriter(csv_buf, fieldnames=banks_all[0].keys())
                writer.writeheader()
                writer.writerows(banks_all)
                st.download_button("⬇ Télécharger banks.csv",
                                   data=csv_buf.getvalue().encode("utf-8"),
                                   file_name="finshield_banks.csv", mime="text/csv")

            st.markdown("#### 📤 Exporter pays IBAN (CSV)")
            ic_all = db_get_all_iban_countries()
            if ic_all:
                csv_buf2 = io.StringIO()
                writer2 = csv.DictWriter(csv_buf2, fieldnames=ic_all[0].keys())
                writer2.writeheader()
                writer2.writerows(ic_all)
                st.download_button("⬇ Télécharger iban_countries.csv",
                                   data=csv_buf2.getvalue().encode("utf-8"),
                                   file_name="finshield_iban_countries.csv", mime="text/csv")

        with exp2:
            st.markdown("#### 📥 Importer des banques (CSV)")
            st.markdown("""<div class='info-box'>
            Format attendu : colonnes <code>code, name, address, city, postal_code, country, bic, type, notes</code>
            </div>""", unsafe_allow_html=True)
            uploaded = st.file_uploader("Choisir un fichier CSV", type=["csv"], key="import_banks")
            if uploaded:
                try:
                    df_up = pd.read_csv(uploaded)
                    # Normalize columns
                    df_up.columns = [c.lower().strip() for c in df_up.columns]
                    required = ["code","name"]
                    if all(r in df_up.columns for r in required):
                        st.dataframe(df_up.head(), use_container_width=True)
                        if st.button("✅ Confirmer l'import"):
                            count = 0
                            for _, row in df_up.iterrows():
                                db_upsert_bank(
                                    str(row.get("code","")).strip(),
                                    str(row.get("name","")).strip(),
                                    str(row.get("address","")).strip(),
                                    str(row.get("city","")).strip(),
                                    str(row.get("postal_code","")).strip(),
                                    str(row.get("country","FR")).strip(),
                                    str(row.get("bic","")).strip().upper(),
                                    str(row.get("type","Etablissement de crédit")).strip(),
                                    str(row.get("notes","")).strip()
                                )
                                count += 1
                            st.success(f"✅ {count} banques importées/mises à jour.")
                            st.rerun()
                    else:
                        st.error(f"Colonnes manquantes. Attendu: code, name. Trouvé: {list(df_up.columns)}")
                except Exception as e:
                    st.error(f"Erreur lecture CSV : {e}")

        st.markdown("---")
        st.markdown("### ⚠️ Zone de réinitialisation")
        with st.expander("Réinitialiser les données (irréversible)"):
            st.markdown("<div class='danger-box'>Ces actions suppriment définitivement les données.</div>", unsafe_allow_html=True)
            cr1, cr2, cr3 = st.columns(3)
            with cr1:
                if st.button("🗑 Vider l'historique rapports"):
                    conn = get_db(); conn.execute("DELETE FROM osint_reports"); conn.commit(); conn.close()
                    st.success("Historique vidé."); st.rerun()
            with cr2:
                if st.button("🗑 Vider la watchlist"):
                    conn = get_db(); conn.execute("DELETE FROM watchlist"); conn.commit(); conn.close()
                    st.success("Watchlist vidée."); st.rerun()
            with cr3:
                if st.button("🔄 Réensemencer banques par défaut"):
                    conn = get_db(); conn.execute("DELETE FROM banks"); conn.commit(); conn.close()
                    seed_banks()
                    st.success("Banques réinitialisées."); st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 5 — HISTORY & WATCHLIST
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## Historique & Surveillance")

    ht1, ht2 = st.tabs(["📋 Historique des rapports", "👁 Liste de surveillance"])

    with ht1:
        reports = db_get_reports(100)
        if reports:
            st.markdown(f"<div class='info-box'>{len(reports)} rapport(s) enregistré(s)</div>", unsafe_allow_html=True)
            # Summary table
            df_rep = pd.DataFrame(reports)[["id","entity","entity_type","score","niveau","recommandation","created_at"]]
            df_rep.columns = ["ID","Entité","Type","Score","Niveau","Recommandation","Date"]
            st.dataframe(df_rep, use_container_width=True, height=300)

            # Detail view
            report_ids = [r["id"] for r in reports]
            sel = st.selectbox("Voir le détail d'un rapport", ["—"] + [f"#{r['id']} — {r['entity']} ({r['created_at'][:10]})" for r in reports])
            if sel != "—":
                idx = int(sel.split("—")[0].replace("#","").strip()) - 1
                rep = reports[idx]
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='label'>Entité</div>
                  <div class='value' style='font-size:1rem;'>{rep['entity']}</div>
                  <div class='sub'>Score : {rep['score']}/100 · Niveau : {rep['niveau']} · {rep['recommandation']}</div>
                  <div class='sub'>{rep['resume']}</div>
                </div>""", unsafe_allow_html=True)
                if rep.get("full_json"):
                    with st.expander("JSON complet"):
                        try:
                            st.json(json.loads(rep["full_json"]))
                        except:
                            st.text(rep["full_json"])

                # Re-generate PDF from stored report
                if st.button("⬇ Régénérer le PDF", key=f"repdf_{rep['id']}"):
                    try:
                        analysis = json.loads(rep.get("full_json","{}"))
                        iban_data = validate_iban(rep.get("iban","")) if rep.get("iban") else {}
                        bank_data = {}
                        if iban_data.get("bank_code"):
                            b = db_get_bank_by_code(iban_data["bank_code"])
                            if b: bank_data = b
                        pdf = generate_pdf_report(rep["entity"], iban_data, bank_data, {"count":0,"results":[]}, analysis)
                        fname = f"FinShield_{rep['entity'].replace(' ','_')}_{rep['created_at'][:10]}.pdf"
                        st.download_button("📥 Télécharger", data=pdf, file_name=fname, mime="application/pdf")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
        else:
            st.markdown("<div class='info-box'>Aucun rapport enregistré. Lancez une analyse dans l'onglet OSINT.</div>", unsafe_allow_html=True)

    with ht2:
        st.markdown("### Ajouter une entité à surveiller")
        with st.form("form_watch"):
            wc1, wc2 = st.columns(2)
            with wc1:
                w_entity = st.text_input("Entité *")
                w_type   = st.selectbox("Type", ["Entreprise","Personne physique","Groupe","Autre"])
            with wc2:
                w_reason = st.text_area("Motif de surveillance", height=68)
                w_risk   = st.selectbox("Niveau de risque", ["FAIBLE","MODERE","ELEVE","CRITIQUE"])
            w_by = st.text_input("Ajouté par (analyste)", placeholder="Analyste KYC")
            w_sub = st.form_submit_button("➕ AJOUTER À LA WATCHLIST")
            if w_sub and w_entity:
                db_add_watchlist(w_entity, w_type, w_reason, w_risk, w_by)
                st.success(f"✅ {w_entity} ajouté à la watchlist.")
                st.rerun()

        st.markdown("### Entités sous surveillance")
        watchlist = db_get_watchlist()
        if watchlist:
            for w in watchlist:
                risk_c = {"FAIBLE":"badge-low","MODERE":"badge-medium","ELEVE":"badge-high","CRITIQUE":"badge-high"}.get(w["risk_level"],"badge-medium")
                wc1, wc2 = st.columns([5,1])
                with wc1:
                    st.markdown(f"""
                    <div class='result-row'>
                      <b>{w['entity']}</b> · <span class='{risk_c}'>{w['risk_level']}</span><br>
                      <small style='color:#5a6a7a;'>{w['entity_type']} · Ajouté le {w['created_at'][:10]} par {w.get('added_by','')}</small><br>
                      <small>{w.get('reason','')}</small>
                    </div>""", unsafe_allow_html=True)
                with wc2:
                    if st.button("🗑", key=f"del_watch_{w['id']}"):
                        db_delete_watchlist(w["id"])
                        st.rerun()
        else:
            st.markdown("<div class='info-box'>Watchlist vide.</div>", unsafe_allow_html=True)
