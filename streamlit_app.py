"""DPS : interface Streamlit.

Lancer : streamlit run streamlit_app.py
Utilise les mêmes moteurs que le reste du projet (dps_foncier.py et droit_tunisien.py).
L'onglet Law Guru est un agent conversationnel (agent_juridique.py).
"""

import base64
import html
import os

import streamlit as st

from agent_juridique import ACCUEIL, ACCUEIL_HORS_CONNEXION, GUIDE_DOSSIER, MODELES, NOM, repondre, reponse_locale
from dps_foncier import (
    Operation,
    cours_action_nouvelle,
    dilution_apport_immeuble,
    simulation_associe,
    valeur_droit_periode,
)

try:
    import anthropic
except ImportError:  # l'agent reste disponible en mode hors connexion
    anthropic = None

st.set_page_config(page_title="DPS Tunisie", page_icon="§", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700;800&display=swap');
:root { --bleu:#4B6F9E; --bleu-fonce:#2F4C75; --creme:#E9E5D6; --creme-clair:#F4F1E6; --encre:#1F2F46; --muet:#5B6B84; --rouge:#A93232; --ambre:#B8862A; --vert:#2F6B57; --filet:rgba(75,111,158,.35); }
html, body, .stApp, [class*="css"] { font-family:'DM Sans', sans-serif; }

/* Fond animé : nappes de couleur qui tournent et dérivent derrière la page */
.stApp { background:var(--creme); color:var(--encre); }
.stApp::before, .stApp::after { content:""; position:fixed; z-index:0; pointer-events:none; inset:-30%; will-change:transform; }
.stApp::before {
  background:
    radial-gradient(38% 38% at 22% 28%, rgba(75,111,158,.62), rgba(75,111,158,0) 70%),
    radial-gradient(34% 34% at 78% 22%, rgba(201,154,46,.46), rgba(201,154,46,0) 70%),
    radial-gradient(40% 40% at 72% 78%, rgba(47,76,117,.46), rgba(47,76,117,0) 70%);
  filter:blur(28px); animation:aurore 16s ease-in-out infinite alternate;
}
.stApp::after {
  background:
    radial-gradient(30% 30% at 30% 75%, rgba(120,150,190,.50), rgba(120,150,190,0) 70%),
    radial-gradient(28% 28% at 85% 55%, rgba(255,255,255,.55), rgba(255,255,255,0) 70%);
  filter:blur(36px); animation:aurore2 22s ease-in-out infinite alternate;
}
.brand { margin:0 0 12px; }
.brand .logo { display:inline-block; line-height:0; background:#fff; border:1px solid var(--filet); border-radius:12px; padding:7px 16px; box-shadow:0 4px 16px rgba(47,76,117,.12); }
.brand .logo img { height:50px; width:auto; }
@media (max-width:700px) { .brand .logo img { height:40px; } }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] { background:transparent !important; position:relative; z-index:1; }
@keyframes aurore { 0% { transform:translate3d(-7%,-5%,0) rotate(0deg) scale(1); } 50% { transform:translate3d(6%,7%,0) rotate(20deg) scale(1.15); } 100% { transform:translate3d(9%,-6%,0) rotate(-16deg) scale(1.05); } }
@keyframes aurore2 { 0% { transform:translate3d(8%,6%,0) rotate(0deg) scale(1.1); } 100% { transform:translate3d(-9%,-7%,0) rotate(-24deg) scale(.95); } }
@keyframes monte { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
@media (prefers-reduced-motion: reduce) { .stApp::before, .stApp::after, * { animation:none !important; transition:none !important; } }

.block-container { padding-top:3.2rem; max-width:1280px; }
footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDeployButton"] { visibility:hidden; }
h1,h2,h3,h4 { font-family:'Playfair Display', serif !important; color:var(--bleu) !important; font-weight:700 !important; letter-spacing:-0.01em; }
h3 { font-size:1.5rem !important; }

.hero { border-bottom:1px solid var(--filet); padding:2px 0 16px; margin-bottom:10px; animation:monte .7s ease both; }
.hero .kicker { text-transform:uppercase; letter-spacing:.16em; font-size:.76rem; font-weight:700; color:var(--bleu); }
.hero .titre { font-family:'Playfair Display', serif; font-weight:700; font-size:clamp(2rem,4.4vw,3.2rem); line-height:1.05; color:var(--bleu-fonce); margin:.3rem 0 0; letter-spacing:-0.02em; }

button[data-baseweb="tab"] { font-weight:600; color:var(--muet); font-size:1rem; }
button[data-baseweb="tab"][aria-selected="true"] { color:var(--bleu-fonce); }

/* Champs : même hauteur, étiquettes alignées */
[data-testid="stWidgetLabel"] { min-height:1.5rem; }
[data-testid="stWidgetLabel"] p { font-weight:600; font-size:.86rem; color:var(--encre); }
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input { font-variant-numeric:tabular-nums; }
[data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.50); border-color:var(--filet) !important; border-radius:10px !important; }
.section { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; color:var(--bleu); margin:.2rem 0 .5rem; }

/* Chiffres clés : sobres, filet bleu en haut, chiffres en serif */
[data-testid="stMetric"] { background:transparent; border-top:2px solid var(--bleu); padding:10px 2px 4px; min-height:96px; animation:monte .6s ease both; }
[data-testid="stMetricLabel"] { min-height:2.4em; }
[data-testid="stMetricLabel"] p { color:var(--muet) !important; font-size:.74rem; text-transform:uppercase; letter-spacing:.08em; font-weight:600; white-space:normal; line-height:1.3; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color:var(--bleu-fonce) !important; font-family:'Playfair Display', serif; font-weight:700; font-size:1.85rem; white-space:normal; line-height:1.1; }

/* Verdicts : une ligne sobre avec un filet de couleur, pas de bloc plein */
.verdict { border-left:3px solid var(--bleu); background:rgba(255,255,255,.55); padding:11px 16px; margin:12px 0; line-height:1.45; font-weight:600; color:var(--encre); animation:monte .5s ease both; }
.verdict.ok { border-left-color:var(--vert); }
.verdict.warn { border-left-color:var(--ambre); }
.verdict.no { border-left-color:var(--rouge); }

[data-testid="stExpander"] { border:1px solid var(--filet); border-radius:10px; background:rgba(244,241,230,.7); }
[data-testid="stExpander"] summary p { font-weight:600; color:var(--bleu-fonce); font-size:.95rem; }

/* Boutons : discrets, alignés à gauche */
.stButton > button { text-align:left; justify-content:flex-start; border-radius:8px; border:1px solid var(--filet); background:rgba(255,255,255,.55); font-weight:500; color:var(--encre); padding:.55rem .85rem; height:auto; transition:border-color .2s ease, background .2s ease, transform .2s ease; }
.stButton > button > div, .stButton > button span { width:100%; justify-content:flex-start; }
.stButton > button [data-testid="stMarkdownContainer"], .stButton > button p { text-align:left; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; display:block; line-height:1.35; }
[data-testid="stButtonGroup"], [data-testid="stButtonGroup"] > div { flex-wrap:wrap !important; row-gap:6px; }
.stButton > button:hover { border-color:var(--bleu); background:#fff; color:var(--bleu-fonce); transform:translateX(3px); }

/* Law Guru : panneau de conversation */
.lg-tete { display:flex; align-items:center; gap:14px; padding:2px 0 12px; border-bottom:1px solid var(--filet); margin-bottom:6px; }
.lg-avatar { width:46px; height:46px; border-radius:50%; background:radial-gradient(circle at 30% 25%, #7C9CC6, var(--bleu-fonce) 70%); color:var(--creme); display:flex; align-items:center; justify-content:center; font-family:'Playfair Display', serif; font-weight:700; font-size:1.05rem; letter-spacing:.02em; flex:none; }
.lg-nom { font-family:'Playfair Display', serif; font-weight:700; font-size:1.3rem; color:var(--bleu-fonce); line-height:1.1; }
.lg-sous { font-size:.8rem; color:var(--muet); }
.lg-etat { margin-left:auto; font-size:.78rem; color:var(--muet); display:flex; align-items:center; gap:6px; }
.lg-etat i { width:8px; height:8px; border-radius:50%; background:var(--vert); display:inline-block; }
.lg-etat i.hors { background:var(--ambre); }
.lg-pied { text-align:center; color:var(--muet); font-size:.76rem; margin-top:6px; }
[data-testid="stChatMessage"] { background:rgba(255,255,255,.72); border:1px solid var(--filet); border-radius:14px; padding:12px 16px; animation:monte .4s ease both; }
[data-testid="stChatMessage"]:has(.u-msg) { background:var(--bleu-fonce); border-color:var(--bleu-fonce); }
[data-testid="stChatMessage"]:has(.u-msg) * { color:#fff !important; }
[data-testid="stChatInput"] { border-radius:14px; }

/* Thème clair imposé : si le navigateur est en mode sombre et que .streamlit/config.toml est absent, rien ne devient noir */
:root, .stApp { color-scheme:light; }
.stApp [data-testid="stMarkdownContainer"] p, .stApp [data-testid="stMarkdownContainer"] li { color:var(--encre); }
[data-testid="stChatMessage"]:not(:has(.u-msg)) * { color:var(--encre) !important; }
[data-testid="stChatMessage"]:not(:has(.u-msg)) { background:rgba(255,255,255,.88); }
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"], [data-testid="stBottom"] > div { background:transparent !important; }
[data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea { background:#fff !important; color:var(--encre) !important; -webkit-text-fill-color:var(--encre); }
[data-testid="stChatInput"] { border:1px solid var(--filet); }
[data-testid="stChatInput"] textarea::placeholder, input::placeholder { color:var(--muet) !important; -webkit-text-fill-color:var(--muet); opacity:1; }
[data-testid="stChatInput"] button { background:var(--bleu-fonce) !important; }
[data-testid="stChatInput"] button svg { fill:#fff !important; color:#fff !important; }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, [data-testid="stNumberInputContainer"] { background:#fff !important; color:var(--encre) !important; border-color:var(--filet) !important; }
[data-baseweb="input"] input, [data-baseweb="base-input"] input, [data-baseweb="select"] input, [data-baseweb="select"] div { color:var(--encre) !important; -webkit-text-fill-color:var(--encre); }
[data-baseweb="input"] svg, [data-baseweb="select"] svg, [data-testid="stNumberInput"] button svg { fill:var(--bleu-fonce) !important; color:var(--bleu-fonce) !important; }
[data-testid="stNumberInput"] button { background:var(--creme-clair) !important; border-color:var(--filet) !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] { background:#fff !important; }
[data-baseweb="popover"] li, [data-baseweb="menu"] li { background:#fff !important; color:var(--encre) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover { background:var(--creme-clair) !important; }
[data-testid="stExpander"] details, [data-testid="stExpander"] summary { background:transparent !important; color:var(--bleu-fonce) !important; }
[data-testid="stExpander"] summary:hover { background:rgba(255,255,255,.6) !important; }
[data-testid="stExpander"] summary svg { fill:var(--bleu-fonce) !important; color:var(--bleu-fonce) !important; }
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] { color:var(--muet) !important; }
button[data-testid="stBaseButton-pills"] { background:rgba(255,255,255,.7) !important; border:1px solid var(--filet) !important; }
button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pills"] * { color:var(--bleu-fonce) !important; }
button[data-testid="stBaseButton-pillsActive"] { background:var(--bleu-fonce) !important; border:1px solid var(--bleu-fonce) !important; }
button[data-testid="stBaseButton-pillsActive"], button[data-testid="stBaseButton-pillsActive"] * { color:#fff !important; }
.stButton > button:disabled { background:rgba(255,255,255,.35); color:var(--muet); }

.pied { margin-top:2.5rem; padding-top:1rem; border-top:1px solid var(--filet); text-align:center; color:var(--muet); font-size:.85rem; }
.pied b { font-family:'Playfair Display', serif; color:var(--bleu-fonce); font-size:1.05rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def avatar(lettres, fond, texte):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="%s"/>'
        '<text x="32" y="41" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="26" fill="%s">%s</text></svg>'
        % (fond, texte, lettres)
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


AVATAR_AGENT = avatar("LG", "#2F4C75", "#E9E5D6")
AVATAR_USER = avatar("V", "#E9E5D6", "#2F4C75")


def fmt(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(x, d=2):
    return fmt(x * 100, d) + " %"


def montant(x):
    return fmt(x, 0 if abs(x) >= 1000 else 3)


def bandeau(texte, ton="ok"):
    st.markdown(f'<div class="verdict {ton}">{html.escape(texte)}</div>', unsafe_allow_html=True)


def section(titre):
    st.markdown(f'<div class="section">{html.escape(titre)}</div>', unsafe_allow_html=True)


def _logo_html() -> str:
    """Logo IHEC Carthage (web/logo-ihec.png), ignoré si le fichier est absent."""
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "logo-ihec.png")
    try:
        with open(chemin, "rb") as f:
            data = base64.b64encode(f.read()).decode()
    except OSError:
        return ""
    return f'<div class="brand"><span class="logo"><img src="data:image/png;base64,{data}" alt="IHEC Carthage"></span></div>'


st.markdown(
    _logo_html() + '<div class="hero"><div class="kicker">DPS · Tunisie</div>'
    '<div class="titre">Droit préférentiel de souscription</div></div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["Droit de souscription", "Apport d'immeuble", NOM])

# ---------------------------------------------------------------- Onglet 1
with tab1:
    with st.container(border=True):
        section("Opération")
        r1 = st.columns(3)
        A = r1[0].number_input("Actions anciennes (A)", min_value=0, value=1_000_000, step=1000, key="s_A")
        C = r1[1].number_input("Cours de clôture la veille (DT)", min_value=0.0, value=8.0, step=0.1, format="%.3f", key="s_C")
        PE = r1[2].number_input("Prix d'émission (DT)", min_value=0.0, value=6.5, step=0.1, format="%.3f", key="s_PE")
        r2 = st.columns(3)
        p = r2[0].number_input("Actions nouvelles offertes", min_value=1, value=1, step=1, key="s_p")
        q = r2[1].number_input("Pour actions anciennes", min_value=1, value=2, step=1, key="s_q")
        D = r2[2].number_input(
            "Différence de jouissance (DT)", min_value=0.0, value=0.35, step=0.05, format="%.3f", key="s_D",
            help="Dividende que les actions nouvelles ne touchent pas. Faute d'information, la Bourse retient le dividende de l'année précédente.",
        )
        section("Position et marché")
        r3 = st.columns(3)
        det = r3[0].number_input("Actions détenues", min_value=0, value=10_000, step=100, key="s_det")
        marche = r3[1].number_input(
            "Prix du droit sur le marché (DT)", min_value=0.0, value=0.0, step=0.01, format="%.3f", key="s_marche",
            help="0 pour utiliser la valeur théorique du droit.",
        )
        ligne = r3[2].number_input(
            "Cours de la ligne principale (DT)", min_value=0.0, value=8.03, step=0.01, format="%.3f", key="s_ligne",
            help="Cours de référence pendant la période de souscription. 0 pour ne pas le calculer.",
        )

    st.subheader("Que faire de vos droits")
    try:
        op = Operation(A, C, PE, p, q, D)
        sim = simulation_associe(op, det, marche if marche > 0 else None)
        m = st.columns(4)
        m[0].metric("Cours de référence après détachement", fmt(sim["cours_theorique_ex_droit"], 3) + " DT")
        m[1].metric("Cours théorique du droit", fmt(sim["valeur_droit_theorique"], 3) + " DT")
        m[2].metric("Actions nouvelles si tout est exercé", fmt(A * p / q, 0))
        m[3].metric("Participation avant l'opération", pct(sim["participation_initiale"]))

        if ligne > 0:
            st.write(
                f"Droit pendant la période (ligne principale à {fmt(ligne, 3)} DT) : "
                f"**{fmt(valeur_droit_periode(op, ligne), 3)} DT**. "
                f"Action nouvelle non assimilée : **{fmt(cours_action_nouvelle(ligne, D), 3)} DT**."
            )

        g = {k: sim[k]["gain_ou_perte"] for k in ("exercer", "vendre", "expirer")}
        tableau = [
            {"Choix": "Exercer les droits", "Participation finale": pct(sim["exercer"]["participation_finale"]), "Gain ou perte (DT)": montant(g["exercer"])},
            {"Choix": "Vendre les droits", "Participation finale": pct(sim["vendre"]["participation_finale"]), "Gain ou perte (DT)": montant(g["vendre"])},
            {"Choix": "Laisser expirer", "Participation finale": pct(sim["expirer"]["participation_finale"]), "Gain ou perte (DT)": montant(g["expirer"])},
        ]
        st.dataframe(tableau, hide_index=True, width="stretch")

        if abs(g["exercer"] - g["vendre"]) < 0.005:
            bandeau(f"Exercer et vendre les droits donnent le même résultat à ce prix. Laisser expirer fait perdre {montant(-g['expirer'])} DT.")
        elif g["vendre"] > g["exercer"]:
            bandeau(f"Vendre les droits rapporte {montant(g['vendre'] - g['exercer'])} DT de plus que les exercer.")
        else:
            bandeau(f"Exercer rapporte {montant(g['exercer'] - g['vendre'])} DT de plus que vendre les droits, car le droit est coté sous sa valeur théorique.")
        cout = det * p / q * PE
        st.caption(
            f"Exercer demande de payer {montant(cout)} DT pour souscrire {fmt(det * p / q, 0)} actions nouvelles. "
            "Valeurs avant frais de courtage et fiscalité."
        )
    except ValueError as e:
        bandeau(str(e), "no")

# ---------------------------------------------------------------- Onglet 2
with tab2:
    with st.container(border=True):
        section("Apport en nature")
        c = st.columns(5)
        aN = c[0].number_input("Actions anciennes", min_value=0, value=1_000_000, step=1000, key="a_N")
        acours = c[1].number_input("Cours (DT)", min_value=0.0, value=20.0, step=0.5, key="a_cours")
        aprix = c[2].number_input("Prix d'émission (DT)", min_value=0.0, value=20.0, step=0.5, key="a_prix")
        adecl = c[3].number_input("Valeur déclarée (DT)", min_value=0.0, value=5_000_000.0, step=100_000.0, key="a_decl")
        areel = c[4].number_input("Valeur réelle (DT)", min_value=0.0, value=3_500_000.0, step=100_000.0, key="a_reel",
                                  help="Valeur réelle ou expertisée de l'immeuble.")

    st.subheader("Effet sur les autres associés")
    try:
        r = dilution_apport_immeuble(aN, acours, aprix, adecl, areel)
        m = st.columns(4)
        m[0].metric("Actions émises à l'apporteur", fmt(r["actions_emises_a_l_apporteur"], 0))
        m[1].metric("Part de l'apporteur", pct(r["part_apporteur"]))
        m[2].metric("Perte par action des autres", fmt(r["perte_par_action_pour_les_autres"], 3) + " DT")
        m[3].metric("Perte totale des autres associés", montant(r["perte_totale_autres_associes"]) + " DT")
        st.progress(min(max(r["part_apporteur"], 0.0), 1.0), text=f"Apporteur {pct(r['part_apporteur'])}, autres associés {pct(1 - r['part_apporteur'])}")
        st.write(
            f"Valeur par action après l'opération : **{fmt(r['valeur_par_action_apres'], 3)} DT**. "
            f"Écart entre valeur déclarée et réelle : **{montant(r['ecart_valeur_declaree_reelle'])} DT**."
        )
        if r["perte_totale_autres_associes"] > 0.005:
            bandeau(f"Les autres associés perdent {montant(r['perte_totale_autres_associes'])} DT à cause de la surévaluation.", "no")
        else:
            bandeau("L'immeuble est évalué à sa valeur réelle : les autres associés ne perdent rien.")
        st.caption("Quand l'immeuble est surévalué, l'apporteur reçoit plus d'actions que son bien ne le justifie. Les autres associés portent la différence.")
    except ValueError as e:
        bandeau(str(e), "no")

# ---------------------------------------------------------------- Onglet 3 : Law Guru
CATEGORIES = {
    "Articles": [
        "Que dit l'article 301 sur le délai de souscription ?",
        "Que prévoit l'article 300 sur la suppression du DPS ?",
        "Que dit l'article 295 sur la libération du capital ?",
        "Que prévoit l'article 306 pour un apport en nature ?",
    ],
    "Notions": [
        "Qu'est-ce que le DPS et à quoi sert-il ?",
        "Quelle différence entre souscription irréductible et réductible ?",
        "Qu'est-ce que la différence de jouissance ?",
        "Exercer, vendre ou laisser expirer ses droits : que choisir ?",
    ],
    "Calculs": [
        "Calcule la valeur du droit : 1 000 000 d'actions, cours 8, émission 6,5, 1 pour 2, différence de jouissance 0,35",
        "Un immeuble déclaré 5 000 000 DT vaut 3 500 000 DT, avec 1 000 000 d'actions à 20 DT : combien perdent les autres associés ?",
    ],
    "Mon dossier": [
        "Ma SA veut supprimer le DPS pour un apport d'immeuble immatriculé. Que dois-je vérifier ?",
        "Je prépare une augmentation en numéraire dans une SARL. Quelles sont les étapes et les délais ?",
        "J'apporte un immeuble non immatriculé : quels sont les risques ?",
    ],
    "Recours": [
        "Quels recours ont les actionnaires minoritaires ?",
        "Dans quels cas une augmentation de capital peut-elle être annulée ?",
    ],
}


def poser(texte):
    st.session_state["en_attente"] = texte


def guide_dossier():
    st.session_state["chat"] += [
        {"role": "user", "content": "Je veux faire passer mon dossier en revue."},
        {"role": "assistant", "content": GUIDE_DOSSIER, "outils": []},
    ]


def effacer():
    st.session_state["chat"] = []


def cle_api():
    return st.session_state.get("cle_api", "").strip() or os.environ.get("ANTHROPIC_API_KEY", "").strip()


def obtenir_reponse(historique):
    """Renvoie (texte, outils utilisés). Bascule en mode hors connexion si l'agent est indisponible."""
    cle = cle_api()
    if cle and anthropic is not None:
        try:
            client = anthropic.Anthropic(api_key=cle)
            return repondre(client, MODELES[st.session_state.get("modele", list(MODELES)[0])], historique)
        except anthropic.AuthenticationError:
            texte, _ = reponse_locale(historique[-1]["content"])
            return "La clé API a été refusée. Voici une réponse hors connexion.\n\n" + texte, ["Réponse hors connexion"]
        except anthropic.APIError as e:
            texte, _ = reponse_locale(historique[-1]["content"])
            return f"{NOM} n'a pas répondu ({type(e).__name__}). Voici une réponse hors connexion.\n\n" + texte, ["Réponse hors connexion"]
    texte, _ = reponse_locale(historique[-1]["content"])
    return texte, ["Réponse hors connexion"]


def afficher_message(msg):
    with st.chat_message(msg["role"], avatar=AVATAR_AGENT if msg["role"] == "assistant" else AVATAR_USER):
        if msg["role"] == "user":
            st.markdown('<span class="u-msg"></span>', unsafe_allow_html=True)
        st.markdown(msg["content"])
        if msg.get("outils"):
            st.caption("Outils utilisés : " + " · ".join(dict.fromkeys(msg["outils"])))


with tab3:
    st.session_state.setdefault("chat", [])
    chat = st.session_state["chat"]
    connecte = bool(cle_api()) and anthropic is not None
    gauche, droite = st.columns([4, 7], gap="large")

    # ---- Questions guidées, rangées par thème
    with gauche:
        section("Questions guidées")
        theme = st.pills("Thème", list(CATEGORIES), default="Articles", key="theme", label_visibility="collapsed") or "Articles"
        for i, question in enumerate(CATEGORIES[theme]):
            st.button(question, key=f"q_{theme}_{i}", on_click=poser, args=(question,), width="stretch")
        if theme == "Mon dossier":
            st.button("Décrire mon dossier pas à pas", key="guide", on_click=guide_dossier, width="stretch")
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
        with st.expander(f"Connexion de {NOM}", expanded=not connecte):
            st.text_input("Clé API Anthropic", type="password", key="cle_api", placeholder="sk-ant-...",
                          help="Reste dans cet onglet du navigateur, n'est jamais enregistrée et n'est envoyée qu'à l'API Anthropic. Vous pouvez aussi définir la variable ANTHROPIC_API_KEY avant de lancer l'application.")
            st.selectbox("Modèle", list(MODELES), key="modele")
            st.caption(
                f"Avec une clé, {NOM} comprend vos messages, lit les articles, contrôle votre dossier et fait les calculs "
                "avec les mêmes moteurs que les autres onglets. Sans clé, il répond à partir des textes lus."
            )
        st.button("Effacer la conversation", on_click=effacer, width="stretch", disabled=not chat)

    # ---- Panneau de conversation
    with droite:
        with st.container(border=True):
            etat = ("<i></i>En ligne" if connecte else "<i class='hors'></i>Hors connexion")
            st.markdown(
                f'<div class="lg-tete"><div class="lg-avatar">LG</div><div><div class="lg-nom">{NOM}</div>'
                f'<div class="lg-sous">Assistant juridique · DPS en Tunisie</div></div><div class="lg-etat">{etat}</div></div>',
                unsafe_allow_html=True,
            )
            zone = st.container(height=520, border=False)
            with zone:
                afficher_message({"role": "assistant", "content": ACCUEIL + ("" if connecte else ACCUEIL_HORS_CONNEXION)})
                for msg in chat:
                    afficher_message(msg)
            prompt = st.chat_input("Écrire un message")
            st.markdown(f'<div class="lg-pied">{NOM} peut se tromper. Vérifiez auprès d\'un avocat ou d\'un notaire tunisien.</div>', unsafe_allow_html=True)

        prompt = prompt or st.session_state.pop("en_attente", None)
        if prompt:
            chat.append({"role": "user", "content": prompt})
            with zone:
                afficher_message(chat[-1])
                with st.chat_message("assistant", avatar=AVATAR_AGENT):
                    with st.spinner("Analyse en cours..."):
                        texte, outils = obtenir_reponse(chat)
            chat.append({"role": "assistant", "content": texte, "outils": outils})
            st.rerun()

st.markdown(
    '<div class="pied">Conçu &amp; développé par <b>M.A</b> · DPS</div>',
    unsafe_allow_html=True,
)
