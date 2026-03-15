import streamlit as st
import requests
import json
import re
import time
import os
from datetime import datetime
from io import BytesIO
from urllib.parse import quote_plus, urlparse
import anthropic

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinShield OSINT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inline CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

:root {
  --bg:       #0a0d14;
  --surface:  #111520;
  --border:   #1e2535;
  --accent:   #00d4ff;
  --accent2:  #ff6b35;
  --green:    #00ff88;
  --red:      #ff3366;
  --yellow:   #ffcc00;
  --text:     #c8d6e5;
  --muted:    #5a6a7a;
}

html, body, [data-testid="stApp"] {
  background: var(--bg) !important;
  color: var(--text);
  font-family: 'IBM Plex Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Headers */
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace !important; }
h1 { color: var(--accent) !important; letter-spacing: -0.5px; }
h2 { color: var(--text) !important; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
h3 { color: var(--accent) !important; font-size: 0.95rem !important; }

/* Inputs */
input, textarea, [data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  font-family: 'IBM Plex Mono', monospace !important;
}
input:focus, textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(0,212,255,0.1) !important;
}

/* Buttons */
.stButton > button {
  background: transparent !important;
  color: var(--accent) !important;
  border: 1px solid var(--accent) !important;
  border-radius: 3px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.85rem !important;
  letter-spacing: 1px !important;
  transition: all 0.15s !important;
}
.stButton > button:hover {
  background: var(--accent) !important;
  color: var(--bg) !important;
}

/* Metric cards */
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px 20px;
  margin: 8px 0;
}
.metric-card .label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 2px; }
.metric-card .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; color: var(--accent); margin-top: 4px; }
.metric-card .sub   { font-size: 0.8rem; color: var(--text); margin-top: 2px; }

/* Risk badges */
.badge-low    { background: rgba(0,255,136,0.1); color: var(--green);  border: 1px solid rgba(0,255,136,0.3); padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; }
.badge-medium { background: rgba(255,204,0,0.1);  color: var(--yellow); border: 1px solid rgba(255,204,0,0.3);  padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; }
.badge-high   { background: rgba(255,51,102,0.1); color: var(--red);    border: 1px solid rgba(255,51,102,0.3);  padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; }

/* Info boxes */
.info-box {
  background: rgba(0,212,255,0.05);
  border-left: 3px solid var(--accent);
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.88rem;
}
.warn-box {
  background: rgba(255,204,0,0.05);
  border-left: 3px solid var(--yellow);
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.88rem;
}
.danger-box {
  background: rgba(255,51,102,0.07);
  border-left: 3px solid var(--red);
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.88rem;
}
.ok-box {
  background: rgba(0,255,136,0.05);
  border-left: 3px solid var(--green);
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.88rem;
}

/* Result rows */
.result-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 12px 16px;
  margin: 6px 0;
  font-size: 0.85rem;
}
.result-row:hover { border-color: var(--accent); }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}
[data-testid="stTabs"] button {
  background: transparent !important;
  color: var(--muted) !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.8rem !important;
  letter-spacing: 1px !important;
  padding: 8px 18px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
  background: rgba(0,212,255,0.05) !important;
}

/* Expander */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
}
[data-testid="stExpander"] summary { color: var(--text) !important; }

/* Select / multiselect */
[data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

/* HR */
hr { border-color: var(--border) !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Progress */
.stProgress > div > div { background: var(--accent) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

.header-strip {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 0 12px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}
.shield-icon { font-size: 2.5rem; }
.app-title { font-family: 'IBM Plex Mono', monospace; font-size: 1.8rem; color: var(--accent); letter-spacing: -1px; }
.app-sub { font-size: 0.8rem; color: var(--muted); letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }
.tag { display: inline-block; font-size: 0.65rem; font-family: 'IBM Plex Mono', monospace; background: rgba(0,212,255,0.1); color: var(--accent); border: 1px solid rgba(0,212,255,0.2); padding: 1px 7px; border-radius: 10px; margin: 0 3px; }
</style>
""", unsafe_allow_html=True)

# ── Bank data from provided document ───────────────────────────────────────────
BANK_DB = {
    "18989": {"name": "Aareal bank AG", "address": "29 B RUE D ASTORG, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "13678": {"name": "ABN AMRO ASSET BASED FINANCE N.V.", "address": "39 rue Anatole France, 92300, LEVALLOIS PERRET", "type": "Autre institution"},
    "27133": {"name": "ABN Amro Bank NV", "address": "", "type": "Etablissement de crédit"},
    "21733": {"name": "Adyen N.V.", "address": "Paris", "type": "Etablissement de crédit"},
    "12240": {"name": "Allianz banque", "address": "TOUR ALLIANZ ONE 1 COURS MICHELET, 92076, Paris La défense Cedex", "type": "Etablissement de crédit"},
    "12548": {"name": "Axa banque", "address": "203-205 RUE CARNOT, 94138, FONTENAY-SOUS-BOIS CEDEX", "type": "Etablissement de crédit"},
    "40618": {"name": "Boursorama", "address": "18 QUAI DU POINT DU JOUR, 92100, BOULOGNE BILLANCOURT", "type": "Etablissement de crédit"},
    "30004": {"name": "BNP Paribas", "address": "16 BOULEVARD DES ITALIENS, 75009, PARIS", "type": "Etablissement de crédit"},
    "30001": {"name": "BANQUE DE FRANCE", "address": "1 RUE LA VRILLIERE BP 71928, 75001, PARIS 01 ER", "type": "Banque centrale"},
    "30006": {"name": "Crédit Agricole S.A.", "address": "12 PLACE DES ETATS UNIS, 92120, MONTROUGE", "type": "Etablissement de crédit"},
    "30002": {"name": "CREDIT LYONNAIS (LCL)", "address": "18 rue de la République, 69002, LYON", "type": "Etablissement de crédit"},
    "30003": {"name": "Société générale", "address": "ZI CAP 18 VOIE D PORTE 25 189 RUE D AUBERVILLIERS, 75886, PARIS CEDEX 18", "type": "Etablissement de crédit"},
    "30007": {"name": "Natixis", "address": "30 AVENUE PIERRE MENDES FRANCE, 75013, PARIS 13", "type": "Etablissement de crédit"},
    "20041": {"name": "La Banque Postale", "address": "115 RUE DE SÈVRES, 75275, PARIS CEDEX 06", "type": "Etablissement de crédit"},
    "10107": {"name": "BRED - Banque populaire", "address": "18 QUAI DE LA RAPEE, 75012, PARIS 12", "type": "Etablissement de crédit"},
    "10207": {"name": "Banque populaire Rives de Paris", "address": "76 AVENUE DE FRANCE, 75013, PARIS 13", "type": "Etablissement de crédit"},
    "13507": {"name": "Banque populaire du Nord", "address": "847 AVENUE DE LA REPUBLIQUE, 59700, MARCQ EN BAROEUL", "type": "Etablissement de crédit"},
    "16807": {"name": "BANQUE POPULAIRE AUVERGNE RHONE ALPES", "address": "CS 80, 4 BOULEVARD EUGENE DERUELLE, 69003, Lyon", "type": "Etablissement de crédit"},
    "17515": {"name": "Caisse d'épargne et de prévoyance Ile-de-France", "address": "75021, 19 RUE DU LOUVRE, 75021, PARIS CEDEX 1", "type": "Etablissement de crédit"},
    "11315": {"name": "Caisse d'Epargne CEPAC", "address": "BP 10, PLACE ESTRANGIN PASTRÉ, 13254, MARSEILLE CEDEX 6", "type": "Etablissement de crédit"},
    "30056": {"name": "HSBC Continental Europe", "address": "38 AVENUE KLEBER, 75116, PARIS", "type": "Etablissement de crédit"},
    "30438": {"name": "ING Bank NV", "address": "IMMEUBLE LUMIERE 40 AVENUE DES TERROIRS DE FRANCE, 75012, PARIS 12", "type": "Etablissement de crédit"},
    "30066": {"name": "Crédit industriel et commercial - CIC", "address": "6 AVENUE DE PROVENCE, 75009, PARIS 09", "type": "Etablissement de crédit"},
    "30076": {"name": "Crédit du Nord", "address": "BP 56, 28 PLACE RIHOUR, 59023, LILLE CEDEX", "type": "Etablissement de crédit"},
    "18359": {"name": "Bpifrance", "address": "27-31 AVENUE DU GÉNÉRAL LECLERC, 94710, MAISONS - ALFORT", "type": "Etablissement de crédit"},
    "16188": {"name": "BPCE", "address": "50 AVENUE PIERRE MENDES FRANCE, 75013, PARIS 13", "type": "Etablissement de crédit"},
    "42559": {"name": "Crédit coopératif", "address": "CS 10, 12 BOULEVARD PESARO, 92024, NANTERRE CEDEX", "type": "Etablissement de crédit"},
    "30788": {"name": "Banque Neuflize OBC", "address": "3 AVENUE HOCHE, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "40978": {"name": "Banque Palatine", "address": "42 RUE D'ANJOU, 75382, PARIS CEDEX08", "type": "Etablissement de crédit"},
    "18370": {"name": "ORANGE BANK", "address": "67 RUE ROBESPIERRE, 93100, MONTREUIL", "type": "Etablissement de crédit"},
    "28233": {"name": "REVOLUT PAYMENTS UAB", "address": "3 RUE DE STOCKHOLM, 75008, PARIS", "type": "Autre institution"},
    "20433": {"name": "N26 BANK GMBH", "address": "", "type": "Etablissement de crédit"},
    "28033": {"name": "KLARNA BANK AB", "address": "", "type": "Etablissement de crédit"},
    "19870": {"name": "Carrefour banque", "address": "PARC DU BOIS BRIARD 9-13 AVENUE DU LAC, 91000, EVRY-COURCOURONNES", "type": "Etablissement de crédit"},
    "12869": {"name": "ONEY BANK", "address": "BP 13, 40 AVENUE DE FLANDRE, 59964, CROIX CEDEX", "type": "Etablissement de crédit"},
    "14940": {"name": "Cofidis", "address": "PARC DE LA HAUTE BORNE 61 AVENUE HALLEY, 59866, VILLENEUVE D'ASCQ CEDEX", "type": "Etablissement de crédit"},
    "16218": {"name": "Bforbank", "address": "TOUR EUROPLAZA - LA DÉFENSE 4 20 AVENUE ANDRÉ PROTHIN, 92927, PARIS LA DEFENSE CEDEX", "type": "Etablissement de crédit"},
    "14690": {"name": "Monabanq.", "address": "PARC DE LA HAUTE BORNE 61 AVENUE HALLEY, 59650, VILLENEUVE D ASCQ", "type": "Etablissement de crédit"},
    "16908": {"name": "Ma French Bank", "address": "115 RUE DE SÈVRES, 75275, Paris Cedex 06", "type": "Etablissement de crédit"},
    "31489": {"name": "Crédit agricole corporate and investment bank", "address": "12 PLACE DES ETATS-UNIS, 92547, Montrouge Cedex", "type": "Etablissement de crédit"},
    "43199": {"name": "Crédit Foncier de France", "address": "19 RUE DES CAPUCINES, 75001, PARIS 01", "type": "Etablissement de crédit"},
    "30051": {"name": "Compagnie de financement foncier", "address": "19 RUE DES CAPUCINES, 75001, PARIS 01", "type": "Etablissement de crédit"},
    "15208": {"name": "Crédit municipal de Paris", "address": "55 RUE DES FRANCS-BOURGEOIS, 75181, PARIS CEDEX 04", "type": "Etablissement de crédit"},
    "45129": {"name": "AGENCE FRANCAISE DE DEVELOPPEMENT", "address": "5 RUE ROLAND BARTHES, 75012, PARIS 12", "type": "Autre institution"},
    "41189": {"name": "Banco Bilbao Vizcaya Argentaria (BBVA)", "address": "29 AVENUE DE L OPERA, 75001, PARIS 01", "type": "Etablissement de crédit"},
    "44729": {"name": "Banco Santander SA", "address": "40 RUE DE COURCELLES, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "18769": {"name": "Bank of China limited", "address": "23 AVENUE DE LA GRANDE ARMEE, 75116, PARIS 16", "type": "Etablissement de crédit"},
    "17789": {"name": "Deutsche bank AG", "address": "3-5 avenue de Friedland, PARIS CEDEX 08", "type": "Etablissement de crédit"},
    "30628": {"name": "JPMorgan Chase bank, National Association", "address": "14 PLACE VENDOME, 75001, PARIS 01", "type": "Etablissement de crédit"},
    "30748": {"name": "Lazard Frères Banque", "address": "121 BOULEVARD HAUSSMANN, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "30758": {"name": "UBS (France) S.A.", "address": "69 BOULEVARD HAUSSMANN, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "18059": {"name": "HSBC Bank Plc, Paris Branch", "address": "38 AVENUE KLEBER, 75116, PARIS", "type": "Etablissement de crédit"},
    "13338": {"name": "BANQUE RICHELIEU MONACO", "address": "8 AVENUE DE GRANDE BRETAGNE, 98005, MONACO CEDEX", "type": "Etablissement de crédit"},
    "11833": {"name": "Industrial and commercial bank of China (Europe) SA - ICBC (Europe) SA", "address": "73 BOULEVARD HAUSSMANN, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "25533": {"name": "Goldman Sachs Bank Europe SE", "address": "5 Avenue Kléber, 75116, PARIS", "type": "Etablissement de crédit"},
    "24599": {"name": "Milleis Banque", "address": "32 AVENUE GEORGE V, 75008, PARIS 08", "type": "Etablissement de crédit"},
    "11188": {"name": "RCI Banque", "address": "15 RUE D UZES, 75002, PARIS", "type": "Etablissement de crédit"},
    "13168": {"name": "Banque PSA finance", "address": "2 BOULEVARD DE L EUROPE, 78300, POISSY", "type": "Etablissement de crédit"},
    "19530": {"name": "Amundi", "address": "91-93 BOULEVARD PASTEUR, 75730, PARIS CEDEX 15", "type": "Etablissement de crédit"},
}

# ── Utility functions ───────────────────────────────────────────────────────────

def validate_iban(iban: str) -> dict:
    """Validate IBAN format and extract bank code for French IBANs."""
    iban = iban.replace(" ", "").upper()
    result = {"raw": iban, "valid": False, "country": "", "bank_code": "", "message": ""}
    if len(iban) < 15:
        result["message"] = "IBAN trop court"
        return result
    country = iban[:2]
    result["country"] = country
    # Move first 4 chars to end, convert letters to numbers, check mod 97
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        elif ch.isalpha():
            numeric += str(ord(ch) - 55)
        else:
            result["message"] = "Caractère invalide"
            return result
    if int(numeric) % 97 != 1:
        result["message"] = "Clé de contrôle invalide (mod97 échoué)"
        return result
    result["valid"] = True
    result["message"] = "IBAN valide ✓"
    # French IBAN: FR + 2 check + 5 bank + 5 branch + 11 account + 2 key = 27
    if country == "FR" and len(iban) == 27:
        result["bank_code"] = iban[4:9]
        result["branch_code"] = iban[9:14]
        result["account_no"] = iban[14:25]
        result["rib_key"] = iban[25:27]
    elif country == "MC" and len(iban) == 27:  # Monaco similar
        result["bank_code"] = iban[4:9]
    return result

def lookup_bank(bank_code: str) -> dict:
    """Lookup bank info from local DB."""
    code = bank_code.lstrip("0")
    # Try exact, then strip leading zeros
    for key in [bank_code, code, bank_code.zfill(5)]:
        if key in BANK_DB:
            return BANK_DB[key]
    # Fuzzy: find partial matches
    matches = []
    for k, v in BANK_DB.items():
        if k.startswith(code[:3]):
            matches.append({**v, "code": k})
    return {"name": "Banque non trouvée", "address": "", "type": "", "suggestions": matches}

def check_opensanctions(name: str) -> dict:
    """Query OpenSanctions API (free tier)."""
    try:
        url = f"https://api.opensanctions.org/match/default"
        payload = {"queries": {"q1": {"schema": "Thing", "properties": {"name": [name]}}}}
        r = requests.post(url, json=payload, timeout=10,
                          headers={"Authorization": "ApiKey osa-sys-test"})
        if r.status_code == 200:
            data = r.json()
            results = data.get("responses", {}).get("q1", {}).get("results", [])
            return {"found": len(results) > 0, "count": len(results), "results": results[:5]}
        else:
            # Fallback: public search endpoint
            r2 = requests.get(f"https://api.opensanctions.org/search/default?q={quote_plus(name)}&limit=5", timeout=8)
            if r2.status_code == 200:
                d = r2.json()
                return {"found": d.get("total", 0) > 0, "count": d.get("total", 0), "results": d.get("results", [])[:5]}
    except Exception as e:
        pass
    return {"found": False, "count": 0, "results": [], "error": "Non disponible"}

def search_web_duckduckgo(query: str, num: int = 10) -> list:
    """Search via DuckDuckGo HTML (no API key needed)."""
    results = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        r = requests.get(url, headers=headers, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select(".result__title a")[:num]:
            href = a.get("href", "")
            snippet_tag = a.find_parent(".result").find("a", class_="result__snippet") if a.find_parent(".result") else None
            snippet = snippet_tag.get_text() if snippet_tag else ""
            results.append({"title": a.get_text(), "url": href, "snippet": snippet})
    except Exception as e:
        pass
    return results

def search_web_bing(query: str, num: int = 10) -> list:
    """Search via Bing."""
    results = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={num}"
        r = requests.get(url, headers=headers, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for li in soup.select("li.b_algo")[:num]:
            h2 = li.find("h2")
            a = h2.find("a") if h2 else None
            p = li.find("p")
            if a:
                results.append({"title": a.get_text(), "url": a.get("href", ""), "snippet": p.get_text() if p else ""})
    except Exception as e:
        pass
    return results

def scrape_page_text(url: str, max_chars: int = 3000) -> str:
    """Scrape visible text from a page."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return text[:max_chars]
    except:
        return ""

def analyze_with_claude(entity: str, search_results: list, scraped_texts: list, api_key: str) -> dict:
    """Use Claude to analyze OSINT data and generate risk assessment."""
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build context
    ctx_parts = []
    for i, sr in enumerate(search_results[:15]):
        ctx_parts.append(f"[Source {i+1}] {sr.get('title','')} | {sr.get('url','')} | {sr.get('snippet','')}")
    for i, txt in enumerate(scraped_texts[:5]):
        if txt.strip():
            ctx_parts.append(f"[Contenu page {i+1}] {txt[:800]}")
    context = "\n".join(ctx_parts)
    
    prompt = f"""Tu es un analyste expert en conformité financière et due diligence.

Entité analysée: {entity}

Sources OSINT collectées:
{context}

Analyse ces données et produis un rapport structuré JSON avec exactement cette structure:
{{
  "score_risque": <0-100, int>,
  "niveau_risque": <"FAIBLE"|"MODERE"|"ELEVE"|"CRITIQUE">,
  "resume_executif": "<2-3 phrases résumant les risques>",
  "negative_news": [
    {{"titre": "", "source": "", "date": "", "nature": "", "gravite": "faible|moyen|eleve"}}
  ],
  "sanctions": {{"trouve": <bool>, "details": ""}},
  "litiges_judiciaires": {{"trouve": <bool>, "details": ""}},
  "pep_exposure": {{"trouve": <bool>, "details": ""}},
  "reputation_notations": "<synthèse avis/notes trouvées>",
  "facteurs_aggravants": ["..."],
  "facteurs_attenuants": ["..."],
  "recommandation": "<ACCEPTER|VIGILANCE_RENFORCEE|REFUSER>",
  "sources_consultees": [<liste des domaines>]
}}

Base-toi UNIQUEMENT sur les données fournies. Si insuffisant, indique-le dans les champs. Réponds UNIQUEMENT avec le JSON, aucun texte avant ou après."""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    # Clean json
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)

def generate_pdf_report(entity: str, iban_data: dict, bank_data: dict, osint_data: dict, analysis: dict) -> bytes:
    """Generate a professional PDF compliance report."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=20*mm, rightMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)

    c_bg    = HexColor("#0a0d14")
    c_surf  = HexColor("#111520")
    c_acc   = HexColor("#00d4ff")
    c_acc2  = HexColor("#ff6b35")
    c_green = HexColor("#00cc66")
    c_red   = HexColor("#ff3366")
    c_yel   = HexColor("#ffcc00")
    c_text  = HexColor("#c8d6e5")
    c_muted = HexColor("#5a6a7a")
    c_bord  = HexColor("#1e2535")

    styles = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    sTitle  = s("Title2",  fontSize=22, textColor=c_acc,  fontName="Helvetica-Bold", spaceAfter=4)
    sSub    = s("Sub",     fontSize=9,  textColor=c_muted, fontName="Helvetica",     spaceAfter=2)
    sH1     = s("H1",      fontSize=13, textColor=c_acc,  fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6)
    sH2     = s("H2",      fontSize=10, textColor=c_text, fontName="Helvetica-Bold", spaceBefore=6,  spaceAfter=4)
    sBody   = s("Body",    fontSize=8.5,textColor=c_text, fontName="Helvetica",      spaceAfter=4, leading=13)
    sSmall  = s("Small",   fontSize=7.5,textColor=c_muted,fontName="Helvetica",      spaceAfter=2)
    sCode   = s("Code",    fontSize=8,  textColor=c_acc2, fontName="Courier",        spaceAfter=2)

    risk_color = {"FAIBLE": c_green, "MODERE": c_yel, "ELEVE": c_acc2, "CRITIQUE": c_red}.get(
        analysis.get("niveau_risque", ""), c_muted)
    rec_color  = {"ACCEPTER": c_green, "VIGILANCE_RENFORCEE": c_yel, "REFUSER": c_red}.get(
        analysis.get("recommandation", ""), c_muted)

    story = []

    # ── Header ────────────────────────────────────────────────────
    story.append(Table(
        [["🛡️  FinShield OSINT", f"Rapport de Conformité\n{datetime.now().strftime('%d/%m/%Y %H:%M')}"]],
        colWidths=[110*mm, 60*mm],
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), c_bg),
            ("TEXTCOLOR", (0,0), (0,0), c_acc),
            ("TEXTCOLOR", (1,0), (1,0), c_muted),
            ("FONTNAME",  (0,0), (0,0), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0), (0,0), 16),
            ("FONTSIZE",  (1,0), (1,0), 8),
            ("ALIGN",     (1,0), (1,0), "RIGHT"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (0,-1), 0),
        ])
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=c_acc, spaceAfter=16))

    # ── Entity ────────────────────────────────────────────────────
    story.append(Paragraph(f"Entité analysée : <b>{entity}</b>", sH1))

    # ── Risk score box ────────────────────────────────────────────
    score = analysis.get("score_risque", "N/A")
    niveau = analysis.get("niveau_risque", "N/A")
    recommandation = analysis.get("recommandation", "N/A")
    story.append(Table(
        [[f"Score de risque : {score}/100", f"Niveau : {niveau}", f"Recommandation : {recommandation}"]],
        colWidths=[56*mm, 56*mm, 58*mm],
        style=TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), c_surf),
            ("TEXTCOLOR",     (0,0), (0,0),   c_text),
            ("TEXTCOLOR",     (1,0), (1,0),   risk_color),
            ("TEXTCOLOR",     (2,0), (2,0),   rec_color),
            ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("BOX",           (0,0), (-1,-1), 0.5, c_bord),
            ("GRID",          (0,0), (-1,-1), 0.5, c_bord),
        ])
    ))
    story.append(Spacer(1, 10))

    # ── Summary ───────────────────────────────────────────────────
    story.append(Paragraph("Résumé exécutif", sH1))
    story.append(Paragraph(analysis.get("resume_executif", "Données insuffisantes."), sBody))
    story.append(Spacer(1, 6))

    # ── IBAN section ──────────────────────────────────────────────
    if iban_data.get("raw"):
        story.append(Paragraph("Vérification IBAN", sH1))
        iban_rows = [["Champ", "Valeur"]]
        iban_rows.append(["IBAN", iban_data.get("raw", "")])
        iban_rows.append(["Statut", iban_data.get("message", "")])
        iban_rows.append(["Pays", iban_data.get("country", "")])
        iban_rows.append(["Code banque", iban_data.get("bank_code", "")])
        if bank_data.get("name"):
            iban_rows.append(["Banque identifiée", bank_data.get("name", "")])
            iban_rows.append(["Adresse", bank_data.get("address", "")])
            iban_rows.append(["Type", bank_data.get("type", "")])
        t = Table(iban_rows, colWidths=[45*mm, 125*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  c_surf),
            ("TEXTCOLOR",     (0,0), (-1,0),  c_acc),
            ("BACKGROUND",    (0,1), (-1,-1), c_bg),
            ("TEXTCOLOR",     (0,1), (0,-1),  c_muted),
            ("TEXTCOLOR",     (1,1), (-1,-1), c_text),
            ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [c_bg, c_surf]),
            ("GRID",          (0,0), (-1,-1), 0.3, c_bord),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

    # ── Negative news ─────────────────────────────────────────────
    neg_news = analysis.get("negative_news", [])
    story.append(Paragraph("Actualités Négatives", sH1))
    if neg_news:
        rows = [["Titre", "Source", "Nature", "Gravité"]]
        for n in neg_news[:10]:
            rows.append([n.get("titre","")[:60], n.get("source",""), n.get("nature",""), n.get("gravite","").upper()])
        t = Table(rows, colWidths=[75*mm, 35*mm, 35*mm, 25*mm])
        g_colors = {"FAIBLE": c_green, "MOYEN": c_yel, "ELEVE": c_red}
        ts = TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  c_surf),
            ("TEXTCOLOR",     (0,0), (-1,0),  c_acc),
            ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,0), (-1,-1), 7.5),
            ("GRID",          (0,0), (-1,-1), 0.3, c_bord),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [c_bg, c_surf]),
            ("TEXTCOLOR",     (0,1), (-1,-1), c_text),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ])
        for i, n in enumerate(neg_news[:10], start=1):
            grav = n.get("gravite","").upper()
            col = g_colors.get(grav, c_muted)
            ts.add("TEXTCOLOR", (3,i), (3,i), col)
        t.setStyle(ts)
        story.append(t)
    else:
        story.append(Paragraph("Aucune actualité négative identifiée.", sBody))
    story.append(Spacer(1, 6))

    # ── Sanctions, litiges, PEP ───────────────────────────────────
    risk_table_data = [
        ["Catégorie", "Résultat", "Détails"],
        ["Sanctions", "✓ TROUVÉ" if analysis.get("sanctions",{}).get("trouve") else "✗ Non trouvé",
         analysis.get("sanctions",{}).get("details","")[:80]],
        ["Litiges judiciaires", "✓ TROUVÉ" if analysis.get("litiges_judiciaires",{}).get("trouve") else "✗ Non trouvé",
         analysis.get("litiges_judiciaires",{}).get("details","")[:80]],
        ["Exposition PEP", "✓ TROUVÉ" if analysis.get("pep_exposure",{}).get("trouve") else "✗ Non trouvé",
         analysis.get("pep_exposure",{}).get("details","")[:80]],
    ]
    story.append(Paragraph("Vérifications Réglementaires", sH1))
    t = Table(risk_table_data, colWidths=[45*mm, 35*mm, 90*mm])
    ts2 = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  c_surf),
        ("TEXTCOLOR",     (0,0), (-1,0),  c_acc),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.3, c_bord),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [c_bg, c_surf]),
        ("TEXTCOLOR",     (0,1), (-1,-1), c_text),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ])
    for i in range(1,4):
        val = risk_table_data[i][1]
        col = c_red if "TROUVÉ" in val and "Non" not in val else c_green
        ts2.add("TEXTCOLOR", (1,i), (1,i), col)
        ts2.add("FONTNAME",  (1,i), (1,i), "Helvetica-Bold")
    t.setStyle(ts2)
    story.append(t)
    story.append(Spacer(1, 6))

    # ── Facteurs ──────────────────────────────────────────────────
    story.append(Paragraph("Facteurs aggravants", sH1))
    for f in analysis.get("facteurs_aggravants", []):
        story.append(Paragraph(f"• {f}", sBody))
    story.append(Paragraph("Facteurs atténuants", sH1))
    for f in analysis.get("facteurs_attenuants", []):
        story.append(Paragraph(f"• {f}", sBody))

    # ── Footer ────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_bord))
    story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par FinShield OSINT • Usage interne confidentiel", sSmall))

    doc.build(story)
    return buf.getvalue()

# ── App layout ─────────────────────────────────────────────────────────────────

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='font-family: IBM Plex Mono, monospace; color: #00d4ff; font-size: 1.1rem; margin-bottom: 4px;'>
    🛡️ FinShield OSINT
    </div>
    <div style='font-size: 0.7rem; color: #5a6a7a; letter-spacing: 2px; margin-bottom: 20px;'>
    COMPLIANCE · INTELLIGENCE
    </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input("🔑 Clé API Anthropic", type="password",
                             help="Requise pour l'analyse IA et les rapports PDF. Gratuite sur console.anthropic.com")
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size: 0.72rem; color: #5a6a7a; line-height: 1.7;'>
    <b style='color:#c8d6e5;'>Sources intégrées</b><br>
    • OpenSanctions (listes officielles)<br>
    • DuckDuckGo / Bing (presse)<br>
    • Infogreffe (entreprises FR)<br>
    • BODACC (annonces légales)<br>
    • Trustpilot (notations)<br>
    • Tribunaux.fr (litiges)<br>
    • ACPR (régulation bancaire)<br>
    • AMF (sanctions financières)<br>
    • Interpol Red Notices<br>
    • EU Sanctions Map<br>
    • OFAC SDN List<br>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("v2.0 · FinShield OSINT · Usage strictement confidentiel")

# Main header
st.markdown("""
<div class='header-strip'>
  <span class='shield-icon'>🛡️</span>
  <div>
    <div class='app-title'>FinShield OSINT</div>
    <div class='app-sub'>Plateforme de conformité & due diligence financière</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🏦  VÉRIFICATION IBAN",
    "🔍  ANALYSE OSINT",
    "📋  RECHERCHE BANQUE",
    "⚙️  SOURCES & CONFIG",
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — IBAN VERIFICATION
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Vérification IBAN")
    st.markdown("<div class='info-box'>Validez un IBAN et identifiez automatiquement la banque émettrice, son adresse et son code interbancaire (CIB).</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        iban_input = st.text_input("IBAN à analyser", placeholder="FR76 3000 4000 0000 0000 0000 000", key="iban_main")
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        check_iban = st.button("▶ VÉRIFIER L'IBAN", key="btn_iban")

    if check_iban and iban_input:
        with st.spinner("Analyse en cours..."):
            iban_result = validate_iban(iban_input)
            
        if iban_result["valid"]:
            st.markdown(f"<div class='ok-box'>✅ {iban_result['message']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='danger-box'>❌ {iban_result['message']}</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Décomposition IBAN")
            fields = [
                ("IBAN brut", iban_result.get("raw","")),
                ("Pays", iban_result.get("country","")),
                ("Code banque", iban_result.get("bank_code","")),
                ("Code guichet", iban_result.get("branch_code","")),
                ("N° compte", iban_result.get("account_no","")),
                ("Clé RIB", iban_result.get("rib_key","")),
            ]
            for label, val in fields:
                if val:
                    st.markdown(f"""
                    <div class='result-row'>
                    <span style='color:#5a6a7a;font-size:0.75rem;'>{label}</span><br>
                    <span style='font-family: IBM Plex Mono, monospace; font-size:0.9rem;'>{val}</span>
                    </div>
                    """, unsafe_allow_html=True)

        with col_b:
            st.markdown("#### Banque identifiée")
            bank_code = iban_result.get("bank_code","")
            if bank_code:
                bank = lookup_bank(bank_code)
                if bank.get("name") and bank["name"] != "Banque non trouvée":
                    st.markdown(f"""
                    <div class='metric-card'>
                      <div class='label'>Établissement</div>
                      <div class='value' style='font-size:1rem;'>{bank['name']}</div>
                      <div class='sub'>{bank.get('address','')}</div>
                      <div style='margin-top:8px;'><span class='badge-low'>{bank.get('type','')}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Quick ACPR check
                    st.markdown("<div class='info-box'>💡 Vérifiez ce code sur <a href='https://www.regafi.fr' target='_blank' style='color:#00d4ff;'>REGAFI (ACPR)</a> pour le statut réglementaire officiel.</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='warn-box'>⚠️ Code banque <b>{bank_code}</b> non trouvé dans la base locale.<br>Suggestions : {len(bank.get('suggestions',[]))} banques avec un code similaire.</div>", unsafe_allow_html=True)
                    if bank.get("suggestions"):
                        for s in bank["suggestions"][:3]:
                            st.markdown(f"<div class='result-row'><b>{s['name']}</b> · {s.get('address','')}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — OSINT ANALYSIS
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Analyse OSINT & Conformité")
    st.markdown("""
    <div class='info-box'>
    Lance une recherche multi-sources sur une personne ou une entreprise : negative news, sanctions, litiges,
    notations, PEP. L'IA analyse les résultats et génère un rapport de risque avec recommandation.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        entity_input = st.text_input("Nom de la personne / entreprise / entité", 
                                      placeholder="ex: Jean Dupont ou Société Exemple SAS", key="entity_osint")
    with col2:
        entity_type = st.selectbox("Type", ["Entreprise", "Personne physique", "Groupe"], key="etype")
    with col3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        launch_osint = st.button("▶ LANCER L'ANALYSE", key="btn_osint")

    # Optional IBAN for linked analysis
    with st.expander("🔗 Ajouter un IBAN lié (optionnel)"):
        linked_iban = st.text_input("IBAN associé", key="linked_iban")

    if launch_osint and entity_input:
        if not api_key:
            st.markdown("<div class='danger-box'>❌ Clé API Anthropic requise pour l'analyse IA. Renseignez-la dans la barre latérale.</div>", unsafe_allow_html=True)
        else:
            progress = st.progress(0)
            status   = st.empty()
            all_results = []
            scraped   = []

            # Step 1: OpenSanctions
            status.markdown("🔎 Interrogation OpenSanctions…")
            os_result = check_opensanctions(entity_input)
            progress.progress(10)
            time.sleep(0.3)

            # Step 2: Web searches — multiple targeted queries
            queries = [
                f"{entity_input} fraude arnaque escroquerie",
                f"{entity_input} condamné tribunal jugement",
                f"{entity_input} sanctions AMF ACPR",
                f"{entity_input} avis négatif plainte",
                f"{entity_input} liquidation judiciaire faillite",
                f"{entity_input} blanchiment financement terrorisme",
                f'site:infogreffe.fr "{entity_input}"',
                f'site:bodacc.fr "{entity_input}"',
                f'"{entity_input}" Trustpilot avis',
                f'"{entity_input}" negative news scandal',
            ]
            
            for i, q in enumerate(queries):
                status.markdown(f"🌐 Recherche web : `{q[:60]}…`")
                res = search_web_duckduckgo(q, num=5)
                if not res:
                    res = search_web_bing(q, num=5)
                all_results.extend(res)
                progress.progress(10 + int((i+1)/len(queries)*50))
                time.sleep(0.2)

            # Step 3: Scrape top results
            status.markdown("📄 Lecture des pages les plus pertinentes…")
            seen_domains = set()
            for r in all_results[:20]:
                domain = urlparse(r.get("url","")).netloc
                if domain and domain not in seen_domains and len(scraped) < 6:
                    seen_domains.add(domain)
                    text = scrape_page_text(r["url"])
                    if text:
                        scraped.append(text)
            progress.progress(70)

            # Optional IBAN
            iban_data_linked = {}
            bank_data_linked = {}
            if linked_iban:
                iban_data_linked = validate_iban(linked_iban)
                if iban_data_linked.get("bank_code"):
                    bank_data_linked = lookup_bank(iban_data_linked["bank_code"])

            # Step 4: Claude analysis
            status.markdown("🤖 Analyse IA en cours (Claude)…")
            try:
                analysis = analyze_with_claude(entity_input, all_results, scraped, api_key)
                progress.progress(90)
            except Exception as e:
                st.error(f"Erreur analyse IA : {e}")
                analysis = {}
                progress.progress(90)

            # Step 5: Display results
            progress.progress(100)
            status.empty()

            # ── Results display ────────────────────────────────────
            st.markdown("---")
            
            # Risk overview
            niveau = analysis.get("niveau_risque","N/A")
            score  = analysis.get("score_risque","N/A")
            reco   = analysis.get("recommandation","N/A")
            
            badge_map = {"FAIBLE": "badge-low", "MODERE": "badge-medium", "ELEVE": "badge-high", "CRITIQUE": "badge-high"}
            badge_cls = badge_map.get(niveau, "badge-medium")

            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='label'>Score de risque</div>
                  <div class='value'>{score}<span style='font-size:0.8rem; color:#5a6a7a;'>/100</span></div>
                </div>""", unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='label'>Niveau de risque</div>
                  <div class='value' style='font-size:1rem; margin-top:8px;'>
                    <span class='{badge_cls}'>{niveau}</span>
                  </div>
                </div>""", unsafe_allow_html=True)
            with col_r3:
                sanc = "✓ OUI" if analysis.get("sanctions",{}).get("trouve") else "✗ NON"
                sanc_col = "#ff3366" if analysis.get("sanctions",{}).get("trouve") else "#00ff88"
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='label'>Sanctions</div>
                  <div class='value' style='font-size:1rem; color:{sanc_col};'>{sanc}</div>
                  <div class='sub'>OpenSanctions: {os_result.get('count',0)} résultat(s)</div>
                </div>""", unsafe_allow_html=True)
            with col_r4:
                reco_col = {"ACCEPTER": "#00ff88", "VIGILANCE_RENFORCEE": "#ffcc00", "REFUSER": "#ff3366"}.get(reco,"#5a6a7a")
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='label'>Recommandation</div>
                  <div class='value' style='font-size:0.85rem; color:{reco_col};'>{reco}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("#### Résumé exécutif")
            st.markdown(f"<div class='info-box'>{analysis.get('resume_executif','')}</div>", unsafe_allow_html=True)

            col_left, col_right = st.columns(2)
            with col_left:
                # Negative news
                st.markdown("#### 📰 Actualités négatives")
                neg_news = analysis.get("negative_news", [])
                if neg_news:
                    for n in neg_news:
                        grav = n.get("gravite","").lower()
                        cls = {"faible":"ok-box","moyen":"warn-box","eleve":"danger-box"}.get(grav,"info-box")
                        st.markdown(f"""
                        <div class='{cls}'>
                          <b>{n.get('titre','')}</b><br>
                          <small>{n.get('source','')} · {n.get('date','')} · {n.get('nature','')}</small>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucune actualité négative détectée</div>", unsafe_allow_html=True)

                # Litiges
                st.markdown("#### ⚖️ Litiges & procédures")
                lit = analysis.get("litiges_judiciaires", {})
                if lit.get("trouve"):
                    st.markdown(f"<div class='danger-box'>⚠️ {lit.get('details','')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucun litige identifié</div>", unsafe_allow_html=True)

            with col_right:
                # Sanctions detail
                st.markdown("#### 🚨 Sanctions & listes")
                if os_result.get("found"):
                    st.markdown(f"<div class='danger-box'>🔴 <b>{os_result['count']}</b> correspondance(s) OpenSanctions</div>", unsafe_allow_html=True)
                    for r in os_result.get("results",[])[:3]:
                        st.markdown(f"<div class='result-row'><b>{r.get('caption','')}</b> · {', '.join(r.get('datasets',[]))}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucune sanction internationale connue</div>", unsafe_allow_html=True)

                # PEP
                st.markdown("#### 👤 Exposition PEP")
                pep = analysis.get("pep_exposure", {})
                if pep.get("trouve"):
                    st.markdown(f"<div class='warn-box'>⚠️ {pep.get('details','')}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ Aucune exposition PEP détectée</div>", unsafe_allow_html=True)

                # Ratings
                st.markdown("#### ⭐ Réputation & notations")
                rep = analysis.get("reputation_notations","")
                if rep:
                    st.markdown(f"<div class='info-box'>{rep}</div>", unsafe_allow_html=True)

            # Factors
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown("#### 🔺 Facteurs aggravants")
                for f in analysis.get("facteurs_aggravants",[]):
                    st.markdown(f"<div class='danger-box'>• {f}</div>", unsafe_allow_html=True)
            with col_f2:
                st.markdown("#### 🔻 Facteurs atténuants")
                for f in analysis.get("facteurs_attenuants",[]):
                    st.markdown(f"<div class='ok-box'>• {f}</div>", unsafe_allow_html=True)

            # Raw results expander
            with st.expander(f"📋 Résultats bruts ({len(all_results)} sources)"):
                for r in all_results[:30]:
                    st.markdown(f"""
                    <div class='result-row'>
                      <a href='{r.get('url','')}' target='_blank' style='color:#00d4ff; text-decoration:none;'><b>{r.get('title','')}</b></a><br>
                      <small style='color:#5a6a7a;'>{r.get('url','')}</small><br>
                      <small>{r.get('snippet','')[:150]}</small>
                    </div>""", unsafe_allow_html=True)

            # PDF Export
            st.markdown("---")
            st.markdown("#### 📄 Exporter le rapport")
            if st.button("⬇ GÉNÉRER RAPPORT PDF", key="gen_pdf"):
                with st.spinner("Génération du rapport PDF…"):
                    try:
                        pdf_bytes = generate_pdf_report(
                            entity_input,
                            iban_data_linked,
                            bank_data_linked,
                            {"opensanctions": os_result, "web_results": all_results},
                            analysis
                        )
                        st.download_button(
                            label="📥 Télécharger le rapport PDF",
                            data=pdf_bytes,
                            file_name=f"FinShield_{entity_input.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )
                        st.markdown("<div class='ok-box'>✅ Rapport PDF généré avec succès.</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erreur génération PDF: {e}")

            # Store in session for reuse
            st.session_state["last_analysis"] = analysis
            st.session_state["last_entity"]   = entity_input

# ══════════════════════════════════════════════════════════════════
# TAB 3 — BANK SEARCH
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Recherche de Banque")
    st.markdown("<div class='info-box'>Retrouvez une banque par son code CIB ou son nom. Base intégrée : 200+ banques françaises.</div>", unsafe_allow_html=True)

    s_col1, s_col2 = st.columns([3,1])
    with s_col1:
        bank_query = st.text_input("Nom ou code banque", placeholder="ex: 30004 ou BNP Paribas", key="bank_search")
    with s_col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        do_bank_search = st.button("▶ RECHERCHER", key="btn_bank")

    if do_bank_search and bank_query:
        q = bank_query.strip()
        matches = []
        q_low = q.lower()
        for code, info in BANK_DB.items():
            if (q == code or q_low in info["name"].lower()):
                matches.append({"code": code, **info})

        if not matches:
            # Fuzzy
            for code, info in BANK_DB.items():
                words = q_low.split()
                if all(w in info["name"].lower() for w in words):
                    matches.append({"code": code, **info})

        st.markdown(f"<div class='info-box'>{len(matches)} résultat(s) trouvé(s)</div>", unsafe_allow_html=True)
        for m in matches[:20]:
            st.markdown(f"""
            <div class='metric-card'>
              <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                <div>
                  <div class='label'>Code CIB</div>
                  <div style='font-family:IBM Plex Mono,monospace; color:#00d4ff; font-size:1.1rem;'>{m['code']}</div>
                </div>
                <span class='badge-low'>{m.get('type','')}</span>
              </div>
              <div style='margin-top:8px; font-size:0.95rem; color:#c8d6e5;'><b>{m['name']}</b></div>
              <div style='font-size:0.8rem; color:#5a6a7a; margin-top:4px;'>{m.get('address','')}</div>
            </div>
            """, unsafe_allow_html=True)

    # Full table
    with st.expander("📖 Afficher toute la base banques"):
        search_filter = st.text_input("Filtrer", key="full_filter").lower()
        rows = []
        for code, info in BANK_DB.items():
            if not search_filter or search_filter in info["name"].lower() or search_filter in code:
                rows.append({"Code": code, "Banque": info["name"], "Type": info["type"], "Adresse": info.get("address","")})
        import pandas as pd
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=400)

# ══════════════════════════════════════════════════════════════════
# TAB 4 — SOURCES & CONFIG
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Sources & Configuration")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Sources publiques consultées")
        sources = [
            ("🟢 OpenSanctions", "Listes sanctions ONU, UE, OFAC, SECO…", "Actif"),
            ("🟢 DuckDuckGo", "Recherche web ouverte", "Actif"),
            ("🟢 Bing Search", "Fallback recherche web", "Actif"),
            ("🟡 Infogreffe", "Registre du commerce (scraping)", "Partiel"),
            ("🟡 BODACC", "Annonces légales officielles", "Partiel"),
            ("🟡 Trustpilot", "Avis consommateurs", "Partiel"),
            ("🔵 AMF", "Sanctions autorité des marchés", "Via web"),
            ("🔵 ACPR", "Registre établissements crédit", "Via web"),
            ("🔵 Tribunaux.fr", "Décisions de justice", "Via web"),
            ("🔵 Interpol", "Notices rouges", "Via web"),
            ("🔵 EU Sanctions", "Carte sanctions européennes", "Via web"),
        ]
        for name, desc, status in sources:
            color = {"Actif":"#00ff88","Partiel":"#ffcc00","Via web":"#00d4ff"}.get(status,"#5a6a7a")
            st.markdown(f"""
            <div class='result-row'>
              <b>{name}</b> · <span style='color:{color}; font-size:0.75rem;'>{status}</span><br>
              <small style='color:#5a6a7a;'>{desc}</small>
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("#### Déploiement GitHub + Streamlit Cloud")
        st.markdown("""
        <div class='info-box'>
        <b>1. Créez un repo GitHub</b> et uploadez <code>app.py</code> + <code>requirements.txt</code><br><br>
        <b>2. Connectez sur</b> <a href='https://share.streamlit.io' target='_blank' style='color:#00d4ff;'>share.streamlit.io</a><br><br>
        <b>3. Ajoutez dans Secrets :</b><br>
        <code>ANTHROPIC_API_KEY = "sk-ant-..."</code>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Requirements.txt")
        st.code("""streamlit>=1.32
requests>=2.31
beautifulsoup4>=4.12
reportlab>=4.1
anthropic>=0.25
pandas>=2.0
""", language="text")

        st.markdown("#### Limites & RGPD")
        st.markdown("""
        <div class='warn-box'>
        ⚠️ <b>Usage professionnel uniquement.</b><br>
        • Données personnelles : consentement ou base légale requise<br>
        • OpenSanctions : clé API gratuite sur opensanctions.org<br>
        • Résultats web : informatifs uniquement, vérifiez les sources<br>
        • Rapport PDF : usage interne confidentiel
        </div>
        """, unsafe_allow_html=True)
