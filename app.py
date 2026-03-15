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
    """Seed all 396 banks from the official French banking registry (Philtr/BdF source)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM banks")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    banks = [
        ('18989', 'Aareal bank AG', '29 B RUE D ASTORG', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13678', 'ABN AMRO ASSET BASED FINANCE N.V.', '39 rue Anatole France', 'LEVALLOIS PERRET', '92300', 'FR', '', 'Autre institution', ''),
        ('11938', 'AGCO FINANCE', 'BP 90 Avenue Blaise Pascal', 'BEAUVAIS CEDEX', '60007', 'FR', '', 'Autre institution', ''),
        ('45129', 'AGENCE FRANCAISE DE DEVELOPPEMENT', '5 RUE ROLAND BARTHES', 'PARIS 12', '75012', 'FR', '', 'Autre institution', ''),
        ('16688', 'AGENCE FRANCE LOCALE', 'TOUR OXYGENE 10 BOULEVARD MARIUS VIVIER MERLE', 'LYON', '69003', 'FR', '', 'Etablissement de crédit', ''),
        ('41829', 'Al Khaliji France', '49 AVENUE GEORGE V', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('26633', 'Allfunds Bank S.A.U.', 'Spaces Opera Garnier 7 Rue Meyerbeer', 'PARIS', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('12240', 'Allianz banque', 'TOUR ALLIANZ ONE 1 COURS MICHELET', 'Paris La defense Cedex', '92076', 'FR', '', 'Etablissement de crédit', ''),
        ('17408', 'ALMA', '176 AVENUE CHARLES DE GAULLE', 'NEUILLY SUR SEINE', '92200', 'FR', '', 'Autre institution', ''),
        ('16160', 'Alsabail', 'BP 80 7 PLACE BRANT', 'STRASBOURG CEDEX', '67001', 'FR', '', 'Autre institution', ''),
        ('19530', 'Amundi', '91-93 BOULEVARD PASTEUR', 'PARIS CEDEX 15', '75730', 'FR', '', 'Etablissement de crédit', ''),
        ('14328', 'Amundi finance', '90 BOULEVARD PASTEUR', 'PARIS 15', '75015', 'FR', '', 'Etablissement de crédit', ''),
        ('15638', 'Andbank Monaco S.A.M.', '1 avenue des Citronniers', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('18979', 'ARAB BANKING CORPORATION SA', '4 RUE AUBER', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('16298', 'Arkea banking services', 'Tour 5 PLACE DE LA PYRAMIDE', 'PARIS LA DEFENSE CEDEX', '92088', 'FR', '', 'Etablissement de crédit', ''),
        ('18829', 'Arkea banque entreprises et institutionnels', '3 AVENUE D ALPHASIS CS 96856', 'SAINT GREGOIRE', '35760', 'FR', '', 'Etablissement de crédit', ''),
        ('14518', 'ARKEA DIRECT BANK', 'La D TOUR ARIANE 5 PLACE DE LA PYRAMIDE', 'PUTEAUX', '92800', 'FR', '', 'Etablissement de crédit', ''),
        ('16088', 'Arkea Home Loans SFH', 'BP 10 232 RUE GENERAL PAULET', 'BREST CEDEX 9', '29802', 'FR', '', 'Etablissement de crédit', ''),
        ('16358', 'Arkea public sector SCF', '1 RUE LICHOU', 'LE RELECQ KERHUON', '29480', 'FR', '', 'Etablissement de crédit', ''),
        ('15980', 'Arkea credit bail', 'IMMEUBLE LE SEXTANT 255 RUE DE SAINT-MALO', 'RENNES CEDEX', '35700', 'FR', '', 'Autre institution', ''),
        ('23890', 'Attijariwafa bank europe', '6 RUE CHAUCHAT', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('16668', 'Australia and New Zealand banking group limited', '6 RUE LAMENNAIS', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13558', 'Auxifip', 'CS 30 12 PLACE DES ETATS-UNIS', 'MONTROUGE CEDEX', '92548', 'FR', '', 'Etablissement de crédit', ''),
        ('16318', 'AXA BANK EUROPE SCF', '203/205 RUE CARNOT', 'FONTENAY SOUS BOIS CEDEX', '94138', 'FR', '', 'Etablissement de crédit', ''),
        ('12548', 'Axa banque', '203-205 RUE CARNOT', 'FONTENAY-SOUS-BOIS CEDEX', '94138', 'FR', 'AXABFRPP', 'Etablissement de crédit', ''),
        ('25080', 'Axa banque financement', '203-205 RUE CARNOT', 'FONTENAY-SOUS-BOIS CEDEX', '94138', 'FR', '', 'Etablissement de crédit', ''),
        ('17188', 'AXA Home Loan SFH', '203 RUE CARNOT', 'FONTENAY-SOUS-BOIS', '94138', 'FR', '', 'Etablissement de crédit', ''),
        ('11078', 'BAIL ACTEA IMMOBILIER', 'TOUR DE LILLE 60 BOULEVARD DE TURIN', 'LILLE', '59777', 'FR', '', 'Autre institution', ''),
        ('15970', 'Bail-Actea', '4 PLACE RICHEBE', 'LILLE', '59800', 'FR', '', 'Autre institution', ''),
        ('14908', 'Banca popolare di Sondrio Suisse', '3 rue Princesse Florestine', 'MONACO CEDEX', '98011', 'MC', '', 'Etablissement de crédit', ''),
        ('41189', 'Banco Bilbao Vizcaya Argentaria (BBVA)', '29 AVENUE DE L OPERA', 'PARIS 01', '75001', 'FR', 'BBVAFRPP', 'Etablissement de crédit', ''),
        ('19229', 'Banco de Sabadell', '127 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('41139', 'Banco do Brasil AG', '29 avenue kleber', 'PARIS', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('44729', 'Banco Santander SA', '40 RUE DE COURCELLES', 'PARIS 08', '75008', 'FR', 'BSCHFRPP', 'Etablissement de crédit', ''),
        ('18089', 'Bank Audi France', '73 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14508', 'Bank Julius Baer (Monaco) S.A.M.', '12 BOULEVARD DES MOULINS', 'Monaco', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('41259', 'Bank Melli Iran', '43 AVENUE MONTAIGNE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('41219', 'BANK OF AMERICA EUROPE', '51 Rue la Boetie', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('18769', 'Bank of China limited', '23 AVENUE DE LA GRANDE ARMEE', 'PARIS 16', '75116', 'FR', 'BKCHFRPP', 'Etablissement de crédit', ''),
        ('19533', 'BANK OF COMMUNICATIONS (LUXEMBOURG) S.A.', 'Avenue des Champs Elysees 90', 'Paris', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14879', 'Bank of India', '4 RUE HALEVY', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('44269', 'Bank Saderat Iran', '16 RUE DE LA PAIX', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('17799', 'Bank Sepah', '20 RUE AUGUSTE VACQUERIE', 'PARIS', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('17579', 'Bank Tejarat', '124 RUE DE PROVENCE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('17599', 'Banque Banorient France', '21 AVENUE GEORGE V', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('12579', 'Banque BCP', '16 RUE HEROLD', 'PARIS', '75001', 'FR', '', 'Etablissement de crédit', ''),
        ('12179', 'Banque BIA', '67 AVENUE FRANKLIN DELANO ROOSEVELT', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('12468', 'Banque cantonale de Geneve France S.A.', '20 PLACE LOUIS PRADEL', 'LYON 01', '69001', 'FR', '', 'Etablissement de crédit', ''),
        ('17519', 'Banque centrale de compensation', '18 RUE DU 4 SEPTEMBRE', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('41439', 'Banque Chaabi du Maroc', '49 AVENUE KLEBER', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('24659', 'Banque Chabrières', '24 RUE AUGUSTE CHABRIÈRES', 'PARIS CEDEX 15', '75737', 'FR', '', 'Etablissement de crédit', ''),
        ('10188', 'Banque Chalus', '5 PLACE DE JAUDE', 'CLERMONT-FERRAND', '63002', 'FR', '', 'Etablissement de crédit', ''),
        ('30087', 'Banque CIC Est', '31 RUE JEAN WENGER-VALENTIN', 'STRASBOURG CEDEX 9', '67958', 'FR', '', 'Etablissement de crédit', ''),
        ('30027', 'Banque CIC Nord Ouest', '33 AVENUE LE CORBUSIER', 'LILLE', '59800', 'FR', '', 'Etablissement de crédit', ''),
        ('30047', 'Banque CIC Ouest', 'BP 84 2 AVENUE JEAN-CLAUDE BONDUELLE', 'NANTES CEDEX 1', '44040', 'FR', '', 'Etablissement de crédit', ''),
        ('10057', 'Banque CIC Sud Ouest', 'BP 50 20 QUAI DES CHARTRONS', 'BORDEAUX CEDEX', '33058', 'FR', '', 'Etablissement de crédit', ''),
        ('10268', 'Banque Courtois', '33 RUE DE REMUSAT', 'TOULOUSE', '31000', 'FR', '', 'Etablissement de crédit', ''),
        ('44149', 'WORMSER FRERES Banque d escompte', '13 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('30001', 'BANQUE DE FRANCE', '1 RUE LA VRILLIERE', 'PARIS 01', '75001', 'FR', 'BDFEFRPP', 'Banque centrale', ''),
        ('10548', 'Banque de Savoie', '6 BOULEVARD DU THEATRE', 'CHAMBERY CEDEX', '73024', 'FR', '', 'Etablissement de crédit', ''),
        ('43030', 'Banque Degroof Petercam France', '44 RUE DE LISBONNE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('12879', 'Banque Delubac et Cie', 'BP 53 16 PLACE SALEON TERRAS', 'LE CHEYLARD', '07160', 'FR', '', 'Etablissement de crédit', ''),
        ('18079', 'Banque des Caraibes', 'BP 55 30 RUE FREBAULT', 'POINTE-A-PITRE CEDEX', '97152', 'FR', '', 'Etablissement de crédit', ''),
        ('30258', 'Banque BTP', '48 RUE LA PEROUSE', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('13149', 'Banque Edel SNC', '60 RUE BUISSONNIERE', 'LABEGE CEDEX', '31676', 'FR', '', 'Etablissement de crédit', ''),
        ('11899', 'Banque Europeenne du Credit Mutuel', '4 RUE FREDERIC', 'STRASBOURG', '67100', 'FR', '', 'Etablissement de crédit', ''),
        ('16548', 'Banque europeenne du credit mutuel Monaco', '8 rue Grimaldi', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('11808', 'Banque federative du credit mutuel', 'BP 41 4 RUE FREDERIC', 'STRASBOURG', '67100', 'FR', '', 'Etablissement de crédit', ''),
        ('11449', 'BANQUE FIDUCIAL', '41 RUE DU CAPITAINE GUYNEMER', 'COURBEVOIE', '92400', 'FR', '', 'Etablissement de crédit', ''),
        ('18719', 'Banque Francaise Commerciale Ocean Indien', '58 RUE ALEXIS DE VILLENEUVE', 'ST DENIS CEDEX', '97404', 'FR', '', 'Etablissement de crédit', ''),
        ('18869', 'Banque francaise mutualiste', '56 RUE DE LA GLACIERE', 'PARIS', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('16038', 'BANQUE HAVILLAND MONACO S.A.M.', '32/34 bd Princesse Charlotte', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('11438', 'Banque Hottinguer', '63 RUE DE LA VICTOIRE', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('40398', 'Banque internationale de commerce BRED', '18 QUAI DE LA RAPEE', 'PARIS 12', '75012', 'FR', '', 'Etablissement de crédit', ''),
        ('24349', 'Banque J. Safra Sarasin Monaco SA', '15bis-17 avenue Ostende', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('13259', 'Banque Kolb', '1-3 PLACE DU GENERAL DE GAULLE', 'MIRECOURT', '88500', 'FR', '', 'Etablissement de crédit', ''),
        ('10228', 'Banque Laydernier', '10 AVENUE DU RHONE', 'ANNECY', '74000', 'FR', '', 'Etablissement de crédit', ''),
        ('17959', 'Banque Michel Inchauspé BAMI', '76 AVENUE DU 8 MAI 1945', 'BAYONNE', '64100', 'FR', '', 'Etablissement de crédit', ''),
        ('18569', 'Banque Misr', '9 RUE AUBER', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('30788', 'Banque Neuflize OBC', '3 AVENUE HOCHE', 'PARIS 08', '75008', 'FR', 'NEIOFR22', 'Etablissement de crédit', ''),
        ('19730', 'Banque Nomura France', '7 PLACE D IENA', 'PARIS CEDEX 16', '75773', 'FR', '', 'Etablissement de crédit', ''),
        ('13489', 'Banque Nuger', 'BP 56 5 PLACE MICHEL DE L HOSPITAL', 'CLERMONT-FERRAND CEDEX', '63002', 'FR', '', 'Etablissement de crédit', ''),
        ('40978', 'Banque Palatine', '42 RUE D ANJOU', 'PARIS CEDEX 08', '75382', 'FR', '', 'Etablissement de crédit', ''),
        ('14707', 'Banque populaire Alsace Lorraine Champagne', 'BP 12 3 RUE FRANCOIS DE CUREL', 'METZ CEDEX 1', '57021', 'FR', '', 'Etablissement de crédit', ''),
        ('10907', 'Banque populaire Aquitaine Centre Atlantique', '10 QUAI DES QUEYRIES', 'BORDEAUX', '33100', 'FR', '', 'Etablissement de crédit', ''),
        ('16807', 'BANQUE POPULAIRE AUVERGNE RHONE ALPES', 'CS 80 4 BOULEVARD EUGENE DERUELLE', 'Lyon', '69003', 'FR', '', 'Etablissement de crédit', ''),
        ('10807', 'Banque populaire Bourgogne Franche-Comte', 'BP 31 14 BD DE LA TREMOUILLE', 'DIJON CEDEX', '21008', 'FR', '', 'Etablissement de crédit', ''),
        ('13507', 'Banque populaire du Nord', '847 AVENUE DE LA REPUBLIQUE', 'MARCQ EN BAROEUL', '59700', 'FR', '', 'Etablissement de crédit', ''),
        ('16607', 'Banque populaire du Sud', '38 BOULEVARD GEORGES CLEMENCEAU', 'PERPIGNAN CEDEX 09', '66966', 'FR', '', 'Etablissement de crédit', ''),
        ('13807', 'Banque populaire Grand Ouest', '15 BOULEVARD DE LA BOUTIERE', 'SAINT GREGOIRE', '35760', 'FR', '', 'Etablissement de crédit', ''),
        ('14607', 'BANQUE POPULAIRE MEDITERRANEE', '457 PROMENADE DES ANGLAIS', 'Nice', '06200', 'FR', '', 'Etablissement de crédit', ''),
        ('17807', 'Banque populaire Occitane', '33 AVENUE GEORGES POMPIDOU', 'BALMA', '31130', 'FR', '', 'Etablissement de crédit', ''),
        ('10207', 'Banque populaire Rives de Paris', '76 AVENUE DE FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('18707', 'Banque populaire Val de France', '9 AVENUE NEWTON', 'MONTIGNY LE BRETONNEUX', '78180', 'FR', '', 'Etablissement de crédit', ''),
        ('11989', 'Banque Pouyanne', '12 PLACE D ARMES', 'ORTHEZ', '64300', 'FR', '', 'Etablissement de crédit', ''),
        ('13168', 'Banque PSA finance', '2 BOULEVARD DE L EUROPE', 'POISSY', '78300', 'FR', '', 'Etablissement de crédit', ''),
        ('17649', 'Banque Revillon', '40 RUE LA BOETIE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('10468', 'Banque Rhone-Alpes', '20 BOULEVARD EDOUARD REY', 'GRENOBLE', '38000', 'FR', '', 'Etablissement de crédit', ''),
        ('19069', 'BANQUE RICHELIEU FRANCE', '1 RUE PAUL CEZANNE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13338', 'BANQUE RICHELIEU MONACO', '8 AVENUE DE GRANDE BRETAGNE', 'MONACO CEDEX', '98005', 'MC', '', 'Etablissement de crédit', ''),
        ('13579', 'Banque Saint-Olive', '84 RUE DU GUESCLIN', 'LYON 06', '69006', 'FR', '', 'Etablissement de crédit', ''),
        ('17779', 'Banque SBA', '68 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('10558', 'Banque Tarneaud', '2 RUE TURGOT', 'LIMOGES', '87000', 'FR', '', 'Etablissement de crédit', ''),
        ('30568', 'Banque Transatlantique S.A.', '26 AVENUE FRANKLIN-ROOSEVELT', 'PARIS CEDEX 08', '75372', 'FR', '', 'Etablissement de crédit', ''),
        ('30588', 'Barclays Bank Ireland', '34/36 avenue de Friedland', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('12448', 'Barclays bank plc monaco', '31 avenue de la costa', 'Monaco', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('10108', 'Bayerische landesbank', '203 RUE DU FAUBOURG SAINT HONORE', 'PARIS CEDEX 08', '75380', 'FR', '', 'Etablissement de crédit', ''),
        ('17619', 'BEMO EUROPE BANQUE PRIVEE', '49 avenue d Iena', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('16218', 'Bforbank', 'TOUR EUROPLAZA 20 AVENUE ANDRE PROTHIN', 'PARIS LA DEFENSE CEDEX', '92927', 'FR', '', 'Etablissement de crédit', ''),
        ('16158', 'BGFIBANK EUROPE', '10 RUE DU GENERAL FOY', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('15818', 'Binckbank NV', '102 RUE VICTOR HUGO', 'LEVALLOIS PERRET', '92300', 'FR', '', 'Etablissement de crédit', ''),
        ('12249', 'BMCE BANK INTERNATIONAL PLC', '6 rue Cambaceres', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14670', 'BMW Finance', '5 RUE DES HERONS', 'SAINT QUENTIN EN YVELINES', '78182', 'FR', '', 'Etablissement de crédit', ''),
        ('30004', 'BNP Paribas', '16 BOULEVARD DES ITALIENS', 'PARIS', '75009', 'FR', 'BNPAFRPP', 'Etablissement de crédit', ''),
        ('13088', 'BNP PARIBAS ANTILLES-GUYANE', '1 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('18020', 'BNP Paribas Factor', 'SEINE WAY 12 RUE LOUIS BLERIOT', 'Rueil-Malmaison', '92500', 'FR', '', 'Autre institution', ''),
        ('15668', 'BNP Paribas home loan SFH', '1 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('30958', 'BNP Paribas Lease Group', '12 RUE DU PORT', 'NANTERRE', '92000', 'FR', '', 'Etablissement de crédit', ''),
        ('18029', 'BNP Paribas Personal Finance', '1 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('41919', 'BNP Paribas Reunion', '1 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('41329', 'BNP Paribas securities services', '3 RUE D ANTIN', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('11498', 'BNP Paribas wealth management Monaco', '15/17 avenue d ostende', 'Monaco', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('16168', 'BOA France', '20 RUE DE SAINT PETERSBOURG', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('40618', 'Boursorama', '18 QUAI DU POINT DU JOUR', 'BOULOGNE BILLANCOURT', '92100', 'FR', 'BOUSFRPP', 'Etablissement de crédit', ''),
        ('16188', 'BPCE', '50 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', 'BPCEFRPP', 'Etablissement de crédit', ''),
        ('12749', 'BPCE Bail', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('11138', 'BPCE Factor', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('14768', 'BPCE FINANCEMENT', '89 QUAI PANHARD ET LEVASSOR', 'PARIS CEDEX 13', '75634', 'FR', '', 'Autre institution', ''),
        ('14888', 'BPCE International et Outremer', '88 AVENUE DE FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('11128', 'BPCE lease', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('16190', 'BPCE lease immo', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('16438', 'BPCE SFH', '50 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('44319', 'BPE', '60 RUE DU LOUVRE', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('18359', 'Bpifrance', '27-31 AVENUE DU GENERAL LECLERC', 'MAISONS-ALFORT', '94710', 'FR', '', 'Etablissement de crédit', ''),
        ('19649', 'Bpifrance Regions', '27-31 AVENUE DU GENERAL LECLERC', 'MAISONS-ALFORT', '94710', 'FR', '', 'Autre institution', ''),
        ('10107', 'BRED Banque populaire', '18 QUAI DE LA RAPEE', 'PARIS 12', '75012', 'FR', 'BREDFRPP', 'Etablissement de crédit', ''),
        ('12779', 'BRED Cofilease', '18 QUAI DE LA RAPEE', 'PARIS 12', '75012', 'FR', '', 'Etablissement de crédit', ''),
        ('14318', 'BRED Gestion', '18 QUAI DE LA RAPEE', 'PARIS 12', '75012', 'FR', '', 'Etablissement de crédit', ''),
        ('23779', 'Byblos bank Europe', '15 RUE LORD BYRON', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('11380', 'C.R.H. Caisse de refinancement de l habitat', '3 RUE LA BOETIE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('41539', 'CA Consumer Finance', '1 RUE VICTOR BASH CS 70001', 'MASSY CEDEX', '91068', 'FR', '', 'Etablissement de crédit', ''),
        ('43799', 'CA INDOSUEZ WEALTH FRANCE', '17 RUE DU DOCTEUR LANCEREAUX', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('18129', 'CACEIS Bank', '1 PLACE VALHUBERT', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('15429', 'Caisse agricole Credit Mutuel', '4 RUE FREDERIC GUILLAUME', 'STRASBOURG', '67000', 'FR', '', 'Etablissement de crédit', ''),
        ('18609', 'Caisse centrale du credit immobilier de France', '26 RUE DE MADRID', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('45539', 'Caisse centrale du credit mutuel', '88-90 RUE CARDINET', 'PARIS CEDEX 17', '75847', 'FR', '', 'Etablissement de crédit', ''),
        ('11315', 'Caisse d Epargne CEPAC', 'PLACE ESTRANGIN PASTRE', 'MARSEILLE CEDEX 6', '13254', 'FR', '', 'Etablissement de crédit', ''),
        ('13335', 'Caisse d epargne Aquitaine Poitou-Charentes', '1 PARVIS CORTO MALTESE', 'BORDEAUX CEDEX', '33076', 'FR', '', 'Etablissement de crédit', ''),
        ('14445', 'Caisse d epargne Bretagne-Pays de Loire', '2 PLACE GRASLIN', 'NANTES', '44003', 'FR', '', 'Etablissement de crédit', ''),
        ('18315', 'Caisse d epargne Cote d Azur', '455 PROMENADE DES ANGLAIS', 'NICE CEDEX 3', '06205', 'FR', '', 'Etablissement de crédit', ''),
        ('18715', 'Caisse d epargne Auvergne et du Limousin', '63 RUE MONTLOSIER', 'CLERMONT FERRAND', '63000', 'FR', '', 'Etablissement de crédit', ''),
        ('12135', 'Caisse d epargne Bourgogne Franche-Comte', '1 ROND POINT DE LA NATION', 'DIJON CEDEX', '21005', 'FR', '', 'Etablissement de crédit', ''),
        ('13135', 'Caisse d epargne Midi-Pyrenees', '10 AVENUE MAXWELL', 'TOULOUSE', '31100', 'FR', '', 'Etablissement de crédit', ''),
        ('13825', 'Caisse d epargne Rhone Alpes', '116 COURS LAFAYETTE', 'LYON Cedex 03', '69404', 'FR', '', 'Etablissement de crédit', ''),
        ('13485', 'Caisse d epargne Languedoc Roussillon', '254 RUE MICHEL TEULE', 'MONTPELLIER CEDEX 4', '34184', 'FR', '', 'Etablissement de crédit', ''),
        ('15135', 'CAISSE D EPARGNE GRAND EST EUROPE', '1 AVENUE DU RHIN', 'STRASBOURG', '67100', 'FR', '', 'Etablissement de crédit', ''),
        ('16275', 'Caisse d epargne Hauts de France', '135 PONT DES FLANDRES', 'Euralille', '59777', 'FR', '', 'Etablissement de crédit', ''),
        ('17515', 'Caisse d epargne Ile-de-France', '19 RUE DU LOUVRE', 'PARIS CEDEX 1', '75021', 'FR', 'CEPAFRPP', 'Etablissement de crédit', ''),
        ('14265', 'Caisse d epargne Loire Drome Ardeche', 'ESPACE FAURIEL 17 RUE P. ET D. PONCHARDIER', 'SAINT-ETIENNE CEDEX 2', '42012', 'FR', '', 'Etablissement de crédit', ''),
        ('14505', 'Caisse d epargne Loire-Centre', '7 RUE D ESCURES', 'ORLEANS', '45000', 'FR', '', 'Etablissement de crédit', ''),
        ('11425', 'Caisse d epargne Normandie', '151 RUE D UELZEN', 'BOIS GUILLAUME BIHOREL', '76230', 'FR', '', 'Etablissement de crédit', ''),
        ('15449', 'Caisse de Bretagne de credit mutuel agricole', '1 RUE LOUIS LICHOU', 'LE RELECQ KERHUON', '29480', 'FR', '', 'Etablissement de crédit', ''),
        ('6', 'Caisse des depots fonds d epargne', '72 AVENUE PIERRE MENDES-FRANCE', 'PARIS CEDEX 13', '75914', 'FR', '', 'Etablissement de crédit', ''),
        ('40031', 'Caisse des depots section generale', '56 RUE DE LILLE', 'PARIS 07SP', '75356', 'FR', '', 'Etablissement de crédit', ''),
        ('10278', 'Caisse federale de credit mutuel', '4 RUE FREDERIC', 'STRASBOURG', '67100', 'FR', '', 'Etablissement de crédit', ''),
        ('15489', 'Caisse federale credit mutuel Maine-Anjou Basse-Normandie', '43 BOULEVARD VOLNEY', 'LAVAL CEDEX 9', '53083', 'FR', '', 'Etablissement de crédit', ''),
        ('15629', 'Caisse federale credit mutuel Nord Europe', '4 PLACE RICHEBE', 'LILLE CEDEX', '59011', 'FR', '', 'Etablissement de crédit', ''),
        ('15519', 'Caisse federale credit mutuel Ocean', '34 RUE LEANDRE MERLET', 'LA ROCHE-SUR-YON CEDEX', '85001', 'FR', '', 'Etablissement de crédit', ''),
        ('18589', 'Caisse francaise de developpement industriel', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('14388', 'Caisse Francaise de Financement Local', '1 PASSERELLE DES REFLETS', 'ISSY-LES-MOULINEAUX', '92130', 'FR', '', 'Etablissement de crédit', ''),
        ('11306', 'CA mutuel Alpes Provence', '25 CHEMIN DES TROIS CYPRES', 'AIX EN PROVENCE', '13097', 'FR', '', 'Etablissement de crédit', ''),
        ('17206', 'CA mutuel Alsace Vosges', '1 PLACE DE LA GARE', 'STRASBOURG', '67008', 'FR', '', 'Etablissement de crédit', ''),
        ('14706', 'CA mutuel Atlantique Vendee', 'LA GARDE ROUTE DE PARIS', 'NANTES CEDEX9', '44949', 'FR', '', 'Etablissement de crédit', ''),
        ('18706', 'CA mutuel Brie Picardie', '500 RUE SAINT-FUSCIEN', 'AMIENS CEDEX 3', '80095', 'FR', '', 'Etablissement de crédit', ''),
        ('14806', 'CA mutuel Centre Loire', '8 ALLEE DES COLLEGES', 'BOURGES', '18000', 'FR', '', 'Etablissement de crédit', ''),
        ('17806', 'CA mutuel Centre-Est', '1 RUE PIERRE TRUCHIS DE LAYS', 'CHAMPAGNE AU MONT D OR', '69410', 'FR', '', 'Etablissement de crédit', ''),
        ('11706', 'CA mutuel Charente-Maritime Deux-Sevres', '14 RUE LOUIS TARDY', 'LAGORD', '17140', 'FR', '', 'Etablissement de crédit', ''),
        ('12406', 'CA mutuel Charente-Perigord', 'RUE D EPAGNAC', 'SOYAUX', '16800', 'FR', '', 'Etablissement de crédit', ''),
        ('13306', 'CA mutuel Aquitaine', '106 QUAI DE BACALAN', 'BORDEAUX CEDEX', '33076', 'FR', '', 'Etablissement de crédit', ''),
        ('13606', 'CA mutuel Ille-et-Vilaine', '4 RUE LOUIS BRAILLE', 'ST JACQUES DE LA LANDE', '35136', 'FR', '', 'Etablissement de crédit', ''),
        ('16806', 'CA mutuel Centre France', '3 AVENUE DE LA LIBERATION', 'CLERMONT FERRAND CEDEX1', '63045', 'FR', '', 'Etablissement de crédit', ''),
        ('11006', 'CA mutuel Champagne-Bourgogne', '269 FAUBOURG CRONCELS', 'TROYES CEDEX', '10080', 'FR', '', 'Etablissement de crédit', ''),
        ('12506', 'CA mutuel Franche-Comte', '11 AVENUE ELISEE CUSENIER', 'BESANCON CEDEX 9', '25084', 'FR', '', 'Etablissement de crédit', ''),
        ('17906', 'CA mutuel Anjou et du Maine', '40 RUE PREMARTINE', 'LE MANS CEDEX 9', '72083', 'FR', '', 'Etablissement de crédit', ''),
        ('12006', 'CA mutuel Corse', '1 AVENUE NAPOLEON III', 'AJACCIO CEDEX', '20193', 'FR', '', 'Etablissement de crédit', ''),
        ('14006', 'CA mutuel Guadeloupe', 'PETIT PEROU', 'ABYMES CEDEX', '97176', 'FR', '', 'Etablissement de crédit', ''),
        ('19806', 'CA mutuel Martinique et Guyane', 'RUE CASE NEGRE PLACE D ARMES', 'LE LAMENTIN CEDEX 2', '97232', 'FR', '', 'Etablissement de crédit', ''),
        ('19906', 'CA mutuel Reunion', 'CITE DES LAURIERS', 'SAINT-DENIS CEDEX', '97462', 'FR', '', 'Etablissement de crédit', ''),
        ('19406', 'CA mutuel Touraine et Poitou', '18 RUE SALVADOR ALLENDE', 'POITIERS CEDEX', '86008', 'FR', '', 'Etablissement de crédit', ''),
        ('16106', 'CA mutuel Lorraine', 'CS 71700', 'NANCY CEDEX', '54017', 'FR', '', 'Etablissement de crédit', ''),
        ('16606', 'CA mutuel Normandie', '15 ESPL. BRILLAUD DE LAUJARDIERE', 'CAEN CEDEX', '14050', 'FR', '', 'Etablissement de crédit', ''),
        ('18206', 'CA mutuel Paris et Ile-de-France', '26 QUAI DE LA RAPEE', 'PARIS CEDEX 12', '75596', 'FR', '', 'Etablissement de crédit', ''),
        ('12206', 'CA mutuel Cotes-d Armor', 'LA CROIX TUAL', 'PLOUFRAGAN', '22440', 'FR', '', 'Etablissement de crédit', ''),
        ('18106', 'CA mutuel des Savoie', '4 AVENUE DU PRE-FELIN', 'ANNECY LE VIEUX', '74985', 'FR', '', 'Etablissement de crédit', ''),
        ('19506', 'CA mutuel Centre Ouest', '29 BOULEVARD DE VANTEAUX', 'LIMOGES CEDEX', '87044', 'FR', '', 'Etablissement de crédit', ''),
        ('12906', 'CA mutuel Finistere', '7 ROUTE DU LOCH', 'QUIMPER CEDEX 9', '29555', 'FR', '', 'Etablissement de crédit', ''),
        ('13506', 'CA mutuel Languedoc', 'AVENUE DE MONPELLIERET', 'LATTES CEDEX', '34977', 'FR', '', 'Etablissement de crédit', ''),
        ('16006', 'CA mutuel Morbihan', 'AVENUE DE KERANGUEN', 'VANNES CEDEX 9', '56956', 'FR', '', 'Etablissement de crédit', ''),
        ('10206', 'CA mutuel Nord Est', '25 RUE LIBERGIER', 'REIMS CEDEX', '51088', 'FR', '', 'Etablissement de crédit', ''),
        ('14506', 'CA mutuel Loire Haute-Loire', '94 RUE BERGSON', 'ST ETIENNE Cedex 1', '42007', 'FR', '', 'Etablissement de crédit', ''),
        ('16706', 'CA mutuel Nord de France', '10 AVENUE FOCH', 'LILLE CEDEX', '59020', 'FR', '', 'Etablissement de crédit', ''),
        ('11206', 'CA mutuel Nord Midi-Pyrenees', '219 AVENUE FRANCOIS VERDIER', 'ALBI CEDEX 9', '81022', 'FR', '', 'Etablissement de crédit', ''),
        ('18306', 'CA mutuel Normandie-Seine', 'CS 70800', 'BOIS GUILLAUME CEDEX', '76238', 'FR', '', 'Etablissement de crédit', ''),
        ('19106', 'CA mutuel Provence-Cote d Azur', 'AVENUE PAUL ARENE', 'DRAGUIGNAN', '83300', 'FR', '', 'Etablissement de crédit', ''),
        ('16906', 'CA mutuel Pyrenees-Gascogne', '11 BOULEVARD PRESIDENT KENNEDY', 'TARBES CEDEX', '65003', 'FR', '', 'Etablissement de crédit', ''),
        ('13906', 'CA mutuel Sud Rhone-Alpes', '12 PLACE DE LA RESISTANCE', 'GRENOBLE', '38000', 'FR', '', 'Etablissement de crédit', ''),
        ('17106', 'CA mutuel Sud-Mediterranee', '30 RUE PIERRE BRETONNEAU', 'PERPIGNAN CEDEX', '66832', 'FR', '', 'Etablissement de crédit', ''),
        ('13106', 'CA mutuel Toulouse 31', '6-7 PLACE JEANNE D ARC', 'TOULOUSE CEDEX 6', '31005', 'FR', '', 'Etablissement de crédit', ''),
        ('14406', 'CA mutuel Val de France', '1 RUE DANIEL BOUTET', 'CHARTRES CEDEX', '28023', 'FR', '', 'Etablissement de crédit', ''),
        ('13798', 'Caisse solidaire', '235 BOULEVARD PAUL PAINLEVE', 'LILLE', '59000', 'FR', '', 'Etablissement de crédit', ''),
        ('12619', 'Caixa geral de depositos S.A.', '38 RUE DE PROVENCE', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('12933', 'Caixabank', '2 rue de Goethe', 'PARIS', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('14648', 'Capitole Finance Tofinso', '2839 AVENUE DE LA LAURAGAISE', 'LABEGE CEDEX', '31682', 'FR', '', 'Etablissement de crédit', ''),
        ('19870', 'Carrefour banque', '9-13 AVENUE DU LAC', 'EVRY-COURCOURONNES', '91000', 'FR', '', 'Etablissement de crédit', ''),
        ('11307', 'CASDEN Banque Populaire', '91 COURS DES ROCHES', 'CHAMPS SUR MARNE', '77420', 'FR', '', 'Etablissement de crédit', ''),
        ('12739', 'CFM Indosuez Wealth', '11 boulevard albert 1er', 'Monaco cedex', '98012', 'MC', '', 'Etablissement de crédit', ''),
        ('17208', 'CHECKOUT', '52 BOULEVARD DE SEBASTOPOL', 'PARIS', '75003', 'FR', '', 'Autre institution', ''),
        ('18233', 'CHINA CONSTRUCTION BANK EUROPE S.A', '86-88 Boulevard Haussmann', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('10918', 'Cholet Dupont', '16 PLACE DE LA MADELEINE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('16700', 'Cicobail', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('14658', 'CIF EUROMORTGAGE', '26 RUE DE MADRID', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('11689', 'CITIBANK EUROPE', '21-25 Rue Balzac', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14218', 'Claas financial services', '12 RUE DU PORT', 'NANTERRE', '92000', 'FR', '', 'Etablissement de crédit', ''),
        ('22040', 'Confederation Nationale du Credit Mutuel', '88-90 Rue Cardinet', 'Paris cedex 17', '75847', 'FR', '', 'Etablissement de crédit', ''),
        ('10218', 'Cooperatieve Rabobank U.A.', '69 BOULEVARD HAUSSMANN', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14940', 'Cofidis', '61 AVENUE HALLEY', 'VILLENEUVE D ASCQ CEDEX', '59866', 'FR', '', 'Etablissement de crédit', ''),
        ('17629', 'Commerzbank ag', '23 rue de la Paix', 'PARIS CEDEX 02', '75084', 'FR', '', 'Etablissement de crédit', ''),
        ('30051', 'Compagnie de financement foncier', '19 RUE DES CAPUCINES', 'PARIS 01', '75001', 'FR', '', 'Etablissement de crédit', ''),
        ('18189', 'Compagnie generale de credit aux particuliers Credipar', '2 BOULEVARD DE L EUROPE', 'POISSY Cedex', '78307', 'FR', '', 'Etablissement de crédit', ''),
        ('31489', 'Credit agricole corporate and investment bank', '12 PLACE DES ETATS-UNIS', 'Montrouge Cedex', '92547', 'FR', '', 'Etablissement de crédit', ''),
        ('15898', 'Credit Agricole home loan SFH', '12 PLACE DES ETATS UNIS', 'MONTROUGE', '92120', 'FR', '', 'Etablissement de crédit', ''),
        ('16850', 'Credit agricole leasing & factoring', '12 PLACE DES ETATS-UNIS', 'MONTROUGE CEDEX', '92548', 'FR', '', 'Etablissement de crédit', ''),
        ('16468', 'Credit Agricole Public Sector SCF', '12 PLACE DES ETATS-UNIS', 'MONTROUGE CEDEX', '92127', 'FR', '', 'Etablissement de crédit', ''),
        ('30006', 'Credit Agricole S.A.', '12 PLACE DES ETATS UNIS', 'MONTROUGE', '92120', 'FR', 'AGRIFRPP', 'Etablissement de crédit', ''),
        ('42559', 'Credit cooperatif', '12 BOULEVARD PESARO', 'NANTERRE CEDEX', '92024', 'FR', 'CCOPFRPP', 'Etablissement de crédit', ''),
        ('30076', 'Credit du Nord', '28 PLACE RIHOUR', 'LILLE CEDEX', '59023', 'FR', 'NORDFRPP', 'Etablissement de crédit', ''),
        ('43199', 'Credit Foncier de France', '19 RUE DES CAPUCINES', 'PARIS 01', '75001', 'FR', '', 'Etablissement de crédit', ''),
        ('15149', 'Credit foncier et communal Alsace et Lorraine', '1 RUE DU DOME', 'STRASBOURG CEDEX', '67003', 'FR', '', 'Etablissement de crédit', ''),
        ('16718', 'Credit Immobilier de France Developpement', '26/28 RUE DE MADRID', 'PARIS CEDEX 08', '75384', 'FR', '', 'Autre institution', ''),
        ('30066', 'Credit industriel et commercial CIC', '6 AVENUE DE PROVENCE', 'PARIS 09', '75009', 'FR', 'CMCIFRPP', 'Etablissement de crédit', ''),
        ('30002', 'CREDIT LYONNAIS LCL', '18 rue de la Republique', 'LYON', '69002', 'FR', 'CRLYFRPP', 'Etablissement de crédit', ''),
        ('10160', 'Credit mobilier de Monaco', '15 avenue de Grande-Bretagne', 'MONACO CEDEX', '98002', 'MC', '', 'Etablissement de crédit', ''),
        ('15208', 'Credit municipal de Paris', '55 RUE DES FRANCS-BOURGEOIS', 'PARIS CEDEX 04', '75181', 'FR', '', 'Etablissement de crédit', ''),
        ('15589', 'Credit mutuel Arkea', '1 RUE LOUIS LICHOU', 'LE RELECQ KERHUON', '29480', 'FR', '', 'Etablissement de crédit', ''),
        ('11978', 'Credit Mutuel Factoring', 'TOUR KUPKA A 18 RUE HOCHE', 'PARIS LA DEFENSE CEDEX', '92980', 'FR', '', 'Etablissement de crédit', ''),
        ('15848', 'Credit Mutuel Home Loan SFH', '6 AVENUE DE PROVENCE', 'PARIS CEDEX 9', '75452', 'FR', '', 'Etablissement de crédit', ''),
        ('13070', 'Credit Mutuel Leasing', '12 RUE GAILLON', 'PARIS CEDEX 02', '75107', 'FR', '', 'Etablissement de crédit', ''),
        ('11600', 'Credit mutuel Real Estate Lease', '4 RUE GAILLON', 'PARIS CEDEX 02', '75107', 'FR', '', 'Etablissement de crédit', ''),
        ('18169', 'Credit suisse Luxembourg S.A.', '25 avenue Kleber', 'PARIS', '75016', 'FR', '', 'Etablissement de crédit', ''),
        ('16000', 'Diac', '14 AVENUE DU PAVE NEUF', 'NOISY-LE-GRAND CEDEX', '93168', 'FR', '', 'Etablissement de crédit', ''),
        ('17290', 'Dexia credit local', '1 PASSERELLE DES REFLETS', 'LA DEFENSE CEDEX', '92913', 'FR', '', 'Etablissement de crédit', ''),
        ('16048', 'Ebi SA', 'IMMEUBLE CONCORDE', 'PARIS LA DEFENSE CEDEX', '92057', 'FR', '', 'Etablissement de crédit', ''),
        ('16658', 'EDENRED PAIEMENT', '166 BOULEVARD GABRIEL PERI', 'MALAKOFF', '92240', 'FR', '', 'Autre institution', ''),
        ('42529', 'Edmond de Rothschild France', '47 RUE DU FAUBOURG SAINT HONORE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('11668', 'Edmond de Rothschild Monaco', 'Carlo Les Terrasses 2 avenue de Monte', 'MONACO CEDEX', '98006', 'MC', '', 'Etablissement de crédit', ''),
        ('18759', 'EFG Bank Monaco', '15 avenue d Ostende Monte Carlo', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('22970', 'Epargne credit des militaires', 'QUARTIER SAINTE MUSSE RUE NICOLAS APPERT', 'Toulon', '83100', 'FR', '', 'Etablissement de crédit', ''),
        ('17979', 'EUROPE ARAB BANK SA', '41 AVENUE DE FRIEDLAND', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13580', 'FACTOFRANCE', 'TOUR D2 17 BIS PLACE DES REFLETS', 'PARIS-LA DEFENSE CEDEX', '92988', 'FR', '', 'Etablissement de crédit', ''),
        ('12478', 'FCE bank plc', '34 rue de la Croix de Fer', 'ST GERMAIN EN LAYE CEDEX', '78174', 'FR', '', 'Etablissement de crédit', ''),
        ('15900', 'FEDERAL FINANCE', '1 ALLEE LOUIS LICHOU', 'LE RELECQ KERHUON', '29480', 'FR', '', 'Etablissement de crédit', ''),
        ('14628', 'FLOA', '71 RUE LUCIEN FAURE', 'BORDEAUX', '33300', 'FR', '', 'Etablissement de crédit', ''),
        ('16760', 'Franfinance', '59 AVENUE DE CHATOU', 'RUEIL-MALMAISON CEDEX', '92853', 'FR', '', 'Autre institution', ''),
        ('18689', 'Fransabank France S.A.', '104 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('16208', 'GE SCF', 'TOUR EUROPLAZA 20 AVENUE ANDRE PROTHIN', 'PARIS-LA-DEFENSE CEDEX', '92063', 'FR', '', 'Etablissement de crédit', ''),
        ('19269', 'Genebanque', '17 COURS VALMY', 'PUTEAUX', '92800', 'FR', '', 'Etablissement de crédit', ''),
        ('17660', 'Genefim', '29 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('25533', 'Goldman Sachs Bank Europe SE', '5 Avenue Kleber', 'PARIS', '75116', 'FR', 'GOLDFRPP', 'Etablissement de crédit', ''),
        ('14120', 'GRESHAM Banque', '20 RUE DE LA BAUME', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('18059', 'HSBC Bank Plc Paris Branch', '38 AVENUE KLEBER', 'PARIS', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('30056', 'HSBC Continental Europe', '38 AVENUE KLEBER', 'PARIS', '75116', 'FR', 'CCFRFRPP', 'Etablissement de crédit', ''),
        ('13888', 'HSBC Factoring France', '38 AVENUE KLEBER', 'PARIS 16', '75116', 'FR', '', 'Autre institution', ''),
        ('14398', 'HSBC Leasing France', '38 AVENUE KLEBER', 'PARIS 16', '75116', 'FR', '', 'Autre institution', ''),
        ('16058', 'HSBC SFH FRANCE', 'IMMEUBLE COEUR DEFENSE 110 ESPLANADE GENERAL DE GAULLE', 'COURBEVOIE', '92400', 'FR', '', 'Etablissement de crédit', ''),
        ('16030', 'IBM France financement', '17 AVENUE DE L EUROPE', 'BOIS-COLOMBES CEDEX', '92275', 'FR', '', 'Autre institution', ''),
        ('11833', 'ICBC Europe SA', '73 BOULEVARD HAUSSMANN', 'PARIS 08', '75008', 'FR', 'ICBKFRPP', 'Etablissement de crédit', ''),
        ('30438', 'ING Bank NV', '40 AVENUE DES TERROIRS DE FRANCE', 'PARIS 12', '75012', 'FR', 'INGBFRPP', 'Etablissement de crédit', ''),
        ('12818', 'IFCIC', '41 RUE DE LA CHAUSSEE D ANTIN', 'PARIS', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('10128', 'Intesa Sanpaolo SpA', '62 RUE DE RICHELIEU', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('16433', 'J.P. Morgan AG', '14 Place Vendome', 'PARIS', '75001', 'FR', '', 'Etablissement de crédit', ''),
        ('12978', 'JCB Finance', '12 RUE DU PORT', 'NANTERRE', '92000', 'FR', '', 'Etablissement de crédit', ''),
        ('15458', 'Joh. Berenberg Gossler & Co. KG', '48 AVENUE VICTOR HUGO', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('14108', 'John Deere financial', 'Rue du Paradis', 'Saint Jean de la ruelle', '45140', 'FR', '', 'Autre institution', ''),
        ('30628', 'JPMorgan Chase bank', '14 PLACE VENDOME', 'PARIS 01', '75001', 'FR', 'CHASFRPP', 'Etablissement de crédit', ''),
        ('27800', 'KBC bank', '6 RUE NICOLAS APPERT', 'LILLE CEDEX', '59030', 'FR', '', 'Etablissement de crédit', ''),
        ('14989', 'KEB Hana Bank', '38 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('20041', 'La Banque Postale', '115 RUE DE SEVRES', 'PARIS CEDEX 06', '75275', 'FR', 'PSSTFRPP', 'Etablissement de crédit', ''),
        ('16178', 'LA BANQUE POSTALE CONSUMER FINANCE', '1-3 AVENUE FRANCOIS MITTERRAND', 'SAINT DENIS', '93200', 'FR', '', 'Autre institution', ''),
        ('16608', 'LA BANQUE POSTALE HOME LOAN SFH', '115 RUE DE SEVRES', 'PARIS CEDEX 06', '75275', 'FR', '', 'Etablissement de crédit', ''),
        ('16478', 'La Banque Postale Leasing & Factoring', '115 RUE DE SEVRES', 'PARIS CEDEX 06', '75275', 'FR', '', 'Autre institution', ''),
        ('16068', 'Helaba Landesbank Hessen-Thuringen', '118 AVENUE DES CHAMPS ELYSEES', 'PARIS', '75108', 'FR', '', 'Etablissement de crédit', ''),
        ('19063', 'Landesbank Saar SAARLB', '2 PLACE RAYMOND MONDON', 'METZ', '57000', 'FR', '', 'Etablissement de crédit', ''),
        ('30748', 'Lazard Freres Banque', '121 BOULEVARD HAUSSMANN', 'PARIS 08', '75008', 'FR', 'LAZAFRPP', 'Etablissement de crédit', ''),
        ('13150', 'LixxBail', '12 PLACE DES ETATS-UNIS', 'MONTROUGE CEDEX', '92548', 'FR', '', 'Etablissement de crédit', ''),
        ('44449', 'LixxCredit', '12 PLACE DES ETATS-UNIS', 'MONTROUGE CEDEX', '92548', 'FR', '', 'Autre institution', ''),
        ('10800', 'Locam', '29 RUE LEON BLUM', 'ST ETIENNE', '42000', 'FR', '', 'Autre institution', ''),
        ('16773', 'Lombard Odier Europe S.A', '8 RUE ROYALE', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('21670', 'Loomis FX Gold and Services', '42 RUE BENOIT MALON', 'Gentilly', '94250', 'FR', '', 'Etablissement de crédit', ''),
        ('10096', 'Lyonnaise de banque', '8 RUE DE LA REPUBLIQUE', 'LYON CEDEX 01', '69207', 'FR', '', 'Etablissement de crédit', ''),
        ('16908', 'Ma French Bank', '115 RUE DE SEVRES', 'Paris Cedex 06', '75275', 'FR', '', 'Etablissement de crédit', ''),
        ('25833', 'Macquarie bank Europe DAC', '41 Avenue George V', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('11508', 'MARKET PAY', '33 AVENUE EMILE ZOLA', 'Boulogne-Billancourt', '92100', 'FR', '', 'Autre institution', ''),
        ('15148', 'Mediobanca', '43 RUE DE LA BIENFAISANCE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('18789', 'Mega international commercial bank Co Ltd', '131 RUE DE TOLBIAC', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('17338', 'MEMO BANK', '8 RUE DU FBG POISSONNIERE', 'PARIS', '75010', 'FR', '', 'Etablissement de crédit', ''),
        ('16233', 'Mercedes-Benz bank AG', '14 place claudel', 'Montigny le bretonneux', '78180', 'FR', '', 'Etablissement de crédit', ''),
        ('24599', 'Milleis Banque', '32 AVENUE GEORGE V', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('19973', 'Mirabaud & Cie Europe SA', '13 AVENUE HOCHE', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('18529', 'Mizuho bank ltd Paris branch', '40 RUE WASHINGTON', 'PARIS CEDEX 08', '75408', 'FR', '', 'Etablissement de crédit', ''),
        ('16989', 'Mobilis banque', '64 BOULEVARD DE CAMBRAI', 'ROUBAIX', '59100', 'FR', '', 'Etablissement de crédit', ''),
        ('14690', 'Monabanq', '61 AVENUE HALLEY', 'VILLENEUVE D ASCQ', '59650', 'FR', '', 'Etablissement de crédit', ''),
        ('41249', 'MUFG Bank Ltd', '18 rue du Quatre Septembre', 'PARIS', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('42799', 'My Money Bank', '20 AV ANDRE PROTHIN', 'PARIS LA DEFENSE CEDEX', '92063', 'FR', '', 'Etablissement de crédit', ''),
        ('17549', 'Naticredibail', '12 RUE DU PORT', 'NANTERRE', '92000', 'FR', '', 'Etablissement de crédit', ''),
        ('14139', 'National bank of Pakistan', '25 RUE JEAN GIRAUDOUX', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('30007', 'Natixis', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', 'NATXFRPP', 'Etablissement de crédit', ''),
        ('16278', 'Natixis Asset Management Finance', '59 AVENUE PIERRE MENDES FRANCE', 'PARIS', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('11470', 'Natixis Coficine', '6 RUE DE L AMIRAL HAMELIN', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('15930', 'NATIXIS PAYMENT SOLUTIONS', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Etablissement de crédit', ''),
        ('18919', 'NATIXIS WEALTH MANAGEMENT', '115 RUE MONTMARTRE', 'PARIS', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('23133', 'NATWEST MARKETS N.V.', '32 rue de Monceau', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('41639', 'NBK France SA', '90 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('45850', 'Oddo BHF SCA', '12 BOULEVARD DE LA MADELEINE', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('12869', 'ONEY BANK', '40 AVENUE DE FLANDRE', 'CROIX CEDEX', '59964', 'FR', '', 'Etablissement de crédit', ''),
        ('17839', 'Opel Bank', '2 BOULEVARD DE L EUROPE', 'Poissy', '78300', 'FR', '', 'Etablissement de crédit', ''),
        ('18370', 'ORANGE BANK', '67 RUE ROBESPIERRE', 'MONTREUIL', '93100', 'FR', '', 'Etablissement de crédit', ''),
        ('27589', 'Oudart S.A.', '10 A RUE DE LA PAIX', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('21349', 'Parilease', '41 AVENUE DE L OPERA', 'PARIS 02', '75002', 'FR', '', 'Autre institution', ''),
        ('17288', 'PICTET & CIE EUROPE S.A. Monaco', 'Villa Miraflores avenue Saint-Michel 02', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('15068', 'Pictet & Cie Europe SA', '34 AVENUE DE MESSINE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14749', 'PSA BANQUE FRANCE', '2 BOULEVARD DE L EUROPE', 'POISSY Cedex', '78307', 'FR', '', 'Etablissement de crédit', ''),
        ('17919', 'Qatar national bank', '65 AVENUE D IENA', 'PARIS 16', '75116', 'FR', '', 'Etablissement de crédit', ''),
        ('43789', 'Quilvest banque privee', '243 BOULEVARD SAINT GERMAIN', 'PARIS 07', '75007', 'FR', '', 'Etablissement de crédit', ''),
        ('15298', 'RBC Investor services bank France SA', '105 RUE REAUMUR', 'PARIS 02', '75002', 'FR', '', 'Etablissement de crédit', ''),
        ('11188', 'RCI Banque', '15 RUE D UZES', 'PARIS', '75002', 'FR', 'RCIEFR22', 'Etablissement de crédit', ''),
        ('28233', 'REVOLUT PAYMENTS UAB', '3 RUE DE STOCKHOLM', 'PARIS', '75008', 'FR', '', 'Autre institution', ''),
        ('27033', 'Riverbank S.A.', '9 rue Christophe Colomb', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13369', 'Rothschild Martin Maurel', '29 AVENUE DE MESSINE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14478', 'ROTHSCHILD & CO WEALTH MANAGEMENT MONACO', '11 BOULEVARD DES MOULINS', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('12098', 'SOCIETE DE BANQUE MONACO', '27 avenue de la Costa', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('16788', 'Santander Consumer Banque', '26 QUAI MICHELET', 'LEVALLOIS PERRET', '92300', 'FR', '', 'Etablissement de crédit', ''),
        ('28533', 'Solarisbank AG', '7 RUE MEYERBEER', 'PARIS', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('16588', 'SFIL', '1-3 RUE DU PASSEUR DE BOULOGNE', 'ISSY LES MOULINEAUX CEDEX 9', '92861', 'FR', '', 'Etablissement de crédit', ''),
        ('43629', 'Societe anonyme de credit a l industrie francaise CALIF', '189 RUE D AUBERVILLIERS', 'PARIS CEDEX 18', '75886', 'FR', '', 'Etablissement de crédit', ''),
        ('30003', 'Societe generale', '189 RUE D AUBERVILLIERS', 'PARIS CEDEX 18', '75886', 'FR', 'SOGEFRPP', 'Etablissement de crédit', ''),
        ('17060', 'SOCIETE GENERALE Factoring', '3 RUE FRANCIS DE PRESSENSE', 'LA PLAINE ST DENIS CEDEX', '93577', 'FR', '', 'Etablissement de crédit', ''),
        ('13368', 'Societe generale private banking Monaco', '11 AVENUE DE GRANDE BRETAGNE', 'MONACO', '98007', 'MC', '', 'Etablissement de crédit', ''),
        ('15968', 'Societe Generale SCF', '17 COURS VALMY', 'PUTEAUX', '92800', 'FR', '', 'Etablissement de crédit', ''),
        ('16228', 'Societe generale SFH', '17 COURS VALMY', 'PUTEAUX', '92800', 'FR', '', 'Etablissement de crédit', ''),
        ('30077', 'Societe marseillaise de credit', '75 RUE PARADIS', 'MARSEILLE 06', '13006', 'FR', '', 'Etablissement de crédit', ''),
        ('12280', 'Socram banque', '2 RUE DU 24 FEVRIER', 'NIORT CEDEX 9', '79092', 'FR', '', 'Etablissement de crédit', ''),
        ('19460', 'Sofax banque', '2 PLACE JEAN MILLIER', 'COURBEVOIE', '92400', 'FR', '', 'Etablissement de crédit', ''),
        ('19259', 'Sogefimur', '29 BOULEVARD HAUSSMANN', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('12438', 'SOFIAP', '7 RUE DE LA PIERRE LEVEE', 'PARIS 11', '75011', 'FR', '', 'Autre institution', ''),
        ('21570', 'Societe financiere de la NEF', '8 AVENUE DES CANUTS', 'VAULX EN VELIN', '69120', 'FR', '', 'Etablissement de crédit', ''),
        ('15250', 'SMBC Bank International plc', '1-3-5 RUE PAUL CEZANNE', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13833', 'Stifel Europe Bank AG', '123 RUE DE BERRI', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('14568', 'Svenska handelsbanken AB', '7 RUE DROUOT', 'PARIS 09', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('17328', 'SWAN', '95 AV DU PRESIDENT WILSON', 'MONTREUIL', '93100', 'FR', '', 'Autre institution', ''),
        ('11238', 'SwissLife banque privee', '7 PLACE VENDOME', 'PARIS 01', '75001', 'FR', '', 'Etablissement de crédit', ''),
        ('13733', 'The bank of New York Mellon SA/NV', '7 RUE SCRIBE', 'PARIS', '75109', 'FR', '', 'Etablissement de crédit', ''),
        ('16618', 'The Export-Import Bank of China', '62 rue de Courcelles', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('15258', 'Bank of Ireland', '20 avenue Franklin Roosevelt', 'PARIS', '75108', 'FR', '', 'Etablissement de crédit', ''),
        ('13878', 'Toyota kreditbank GmbH', '36 BOULEVARD DE LA REPUBLIQUE', 'VAUCRESSON', '92420', 'FR', '', 'Etablissement de crédit', ''),
        ('16798', 'Treezor SAS', '94 RUE DE VILLIERS', 'LEVALLOIS PERRET', '92300', 'FR', '', 'Autre institution', ''),
        ('43849', 'Tunisian foreign bank', '19 RUE DES PYRAMIDES', 'PARIS 01', '75001', 'FR', '', 'Etablissement de crédit', ''),
        ('30758', 'UBS France S.A.', '69 BOULEVARD HAUSSMANN', 'PARIS 08', '75008', 'FR', 'UBSWFRPP', 'Etablissement de crédit', ''),
        ('11999', 'UBS Monaco s.a.', '2 avenue de Grande Bretagne', 'MONACO CEDEX', '98007', 'MC', '', 'Etablissement de crédit', ''),
        ('24333', 'UBS Europe SE', '69 Boulevard Haussmann', 'PARIS', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('11998', 'Unicredit bank AG', '117 avenue des Champs Elysees', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('13528', 'Unicredit SpA', '117 AVENUE DES CHAMPS ELYSEES', 'PARIS 08', '75008', 'FR', '', 'Etablissement de crédit', ''),
        ('18280', 'Unifergie', '12 PLACE DES ETATS-UNIS', 'MONTROUGE CEDEX', '92548', 'FR', '', 'Etablissement de crédit', ''),
        ('16648', 'UNION BANCAIRE PRIVEE UBP SA Monaco', '11 bld des Moulins', 'MONACO', '98000', 'MC', '', 'Etablissement de crédit', ''),
        ('43899', 'Union de banques arabes et francaises UBAF', '2 AVENUE GAMBETTA', 'PARIS LA DEFENSE CEDEX', '92066', 'FR', '', 'Etablissement de crédit', ''),
        ('19570', 'Union financiere de France banque', '32 AVENUE D IENA', 'PARIS CEDEX 16', '75783', 'FR', '', 'Etablissement de crédit', ''),
        ('15128', 'Volkswagen bank GmbH', 'PARC D AFFAIRES SILIC', 'VILLEPINTE', '93420', 'FR', '', 'Etablissement de crédit', ''),
        ('14633', 'Western union international bank GmbH', '5-6 PLACE DE L IRIS', 'LA DEFENSE Cedex', '92095', 'FR', '', 'Etablissement de crédit', ''),
        ('16488', 'YOUNITED', '21 RUE DE CHATEAUDUN', 'PARIS', '75009', 'FR', '', 'Etablissement de crédit', ''),
        ('12558', 'VFS Finance France', 'TOUR ATLANTIQUE 1 PLACE DE LA PYRAMIDE', 'PARIS', '92911', 'FR', '', 'Autre institution', ''),
        ('16528', 'XPOLLENS', 'RUE RAYMOND LOSSERAND', 'PARIS 14', '75014', 'FR', '', 'Autre institution', ''),
        ('17018', 'YAMAHA MOTOR FINANCE FRANCE', '5 AVENUE DU FIEF', 'CERGY-PONTOISE CEDEX', '95078', 'FR', '', 'Autre institution', ''),
        ('19940', 'BPCE ENERGECO', '30 AVENUE PIERRE MENDES FRANCE', 'PARIS 13', '75013', 'FR', '', 'Autre institution', ''),
        ('19190', 'BPCE LEASE REUNION', '32 BOULEVARD DU CHAUDRON', 'SAINT DENIS MESSAG CEDEX 9', '97408', 'FR', '', 'Autre institution', ''),
        ('18359', 'Bpifrance', '27-31 AVENUE DU GENERAL LECLERC', 'MAISONS-ALFORT', '94710', 'FR', '', 'Etablissement de crédit', ''),
        ('15468', 'Scania finance France', 'ZONE INDUSTRIELLE D ECOUFLANT', 'ANGERS CEDEX 01', '49009', 'FR', '', 'Autre institution', ''),
        ('18230', 'SOFIPROTEOL', '11 RUE DE MONCEAU', 'PARIS', '75008', 'FR', '', 'Autre institution', ''),
        ('17439', 'SOFIDER', '3 RUE LABOURDONNAIS', 'SAINT-DENIS CEDEX', '97477', 'FR', '', 'Etablissement de crédit', ''),
        ('60220', 'Caisse de developpement de la Corse', '6 AVENUE DE PARIS', 'AJACCIO CEDEX 01', '20176', 'FR', '', 'Autre institution', ''),
        ('11190', 'Caisse de garantie du logement locatif social', '10 avenue Ledru-Rollin', 'PARIS CEDEX 12', '75579', 'FR', '', 'Autre institution', ''),
    ]
    c.executemany("""INSERT OR IGNORE INTO banks
        (code,name,address,city,postal_code,country,bic,type,notes)
        VALUES (?,?,?,?,?,?,?,?,?)""", banks)
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
    """Search via DuckDuckGo (primary) + Bing (fallback)."""
    from bs4 import BeautifulSoup
    results = []
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    # DuckDuckGo HTML
    try:
        r = requests.get(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
                         headers={"User-Agent": ua}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select(".result")[:num]:
            a = item.find("a", class_="result__a")
            snip = item.find("a", class_="result__snippet")
            if a and a.get("href","").startswith("http"):
                results.append({"title": a.get_text(strip=True),
                                 "url": a.get("href",""),
                                 "snippet": snip.get_text(strip=True) if snip else ""})
    except: pass
    # Bing fallback
    if len(results) < 3:
        try:
            r = requests.get(f"https://www.bing.com/search?q={quote_plus(query)}&count={num}",
                              headers={"User-Agent": ua}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for li in soup.select("li.b_algo")[:num]:
                a = li.find("h2", recursive=False)
                a = a.find("a") if a else li.find("a")
                p = li.find("p")
                if a and a.get("href","").startswith("http"):
                    results.append({"title": a.get_text(strip=True),
                                     "url": a.get("href",""),
                                     "snippet": p.get_text(strip=True) if p else ""})
        except: pass
    return results[:num]


def build_search_queries(entity: str) -> list:
    """
    Génère 60+ requêtes couvrant tous les pays / langues :
    FR, EN, ES, PT, DE, IT, AR, ZH, RU + registres monde entier.
    """
    e = entity
    queries = []

    # ── FRANÇAIS ──────────────────────────────────────────────────
    queries += [
        f'"{e}" fraude arnaque escroquerie',
        f'"{e}" condamné condamnation tribunal',
        f'"{e}" mis en examen perquisition garde à vue',
        f'"{e}" liquidation judiciaire redressement faillite',
        f'"{e}" blanchiment financement du terrorisme',
        f'"{e}" corruption détournement malversation',
        f'"{e}" sanction AMF ACPR interdiction',
        f'"{e}" mise en cause plainte dépôt de plainte',
        f'"{e}" faux usage de faux abus de confiance',
        f'"{e}" interdit bancaire liste noire',
    ]
    # ── ANGLAIS ───────────────────────────────────────────────────
    queries += [
        f'"{e}" fraud scam money laundering',
        f'"{e}" corruption bribery convicted sentenced prison',
        f'"{e}" sanctions blacklist OFAC banned',
        f'"{e}" criminal charges lawsuit indicted arrested',
        f'"{e}" fraud warning alert exposed',
        f'"{e}" Ponzi scheme embezzlement misappropriation',
        f'"{e}" regulatory action enforcement penalty',
        f'"{e}" terrorism financing terrorist',
    ]
    # ── ESPAGNOL ──────────────────────────────────────────────────
    queries += [
        f'"{e}" fraude estafa corrupción condenado',
        f'"{e}" blanqueo dinero sanción',
        f'"{e}" detenido arrestado investigado',
    ]
    # ── PORTUGAIS ─────────────────────────────────────────────────
    queries += [
        f'"{e}" fraude golpe corrupção preso condenado',
        f'"{e}" lavagem dinheiro sanção',
    ]
    # ── ALLEMAND ──────────────────────────────────────────────────
    queries += [
        f'"{e}" Betrug Korruption verurteilt verhaftet',
        f'"{e}" Geldwäsche Sanktion Strafe',
    ]
    # ── ITALIEN ───────────────────────────────────────────────────
    queries += [
        f'"{e}" truffa corruzione condannato arrestato',
        f'"{e}" riciclaggio sanzione',
    ]
    # ── ARABE ─────────────────────────────────────────────────────
    queries += [
        f'"{e}" احتيال غسيل أموال فساد',
        f'"{e}" عقوبات قائمة سوداء',
    ]
    # ── RUSSE ─────────────────────────────────────────────────────
    queries += [
        f'"{e}" мошенничество коррупция арест осуждён',
        f'"{e}" санкции отмывание денег',
    ]
    # ── RÉSEAUX SOCIAUX ───────────────────────────────────────────
    queries += [
        f'site:twitter.com "{e}" arnaque fraud scam warning',
        f'site:linkedin.com "{e}"',
        f'site:facebook.com "{e}" arnaque plainte fraude',
        f'site:reddit.com "{e}" scam fraud arnaque',
        f'site:instagram.com "{e}" scam arnaque',
        f'site:youtube.com "{e}" arnaque fraud',
    ]
    # ── AVIS & NOTATIONS ──────────────────────────────────────────
    queries += [
        f'site:trustpilot.com "{e}"',
        f'site:avis-verifies.com "{e}"',
        f'site:glassdoor.com "{e}"',
        f'"{e}" avis client plainte mauvaise expérience victime',
        f'"{e}" déconseillé arnaqueur témoignage',
    ]
    # ── SIGNALEMENTS ARNAQUES ──────────────────────────────────────
    queries += [
        f'site:signal-arnaques.com "{e}"',
        f'site:cybermalveillance.gouv.fr "{e}"',
        f'site:escroqueries.fr "{e}"',
        f'"{e}" arnaque signalé victime forum',
    ]
    # ── REGISTRES LÉGAUX MONDE ENTIER ─────────────────────────────
    queries += [
        # France
        f'site:infogreffe.fr "{e}"',
        f'site:bodacc.fr "{e}"',
        f'site:pappers.fr "{e}"',
        f'site:societe.com "{e}"',
        f'site:verif.com "{e}"',
        f'site:legifrance.gouv.fr "{e}"',
        f'site:justice.fr "{e}"',
        # International
        f'site:companieshouse.gov.uk "{e}"',
        f'site:opencorporates.com "{e}"',
        f'site:sec.gov "{e}"',
        f'site:pacer.gov "{e}"',
        f'"{e}" company registry incorporated',
        f'"{e}" court records judgment filed',
    ]
    # ── SANCTIONS INTERNATIONALES ─────────────────────────────────
    queries += [
        f'site:opensanctions.org "{e}"',
        f'site:ofac.treas.gov "{e}"',
        f'site:sanctionsmap.eu "{e}"',
        f'site:un.org/sc/suborg/en/sanctions "{e}"',
        f'site:amf-france.org "{e}"',
        f'site:acpr.banque-france.fr "{e}"',
        f'"{e}" EU UN OFAC SDN sanctioned blacklisted',
        f'"{e}" Interpol red notice wanted',
    ]
    # ── PRESSE MONDIALE ───────────────────────────────────────────
    queries += [
        f'site:reuters.com "{e}"',
        f'site:bloomberg.com "{e}"',
        f'site:ft.com "{e}"',
        f'site:bbc.com "{e}"',
        f'site:theguardian.com "{e}"',
        f'site:lemonde.fr "{e}"',
        f'site:lesechos.fr "{e}"',
        f'site:bfmtv.com "{e}"',
        f'site:latribune.fr "{e}"',
        f'site:spiegel.de "{e}"',
        f'site:elpais.com "{e}"',
    ]

    return queries


def scrape_page(url: str, max_chars=3000) -> str:
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header","aside"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)[:max_chars]
    except:
        return ""


# ══════════════════════════════════════════════════════════════════
# KEYWORD-BASED RISK ENGINE — multilingue (FR/EN/ES/PT/DE/IT/AR/ZH/RU)
# ══════════════════════════════════════════════════════════════════
RISK_KEYWORDS = {
    "sanctions": {
        # FR
        "sanction":5,"sanctionné":5,"sanctions":5,"ofac":5,"gel des avoirs":5,
        "liste noire":5,"blacklist":5,"embargo":4,"liste ue":4,"liste onu":4,
        "seco":4,"amf sanction":5,"acpr sanction":5,"interdiction bancaire":5,
        "interdit bancaire":4,"interdiction d exercer":5,
        # EN
        "sanctioned":5,"blacklisted":5,"ofac list":5,"sdn list":5,
        "eu sanctions":4,"un sanctions":4,"asset freeze":5,"travel ban":4,
        "debarred":4,"banned":4,"restricted":3,
        # ES/PT
        "sancionado":4,"lista negra":4,"embargo":4,"vetado":4,
        # DE/IT
        "sanktioniert":4,"schwarze liste":4,"sanzionato":4,
        # AR
        "عقوبات":5,"قائمة سوداء":5,"تجميد":4,
        # RU
        "санкции":5,"чёрный список":5,"заморозка":4,
    },
    "fraud": {
        # FR
        "fraude":5,"frauduleux":5,"escroquerie":5,"arnaque":4,
        "abus de confiance":5,"détournement":5,"malversation":5,
        "falsification":4,"faux et usage de faux":5,"corruption":5,
        "pot-de-vin":5,"blanchiment":5,"blanchiment d argent":5,
        "financement du terrorisme":5,"financement terrorisme":5,
        "abus de biens sociaux":4,"tromperie":3,"publicité mensongère":2,
        "pratiques commerciales trompeuses":3,"abus de position dominante":3,
        # EN
        "fraud":5,"fraudulent":5,"scam":4,"embezzlement":5,
        "money laundering":5,"bribery":5,"corruption":5,"forgery":4,
        "misappropriation":5,"terrorist financing":5,"ponzi":5,
        "racketeering":5,"extortion":4,"counterfeiting":4,
        # ES
        "fraude":5,"estafa":5,"corrupción":5,"blanqueo":5,
        "malversación":5,"soborno":4,"falsificación":4,
        # PT
        "fraude":5,"golpe":4,"corrupção":5,"lavagem":5,"suborno":4,
        # DE
        "betrug":5,"korruption":5,"geldwäsche":5,"bestechung":4,
        "veruntreuung":5,"fälschung":4,
        # IT
        "truffa":5,"corruzione":5,"riciclaggio":5,"frode":5,
        "peculato":5,"falsificazione":4,
        # AR
        "احتيال":5,"غسيل الأموال":5,"فساد":5,"رشوة":4,"تزوير":4,
        # RU
        "мошенничество":5,"коррупция":5,"отмывание":5,
        "взяточничество":4,"фальсификация":4,
        # ZH
        "欺诈":5,"洗钱":5,"腐败":5,"贿赂":4,
    },
    "judicial": {
        # FR
        "condamné":5,"condamnation":5,"mis en examen":4,"garde à vue":3,
        "perquisition":3,"liquidation judiciaire":4,"redressement judiciaire":4,
        "faillite":4,"procédure collective":4,"tribunal correctionnel":4,
        "tribunal de commerce":3,"jugement":3,"plainte":3,
        "dépôt de bilan":4,"dissolution":3,"peine de prison":5,
        "incarcéré":5,"inculpé":4,"mise en cause":3,"procès":3,
        "arrêté":3,"interpellé":3,"mandat d arrêt":5,"détention":4,
        # EN
        "convicted":5,"conviction":5,"indicted":4,"arrested":4,
        "imprisoned":5,"bankruptcy":4,"liquidation":4,"sued":3,
        "lawsuit":3,"court ruling":3,"criminal charges":5,
        "plea guilty":5,"sentenced":5,"warrant":4,"detained":4,
        "extradited":5,"deported":4,"defaulted":3,
        # ES
        "condenado":5,"arrestado":4,"investigado":3,"demanda":3,
        "quiebra":4,"imputado":4,"detenido":4,
        # PT
        "condenado":5,"preso":5,"investigado":3,"falência":4,
        "indiciado":4,"detido":4,
        # DE
        "verurteilt":5,"verhaftet":4,"angeklagt":4,"insolvenz":4,
        "ermittlung":3,"haftbefehl":5,
        # IT
        "condannato":5,"arrestato":4,"indagato":3,"fallimento":4,
        "imputato":4,"detenuto":4,
        # AR
        "مدان":5,"معتقل":4,"محقق":3,"إفلاس":4,"اعتقال":4,
        # RU
        "осуждён":5,"арестован":4,"обвиняемый":4,"банкротство":4,
        "задержан":3,"обыск":3,
    },
    "reputation": {
        # FR
        "arnaqueur":4,"escroc":4,"mauvais payeur":3,"litige client":2,
        "plainte client":3,"très mauvais":2,"déconseillé":2,
        "méfiez-vous":3,"alerte":3,"avertissement":3,"mise en garde":3,
        "signalement":3,"dénonciation":3,"victime":2,
        # EN
        "scammer":4,"bad reviews":2,"complaint":2,"warning":3,
        "alert":3,"avoid":2,"do not trust":3,"rip off":3,
        "victim":2,"dishonest":3,"untrustworthy":3,
        # ES
        "estafador":4,"queja":2,"advertencia":3,"víctima":2,
        # PT
        "golpista":4,"reclamação":2,"alerta":3,"vítima":2,
    },
    "pep": {
        # FR
        "personnalité politique":3,"personnage politiquement exposé":4,"pep":3,
        "ministre":3,"député":3,"sénateur":3,"préfet":3,"ambassadeur":3,
        "haut fonctionnaire":3,"magistrat":3,"élu":2,
        # EN
        "politically exposed":4,"politician":3,"minister":3,
        "senator":3,"ambassador":3,"official":2,"government":2,
        # ES/PT
        "político":3,"ministro":3,"senador":3,"funcionario":2,
        # AR
        "سياسي":3,"وزير":3,"مسؤول":2,
        # RU
        "политик":3,"министр":3,"чиновник":2,
    },
    "positive": {
        # FR
        "agréé":2,"accrédité":2,"certifié":2,"récompensé":2,"fiable":2,
        "reconnu":1,"bien noté":2,"recommandé":2,"régulé":2,"conforme":2,
        # EN
        "accredited":2,"certified":2,"award":1,"trusted":2,"reliable":2,
        "regulated":2,"licensed":2,"compliant":2,"reputable":2,
        # ES/PT
        "certificado":2,"acreditado":2,"regulado":2,"confiable":2,
    },
}

SOURCE_CREDIBILITY = {
    # Presse FR
    "lemonde.fr":1.5,"lefigaro.fr":1.5,"liberation.fr":1.3,"bfmtv.com":1.3,
    "franceinfo.fr":1.4,"latribune.fr":1.4,"lesechos.fr":1.5,"capital.fr":1.3,
    "challenges.fr":1.3,"leparisien.fr":1.3,"20minutes.fr":1.1,
    # Presse internationale
    "reuters.com":1.6,"bloomberg.com":1.6,"ft.com":1.6,"wsj.com":1.5,
    "theguardian.com":1.5,"nytimes.com":1.5,"bbc.com":1.4,
    "spiegel.de":1.4,"elpais.com":1.4,"corriere.it":1.3,
    # Régulateurs / justice
    "opensanctions.org":2.0,"legifrance.gouv.fr":2.0,"justice.fr":2.0,
    "bodacc.fr":1.8,"infogreffe.fr":1.8,"amf-france.org":2.0,
    "acpr.banque-france.fr":2.0,"interpol.int":2.0,"europol.europa.eu":2.0,
    "tracfin.gouv.fr":2.0,"tribunal.fr":1.8,"courdecassation.fr":1.9,
    "sec.gov":2.0,"ofac.treas.gov":2.0,"pacer.gov":1.8,
    "companieshouse.gov.uk":1.7,"opencorporates.com":1.5,
    "pappers.fr":1.6,"societe.com":1.4,"verif.com":1.3,
    # Avis
    "trustpilot.com":1.1,"avis-verifies.com":1.0,"glassdoor.com":1.0,
    # Arnaques
    "signal-arnaques.com":1.5,"cybermalveillance.gouv.fr":1.8,
    "escroqueries.fr":1.4,
}

def _text_lower(s): return s.lower() if s else ""


def analyze_local(entity: str, search_results: list, scraped_texts: list,
                  os_result: dict, filter_level: int = 0) -> dict:
    """
    Moteur multilingue. filter_level 0-10 :
      0   = aucun filtre (tout remonte pour revue humaine)
      1-3 = entité présente dans la source
      4-6 = entité dans ±400 chars du mot-clé
      7-9 = entité dans ±180 chars
      10  = entité dans ±60 chars (extrême)
    """
    require_entity_in_source = (filter_level >= 1)
    if filter_level == 0:
        proximity_window = None
    elif filter_level <= 3:
        proximity_window = None
    elif filter_level <= 6:
        proximity_window = 400
    elif filter_level <= 9:
        proximity_window = 180
    else:
        proximity_window = 60

    min_neg_score = max(0.3, filter_level * 0.25)

    entity_low   = entity.lower().strip()
    entity_words = [w for w in entity_low.split() if len(w) >= 3]
    entity_tokens = list(set([entity_low] + entity_words))
    if len(entity_words) >= 2:
        entity_tokens.append(entity_words[0])
        entity_tokens.append(entity_words[-1])

    def entity_present(txt: str) -> bool:
        t = txt.lower()
        return any(tok in t for tok in entity_tokens)

    def entity_near_kw(txt_low: str, kw_idx: int) -> bool:
        if proximity_window is None:
            return True
        ctx = txt_low[max(0, kw_idx - proximity_window): kw_idx + proximity_window + len(entity_low)]
        return any(tok in ctx for tok in entity_tokens)

    scores_by_cat = {k: 0.0 for k in RISK_KEYWORDS}
    negative_news = []
    all_articles  = []   # TOUS les articles pour revue humaine
    all_text_sources = []

    # Build source list
    for r in search_results:
        combined = f"{r.get('title','')} {r.get('snippet','')}".strip()
        if not combined:
            continue
        domain = urlparse(r.get("url","")).netloc.replace("www.","")
        cred   = SOURCE_CREDIBILITY.get(domain, 1.0)
        entity_found = entity_present(combined)

        # Store ALL articles for human review
        all_articles.append({
            "title":   r.get("title",""),
            "url":     r.get("url",""),
            "snippet": r.get("snippet",""),
            "domain":  domain,
            "entity_mentioned": entity_found,
        })

        if require_entity_in_source and not entity_found:
            continue
        all_text_sources.append({
            "text": combined, "title": r.get("title",""),
            "url": r.get("url",""), "domain": domain, "cred": cred,
        })

    for t in scraped_texts:
        if not t:
            continue
        if require_entity_in_source and not entity_present(t):
            continue
        all_text_sources.append({
            "text": t, "title": "", "url": "", "domain": "", "cred": 1.0,
        })

    # Scoring
    nature_map = {
        "sanctions":"Sanction / Liste noire", "fraud":"Fraude / Corruption",
        "judicial":"Litige judiciaire",       "reputation":"Réputation négative",
        "pep":"Exposition PEP"
    }
    for src in all_text_sources:
        txt_low = src["text"].lower()
        for cat, kws in RISK_KEYWORDS.items():
            cat_hits = []
            for kw, weight in kws.items():
                idx = txt_low.find(kw)
                while idx != -1:
                    if entity_near_kw(txt_low, idx):
                        effective = weight * src["cred"]
                        cat_hits.append((kw, round(effective, 1)))
                        scores_by_cat[cat] += effective
                        break
                    idx = txt_low.find(kw, idx + 1)

            if cat != "positive" and cat_hits and src.get("title"):
                neg_score = sum(w for _, w in cat_hits)
                if neg_score >= min_neg_score:
                    gravite = "eleve" if neg_score >= 7 else ("moyen" if neg_score >= 4 else "faible")
                    negative_news.append({
                        "titre":      src["title"][:120],
                        "source":     src.get("domain",""),
                        "url":        src.get("url",""),
                        "date":       "",
                        "nature":     nature_map.get(cat, cat),
                        "gravite":    gravite,
                        "mots_cles":  [kw for kw, _ in cat_hits[:5]],
                        "score_brut": round(neg_score, 1),
                        "cat":        cat,
                    })

    # Deduplicate negative_news
    seen_titles, neg_dedup = set(), []
    for n in sorted(negative_news, key=lambda x: x["score_brut"], reverse=True):
        key = n["titre"][:45].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            neg_dedup.append(n)

    if os_result.get("found"):
        scores_by_cat["sanctions"] += os_result["count"] * 12

    raw = (
        scores_by_cat["sanctions"] * 3.0 +
        scores_by_cat["fraud"]     * 2.5 +
        scores_by_cat["judicial"]  * 2.0 +
        scores_by_cat["reputation"]* 1.2 +
        scores_by_cat["pep"]       * 0.8
    )
    positive_offset = scores_by_cat["positive"] * 2.5
    score = min(100, max(0, int(raw * 1.8 - positive_offset)))

    if score >= 70:    niveau = "CRITIQUE"
    elif score >= 45:  niveau = "ELEVE"
    elif score >= 20:  niveau = "MODERE"
    else:              niveau = "FAIBLE"

    if score >= 60 or os_result.get("found") or scores_by_cat["sanctions"] > 8:
        reco = "REFUSER"
    elif score >= 25 or len(neg_dedup) >= 2:
        reco = "VIGILANCE_RENFORCEE"
    else:
        reco = "ACCEPTER"

    sanctions_trouve  = os_result.get("found", False) or scores_by_cat["sanctions"] > 5
    sanctions_details = ""
    if os_result.get("found"):
        sanctions_details = f"{os_result['count']} résultat(s) OpenSanctions : " + \
            ", ".join(r.get("caption","") for r in os_result.get("results",[])[:3])
    elif scores_by_cat["sanctions"] > 5:
        kws_f = set(kw for src in all_text_sources
                    for kw in RISK_KEYWORDS["sanctions"] if kw in src["text"].lower())
        sanctions_details = "Indicateurs : " + ", ".join(list(kws_f)[:5])

    litiges_trouve  = scores_by_cat["judicial"] > 4
    litiges_details = ""
    if litiges_trouve:
        kws_j = set(kw for src in all_text_sources
                    for kw in RISK_KEYWORDS["judicial"] if kw in src["text"].lower())
        litiges_details = "Indicateurs : " + ", ".join(list(kws_j)[:6])

    pep_trouve  = scores_by_cat["pep"] > 3
    pep_details = "Exposition potentielle à des personnes politiquement exposées." if pep_trouve else ""

    rep_score = scores_by_cat["reputation"]
    pos_score = scores_by_cat["positive"]
    if rep_score > pos_score * 1.5:
        rep_notations = f"Réputation dégradée (négatif:{round(rep_score,1)} / positif:{round(pos_score,1)})"
    elif pos_score > rep_score * 1.5:
        rep_notations = f"Réputation globalement positive (positif:{round(pos_score,1)})"
    else:
        rep_notations = "Réputation neutre ou insuffisamment documentée."

    nb_neg     = len(neg_dedup)
    src_count  = len(all_text_sources)
    nb_total   = len(search_results)

    resume_parts = [f"Screening de {nb_total} résultats ({src_count} analysés)."]
    if nb_neg:
        resume_parts.append(f"{nb_neg} signal(aux) négatif(s) détecté(s) pour {entity}.")
    else:
        resume_parts.append(f"Aucun signal négatif significatif pour {entity}.")
    if sanctions_trouve:
        resume_parts.append("⚠️ Indicateurs de sanctions détectés.")
    elif score < 20:
        resume_parts.append("Profil de risque faible.")

    aggravants, attenuants = [], []
    if os_result.get("found"):
        aggravants.append(f"{os_result['count']} entrée(s) OpenSanctions confirmée(s)")
    if scores_by_cat["fraud"] > 5:
        aggravants.append(f"Mots-clés fraude/corruption (score:{round(scores_by_cat['fraud'],1)})")
    if scores_by_cat["judicial"] > 4:
        aggravants.append(f"Indicateurs procédures judiciaires (score:{round(scores_by_cat['judicial'],1)})")
    if nb_neg >= 3:
        aggravants.append(f"{nb_neg} actualités négatives détectées")
    if pos_score > 4:
        attenuants.append(f"Signaux positifs détectés (score:{round(pos_score,1)})")
    if nb_neg == 0 and not os_result.get("found"):
        attenuants.append("Aucun signal négatif significatif détecté")
    if scores_by_cat["sanctions"] == 0:
        attenuants.append("Absent des bases de sanctions consultées")

    confidence = "ELEVEE" if src_count >= 10 else ("MOYENNE" if src_count >= 4 else "FAIBLE")

    return {
        "score_risque":        score,
        "niveau_risque":       niveau,
        "resume_executif":     " ".join(resume_parts),
        "negative_news":       neg_dedup[:20],
        "all_articles":        all_articles,       # TOUS pour revue humaine
        "sanctions":           {"trouve": sanctions_trouve,  "details": sanctions_details},
        "litiges_judiciaires": {"trouve": litiges_trouve,    "details": litiges_details},
        "pep_exposure":        {"trouve": pep_trouve,        "details": pep_details},
        "reputation_notations":rep_notations,
        "facteurs_aggravants": aggravants,
        "facteurs_attenuants": attenuants,
        "recommandation":      reco,
        "sources_consultees":  list(set(s["domain"] for s in all_text_sources if s.get("domain")))[:25],
        "confiance_analyse":   confidence,
        "scores_categories":   {k: round(v, 1) for k, v in scores_by_cat.items()},
        "nb_sources_filtrees": src_count,
        "nb_sources_total":    nb_total,
        "filter_level_used":   filter_level,
        "moteur":              "local_multilang_v4",
    }


def analyze_with_groq(entity, search_results, scraped_texts, groq_key) -> dict:
    """Groq LLM boost — gratuit 14 400 req/jour sur console.groq.com"""
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
{{"score_risque":0,"niveau_risque":"FAIBLE","resume_executif":"","negative_news":[{{"titre":"","source":"","date":"","nature":"","gravite":"faible","url":""}}],"sanctions":{{"trouve":false,"details":""}},"litiges_judiciaires":{{"trouve":false,"details":""}},"pep_exposure":{{"trouve":false,"details":""}},"reputation_notations":"","facteurs_aggravants":[],"facteurs_attenuants":[],"recommandation":"ACCEPTER","confiance_analyse":"MOYENNE"}}"""
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}],
                  "max_tokens":1800,"temperature":0.1}, timeout=30)
        if r.status_code == 200:
            raw = r.json()["choices"][0]["message"]["content"].strip()
            raw = re.sub(r'^```json\s*','',raw); raw = re.sub(r'\s*```$','',raw)
            result = json.loads(raw)
            result["moteur"] = "groq_llama3"
            return result
    except: pass
    return None


def analyze_with_ollama(entity, search_results, scraped_texts) -> dict:
    """Ollama local — 100% privé, aucune donnée envoyée."""
    ctx = [f"[S{i+1}] {sr.get('title','')} | {sr.get('snippet','')[:150]}"
           for i, sr in enumerate(search_results[:10])]
    prompt = f"""Analyste KYC. Entité: «{entity}»\nSources: {chr(10).join(ctx)}
Réponds UNIQUEMENT en JSON: {{"score_risque":0,"niveau_risque":"FAIBLE","resume_executif":"","negative_news":[],"sanctions":{{"trouve":false,"details":""}},"litiges_judiciaires":{{"trouve":false,"details":""}},"pep_exposure":{{"trouve":false,"details":""}},"reputation_notations":"","facteurs_aggravants":[],"facteurs_attenuants":[],"recommandation":"ACCEPTER","confiance_analyse":"MOYENNE"}}"""
    try:
        r = requests.post("http://localhost:11434/api/generate",
            json={"model":"llama3.2","prompt":prompt,"stream":False}, timeout=60)
        if r.status_code == 200:
            raw = r.json().get("response","").strip()
            raw = re.sub(r'^```json\s*','',raw); raw = re.sub(r'\s*```$','',raw)
            result = json.loads(raw)
            result["moteur"] = "ollama_local"
            return result
    except: pass
    return None

def generate_pdf_report(entity, iban_result, bank_info, os_result, analysis,
                        human_decision=None, human_comment="", analyst_name=""):
    """
    Génère le rapport PDF.
    human_decision : None | 'RAS' | 'RISQUE_CONFIRME'
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.units import mm

    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              leftMargin=18*mm, rightMargin=18*mm,
                              topMargin=16*mm,  bottomMargin=16*mm)

    BG=HexColor("#0a0d14"); SURF=HexColor("#111520"); BORD=HexColor("#1e2535")
    ACC=HexColor("#00d4ff"); GREEN=HexColor("#00cc66"); RED=HexColor("#ff3366")
    YEL=HexColor("#ffcc00"); TEXT=HexColor("#c8d6e5"); MUTED=HexColor("#5a6a7a")
    ACC2=HexColor("#ff6b35"); WHITE=HexColor("#ffffff")

    styles = getSampleStyleSheet()
    def S(nm,**kw): return ParagraphStyle(nm,parent=styles["Normal"],**kw)
    sH1   = S("H1", fontSize=11,textColor=ACC,  fontName="Helvetica-Bold",spaceBefore=12,spaceAfter=5)
    sBody = S("B",  fontSize=8.5,textColor=TEXT,fontName="Helvetica",     spaceAfter=3, leading=13)
    sSmall= S("Sm", fontSize=7.5,textColor=MUTED,fontName="Helvetica",    spaceAfter=2)
    sMono = S("Mo", fontSize=8,  textColor=ACC2, fontName="Courier",      spaceAfter=2)
    sWarn = S("W",  fontSize=9,  textColor=YEL,  fontName="Helvetica-Bold",spaceAfter=4)
    sOK   = S("OK", fontSize=9,  textColor=GREEN,fontName="Helvetica-Bold",spaceAfter=4)
    sRed  = S("Rd", fontSize=9,  textColor=RED,  fontName="Helvetica-Bold",spaceAfter=4)

    niveau  = analysis.get("niveau_risque","N/A")
    score   = analysis.get("score_risque","N/A")
    reco    = analysis.get("recommandation","N/A")
    fl      = analysis.get("filter_level_used", "N/A")
    rcolor  = {"FAIBLE":GREEN,"MODERE":YEL,"ELEVE":ACC2,"CRITIQUE":RED}.get(niveau,MUTED)
    rccolor = {"ACCEPTER":GREEN,"VIGILANCE_RENFORCEE":YEL,"REFUSER":RED}.get(reco,MUTED)
    now_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

    story = []

    # ── Header ────────────────────────────────────────────────────
    story.append(Table(
        [["🛡️  FinShield OSINT — Rapport de Conformité",
          f"Généré le\n{now_str}"]],
        colWidths=[120*mm,52*mm],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BG),
            ("TEXTCOLOR",(0,0),(0,0),ACC),("TEXTCOLOR",(1,0),(1,0),MUTED),
            ("FONTNAME",(0,0),(0,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(0,0),14),
            ("FONTSIZE",(1,0),(1,0),8),("ALIGN",(1,0),(1,0),"RIGHT"),
            ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ])))
    story.append(HRFlowable(width="100%",thickness=1.5,color=ACC,spaceAfter=12))

    # ── Entity ────────────────────────────────────────────────────
    story.append(Paragraph(f"Entité analysée : <b>{entity}</b>", sH1))

    # ── Human validation stamp ────────────────────────────────────
    if human_decision == "RAS":
        stamp_color = GREEN
        stamp_text  = "✅  VALIDATION HUMAINE — RAS (Rien à Signaler)"
        stamp_sub   = f"L'analyste confirme : aucune information négative retenue après examen."
    elif human_decision == "RISQUE_CONFIRME":
        stamp_color = RED
        stamp_text  = "⚠️  VALIDATION HUMAINE — INFORMATIONS NÉGATIVES CONFIRMÉES"
        stamp_sub   = f"L'analyste confirme les signaux détectés par FinShield."
    else:
        stamp_color = MUTED
        stamp_text  = "⏳  EN ATTENTE DE VALIDATION HUMAINE"
        stamp_sub   = "Ce rapport est un résultat automatique non encore validé par un analyste."

    story.append(Table(
        [[stamp_text]],
        colWidths=[172*mm],
        style=TableStyle([
            ("BACKGROUND",(0,0),(0,0),BG),
            ("TEXTCOLOR",(0,0),(0,0),stamp_color),
            ("FONTNAME",(0,0),(0,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(0,0),10),
            ("ALIGN",(0,0),(0,0),"CENTER"),("VALIGN",(0,0),(0,0),"MIDDLE"),
            ("TOPPADDING",(0,0),(0,0),10),("BOTTOMPADDING",(0,0),(0,0),6),
            ("BOX",(0,0),(0,0),1.5,stamp_color),
        ])))
    story.append(Paragraph(stamp_sub, sSmall))

    if analyst_name or human_comment:
        rows = []
        if analyst_name:
            rows.append(["Analyste",    analyst_name])
        if human_comment:
            rows.append(["Commentaire", human_comment])
        rows.append(["Date validation", now_str])
        t = Table(rows, colWidths=[38*mm,134*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),BG),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),
            ("TEXTCOLOR",(0,0),(0,-1),MUTED),("TEXTCOLOR",(1,0),(-1,-1),TEXT),
            ("GRID",(0,0),(-1,-1),0.3,BORD),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(t)
    story.append(Spacer(1,8))

    # ── Score box ─────────────────────────────────────────────────
    story.append(Table(
        [[f"Score : {score}/100", f"Niveau : {niveau}",
          f"Recommandation : {reco}", f"Filtre : {fl}/10"]],
        colWidths=[40*mm,38*mm,60*mm,34*mm],
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),SURF),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9),
            ("TEXTCOLOR",(0,0),(0,0),TEXT),
            ("TEXTCOLOR",(1,0),(1,0),rcolor),("TEXTCOLOR",(2,0),(2,0),rccolor),
            ("TEXTCOLOR",(3,0),(3,0),MUTED),
            ("BOX",(0,0),(-1,-1),0.5,BORD),("GRID",(0,0),(-1,-1),0.5,BORD),
        ])))
    story.append(Spacer(1,8))

    # ── Summary ───────────────────────────────────────────────────
    story.append(Paragraph("Résumé exécutif", sH1))
    story.append(Paragraph(analysis.get("resume_executif","Non disponible."), sBody))
    story.append(HRFlowable(width="100%",thickness=0.5,color=BORD,spaceAfter=6))

    # ── IBAN ──────────────────────────────────────────────────────
    if iban_result and iban_result.get("raw"):
        story.append(Paragraph("Vérification IBAN", sH1))
        rows = [["Champ","Valeur"]]
        for f,v in [("IBAN",iban_result.get("formatted","")),
                    ("Statut",iban_result.get("message","")),
                    ("Pays",iban_result.get("country","")),
                    ("Code banque",iban_result.get("bank_code",""))]:
            if v: rows.append([f,v])
        if bank_info:
            rows += [("Banque",bank_info.get("name","")),
                     ("Adresse",f"{bank_info.get('address','')} {bank_info.get('city','')}".strip()),
                     ("BIC",bank_info.get("bic","")),
                     ("Type",bank_info.get("type",""))]
        t = Table(rows, colWidths=[40*mm,132*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),
            ("TEXTCOLOR",(0,1),(0,-1),MUTED),("TEXTCOLOR",(1,1),(-1,-1),TEXT),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),
            ("GRID",(0,0),(-1,-1),0.3,BORD),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(t); story.append(Spacer(1,8))

    # ── Regulatory checks ─────────────────────────────────────────
    story.append(Paragraph("Vérifications Réglementaires (KYC/AML)", sH1))
    san = analysis.get("sanctions",{})
    lit = analysis.get("litiges_judiciaires",{})
    pep = analysis.get("pep_exposure",{})
    rc  = [["Catégorie","Résultat","Détails"],
           ["Sanctions","DÉTECTÉ" if san.get("trouve") else "Non détecté",san.get("details","")[:85]],
           ["OpenSanctions",f"{os_result.get('count',0)} hit(s)",
            ", ".join(r.get("caption","") for r in os_result.get("results",[])[:2])[:85]],
           ["Litiges judiciaires","DÉTECTÉ" if lit.get("trouve") else "Non détecté",lit.get("details","")[:85]],
           ["Exposition PEP","DÉTECTÉ" if pep.get("trouve") else "Non détecté",pep.get("details","")[:85]]]
    t = Table(rc, colWidths=[40*mm,28*mm,104*mm])
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),("TEXTCOLOR",(0,1),(-1,-1),TEXT),
        ("GRID",(0,0),(-1,-1),0.3,BORD),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ])
    for i in range(1,5):
        col = RED if "DÉTECTÉ" in str(rc[i][1]) or (i==2 and os_result.get("count",0)>0) else GREEN
        ts.add("TEXTCOLOR",(1,i),(1,i),col)
        ts.add("FONTNAME",(1,i),(1,i),"Helvetica-Bold")
    t.setStyle(ts); story.append(t); story.append(Spacer(1,8))

    # ── Negative news ─────────────────────────────────────────────
    neg = analysis.get("negative_news",[])
    story.append(Paragraph(f"Signaux Négatifs Détectés ({len(neg)})", sH1))
    if neg:
        nh = [["Titre","Source","Nature","Gravité","Mots-clés"]]
        for n in neg[:15]:
            nh.append([
                n.get("titre","")[:65],
                n.get("source","")[:20],
                n.get("nature","")[:25],
                n.get("gravite","").upper(),
                ", ".join(n.get("mots_cles",[])[:3])[:30],
            ])
        t = Table(nh, colWidths=[65*mm,25*mm,30*mm,18*mm,34*mm])
        gmap = {"FAIBLE":GREEN,"MOYEN":YEL,"ELEVE":RED}
        ts2 = TableStyle([
            ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),7),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),("TEXTCOLOR",(0,1),(-1,-1),TEXT),
            ("GRID",(0,0),(-1,-1),0.3,BORD),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ])
        for i,n in enumerate(neg[:15],1):
            c = gmap.get(n.get("gravite","").upper(),MUTED)
            ts2.add("TEXTCOLOR",(3,i),(3,i),c)
            ts2.add("FONTNAME",(3,i),(3,i),"Helvetica-Bold")
        t.setStyle(ts2); story.append(t)
    else:
        story.append(Paragraph("Aucun signal négatif détecté dans les sources consultées.", sBody))
    story.append(Spacer(1,6))

    # ── All articles (human review list) ──────────────────────────
    all_art = analysis.get("all_articles",[])
    story.append(Paragraph(f"Liste complète des sources pour revue humaine ({len(all_art)} articles)", sH1))
    if all_art:
        ah = [["Titre","Domaine","Entité mentionnée"]]
        for a in all_art[:40]:
            ah.append([
                a.get("title","")[:75],
                a.get("domain","")[:30],
                "✓" if a.get("entity_mentioned") else "—"
            ])
        t = Table(ah, colWidths=[110*mm,42*mm,20*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),SURF),("TEXTCOLOR",(0,0),(-1,0),ACC),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),7),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,SURF]),("TEXTCOLOR",(0,1),(-1,-1),TEXT),
            ("GRID",(0,0),(-1,-1),0.3,BORD),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("TEXTCOLOR",(2,1),(-1,-1),GREEN),
        ]))
        story.append(t)
    story.append(Spacer(1,6))

    # ── Factors ───────────────────────────────────────────────────
    fa = analysis.get("facteurs_aggravants",[])
    fat = analysis.get("facteurs_attenuants",[])
    if fa or fat:
        story.append(Paragraph("Facteurs de Risque", sH1))
        c1 = [Paragraph("⚠ Aggravants", S("fa",fontSize=8.5,textColor=RED,fontName="Helvetica-Bold"))]
        for f in fa: c1.append(Paragraph(f"• {f}", sBody))
        c2 = [Paragraph("✓ Atténuants", S("ft",fontSize=8.5,textColor=GREEN,fontName="Helvetica-Bold"))]
        for f in fat: c2.append(Paragraph(f"• {f}", sBody))
        story.append(Table([[c1,c2]], colWidths=[86*mm,86*mm],
            style=TableStyle([
                ("VALIGN",(0,0),(-1,-1),"TOP"),("BACKGROUND",(0,0),(-1,-1),BG),
                ("GRID",(0,0),(-1,-1),0.3,BORD),
                ("TOPPADDING",(0,0),(-1,-1),7),("LEFTPADDING",(0,0),(-1,-1),7),
            ])))
        story.append(Spacer(1,8))

    # ── Footer ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%",thickness=0.5,color=BORD,spaceAfter=4))
    verdict = f"VALIDATION : {human_decision or 'EN ATTENTE'}"
    if analyst_name: verdict += f" par {analyst_name}"
    story.append(Paragraph(
        f"FinShield OSINT v2 · {now_str} · {verdict} · "
        f"CONFIDENTIEL — Usage interne · Résultat informatif, non constitutif d'un avis juridique.",
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
    st.markdown("## Screening OSINT & Due Diligence")
    st.markdown("""<div class='info-box'>
    <b>100% gratuit — aucune clé API requise.</b>
    Interroge 50+ sources : presse, réseaux sociaux (Twitter/LinkedIn/Facebook/Reddit),
    Trustpilot, Infogreffe, BODACC, signal-arnaques.com, justice.fr, AMF, ACPR, OpenSanctions, Reuters, Bloomberg et plus.
    Filtre strict : seuls les signaux directement associés à l entité sont retenus.
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3,1,1])
    with c1:
        entity_input = st.text_input("Entité à analyser", placeholder="Ex: Jean Dupont  ou  Société XYZ SAS", key="entity_osint")
    with c2:
        entity_type = st.selectbox("Type", ["Entreprise","Personne physique","Groupe bancaire","Autre"])
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        launch_btn = st.button("▶ LANCER LE SCREENING", key="btn_osint")

    with st.expander("⚙️ Options"):
        oa, ob = st.columns(2)
        with oa:
            linked_iban  = st.text_input("IBAN lié (optionnel)", key="linked_iban")
            add_to_watch = st.checkbox("Ajouter à la surveillance après analyse")
        with ob:
            groq_key_tab = st.text_input("Clé Groq (optionnel — booste l analyse)", type="password",
                                          placeholder="gsk_... gratuit sur console.groq.com", key="groq_tab")
            st.markdown("""<div style='font-size:0.75rem;color:#5a6a7a;margin-top:12px;margin-bottom:4px;'>
            <b style='color:#c8d6e5;'>🎚️ Niveau de filtrage des résultats</b><br>
            <span style='color:#00ff88;'>0</span> = tout remonter (faux positifs possibles) &nbsp;·&nbsp;
            <span style='color:#ffcc00;'>5</span> = équilibré &nbsp;·&nbsp;
            <span style='color:#ff3366;'>10</span> = extrême (entité dans ±60 chars du mot-clé)
            </div>""", unsafe_allow_html=True)
            filter_level = st.slider("Filtrage", min_value=0, max_value=10, value=3,
                                      key="filter_slider",
                                      help="0 = aucun filtre · 3 = légèrement filtré (défaut) · 7 = strict · 10 = extrême")
            filter_labels = {0:"Aucun filtre",1:"Très léger",2:"Léger",3:"Léger+",
                             4:"Modéré",5:"Modéré+",6:"Modéré++",
                             7:"Strict",8:"Strict+",9:"Très strict",10:"Extrême"}
            fl_color = "#00ff88" if filter_level <= 2 else ("#ffcc00" if filter_level <= 6 else "#ff3366")
            st.markdown(f"<div style='font-size:0.75rem;color:{fl_color};font-family:IBM Plex Mono,monospace;'>"
                        f"Niveau {filter_level} — {filter_labels[filter_level]}</div>", unsafe_allow_html=True)

    # ── Session state for PDF persistence ─────────────────────────
    if "osint_analysis"  not in st.session_state: st.session_state["osint_analysis"]  = None
    if "osint_entity"    not in st.session_state: st.session_state["osint_entity"]    = ""
    if "osint_iban_data" not in st.session_state: st.session_state["osint_iban_data"] = {}
    if "osint_bank_data" not in st.session_state: st.session_state["osint_bank_data"] = {}
    if "osint_os_result" not in st.session_state: st.session_state["osint_os_result"] = {}
    if "osint_has_risk"  not in st.session_state: st.session_state["osint_has_risk"]  = False
    if "osint_results"   not in st.session_state: st.session_state["osint_results"]   = []

    if launch_btn and entity_input.strip():
        prog = st.progress(0)
        stat = st.empty()

        # STEP 1 — OpenSanctions
        stat.markdown("🔎 **[1/5]** Listes sanctions internationales (OpenSanctions)...")
        os_result = check_opensanctions(entity_input.strip())
        prog.progress(5)

        # STEP 2 — Build & run 50+ queries
        queries = build_search_queries(entity_input.strip())
        all_results = []
        stat.markdown(f"🌐 **[2/5]** Interrogation de 50+ sources ({len(queries)} requêtes)...")
        for i, q in enumerate(queries):
            hits = search_web(q, num=5)
            all_results.extend(hits)
            prog.progress(5 + int((i + 1) / len(queries) * 45))
            time.sleep(0.08)

        # Deduplicate by URL
        seen_urls, unique = set(), []
        for r in all_results:
            u = r.get("url","")
            if u and u not in seen_urls:
                seen_urls.add(u)
                unique.append(r)
        all_results = unique

        # STEP 3 — Deep scraping (priority: legal/press/review domains)
        stat.markdown("📄 **[3/5]** Lecture approfondie des pages pertinentes...")
        priority = ["trustpilot","infogreffe","bodacc","signal-arnaques","cybermalveillance",
                    "pappers","societe.com","verif.com","amf-france","acpr","justice.fr",
                    "lemonde","lefigaro","bfmtv","lesechos","latribune","reuters","bloomberg"]
        sorted_r = sorted(all_results,
            key=lambda r: 2 if any(p in r.get("url","") for p in priority) else 0,
            reverse=True)
        scraped, seen_dom = [], set()
        for r in sorted_r[:40]:
            dom = urlparse(r.get("url","")).netloc.replace("www.","")
            if dom and dom not in seen_dom and len(scraped) < 12:
                seen_dom.add(dom)
                txt = scrape_page(r["url"], max_chars=2000)
                if txt and len(txt) > 80:
                    scraped.append(txt)
        prog.progress(62)

        # STEP 4 — IBAN
        iban_data, bank_data = {}, {}
        if linked_iban.strip():
            iban_data = validate_iban(linked_iban.strip())
            if iban_data.get("bank_code"):
                b = db_get_bank_by_code(iban_data["bank_code"])
                if b: bank_data = b

        # STEP 5 — Analysis
        stat.markdown("🔍 **[4/5]** Analyse des signaux (filtre strict entité)...")
        fl = st.session_state.get('filter_slider', 3)
        analysis = analyze_local(entity_input.strip(), all_results, scraped, os_result, filter_level=fl)

        # Optional Groq boost
        gk = groq_key_tab.strip() or (api_key.strip() if api_key else "")
        if gk:
            stat.markdown("⚡ **[5/5]** Enrichissement LLM (Groq)...")
            try:
                gr = analyze_with_groq(entity_input.strip(), all_results[:30], scraped[:4], gk)
                if gr and gr.get("score_risque",0) >= analysis.get("score_risque",0):
                    gr["scores_categories"] = analysis.get("scores_categories",{})
                    gr["nb_sources_filtrees"] = analysis.get("nb_sources_filtrees",0)
                    gr["nb_sources_total"]    = analysis.get("nb_sources_total",0)
                    gr["_moteur_label"] = "⚡ Groq llama-3.1 + filtrage strict"
                    analysis = gr
            except: pass
        prog.progress(90)

        # Save
        stat.markdown("💾 **[5/5]** Enregistrement...")
        db_save_report(entity_input.strip(), entity_type,
                       linked_iban or "",
                       analysis.get("score_risque",0),
                       analysis.get("niveau_risque",""),
                       analysis.get("recommandation",""),
                       analysis.get("resume_executif",""),
                       json.dumps(analysis, ensure_ascii=False))
        if add_to_watch:
            db_add_watchlist(entity_input.strip(), entity_type,
                             "Screening auto", analysis.get("niveau_risque",""), "Auto")

        # Persist in session
        score  = analysis.get("score_risque", 0)
        niveau = analysis.get("niveau_risque","FAIBLE")
        neg_n  = analysis.get("negative_news",[])
        has_risk = (
            score >= 20
            or os_result.get("found")
            or analysis.get("sanctions",{}).get("trouve")
            or analysis.get("litiges_judiciaires",{}).get("trouve")
            or len(neg_n) >= 2
            or niveau in ("ELEVE","CRITIQUE")
        )
        st.session_state["osint_analysis"]  = analysis
        st.session_state["osint_entity"]    = entity_input.strip()
        st.session_state["osint_iban_data"] = iban_data
        st.session_state["osint_bank_data"] = bank_data
        st.session_state["osint_os_result"] = os_result
        st.session_state["osint_has_risk"]  = has_risk
        st.session_state["osint_results"]   = all_results

        prog.progress(100)
        stat.empty()

    # ── DISPLAY (from session state, persists after button click) ──
    analysis  = st.session_state.get("osint_analysis")
    entity_d  = st.session_state.get("osint_entity","")
    iban_data = st.session_state.get("osint_iban_data",{})
    bank_data = st.session_state.get("osint_bank_data",{})
    os_result = st.session_state.get("osint_os_result",{})
    has_risk  = st.session_state.get("osint_has_risk", False)
    all_results = st.session_state.get("osint_results",[])

    if analysis:
        st.markdown("---")
        score   = analysis.get("score_risque",0)
        niveau  = analysis.get("niveau_risque","FAIBLE")
        reco    = analysis.get("recommandation","ACCEPTER")
        neg_n   = analysis.get("negative_news",[])
        nb_filt = analysis.get("nb_sources_filtrees",0)
        nb_tot  = analysis.get("nb_sources_total", len(all_results))
        moteur  = analysis.get("_moteur_label", analysis.get("moteur","🔍 local strict v3"))
        sc_cat  = analysis.get("scores_categories",{})
        cat_str = "  ·  ".join(f"{k}:{v}" for k,v in sc_cat.items() if v > 0)

        st.markdown(f"""<div style='background:rgba(0,212,255,0.04);border:1px solid #1e2535;
        border-radius:4px;padding:7px 14px;margin:4px 0 10px;font-size:0.73rem;'>
        <span style='color:#5a6a7a;'>Moteur :</span>
        <b style='color:#00d4ff;font-family:IBM Plex Mono,monospace;'>{moteur}</b>
        &nbsp;·&nbsp;<span style='color:#5a6a7a;'>{nb_tot} résultats bruts
        → <b style='color:#c8d6e5;'>{nb_filt} mentionnant directement {entity_d}</b></span>
        {"  ·  <span style='color:#5a6a7a;'>Signaux : "+cat_str+"</span>" if cat_str else ""}
        </div>""", unsafe_allow_html=True)

        # ── RAS ────────────────────────────────────────────────────
        if not has_risk:
            st.markdown(f"""
            <div style='background:rgba(0,255,136,0.07);border:2px solid #00ff88;border-radius:8px;
            padding:28px;margin:12px 0;text-align:center;'>
              <div style='font-size:2.5rem;'>✅</div>
              <div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;color:#00ff88;margin:10px 0;'>
                RAS — AUCUN RISQUE DÉTECTÉ
              </div>
              <div style='color:#c8d6e5;font-size:0.95rem;'><b>{entity_d}</b></div>
              <div style='color:#5a6a7a;font-size:0.8rem;margin-top:10px;'>
                Score : {score}/100 · {nb_tot} sources interrogées · {nb_filt} mentions directes · Aucun signal négatif confirmé
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"<div class='ok-box'>{analysis.get('resume_executif','')}</div>", unsafe_allow_html=True)

        # ── RISK DETECTED ─────────────────────────────────────────
        else:
            bmap  = {"FAIBLE":"badge-low","MODERE":"badge-medium","ELEVE":"badge-high","CRITIQUE":"badge-high"}.get(niveau,"badge-medium")
            rc_c  = {"ACCEPTER":"#00ff88","VIGILANCE_RENFORCEE":"#ffcc00","REFUSER":"#ff3366"}.get(reco,"#5a6a7a")
            sc_c  = "#ff3366" if os_result.get("found") or analysis.get("sanctions",{}).get("trouve") else "#00ff88"

            mc1,mc2,mc3,mc4 = st.columns(4)
            with mc1:
                st.markdown(f"<div class='metric-card'><div class='label'>Score</div><div class='value'>{score}<span style='font-size:0.8rem;color:#5a6a7a;'>/100</span></div></div>", unsafe_allow_html=True)
            with mc2:
                st.markdown(f"<div class='metric-card'><div class='label'>Niveau</div><div class='value' style='font-size:0.95rem;margin-top:8px;'><span class='{bmap}'>{niveau}</span></div></div>", unsafe_allow_html=True)
            with mc3:
                sc_t = f"🔴 {os_result.get('count',0)} hit(s) OS" if os_result.get("found") else ("⚠ Indicateurs" if analysis.get("sanctions",{}).get("trouve") else "✅ Aucune sanction")
                st.markdown(f"<div class='metric-card'><div class='label'>Sanctions</div><div class='value' style='font-size:0.8rem;color:{sc_c};'>{sc_t}</div></div>", unsafe_allow_html=True)
            with mc4:
                st.markdown(f"<div class='metric-card'><div class='label'>Recommandation</div><div class='value' style='font-size:0.72rem;color:{rc_c};'>{reco}</div></div>", unsafe_allow_html=True)

            st.markdown(f"<div class='warn-box'><b>⚠ Résumé :</b> {analysis.get('resume_executif','')}</div>", unsafe_allow_html=True)

            dl, dr = st.columns(2)
            with dl:
                st.markdown("#### 📰 Signaux négatifs (entité confirmée)")
                if neg_n:
                    for n in neg_n[:8]:
                        g   = n.get("gravite","").lower()
                        cls = {"faible":"info-box","moyen":"warn-box","eleve":"danger-box"}.get(g,"warn-box")
                        url = n.get("url","")
                        lnk = f" <a href='{url}' target='_blank' style='color:#00d4ff;font-size:0.72rem;'>→ lire</a>" if url else ""
                        kws = ", ".join(n.get("mots_cles",[])[:3])
                        st.markdown(f"""<div class='{cls}'>
                        <b>{n.get('titre','')[:90]}</b>{lnk}<br>
                        <small>{n.get('source','')} · {n.get('nature','')} · <span style='color:#ffcc00;'>{kws}</span></small>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='info-box'>Signaux faibles — vérification humaine recommandée.</div>", unsafe_allow_html=True)

                lit = analysis.get("litiges_judiciaires",{})
                st.markdown("#### ⚖️ Litiges")
                if lit.get("trouve"):
                    st.markdown(f"<div class='danger-box'>⚠️ {lit.get('details','')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>Aucun litige identifié</div>", unsafe_allow_html=True)

            with dr:
                st.markdown("#### 🚨 Sanctions")
                if os_result.get("found"):
                    st.markdown(f"<div class='danger-box'>🔴 {os_result['count']} entrée(s) OpenSanctions</div>", unsafe_allow_html=True)
                    for r in os_result.get("results",[])[:3]:
                        st.markdown(f"<div class='result-row'><b>{r.get('caption','')}</b> · {', '.join(r.get('datasets',[]))}</div>", unsafe_allow_html=True)
                elif analysis.get("sanctions",{}).get("trouve"):
                    st.markdown(f"<div class='warn-box'>⚠️ {analysis['sanctions']['details']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>Absent des listes de sanctions</div>", unsafe_allow_html=True)

                pep = analysis.get("pep_exposure",{})
                st.markdown("#### 👤 PEP & Réputation")
                if pep.get("trouve"):
                    st.markdown(f"<div class='warn-box'>{pep.get('details','')}</div>", unsafe_allow_html=True)
                rep = analysis.get("reputation_notations","")
                if rep:
                    c = "warn-box" if "dégradée" in rep else "ok-box"
                    st.markdown(f"<div class='{c}'>⭐ {rep}</div>", unsafe_allow_html=True)

            fa1, fa2 = st.columns(2)
            with fa1:
                for f in analysis.get("facteurs_aggravants",[]):
                    st.markdown(f"<div class='danger-box'>🔺 {f}</div>", unsafe_allow_html=True)
            with fa2:
                for f in analysis.get("facteurs_attenuants",[]):
                    st.markdown(f"<div class='ok-box'>🔻 {f}</div>", unsafe_allow_html=True)

            with st.expander(f"📋 Sources brutes ({len(all_results)} résultats · {nb_filt} filtrés)"):
                for r in all_results[:50]:
                    dom  = urlparse(r.get("url","")).netloc
                    txt  = (r.get("title","") + " " + r.get("snippet","")).lower()
                    risk_kw = any(kw in txt for cat in ["fraud","sanctions","judicial"]
                                  for kw in RISK_KEYWORDS.get(cat,{}).keys())
                    bdr = "border-left:3px solid #ff3366;" if risk_kw else ""
                    st.markdown(f"""<div class='result-row' style='{bdr}'>
                    <a href='{r.get("url","")}' target='_blank' style='color:#00d4ff;text-decoration:none;'><b>{r.get("title","")[:100]}</b></a><br>
                    <small style='color:#5a6a7a;'>{dom}</small>
                    <small> · {r.get("snippet","")[:130]}</small>
                    </div>""", unsafe_allow_html=True)

        # ── ALL ARTICLES FOR HUMAN REVIEW ────────────────────────
        st.markdown("---")
        all_art = analysis.get("all_articles", [])
        with st.expander(f"📋 Liste complète pour revue humaine — {len(all_art)} articles collectés ({nb_filt} mentionnant directement l entité)", expanded=False):
            st.markdown("""<div class='info-box'>
            <b>Revue humaine requise.</b> Consultez chaque article, identifiez les informations négatives,
            puis utilisez la zone de validation ci-dessous pour documenter votre décision.
            La colonne <b>Entité ✓</b> indique si le nom recherché apparaît dans l article.
            </div>""", unsafe_allow_html=True)
            # Split into two lists: entity-mentioned vs generic
            art_entity  = [a for a in all_art if a.get("entity_mentioned")]
            art_generic = [a for a in all_art if not a.get("entity_mentioned")]

            st.markdown(f"**Articles mentionnant directement {entity_d} ({len(art_entity)})**")
            for a in art_entity:
                url = a.get("url","")
                link = f"<a href='{url}' target='_blank' style='color:#00d4ff;'>→ lire</a>" if url else ""
                st.markdown(f"""<div class='result-row' style='border-left:3px solid #00d4ff;'>
                <b>{a.get("title","")[:100]}</b> {link}<br>
                <small style='color:#5a6a7a;'>{a.get("domain","")} · {a.get("snippet","")[:120]}</small>
                </div>""", unsafe_allow_html=True)

            if art_generic:
                st.markdown(f"**Autres articles (sans mention directe — {len(art_generic)})**")
                for a in art_generic[:20]:
                    url = a.get("url","")
                    link = f"<a href='{url}' target='_blank' style='color:#5a6a7a;'>→ lire</a>" if url else ""
                    st.markdown(f"""<div class='result-row'>
                    <span style='color:#5a6a7a;'>{a.get("title","")[:100]}</span> {link}
                    </div>""", unsafe_allow_html=True)

        # ── HUMAN VALIDATION SECTION ──────────────────────────────
        st.markdown("---")
        st.markdown("""<div class='section-title'>✍️ VALIDATION HUMAINE</div>""", unsafe_allow_html=True)
        st.markdown("""<div class='info-box'>
        Après avoir examiné les articles ci-dessus, renseignez votre décision.
        Le rapport PDF sera daté et horodaté avec votre validation.
        </div>""", unsafe_allow_html=True)

        vh1, vh2 = st.columns([1, 2])
        with vh1:
            analyst_name = st.text_input("👤 Nom de l analyste", placeholder="ex: Marie Dupont",
                                          key="analyst_name")
            human_decision = st.radio(
                "Décision après analyse",
                ["En attente", "✅ RAS — Rien à signaler", "⚠️ Informations négatives confirmées"],
                key="human_decision",
                help="RAS : aucun risque après vérification humaine | Négatif : les signaux sont avérés"
            )
        with vh2:
            human_comment = st.text_area(
                "Commentaire de l analyste",
                placeholder="Ex: RAS apres verification (homonyme). Ou: Condamnation confirmee tribunal Paris 2022, article consulte.",
                height=120,
                key="human_comment"
            )

        # Map radio to decision code
        decision_map = {
            "En attente": None,
            "✅ RAS — Rien à signaler": "RAS",
            "⚠️ Informations négatives confirmées": "RISQUE_CONFIRME"
        }
        h_decision = decision_map.get(human_decision, None)

        # PDF Generation
        st.markdown("")
        pdf_c1, pdf_c2 = st.columns([1, 2])
        with pdf_c1:
            if h_decision is None:
                btn_lbl = "⬇ GÉNÉRER RAPPORT (en attente)"
            elif h_decision == "RAS":
                btn_lbl = "⬇ GÉNÉRER RAPPORT PDF — RAS ✅"
            else:
                btn_lbl = "⬇ GÉNÉRER RAPPORT PDF — RISQUE ⚠️"

            if st.button(btn_lbl, key="gen_pdf_main"):
                with st.spinner("Génération du rapport PDF..."):
                    try:
                        pdf_bytes = generate_pdf_report(
                            entity_d,
                            iban_data,
                            bank_data,
                            os_result,
                            analysis,
                            human_decision=h_decision,
                            human_comment=human_comment,
                            analyst_name=analyst_name
                        )
                        suffix = "RAS" if h_decision == "RAS" else ("RISQUE" if h_decision else "ATTENTE")
                        fname  = f"FinShield_{entity_d.replace(' ','_')}_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        st.download_button(
                            label="📥 Télécharger le rapport PDF",
                            data=pdf_bytes,
                            file_name=fname,
                            mime="application/pdf",
                            key="dl_pdf_main"
                        )
                        if h_decision == "RAS":
                            st.markdown("<div class='ok-box'>✅ Rapport RAS généré et daté.</div>", unsafe_allow_html=True)
                        elif h_decision == "RISQUE_CONFIRME":
                            st.markdown("<div class='danger-box'>⚠️ Rapport RISQUE CONFIRMÉ généré.</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='warn-box'>⏳ Rapport généré — validation en attente.</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erreur PDF : {e}")
                        import traceback
                        st.code(traceback.format_exc())

        with pdf_c2:
            decision_display = {
                None:              ("⏳ En attente","#5a6a7a"),
                "RAS":             ("✅ RAS — Rien à signaler","#00ff88"),
                "RISQUE_CONFIRME": ("⚠️ Risque confirmé","#ff3366"),
            }
            d_label, d_color = decision_display.get(h_decision, ("—","#5a6a7a"))
            st.markdown(f"""<div class='metric-card'>
            <div class='label'>Contenu du rapport</div>
            <div class='sub' style='margin-top:6px;line-height:1.9;'>
            Score {score}/100 · {niveau} · {reco}<br>
            {len(neg_n)} signal(aux) · {nb_tot} sources · {nb_filt} mentions directes<br>
            IBAN {" ✓" if iban_data.get("raw") else "—"} · {len(all_art)} articles listés<br>
            <b style='color:{d_color};'>{d_label}</b>
            {"<br><span style='color:#5a6a7a;font-size:0.78rem;'>" + (analyst_name or "Analyste non renseigné") + "</span>" if h_decision else ""}
            </div></div>""", unsafe_allow_html=True)


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
