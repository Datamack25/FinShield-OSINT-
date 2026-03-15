# 🛡️ FinShield OSINT
### Plateforme de conformité financière & due diligence

Application Streamlit multi-onglets pour l'analyse OSINT, la vérification d'IBAN et la recherche bancaire.

---

## Fonctionnalités

| Onglet | Description |
|--------|-------------|
| 🏦 Vérification IBAN | Validation mod97, décomposition, lookup banque |
| 🔍 Analyse OSINT | Negative news, sanctions, litiges, PEP + rapport PDF |
| 📋 Recherche Banque | Base 200+ banques FR par code CIB ou nom |
| ⚙️ Sources & Config | Documentation des sources, guide déploiement |

## Sources intégrées
- **OpenSanctions** — listes ONU, UE, OFAC, SECO
- **DuckDuckGo / Bing** — presse et web ouvert
- **Infogreffe / BODACC** — registre FR et annonces légales
- **Trustpilot / avis** — notation consommateurs
- **AMF / ACPR / Tribunaux.fr** — régulation et justice
- **Base CIB** — 200+ établissements bancaires français

## Déploiement

### Local
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud (GitHub)
1. Forkez ce repo
2. Connectez sur [share.streamlit.io](https://share.streamlit.io)
3. Dans **Secrets**, ajoutez :
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

## Configuration
La clé API Anthropic peut être saisie dans la sidebar ou via les Secrets Streamlit.
Obtenez une clé gratuite sur [console.anthropic.com](https://console.anthropic.com).

## ⚠️ Avertissement légal
Usage professionnel uniquement. Respectez le RGPD et les législations locales.
Les résultats sont informatifs — vérifiez toujours les sources primaires.
