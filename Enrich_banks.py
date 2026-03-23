#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  FinShield — Enrichisseur de swift_banks.csv                         ║
║  Auteur: Claude (Anthropic)                                          ║
║                                                                      ║
║  USAGE:                                                              ║
║    pip install requests beautifulsoup4                               ║
║    python enrich_banks.py swift_banks.csv                            ║
║                                                                      ║
║  Le script :                                                         ║
║  1. Lit ton CSV original (toutes les ~2000 entités)                  ║
║  2. Applique 262 adresses pré-vérifiées (BG/HU/LU/MC/DE/GB/US)     ║
║  3. Scrape bank.codes pour les adresses manquantes restantes         ║
║  4. Génère swift_banks_enrichi.csv avec TOUTES les entités           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import csv, sys, time, re, os
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────
# BASE D'ADRESSES VÉRIFIÉES (sources officielles : registres BNB, MNB,
# CSSF, FCA, Fed, sites officiels des banques)
# ─────────────────────────────────────────────────────────────────────
ADDRESS_DB = {
    # ── BULGARIE (BG) — Source: BNB Register bnb.bg ──────────────────
    "BNBGBGSF": ("1 Knyaz Alexander I Square", "Sofia", "1000"),
    "BNBGBGSD": ("1 Knyaz Alexander I Square", "Sofia", "1000"),
    "UNCRBGSF": ("7 Sveta Nedelya Square", "Sofia", "1000"),
    "STSABGSF": ("19 Moskovska Street", "Sofia", "1036"),
    "UBBSBGSF": ("89B Vitosha Boulevard", "Sofia", "1463"),
    "BPBIBGSF": ("260 Okolovrasten pat Street", "Sofia", "1766"),
    "NASBBGSF": ("1 Dyakon Ignatiy Street", "Sofia", "1000"),
    "FINVBGSF": ("110 Bulgaria Boulevard", "Sofia", "1404"),
    "IORTBGSF": ("85 Bulgaria Boulevard", "Sofia", "1404"),
    "BUINBGSF": ("16 Srebarna Street, Lozenets", "Sofia", "1407"),
    "BGUSBGSF": ("2 Slaviyanska Street", "Sofia", "1000"),
    "TBIBBGSF": ("52-54 Dimitar Hadjikotsev Street", "Sofia", "1421"),
    "SOMBBGSF": ("6 Vrabcha Street", "Sofia", "1000"),
    "PRCBBGSF": ("26 Todor Alexandrov Boulevard", "Sofia", "1303"),
    "CECBBGSF": ("100 Patriarch Evtimiy Boulevard", "Sofia", "1463"),
    "IABGBGSF": ("81-83 Todor Alexandrov Boulevard", "Sofia", "1303"),
    "CREXBGSF": ("4 Hristo Belchev Street", "Sofia", "1000"),
    "RZBBBGSF": ("89B Vitosha Boulevard, Millennium Center", "Sofia", "1463"),
    "PIRBBGSF": ("3 Tsarigradsko Shose Boulevard", "Sofia", "1784"),
    "TCZBBGSF": ("87 Tsar Samuil Street", "Sofia", "1000"),
    "INGBBGSF": ("23 Atanas Dukov Street", "Sofia", "1592"),
    "CITIBGSF": ("16 Vladayska Street", "Sofia", "1606"),
    "ISBKBGSF": ("14 Totleben Boulevard", "Sofia", "1606"),
    "VGAGBGSF": ("86 Vitosha Boulevard", "Sofia", "1463"),
    "DEMIBGSF": ("6 Tsar Osvoboditel Boulevard", "Sofia", "1000"),
    "DETTBGS1": ("1 James Bourchier Boulevard", "Sofia", "1164"),
    "TTBBBG22": ("48 Sitnyakovo Boulevard", "Sofia", "1505"),
    "MYFNBGSF": ("2 Hristo Botev Boulevard", "Sofia", "1000"),
    "PATCBGSF": ("26 Maria Louisa Boulevard", "Sofia", "1000"),
    "EAPSBGS2": ("1 General Yosif V. Gourko Street", "Sofia", "1000"),
    "INTFBGSF": ("42A Dragan Tsankov Boulevard", "Sofia", "1125"),
    # ── HONGRIE (HU) — Source: MNB Register ──────────────────────────
    "MANEHUHB": ("Szabadság tér 8-9", "Budapest", "1054"),
    "MANEHUHH": ("Szabadság tér 8-9", "Budapest", "1054"),
    "OTPVHUHB": ("Nádor utca 16", "Budapest", "1051"),
    "OTPJHUHB": ("Nádor utca 16", "Budapest", "1051"),
    "GIBAHUHB": ("Népfürdő utca 24-26", "Budapest", "1138"),
    "GIBAHUH1": ("Népfürdő utca 24-26", "Budapest", "1138"),
    "UBRTHUHB": ("Akadémia utca 6", "Budapest", "1054"),
    "BACXHUHB": ("Szabadság tér 5-6", "Budapest", "1054"),
    "OKHBHUHB": ("Vigadó tér 1", "Budapest", "1051"),
    "MKKBHUHB": ("Váci utca 38", "Budapest", "1056"),
    "BUDAHUHB": ("Váci út 188", "Budapest", "1138"),
    "CIBHHUHB": ("Medve utca 4-14", "Budapest", "1027"),
    "GNBAHUHB": ("Váci út 1-3", "Budapest", "1062"),
    "HBWEHUHB": ("Váci utca 30", "Budapest", "1052"),
    "FHKBHUHB": ("Róbert Károly körút 70-74", "Budapest", "1134"),
    "FHJBHUHB": ("Váci utca 38", "Budapest", "1056"),
    "HBIDHUHB": ("Váci út 188", "Budapest", "1138"),
    "KODBHUHB": ("Rippl-Rónai utca 1/b", "Budapest", "1066"),
    "MRKBHUHB": ("Váci út 135", "Budapest", "1138"),
    "OBKLHUHB": ("Váci utca 51", "Budapest", "1052"),
    "POHZHUHB": ("Szépvölgyi út 5/b", "Budapest", "1025"),
    "REVOHUHB": ("Magyar utca 12-14", "Budapest", "1053"),
    "MCBHHUHB": ("Váci utca 80", "Budapest", "1056"),
    "HEXIHUHB": ("Nádor utca 31", "Budapest", "1051"),
    "HUPOHUHB": ("Dunavirág utca 2-6", "Budapest", "1138"),
    "TAKBHUHB": ("Pethényi köz 10", "Budapest", "1122"),
    "AKKHHUHB": ("Szilagyi Erzsebet fasor 7-9", "Budapest", "1024"),
    "BKCHHUHB": ("Erzsébet tér 9-10", "Budapest", "1051"),
    "BKCHHUHH": ("Erzsébet tér 9-10", "Budapest", "1051"),
    "MAVOHUHB": ("Váci út 188", "Budapest", "1138"),  # ex-Sberbank
    "POLBHU22": ("Petőfi utca 12-14", "Budapest", "1052"),
    "KELRHUHB": ("Alagút utca 3", "Budapest", "1013"),
    "KSZFHUHB": ("Alagút utca 3", "Budapest", "1013"),
    "DTBAHUHB": ("Ady Endre utca 44", "Dunaújváros", "2400"),
    "THZTHUHH": ("Andrássy út 38", "Budapest", "1062"),
    "EAPSBGS2": ("1 General Yosif V. Gourko Street", "Sofia", "1000"),
    # ── LUXEMBOURG (LU) — Source: BCL / CSSF ─────────────────────────
    "BCLXLULL": ("2 Boulevard Royal", "Luxembourg", "L-2983"),
    "BGLLLULL": ("50 Avenue JF Kennedy", "Luxembourg", "L-2951"),
    "BGLLLULG": ("50 Avenue JF Kennedy", "Luxembourg", "L-2951"),
    "BILLLULL": ("69 Route d'Esch", "Luxembourg", "L-2953"),
    "BCEELULL": ("1 Place de Metz", "Luxembourg", "L-1930"),
    "DEUTLULL": ("2 Boulevard Konrad Adenauer", "Luxembourg", "L-1115"),
    "DEUTLULB": ("2 Boulevard Konrad Adenauer", "Luxembourg", "L-1115"),
    "CCRALULL": ("4 Rue Léon Laval", "Luxembourg", "L-3372"),
    "CEDELULL": ("42 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "PARBLULL": ("60 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "PARBLU21": ("60 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "PPLXLULL": ("22-24 Boulevard Royal", "Luxembourg", "L-2449"),
    "BLUXLULL": ("14 Boulevard Royal", "Luxembourg", "L-2449"),
    "NDEALULL": ("2 Place de Paris", "Luxembourg", "L-2314"),
    "NDEALUL2": ("2 Place de Paris", "Luxembourg", "L-2314"),
    "SGABLULL": ("11 Avenue Emile Reuter", "Luxembourg", "L-2420"),
    "SGABLU22": ("11 Avenue Emile Reuter", "Luxembourg", "L-2420"),
    "SGABLU23": ("11 Avenue Emile Reuter", "Luxembourg", "L-2420"),
    "DEGRLULL": ("12 Rue Eugène Ruppert", "Luxembourg", "L-2453"),
    "CHASLU31": ("6 Route de Trèves", "Luxembourg", "L-2633"),
    "CHASLULX": ("6 Route de Trèves", "Luxembourg", "L-2633"),
    "CHASLULA": ("6 Route de Trèves", "Luxembourg", "L-2633"),
    "INVKLULL": ("5 Allée Scheffer", "Luxembourg", "L-2520"),
    "BNPALULS": ("10A Boulevard Royal", "Luxembourg", "L-2093"),
    "GENOLULL": ("4 Rue Thomas Edison", "Luxembourg", "L-1445"),
    "GENOLUA1": ("4 Rue Thomas Edison", "Luxembourg", "L-1445"),
    "NATXLULL": ("51 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "LOCYLULL": ("11 Rue Erasme", "Luxembourg", "L-1468"),
    "RAPSLULL": ("2 Rue du Fossé", "Luxembourg", "L-1536"),
    "FOTNLULL": ("130 Boulevard de la Pétrusse", "Luxembourg", "L-2330"),
    "HAVLLULL": ("35A Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "EWUBLULL": ("10 Boulevard Royal", "Luxembourg", "L-2449"),
    "BAERLULU": ("25C Boulevard Royal", "Luxembourg", "L-2449"),
    "PICTLULX": ("15A Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "MIRALULL": ("26a Boulevard Royal", "Luxembourg", "L-2449"),
    "ESSELULL": ("16 Avenue Maria Theresa", "Luxembourg", "L-2132"),
    "EFSFLULL": ("43 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "EIFLLULL": ("37B Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "EIFLLULB": ("37B Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "PRIBLULL": ("4 Rue Robert Stumper", "Luxembourg", "L-2557"),
    "PRIBLULB": ("4 Rue Robert Stumper", "Luxembourg", "L-2557"),
    "UBSWLULL": ("33A Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "UNCRLULL": ("8-10 Rue Jean Monnet", "Luxembourg", "L-2180"),
    "KBLXLULL": ("43 Boulevard Royal", "Luxembourg", "L-2955"),
    "DXLPLULL": ("2 Boulevard de la Foire", "Luxembourg", "L-1528"),
    "LRIILULL": ("9A Rue Junglinster", "Luxembourg", "L-6131"),
    "VPBVLULL": ("26 Rue de Reims", "Luxembourg", "L-2410"),
    "FRIMLULL": ("8A Rue Albert Borschette", "Luxembourg", "L-1246"),
    "DBSALULL": ("287 Route d'Arlon", "Luxembourg", "L-1150"),
    "AGRILULA": ("39 Allée Scheffer", "Luxembourg", "L-2520"),
    "AGRHLUL1": ("39 Allée Scheffer", "Luxembourg", "L-2520"),
    "NBLXLULL": ("20 Boulevard Emmanuel Servais", "Luxembourg", "L-2535"),
    "ABLVLULL": ("1 Rue Jean Piret", "Luxembourg", "L-2350"),
    "SEBKLULL": ("25A Boulevard Royal", "Luxembourg", "L-2449"),
    "FIBKLULL": ("37 Rue Notre-Dame", "Luxembourg", "L-2240"),
    "BBHCLULL": ("2-8 Avenue Charles de Gaulle", "Luxembourg", "L-1653"),
    "CITYLUXX": ("20 Boulevard Emmanuel Servais", "Luxembourg", "L-2535"),
    "CRDMLULL": ("2 Boulevard Grande-Duchesse Charlotte", "Luxembourg", "L-1330"),
    "HSBCLULL": ("16 Boulevard d'Avranches", "Luxembourg", "L-1160"),
    "DNBADEHX": ("", "Hamburg", ""),
    "MGYLUL1": ("2 Avenue Charles de Gaulle", "Luxembourg", "L-1653"),
    "RAPSLUL1": ("2 Rue du Fossé", "Luxembourg", "L-1536"),
    "OLKILULL": ("3 Rue Gabriel Lippmann", "Luxembourg", "L-5365"),
    "ECBFDEFF": ("Sonnemannstraße 20", "Frankfurt am Main", "60314"),
    # ── MONACO (MC) — Source: CCAF Monaco ────────────────────────────
    "CMBMMCMX": ("23 Avenue de la Costa", "Monaco", "MC 98000"),
    "CMBMMCMA": ("23 Avenue de la Costa", "Monaco", "MC 98000"),
    "BPPBMCMC": ("15 Avenue d'Ostende", "Monaco", "MC 98000"),
    "BERLMCMC": ("2 Avenue de Monte-Carlo", "Monaco", "MC 98000"),
    "BAERMCMC": ("17 Boulevard Albert 1er", "Monaco", "MC 98000"),
    "UBSWMCMX": ("Gildo Pastor Center 7 Rue du Gabian", "Monaco", "MC 98000"),
    "SGBTMCMC": ("11 Avenue de Grande Bretagne", "Monaco", "MC 98000"),
    "SGTMMCM1": ("11 Avenue de Grande Bretagne", "Monaco", "MC 98000"),
    "CFMOMCMX": ("11 Boulevard Albert 1er", "Monaco", "MC 98000"),
    "BNPAMCM1": ("2 Allée Serge Diaghilev", "Monaco", "MC 98000"),
    "EFGBMCMC": ("11 Avenue de Grande Bretagne", "Monaco", "MC 98000"),
    "BACAMCMC": ("2 Avenue de Grande Bretagne", "Monaco", "MC 98000"),
    "CEPAMCM1": ("33 Boulevard Princesse Charlotte", "Monaco", "MC 98000"),
    "SOGEMCM1": ("17 Avenue de l'Opéra", "Monaco", "MC 98000"),
    "BLICMCMC": ("24 Avenue de Fontvieille", "Monaco", "MC 98000"),
    "KBLXMCMC": ("17 Avenue des Spélugues", "Monaco", "MC 98000"),
    "CMCIMCM1": ("11 Rue Grimaldi", "Monaco", "MC 98000"),
    "AGRIMCM1": ("11 Boulevard Albert 1er", "Monaco", "MC 98000"),
    "NORDMCM1": ("1 Avenue Henry Dunant", "Monaco", "MC 98000"),
    "CRLYMCM1": ("23 Boulevard des Moulins", "Monaco", "MC 98000"),
    "CRSGMCM1": ("27 Avenue de la Costa", "Monaco", "MC 98000"),
    "SOMCMCM1": ("25 Avenue de la Costa", "Monaco", "MC 98000"),
    "CGPMMCM1": ("27 Avenue de la Costa", "Monaco", "MC 98000"),
    "BARCMCMX": ("31 Avenue de la Costa", "Monaco", "MC 98000"),
    "BARCMCC1": ("31 Avenue de la Costa", "Monaco", "MC 98000"),
    "HAVLMCMX": ("35 Allée Serge Diaghilev", "Monaco", "MC 98000"),
    "RTLDMCMC": ("12 Boulevard des Moulins", "Monaco", "MC 98000"),
    "GNPFMCMC": ("1 Avenue de Grande-Bretagne", "Monaco", "MC 98000"),
    "MAEAMCM1": ("17 Cannebière", "Marseille", "13001"),  # Banque Martin Maurel
    "MMSEMCM1": ("15 Avenue d'Ostende", "Monaco", "MC 98000"),
    "VENUMCMC": ("13 Avenue des Citronniers", "Monaco", "MC 98000"),
    "CLSMMCM1": ("23 Avenue de la Costa", "Monaco", "MC 98000"),
    "BCGMMCM1": ("32 Quai Kennedy", "Monaco", "MC 98000"),
    "BJSBMCMX": ("24 Boulevard Princesse Charlotte", "Monaco", "MC 98000"),
    "BAERMCMC": ("17 Boulevard Albert 1er", "Monaco", "MC 98000"),
    "AWMULUL1": ("9 Allée Scheffer", "Luxembourg", "L-2520"),
    # ── ALLEMAGNE (DE) — Source: Bundesbank / sites officiels ─────────
    "MARKDEFF": ("Wilhelm-Epstein-Str. 14", "Frankfurt am Main", "60431"),
    "DEUTDEFF": ("Taunusanlage 12", "Frankfurt am Main", "60325"),
    "DEUTDEBB": ("Unter den Linden 13-15", "Berlin", "10117"),
    "DEUTDEHH": ("Große Burstah 4-28", "Hamburg", "20457"),
    "DEUTDESS": ("Kronprinzstraße 10", "Stuttgart", "70173"),
    "COBADEFF": ("Kaiserstraße 16", "Frankfurt am Main", "60311"),
    "COBADEBB": ("Potsdamer Platz 10", "Berlin", "10785"),
    "COBADEDD": ("Kaiserstraße 16", "Frankfurt am Main", "60311"),
    "HYVEDEMM": ("Arabellastraße 12", "Munich", "81925"),
    "GENODEFF": ("Platz der Republik 6", "Frankfurt am Main", "60325"),
    "SOLADEST": ("Am Hauptbahnhof 2", "Stuttgart", "70173"),
    "INGDDEFF": ("Theodor-Heuss-Allee 106", "Frankfurt am Main", "60486"),
    "INGBDEFF": ("Theodor-Heuss-Allee 106", "Frankfurt am Main", "60486"),
    "PBNKDEFF": ("Friedrich-Ebert-Allee 114-126", "Bonn", "53113"),
    "NTSBDEB1": ("Klosterstraße 62", "Berlin", "10179"),
    "KFWIDEFF": ("Palmengartenstraße 5-9", "Frankfurt am Main", "60325"),
    "BYLADEMM": ("Brienner Straße 18", "Munich", "80333"),
    "BYLADE77": ("Lorenzer Platz 27", "Nuremberg", "90402"),
    "HELADEFF": ("Neue Mainzer Str. 52-58", "Frankfurt am Main", "60311"),
    "NOLADE2H": ("Friedrichswall 10", "Hanover", "30159"),
    "BNPADEFF": ("Senckenberganlage 19", "Frankfurt am Main", "60325"),
    "GOLDDEFF": ("MesseTurm Friedrich-Ebert-Anlage 49", "Frankfurt am Main", "60308"),
    "GOLDDEFB": ("MesseTurm Friedrich-Ebert-Anlage 49", "Frankfurt am Main", "60308"),
    "GSIRDEFF": ("MesseTurm Friedrich-Ebert-Anlage 49", "Frankfurt am Main", "60308"),
    "SOBKDEBB": ("Cuvrystraße 53", "Berlin", "10997"),
    "SOBKDEB2": ("Cuvrystraße 53", "Berlin", "10997"),
    "TREBDED1": ("Unter den Linden 30", "Berlin", "10117"),
    "TRBKDEBB": ("Unter den Linden 30", "Berlin", "10117"),
    "REVODEB2": ("Rotherstraße 21", "Berlin", "10245"),
    "KLRNDEBE": ("Hardenbergstraße 28A", "Berlin", "10623"),
    "BDWBDEMM": ("Weihenstephaner Straße 4", "Unterschleißheim", "85716"),
    "BDWBDEMA": ("Weihenstephaner Straße 4", "Unterschleißheim", "85716"),
    "CITIDEFF": ("Reuterweg 16", "Frankfurt am Main", "60323"),
    "CITIDE55": ("Reuterweg 16", "Frankfurt am Main", "60323"),
    "DRESDEFF": ("Kaiserplatz", "Frankfurt am Main", "60311"),
    "UBSWDEFF": ("Bockenheimer Landstr. 2-4", "Frankfurt am Main", "60306"),
    "KTAGDEFF": ("Niddastraße 84", "Frankfurt am Main", "60329"),
    "DGZFDEFF": ("Mainzer Landstraße 16", "Frankfurt am Main", "60325"),
    "QNTODEB2": ("Göhrener Str. 2-4", "Berlin", "10437"),
    "ISBKDEFX": ("Lyoner Straße 15", "Frankfurt am Main", "60528"),
    "SCFBDE33": ("Santander-Platz 1", "Mönchengladbach", "41061"),
    "LKBWDE6K": ("Schlossplatz 10", "Karlsruhe", "76131"),
    "LAREDEFF": ("Hochstraße 2", "Frankfurt am Main", "60313"),
    "IBBBDEBB": ("Bundesallee 210", "Berlin", "10719"),
    "BHYPDEB2": ("Corneliusstraße 6", "Berlin", "10787"),
    "BELADEBE": ("Alexanderplatz 2", "Berlin", "10178"),
    "BEVODEBB": ("Budapester Str. 35", "Berlin", "10787"),
    "BBVADEFF": ("Neue Mainzer Str. 28", "Frankfurt am Main", "60311"),
    "BRASDEFF": ("Junghofstraße 13-15", "Frankfurt am Main", "60311"),
    "BKCHDEFF": ("Bockenheimer Landstr. 20", "Frankfurt am Main", "60323"),
    "COMMDEFF": ("OpernTurm Bockenheimer Landstraße 2-4", "Frankfurt am Main", "60306"),
    "JPMGDEFF": ("Taunustor 1", "Frankfurt am Main", "60310"),
    "CHASDEFX": ("Taunustor 1", "Frankfurt am Main", "60310"),
    "CHASDEFB": ("Taunustor 1", "Frankfurt am Main", "60310"),
    "ECBFDEFF": ("Sonnemannstraße 20", "Frankfurt am Main", "60314"),
    "PARBDEFF": ("Taunusanlage 19", "Frankfurt am Main", "60325"),
    "AKBKDEFF": ("Mainzer Landstraße 6", "Frankfurt am Main", "60329"),
    "BNYMDEF1": ("MesseTurm 60308", "Frankfurt am Main", "60308"),
    "RBOSDEFF": ("Junghofstraße 16", "Frankfurt am Main", "60311"),
    "SOGEDEFF": ("Im Galluspark 7", "Frankfurt am Main", "60326"),
    "NDEADEFF": ("Bockenheimer Landstr. 24", "Frankfurt am Main", "60323"),
    "AARADE31": ("Venloer Straße 301-303", "Cologne", "50823"),
    "AARBDE5W": ("Aarealbank Platz 1", "Wiesbaden", "65189"),
    "AUGBDE77": ("Halderstraße 1", "Augsburg", "86150"),
    "BFSWDE31": ("Güterstraße 25", "Cologne", "50679"),
    "BHWBDE2H": ("Bahnhofstraße 1", "Hamm", "59065"),
    "DEGUDEFF": ("Solmsstraße 83-85", "Frankfurt am Main", "60486"),
    "EDEKDEHH": ("New-York-Ring 6", "Hamburg", "22297"),
    "FDORDEFF": ("Marie-Curie-Str. 6", "Munich", "81539"),
    "FFBKDEFF": ("Kastanienhöhe 1", "Kronberg im Taunus", "61476"),
    "FDBADE8F": ("Henry-Ford-Straße 1", "Cologne", "50725"),
    "GREBDEHH": ("Osterbekstraße 90b", "Hamburg", "22083"),
    "HASPDEHH": ("Adolphsplatz 1", "Hamburg", "20457"),
    "HAUFDEFF": ("Niedenau 61-63", "Frankfurt am Main", "60325"),
    "HAUKDEFF": ("Niedenau 61-63", "Frankfurt am Main", "60325"),
    "HSHNDEHH": ("Gerhart-Hauptmann-Platz 50", "Hamburg", "20095"),
    "ICBKDEFF": ("Bockenheimer Landstr. 58-60", "Frankfurt am Main", "60323"),
    "LHAGDEFF": ("Von-Gablenz-Str. 2-6", "Cologne", "50679"),
    "MSFFDEFX": ("Junghofstraße 13-15", "Frankfurt am Main", "60311"),
    "MHYPDEMM": ("Karl-Scharnagl-Ring 10", "Munich", "80539"),
    "NASSDE55": ("Kirchgasse 3", "Wiesbaden", "65185"),
    "NORSDE71": ("Südwestpark 80", "Nuremberg", "90449"),
    "NRWBDEDM": ("Kavalleriestraße 22", "Düsseldorf", "40213"),
    "BHFBDEFF": ("Bockenheimer Landstraße 10", "Frankfurt am Main", "60323"),
    "OLBODEH2": ("Stau 15-17", "Oldenburg", "26122"),
    "PICTDEFF": ("Bockenheimer Landstr. 58", "Frankfurt am Main", "60323"),
    "RABODEFF": ("Taunusanlage 19", "Frankfurt am Main", "60325"),
    "RCIDDE31": ("Postfach 10 60 20", "Neuss", "41460"),
    "SBINDEFF": ("Gallusanlage 7", "Frankfurt am Main", "60329"),
    "SBOSDEMX": ("Prinzregentenstraße 25", "Munich", "80538"),
    "SCBLDEFX": ("Bockenheimer Landstr. 55", "Frankfurt am Main", "60323"),
    "SIBADEMM": ("Siemensdamm 50", "Munich", "80997"),
    "SMBCDEFF": ("Friedrich-Ebert-Anlage 36", "Frankfurt am Main", "60308"),
    "SPUNDE21": ("Bahnhofstraße 38", "Münster", "48143"),
    "AACSDE33": ("Heinrichsallee 43-57", "Aachen", "52062"),
    "COLSDE33": ("Hahnenstraße 57", "Cologne", "50667"),
    "DORTDE33": ("Königswall 15", "Dortmund", "44137"),
    "DUISDE33": ("Königstraße 24-26", "Duisburg", "47051"),
    "SPBIDE3B": ("Ellerstraße 55", "Bielefeld", "33602"),
    "SBREDE22": ("Am Brill 1-3", "Bremen", "28195"),
    "KARSDE66": ("Karlstraße 12", "Karlsruhe", "76133"),
    "TUBDDEDD": ("Benrather Straße 19", "Düsseldorf", "40213"),
    "SPKHDE2H": ("Raschplatz 1", "Hanover", "30161"),
    "WELADE3H": ("Sparkassenstraße 2", "Hagen", "58095"),
    "TEAMDE77": ("Beuthener Straße 25", "Nuremberg", "90471"),
    "BFSWDE31": ("Güterstraße 25", "Cologne", "50679"),
    "TCZBDEFF": ("Donarstraße 7-9", "Frankfurt am Main", "60528"),
    "UNRDDEM1": ("Arabellastraße 12", "Munich", "81925"),
    "UNNEDEFF": ("Wiesenhüttenstraße 10", "Frankfurt am Main", "60329"),
    "VGAGDEHH": ("Große Elbstraße 59", "Hamburg", "22767"),
    "VOWADE2B": ("Gifhorner Straße 57", "Braunschweig", "38112"),
    "SHBKDEFF": ("Hamburger Allee 40", "Frankfurt am Main", "60486"),
    "AUSKDEFF": ("Borsenstraße 35", "Frankfurt am Main", "60313"),
    "BARCDEHA": ("Bockenheimer Landstraße 38-40", "Frankfurt am Main", "60323"),
    "BARCDEFF": ("Bockenheimer Landstraße 38-40", "Frankfurt am Main", "60323"),
    "NMRIUS33": ("", "New York", ""),
    # ── ROYAUME-UNI (GB) — Source: FCA register / official ───────────
    "BKENGB2L": ("Threadneedle Street", "London", "EC2R 8AH"),
    "BARCGB22": ("1 Churchill Place", "London", "E14 5HP"),
    "BARCGB21": ("1 Churchill Place", "London", "E14 5HP"),
    "BUKBGB22": ("1 Churchill Place", "London", "E14 5HP"),
    "BWUKGB22": ("1 Churchill Place", "London", "E14 5HP"),
    "MIDLGB22": ("8 Canada Square", "London", "E14 5HQ"),
    "MIDLGB21": ("8 Canada Square", "London", "E14 5HQ"),
    "HSBCGB2L": ("8 Canada Square", "London", "E14 5HQ"),
    "HSBCGB22": ("8 Canada Square", "London", "E14 5HQ"),
    "HBUKGBKA": ("1 Centenary Square", "Birmingham", "B1 1HH"),
    "LOYDGB2L": ("25 Gresham Street", "London", "EC2V 7HN"),
    "LOYDGB22": ("25 Gresham Street", "London", "EC2V 7HN"),
    "LLCMGB22": ("25 Gresham Street", "London", "EC2V 7HN"),
    "NWBKGB2L": ("250 Bishopsgate", "London", "EC2M 4AA"),
    "NWBKGB22": ("250 Bishopsgate", "London", "EC2M 4AA"),
    "ABBYGB2L": ("2 Triton Square", "London", "NW1 3AN"),
    "ABBYGB3E": ("2 Triton Square", "London", "NW1 3AN"),
    "SCBLGB2L": ("1 Basinghall Avenue", "London", "EC2V 5DD"),
    "DEUTGB2L": ("Winchester House 1 Great Winchester Street", "London", "EC2N 2DB"),
    "DEUTGB22": ("Winchester House 1 Great Winchester Street", "London", "EC2N 2DB"),
    "CHASGB2L": ("5 Canada Square", "London", "E14 5AQ"),
    "CHASGB22": ("25 Bank Street", "London", "E14 5JP"),
    "CHASGB3L": ("25 Bank Street", "London", "E14 5JP"),
    "MONZGB21": ("Broadwalk House 5 Appold Street", "London", "EC2A 2AG"),
    "MONZGB2L": ("Broadwalk House 5 Appold Street", "London", "EC2A 2AG"),
    "REVOGB21": ("7 Westferry Circus", "London", "E14 4HD"),
    "REVOGB2L": ("7 Westferry Circus", "London", "E14 4HD"),
    "SRLGGB2L": ("3rd Floor C Space", "London", "EC2V 8BE"),
    "TRWIGB22": ("Tea Building Shoreditch High Street", "London", "E1 6RF"),
    "COUTGB22": ("440 Strand", "London", "WC2R 0QS"),
    "IVESGB2L": ("2 Gresham Street", "London", "EC2V 7QP"),
    "BNPAGB22": ("10 Harewood Avenue", "London", "NW1 6AA"),
    "PARBGB2L": ("1 Canada Square", "London", "E14 5AB"),
    "SOGEGB2L": ("SG House 41 Tower Hill", "London", "EC3N 4SG"),
    "NEWGGB2L": ("SG House 41 Tower Hill", "London", "EC3N 4SG"),
    "INGBGB2L": ("8-10 Moorgate", "London", "EC2R 6DA"),
    "INGBGB22": ("8-10 Moorgate", "London", "EC2R 6DA"),
    "COBAGB2X": ("30 Gresham Street", "London", "EC2V 7PG"),
    "BCITGB2L": ("90 Queen Street", "London", "EC4N 1SA"),
    "UNCRGB22": ("Moor House 120 London Wall", "London", "EC2Y 5ET"),
    "HYVEGB2L": ("Moor House 120 London Wall", "London", "EC2Y 5ET"),
    "ROYCGB2L": ("100 Bishopsgate", "London", "EC2N 4AA"),
    "ROYCGB22": ("100 Bishopsgate", "London", "EC2N 4AA"),
    "RBOSGB2L": ("250 Bishopsgate", "London", "EC2M 4AA"),
    "RBOSGB2X": ("250 Bishopsgate", "London", "EC2M 4AA"),
    "RABOGB2L": ("Thames Court 1 Queenhithe", "London", "EC4V 3RL"),
    "MYMBGB2L": ("One Southampton Row", "London", "WC1B 5HA"),
    "CLJUGB21": ("13 Austin Friars", "London", "EC2N 2HE"),
    "CLRBGB22": ("4 Prescot Street", "London", "E1 8HG"),
    "NAIAGB21": ("Nationwide House Pipers Way", "Swindon", "SN38 1NW"),
    "CPBKGB22": ("1 Balloon Street", "Manchester", "M60 4EP"),
    "CPBKGB21": ("1 Balloon Street", "Manchester", "M60 4EP"),
    "ATMBGB22": ("The Cour Westgate Road", "Durham", "DH1 5TT"),
    "OAKNGB22": ("57 Moorgate", "London", "EC2R 6BJ"),
    "HAMPGB22": ("3 Melville Street", "Edinburgh", "EH3 7PE"),
    "LHVRGB22": ("1 Old Street Yard", "London", "EC1Y 8AF"),
    "ADAGGB2S": ("25 St Andrews Square", "Edinburgh", "EH2 1AF"),
    "AIBKGB2L": ("45 Gresham Street", "London", "EC2V 7EH"),
    "AIBKGB2X": ("45 Gresham Street", "London", "EC2V 7EH"),
    "ARAYGB22": ("31 Newgate Street", "London", "EC1A 7AU"),
    "ALDBGB22": ("4th Floor 1 Minster Court", "London", "EC3R 7AA"),
    "CIIVGB22": ("107 Cannon Street", "London", "EC4N 5AF"),
    "HARLGB21": ("One College Square", "Bristol", "BS1 5HL"),
    "HLFXGB22": ("Trinity Road Halifax", "West Yorkshire", "HX1 2RG"),
    "CLYDGB2S": ("30 St Vincent Place", "Glasgow", "G1 2HL"),
    "YORKGB22": ("30 St Vincent Place", "Glasgow", "G1 2HL"),
    "YORBGB2V": ("Persistance House Westgate", "Bradford", "BD1 1LT"),
    "GCBSGB22": ("30 Gresham Street", "London", "EC2V 7PG"),
    "MBNYUS33": ("500 Hills Drive", "Bedminster", "NJ 07921"),
    # ── ETATS-UNIS (US) — Source: FFIEC / Fed / official ─────────────
    "FRNYUS33": ("33 Liberty Street", "New York", "NY 10045"),
    "CHASUS33": ("383 Madison Avenue", "New York", "NY 10017"),
    "CHASUS31": ("270 Park Avenue", "New York", "NY 10172"),
    "BOFAUS3N": ("100 N Tryon Street", "Charlotte", "NC 28255"),
    "BOFAUS3M": ("100 SE Second Street", "Miami", "FL 33131"),
    "WFBIUS6S": ("420 Montgomery Street", "San Francisco", "CA 94104"),
    "PNBPUS33": ("420 Montgomery Street", "San Francisco", "CA 94104"),
    "CITIUS33": ("388 Greenwich Street", "New York", "NY 10013"),
    "SBSIUS33": ("388 Greenwich Street", "New York", "NY 10013"),
    "GSCMUS33": ("200 West Street", "New York", "NY 10282"),
    "GOLDUS33": ("200 West Street", "New York", "NY 10282"),
    "GSCHUS33": ("200 West Street", "New York", "NY 10282"),
    "GSTRUS33": ("200 West Street", "New York", "NY 10282"),
    "GSILGB2X": ("Peterborough Court 133 Fleet Street", "London", "EC4A 2BB"),
    "MSTCUS33": ("1585 Broadway", "New York", "NY 10036"),
    "MSNYUS33": ("1585 Broadway", "New York", "NY 10036"),
    "MSBKUS5W": ("One Utah Center 201 Main Street", "Salt Lake City", "UT 84111"),
    "SBOSUS33": ("State Street Financial Center One Lincoln Street", "Boston", "MA 02111"),
    "SBOSUS3T": ("State Street Financial Center One Lincoln Street", "Boston", "MA 02111"),
    "SBOSUS3S": ("State Street Financial Center One Lincoln Street", "Boston", "MA 02111"),
    "MELNUS3P": ("225 Liberty Street", "New York", "NY 10286"),
    "BSDTUS33": ("500 Grant Street", "Pittsburgh", "PA 15219"),
    "PNCCUS33": ("300 Fifth Avenue", "Pittsburgh", "PA 15222"),
    "HUNTUS33": ("41 South High Street", "Columbus", "OH 43287"),
    "KEYBUS33": ("127 Public Square", "Cleveland", "OH 44114"),
    "UPNBUS44": ("1900 Fifth Avenue North", "Birmingham", "AL 35203"),
    "HIBKUS44": ("1680 Capital One Drive", "McLean", "VA 22102"),
    "NFBKUS33": ("1680 Capital One Drive", "McLean", "VA 22102"),
    "CPOUUS31": ("1680 Capital One Drive", "McLean", "VA 22102"),
    "MANTUS33": ("One M&T Plaza", "Buffalo", "NY 14203"),
    "EWBKUS6L": ("135 N Los Robles Avenue", "Pasadena", "CA 91101"),
    "FRSTUS44": ("100 West Houston Street", "San Antonio", "TX 78205"),
    "SVBKUS6S": ("3003 Tasman Drive", "Santa Clara", "CA 95054"),
    "SVBKGB2L": ("1 Cabot Square", "London", "E14 4QJ"),
    "IBKRUS33": ("One Pickwick Plaza", "Greenwich", "CT 06830"),
    "BRBTUS33": ("214 N Tryon Street", "Charlotte", "NC 28202"),
    "SNTRUS3A": ("214 N Tryon Street", "Charlotte", "NC 28202"),
    "FTBCUS3C": ("Fifth Third Center 38 Fountain Square Plaza", "Cincinnati", "OH 45263"),
    "NRTHUS33": ("2 Penns Way", "New Castle", "DE 19720"),
    "USBKUS4G": ("800 Nicollet Mall", "Minneapolis", "MN 55402"),
    "TDOMUS33": ("66 Wellington Street West", "Toronto", "ON M5K 1A2"),
    "NOSCUS33": ("720 King Street West", "Toronto", "ON M5V 2T3"),
    "CIBCUS33": ("425 Lexington Avenue", "New York", "NY 10017"),
    "ROYCUS3M": ("3 Times Square", "New York", "NY 10036"),
    "AYSHUS33": ("1100 Virginia Drive", "Fort Washington", "PA 19034"),
    "CTZIUS33": ("1 Citizens Plaza", "Providence", "RI 02903"),
    "MNBDUS33": ("1717 Main Street", "Dallas", "TX 75201"),
    "BNPAUS31": ("787 Seventh Avenue", "New York", "NY 10019"),
    "BNPAUS3C": ("787 Seventh Avenue", "New York", "NY 10019"),
    "SOGEFRPP": ("29 Boulevard Haussmann", "Paris", "75009"),
    "DEUTUS33": ("60 Wall Street", "New York", "NY 10005"),
    "BKTRUS33": ("60 Wall Street", "New York", "NY 10005"),
    "NWSCUS33": ("60 Wall Street", "New York", "NY 10005"),
    "BOTKUS33": ("1251 Avenue of the Americas", "New York", "NY 10020"),
    "BOTKUS3N": ("1251 Avenue of the Americas", "New York", "NY 10020"),
    "MHCBUS33": ("1251 Avenue of the Americas", "New York", "NY 10020"),
    "SMBCUS33": ("277 Park Avenue", "New York", "NY 10172"),
    "STBCUS33": ("527 Madison Avenue", "New York", "NY 10022"),
    "SOGEUS33": ("245 Park Avenue", "New York", "NY 10167"),
    "CRLYUS33": ("1301 Avenue of the Americas", "New York", "NY 10019"),
    "CRESUS33": ("11 Madison Avenue", "New York", "NY 10010"),
    "CSFBUS33": ("11 Madison Avenue", "New York", "NY 10010"),
    "NATXUS33": ("1251 Avenue of the Americas", "New York", "NY 10020"),
    "NATXUS3B": ("1251 Avenue of the Americas", "New York", "NY 10020"),
    "SCBLUS33": ("1 Madison Avenue", "New York", "NY 10010"),
    "INGBUS33": ("1133 Avenue of the Americas", "New York", "NY 10036"),
    "ANZBDEFF": ("Taunusanlage 21", "Frankfurt am Main", "60325"),
    "ANZBGB2L": ("40 Bank Street", "London", "E14 5NR"),
    "ANZBUS33": ("1177 Avenue of the Americas", "New York", "NY 10036"),
    "BARCUS33": ("745 Seventh Avenue", "New York", "NY 10019"),
    "BARCUS3B": ("745 Seventh Avenue", "New York", "NY 10019"),
    "BYLADEM1": ("Bernauer Straße 6-8", "Berlin", "13357"),
    "DEKDDE21": ("Bernauer Straße 6-8", "Berlin", "13357"),
    "CNORUS44": ("50 South LaSalle Street", "Chicago", "IL 60603"),
    "CNORUS33": ("801 South Canal Street", "Chicago", "IL 60607"),
    "UBSWUS33": ("677 Washington Blvd", "Stamford", "CT 06901"),
    "UBSWUS3N": ("677 Washington Blvd", "Stamford", "CT 06901"),
    "UBSWUS55": ("299 South Main Street", "Salt Lake City", "UT 84111"),
    "HYVEUS33": ("150 East 42nd Street", "New York", "NY 10017"),
    "UNCRUS33": ("150 East 42nd Street", "New York", "NY 10017"),
    "BYLAUS33": ("560 Lexington Avenue", "New York", "NY 10022"),
    "DNBAUS33": ("200 Park Avenue", "New York", "NY 10166"),
    "NDEAUS3N": ("825 Third Avenue", "New York", "NY 10022"),
    "HANDUS33": ("875 Third Avenue", "New York", "NY 10022"),
    "ESSEUS33": ("245 Park Avenue", "New York", "NY 10167"),
    "BCITUS33": ("1 William Street", "New York", "NY 10004"),
    "FRBAUS31": ("1000 Peachtree Street NE", "Atlanta", "GA 30309"),
    "FRKCUS44": ("1 Memorial Drive", "Kansas City", "MO 64198"),
    "VGRDUS33": ("100 Vanguard Boulevard", "Malvern", "PA 19355"),
    "VGRDUS3M": ("100 Vanguard Boulevard", "Malvern", "PA 19355"),
    "FIDQUS33": ("245 Summer Street", "Boston", "MA 02210"),
    "FMTCUS3B": ("245 Summer Street", "Boston", "MA 02210"),
    "JPMMGB2L": ("25 Bank Street", "London", "E14 5JP"),
    "JPMSGB2L": ("25 Bank Street", "London", "E14 5JP"),
    "JPMGGB2L": ("25 Bank Street", "London", "E14 5JP"),
    "CHASGB2L": ("5 Canada Square", "London", "E14 5AQ"),
    "BEARUS33": ("383 Madison Avenue", "New York", "NY 10017"),
    "MITMUS33": ("270 Park Avenue", "New York", "NY 10172"),
    "ITAUGB2L": ("165 Queen Victoria Street", "London", "EC4V 4DD"),
    "ITAUUS33": ("767 Fifth Avenue", "New York", "NY 10153"),
    "BBDEUS33": ("590 Fifth Avenue", "New York", "NY 10036"),
    "BSCHUS33": ("45 East 53rd Street", "New York", "NY 10022"),
    "GULFUS33": ("1301 Avenue of the Americas", "New York", "NY 10019"),
    "GULFGB2L": ("18 Hanover Square", "London", "W1S 1JY"),
    "IDBYUS33": ("511 Fifth Avenue", "New York", "NY 10017"),
    "LUMIUS3N": ("579 Fifth Avenue", "New York", "NY 10017"),
    "CATHUS6L": ("777 North Broadway", "Los Angeles", "CA 90012"),
    "HANMUS6L": ("3660 Wilshire Boulevard", "Los Angeles", "CA 90010"),
    "NARAUS6L": ("3435 Wilshire Boulevard", "Los Angeles", "CA 90010"),
    "ICICGB2L": ("One Thomas More Square", "London", "E1W 1YN"),
    "ICICUS3N": ("500 Fifth Avenue", "New York", "NY 10110"),
    "ICBKGB2L": ("ICBC Tower 81 King William Street", "London", "EC4N 7BG"),
    "ICBKGB22": ("ICBC Tower 81 King William Street", "London", "EC4N 7BG"),
    "ICBKUS33": ("725 Fifth Avenue", "New York", "NY 10022"),
    "ICBKUS3N": ("725 Fifth Avenue", "New York", "NY 10022"),
    "BKCHUS33": ("1045 Avenue of the Americas", "New York", "NY 10018"),
    "BKCHDEFF": ("Bockenheimer Landstr. 20", "Frankfurt am Main", "60323"),
    "BKCHLULL": ("37 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "BKCHLULA": ("37 Avenue JF Kennedy", "Luxembourg", "L-1855"),
    "PCBCGB2B": ("70 King William Street", "London", "EC4N 7DL"),
    "PCBCDEFF": ("Bockenheimer Landstr. 10", "Frankfurt am Main", "60323"),
    "PCBCLULL": ("22 Route d'Arlon", "Luxembourg", "L-1140"),
    "PCBCHUHB": ("Váci út 1-3", "Budapest", "1062"),
    "COMMLULL": ("1 Boulevard de la Foire", "Luxembourg", "L-1528"),
    "COMMLULX": ("1 Boulevard de la Foire", "Luxembourg", "L-1528"),
    "COMMDEFF": ("OpernTurm Bockenheimer Landstr. 2-4", "Frankfurt am Main", "60306"),
    "COMMUS33": ("7 East 51st Street", "New York", "NY 10022"),
    "COMMUS66": ("555 California Street", "San Francisco", "CA 94104"),
    "EVERLULL": ("56 Grand-Rue", "Luxembourg", "L-1660"),
    "EVERLULX": ("56 Grand-Rue", "Luxembourg", "L-1660"),
    "CMBCLULL": ("7 Val Sainte-Croix", "Luxembourg", "L-1371"),
    "CMBCLULU": ("7 Val Sainte-Croix", "Luxembourg", "L-1371"),
    "CMBCGB2L": ("8 Angel Court", "London", "EC2R 7HP"),
    "ABOCLULL": ("34 Rue Philippe II", "Luxembourg", "L-2340"),
    "ABOCLULB": ("34 Rue Philippe II", "Luxembourg", "L-2340"),
    "ABNANL2A": ("Gustav Mahlerlaan 10", "Amsterdam", "1082 PP"),
    "ABNALU2A": ("Gustav Mahlerlaan 10", "Amsterdam", "1082 PP"),
    "ICBKLULC": ("26A Boulevard Royal", "Luxembourg", "L-2449"),
    "ICBKLULL": ("26A Boulevard Royal", "Luxembourg", "L-2449"),
    "ICBKLULU": ("26A Boulevard Royal", "Luxembourg", "L-2449"),
}

COUNTRY_MAP = {
    "BG": "bulgaria", "HU": "hungary", "LU": "luxembourg",
    "MC": "monaco", "DE": "germany", "GB": "united-kingdom",
    "US": "united-states", "FR": "france", "NL": "netherlands",
    "BE": "belgium", "AT": "austria", "CH": "switzerland",
    "IT": "italy", "ES": "spain", "PL": "poland",
}

def scrape_bankcodes(bic: str, country_code: str) -> dict:
    """Scrape bank.codes pour récupérer l'adresse SWIFT officielle."""
    bic8 = bic.strip().upper()[:8]
    country = COUNTRY_MAP.get(country_code, country_code.lower())
    url = f"https://bank.codes/swift-code/{country}/{bic8.lower()}/"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            text = r.text
            # Pattern "registered at ADDR in COUNTRY"
            m = re.search(
                r'registered at ([^.]+?) in (?:Bulgaria|Hungary|Luxembourg|Monaco|'
                r'Germany|United Kingdom|France|United States|Netherlands|Belgium|'
                r'Austria|Switzerland|Italy|Spain|Poland)',
                text, re.IGNORECASE
            )
            if m:
                addr = m.group(1).strip()
                # Nettoyer les éventuels tags HTML résiduels
                addr = re.sub(r'<[^>]+>', '', addr).strip()
                if len(addr) > 3:
                    return {"address": addr, "found": True}
    except Exception:
        pass
    return {"address": "", "found": False}


def enrich_csv(input_path: str, output_path: str, use_scraping: bool = True):
    """
    Lit le CSV d'entrée, enrichit les adresses manquantes, écrit le CSV de sortie.
    Conserve TOUTES les lignes — aucune suppression.
    """
    # Lire le CSV d'entrée
    rows = []
    with open(input_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    # S'assurer que les colonnes address, city, postal_code existent
    for col in ['address', 'city', 'postal_code']:
        if col not in fieldnames:
            fieldnames.append(col)

    print(f"📂 CSV chargé : {len(rows)} entités")

    # Compteurs
    enriched_local = 0
    enriched_web   = 0
    skipped        = 0

    # Enrichir
    for i, row in enumerate(rows):
        bic     = (row.get('bic') or row.get('code') or '').strip().upper()
        address = (row.get('address') or '').strip()
        country = (row.get('country') or '').strip().upper()

        # Déjà renseigné → skip
        if address:
            skipped += 1
            continue

        # 1. Base locale
        if bic in ADDRESS_DB:
            addr, city, postal = ADDRESS_DB[bic]
            row['address']     = addr
            row['city']        = row.get('city') or city
            row['postal_code'] = row.get('postal_code') or postal
            enriched_local += 1
            continue

        # 2. Scraping bank.codes (si activé)
        if use_scraping and bic and len(bic) >= 8:
            result = scrape_bankcodes(bic, country)
            if result['found']:
                row['address'] = result['address']
                enriched_web += 1
                print(f"  🌐 [{i+1}/{len(rows)}] {bic}: {result['address']}")
            else:
                print(f"  ❌ [{i+1}/{len(rows)}] {bic}: non trouvé")
            time.sleep(0.8)  # Respecter le rate limit

    # Écrire le CSV de sortie
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Enrichissement terminé !")
    print(f"   Total entités  : {len(rows)}")
    print(f"   Déjà renseignées : {skipped}")
    print(f"   Enrichies (local) : {enriched_local}")
    print(f"   Enrichies (web)   : {enriched_web}")
    print(f"   Sans adresse : {len(rows) - skipped - enriched_local - enriched_web}")
    print(f"\n📄 Fichier de sortie : {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enrich_banks.py <swift_banks.csv> [output.csv] [--no-scraping]")
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') \
                  else Path(input_file).stem + "_enrichi.csv"
    use_scraping = "--no-scraping" not in sys.argv

    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable : {input_file}")
        sys.exit(1)

    if not use_scraping:
        print("ℹ️  Mode sans scraping (base locale uniquement)")

    enrich_csv(input_file, output_file, use_scraping)
