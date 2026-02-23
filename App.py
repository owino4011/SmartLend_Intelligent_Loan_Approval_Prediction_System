import streamlit as st
import pandas as pd
import joblib
from io import BytesIO
from pathlib import Path
from src.utils import get_logger
from auth import auth as auth_logic
from dashboards import admin_dashboard
import uuid
import time
import requests

#Logger
logger = get_logger("streamlit", "logs/streamlit_output.log")

#Page setup
st.set_page_config(
    page_title="SMARTLEND: INTELLIGENT LOAN APPROVAL PREDICTOR",
    page_icon="💰",
    layout="centered"
)

#Compatibility helper for rerun
def safe_rerun():
    try:
        if hasattr(st, "rerun"):
            st.rerun()
            return
    except Exception:
        pass
    try:
        if hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params(_rerun=str(uuid.uuid4()))
            return
    except Exception:
        pass
    st.stop()

#AUTH STATE
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

#LOGIN / SIGNUP / RESET LOGIC
if not st.session_state.authenticated:

    IMAGE_URL = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4"
    cb = int(time.time())

    #Simple inline SVG used as an immediate watermark (no network)
    svg_data = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'>"
        "<g fill='none' stroke='%23006b5a' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'>"
        "<circle cx='36' cy='40' r='18' />"
        "<rect x='64' y='28' width='36' height='24' rx='4' ry='4' />"
        "<path d='M56 78c6-8 18-8 24 0' />"
        "</g>"
        "<text x='60' y='106' font-size='12' text-anchor='middle' fill='%23006b5a' font-family='sans-serif'>SMARTLEND</text>"
        "</svg>"
    )
    svg_data_uri = "data:image/svg+xml;utf8," + svg_data

    login_bg_html = (
        "<div id=\"smartlend-login-bg\" style=\""
        "position: fixed;"
        "inset: 0;"
        "width: 100%;"
        "height: 100%;"
        #layered backgrounds: gradient (tint), embedded svg watermark (immediate), large photo (loads)
        "background-image: "
        "linear-gradient(180deg, rgba(3,169,244,0.14), rgba(0,150,136,0.10)), "
        "url('" + svg_data_uri + "'), "
        "url('" + IMAGE_URL + "?q=80&w=1920&auto=format&fit=crop&cb=" + str(cb) + "');"
        "background-repeat: no-repeat, no-repeat, no-repeat;"
        #watermark small and centered (middle layer), photo covers entire area (bottom layer)
        "background-position: center center, center center, center center;"
        "background-size: cover, 18% auto, cover;"
        #mild adjustment so watermark & photo look subtle
        "filter: saturate(1.04) contrast(1.02) brightness(1.01);"
        "z-index: -99999;"
        "pointer-events: none;"
        "\"></div>\n\n"
        "<style>\n"
        "/* Ensure Streamlit containers are transparent so the fixed DIV shows through */\n"
        "html, body, .stApp, .block-container, [data-testid=\"stAppViewContainer\"], .main { background: transparent !important; }\n"
        "header, footer, div[data-testid=\"stToolbar\"] { background: transparent !important; }\n\n"
        "/* Define the authoritative auth-message color here (intense green to match main app) */\n"
        ":root { --auth-msg-color: #007a33; }\n\n"
        "/* Frosted glass style applied to the main block container so text stays readable */\n"
        ".stApp .block-container {\n"
        "    background: rgba(255, 255, 255, 0.86) !important;\n"
        "    -webkit-backdrop-filter: blur(6px) saturate(108%) !important;\n"
        "    backdrop-filter: blur(6px) saturate(108%) !important;\n"
        "    border-radius: 14px !important;\n"
        "    padding: 2rem !important;\n"
        "    box-shadow: 0 12px 40px rgba(2,12,40,0.18) !important;\n"
        "    position: relative !important;\n"
        "    z-index: 2 !important;\n"
        "}\n\n"
        "/* Keep the teal button color exactly as requested (#009999) for action buttons */\n"
        ":root { --login-btn: #009999; --login-btn-hover: #00b3b3; }\n"
        "div.stButton > button:first-child, .stButton > button {\n"
        "    border-radius: 10px !important;\n"
        "    background-color: var(--login-btn) !important;\n"
        "    color: white !important;\n"
        "    font-weight: 500 !important;\n"
        "    padding: 0.6rem 1.2rem !important;\n"
        "    transition: 0.18s !important;\n"
        "    border: none !important;\n"
        "    box-shadow: 0 6px 18px rgba(0,0,0,0.06) !important;\n"
        "}\n"
        "div.stButton > button:first-child:hover, .stButton > button:hover {\n"
        "    background-color: var(--login-btn-hover) !important;\n"
        "    color: white !important;\n"
        "}\n\n"
        "/* Auth/error message class — now uses the intense green */\n"
        ".msg-blue { color: var(--auth-msg-color) !important; font-weight: 600 !important; margin: 8px 0 !important; }\n\n"
        "/* Radio accent (circle) color to match login button teal */\n"
        "input[type=\"radio\"] { accent-color: var(--login-btn) !important; }\n\n"
        "/* Ensure text remains dark/readable */\n"
        ".stApp .stMarkdown, .stApp .stText, .stApp .stTitle, .stApp h1, .stApp h2, .stApp h3 { color: #0b0b0b !important; }\n\n"
        "@media (max-width: 1000px) {\n"
        "    .stApp .block-container { padding: 1rem !important; border-radius: 10px !important; }\n"
        "}\n"
        "</style>\n"
    )

    st.markdown(login_bg_html, unsafe_allow_html=True)
  
    st.markdown(
        """
        <style>
        .smartlend-hero {
            background: linear-gradient(135deg, #007a33 0%, #005a28 100%);
            padding: 28px 28px 24px 28px;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.18);
            margin-bottom: 1.2rem;
            position: relative;
            overflow: hidden;
        }
        .smartlend-hero::after {
            content: "";
            position: absolute;
            right: -60px;
            top: -60px;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(255,255,255,0.12), transparent 70%);
            transform: rotate(25deg);
        }
        .smartlend-title {
            color: white;
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 6px;
            letter-spacing: 0.3px;
        }
        .smartlend-sub {
            color: rgba(255,255,255,0.92);
            font-size: 15px;
            line-height: 1.5;
        }
        @media (max-width: 640px) {
            .smartlend-title { font-size: 24px; }
            .smartlend-hero { padding: 22px; }
        }
        </style>
        <div class="smartlend-hero">
            <div class="smartlend-title">🔐 Welcome to SMARTLEND</div>
            <div class="smartlend-sub">
                Secure access to your intelligent loan services — sign in, create an account,
                or recover your password.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        /* Keep logout/login button consistent; reuse auth message color via CSS variable name 'msg-blue' */
        :root { --logout-color: #009999; --logout-color-hover: #00b3b3; --msg-blue: var(--auth-msg-color); }

        /* Apply rounded rectangle style & color (match logout button color) for action buttons on login page */
        div.stButton > button:first-child {
            border-radius: 10px;
            background-color: var(--logout-color);
            color: white;
            font-weight: 500;
            padding: 0.6rem 1.2rem;
            transition: 0.18s;
        }
        div.stButton > button:first-child:hover {
            background-color: var(--logout-color-hover);
            color: white;
        }

        /* Blue message style (reused class name) now wired to the intense green */
        .msg-blue {
            color: var(--msg-blue);
            font-weight: 600;
            margin: 8px 0;
        }

        /* Radio accent (circle) color to match logout button color */
        input[type="radio"] {
            accent-color: var(--logout-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    mode = st.radio("**Choose action**", ["Login", "Sign up", "Reset password"], key="auth_mode")
    email = st.text_input("Email", key="auth_email")

    #Show password input only for Login and Sign up (not for Reset password)
    if mode != "Reset password":
        password = st.text_input("Password", type="password", key="auth_password")
    else:
        #placeholder so later references don't error
        password = ""

    # Show role selector ONLY when Login is chosen (Option A)
    if mode == "Login":
        role_select = st.selectbox("**Login as**", ["Applicant", "Admin"], key="auth_role_select")
    else:
        role_select = None  # explicit placeholder; won't be used for Signup/Reset


    #LOGIN
    if mode == "Login" and st.button("Login"):
        if not email.strip() or not password:
            # Auth-colored message (replaces st.warning)
            st.markdown("<div class='msg-blue'>⚠️ Email and password required</div>", unsafe_allow_html=True)
        else:
            ok, msg, user = auth_logic.login_user(email.strip(), password)

            if not ok:
                #Keep original message text but render in auth color and add contextual instruction if suitable.
                msg_text = str(msg).strip()
                if "not found" in msg_text.lower() or "no account" in msg_text.lower():
                    st.markdown(f"<div class='msg-blue'>❗ {msg_text}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='msg-blue'>❗ {msg_text}</div>", unsafe_allow_html=True)
            else:
                #login succeeded; ensure role matches the role_select
                if role_select == "Admin":
                    if user.get("role") != "admin":
                        # Auth-colored role mismatch message
                        st.markdown("<div class='msg-blue'>🚫 This account is not an admin. Choose Applicant or use an admin account.</div>", unsafe_allow_html=True)
                    else:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        safe_rerun()
                else:  # Applicant
                    if user.get("role") != "applicant":
                        st.markdown("<div class='msg-blue'>🚫 This account is not an applicant. Choose Admin or use an applicant account.</div>", unsafe_allow_html=True)
                    else:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        safe_rerun()

    #SIGNUP (applicants only) ---
    if mode == "Sign up" and st.button("Create account"):
        # Signup creates applicants only (no role dropdown shown during Sign up per Option A)
        if not email.strip() or not password:
            st.markdown("<div class='msg-blue'>⚠️ Email and password required.</div>", unsafe_allow_html=True)
        else:
            ok, user_or_msg = auth_logic.signup_user(email.strip(), password)
            if ok:
                st.session_state.authenticated = True
                st.session_state.user = user_or_msg
                safe_rerun()
            else:
                st.markdown(f"<div class='msg-blue'>❗ {user_or_msg}</div>", unsafe_allow_html=True)

    #RESET PASSWORD (UX for both admin and applicants) 
    if mode == "Reset password":
        #request token
        if st.button("Request reset token"):
            if not email.strip():
                st.markdown("<div class='msg-blue'>📧 Email required — enter your account email to receive the reset token.</div>", unsafe_allow_html=True)
            else:
                ok, token_or_msg = auth_logic.request_reset(email.strip())
                if ok:
                    
                    st.success("Reset token:")
                    st.code(token_or_msg)
                    st.session_state.reset_token_requested = True
                    st.session_state.last_reset_token = token_or_msg
                else:
                    st.markdown(f"<div class='msg-blue'>❗ {token_or_msg}</div>", unsafe_allow_html=True)

        #show token + new password fields AFTER requesting
        if st.session_state.get("reset_token_requested"):
            st.markdown("### 🔑 Enter Reset Token & New Password")

            entered_token = st.text_input("Enter reset token", key="entered_reset_token")
            new_pw = st.text_input("New password", type="password", key="reset_new_password")

            if st.button("Confirm password reset"):
                if not entered_token.strip() or not new_pw.strip():
                    st.markdown("<div class='msg-blue'>⚠️ Token and new password required — please provide both.</div>", unsafe_allow_html=True)
                else:
                    ok, msg = auth_logic.reset_password(email.strip(), entered_token.strip(), new_pw.strip())
                    if ok:
                        st.success("Password reset successful. Please log in.")
                        #Clear reset session markers
                        st.session_state.reset_token_requested = False
                        st.session_state.last_reset_token = None
                    else:
                        st.markdown(f"<div class='msg-blue'>❗ {msg}</div>", unsafe_allow_html=True)

    st.stop()

#AFTER LOGIN

USER = st.session_state.user

with st.sidebar:
    st.markdown("### 🔐 Account")

    st.markdown(
        f"""
        <div style="margin-bottom:10px;">
            Logged in as<br>
            <strong>{USER['email']}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🚪 Logout"):
        st.session_state.clear()
        safe_rerun()

st.sidebar.markdown("---")

#ADMIN DASHBOARD
if USER.get("role") == "admin":
    admin_dashboard.show_admin()
    st.stop()   # ⛔ Prevent applicant UI & sidebar from rendering


#WELCOME MESSAGE
st.success(f"Welcome back, {USER['email']} 🎉")
from auth import db

#ORIGINAL APP CODE STARTS HERE
MODEL_PATH = "models/loan_approval_model.pkl"

# ------------------ Begin: model-download helper ------------------
MODEL_URL = "https://github.com/owino4011/SmartLend_Intelligent_Loan_Approval_Prediction_System/releases/download/v1/loan_approval_model.pkl"

def download_model_if_missing(model_path_str: str = MODEL_PATH, model_url: str = MODEL_URL):
    model_path = Path(model_path_str)
    if model_path.exists():
        return
    model_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with requests.get(model_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            chunk_size = 8192
            with open(model_path, "wb") as f:
                if total:
                    downloaded = 0
                    with st.spinner("Downloading model..."):
                        progress = st.progress(0)
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                pct = int(downloaded / total * 100)
                                progress.progress(min(pct, 100))
                else:
                    with st.spinner("Downloading model..."):
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
    except Exception as e:
        st.warning(f"Model download failed: {e}")
        raise

try:
    download_model_if_missing()
except Exception:
    # allow app to continue so joblib.load handles absence gracefully
    pass
# ------------------ End: model-download helper ------------------

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

#Hybrid Themed CSS
st.markdown(
    """
    <style>
    .stApp { font-family: 'Poppins', sans-serif; }
    .small-docs * { font-size: 12px !important; }
    @media (prefers-color-scheme: light) {
        :root {
            --box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            --title-bg: #007a33;
            --title-text: white;
            --subtitle-text: #003300;
            --button-bg: #009999;
            --button-bg-hover: #00b3b3;
            --button-text: white;
        }
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --box-shadow: 0 1px 4px rgba(255,255,255,0.2);
            --title-bg: #006622;
            --title-text: white;
            --subtitle-text: #c0ffd2;
            --button-bg: #00aaaa;
            --button-bg-hover: #00cccc;
            --button-text: black;
        }
    }
    .title-box {
        background-color: var(--title-bg);
        border-radius: 15px;
        padding: 15px 25px;
        display: flex;
        flex-direction: row;
        align-items: center;
        box-shadow: var(--box-shadow);
        text-align: left;
        gap: 10px;
    }
    .title-box .icon { font-size: 32px; }
    .title-box h1 { color: var(--title-text) !important; font-size: 28px !important; margin: 0; }
    .title-sub { font-size: 15px; color: var(--subtitle-text); margin: 0; padding-left: 42px; }
    div.stButton > button:first-child {
        background-color: var(--button-bg);
        color: var(--button-text);
        border-radius: 8px;
        border: none;
        font-weight: 500;
        transition: 0.3s;
        padding: 0.6rem 1.2rem;
    }
    div.stButton > button:first-child:hover {
        background-color: var(--button-bg-hover);
        color: var(--button-text);
    }
    .footer { text-align: center; font-size: 14px; color: gray; margin-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True
)

#Header
st.markdown(
    """
    <div class='title-box'>
        <span class='icon'>💰</span>
        <h1>SMARTLEND: INTELLIGENT LOAN APPROVAL PREDICTOR</h1>
    </div>
    <p class='title-sub'>Use this tool to get a quick loan approval prediction based on applicant & loan details.</p>
    """,
    unsafe_allow_html=True
)

#Load model
try:
    pipeline = joblib.load(MODEL_PATH)
except Exception as e:
    pipeline = None
    st.warning("⚠️ Model not loaded. Please ensure `models/loan_approval_model.pkl` exists.")
    logger.error("Model load failed: %s", e)

#Bounds & options
NUM_BOUNDS = {
    "person_age": {"min_value": 20, "max_value": 100, "median": 40},
    "person_income": {"min_value": 8000, "max_value": 7200766, "median": 45000},
    "person_emp_exp": {"min_value": 0, "max_value": 50, "median": 5},
    "loan_amnt": {"min_value": 500, "max_value": 35000, "median": 5000},
    "loan_int_rate": {"min_value": 5.42, "max_value": 20.0, "median": 10.0},
    "loan_percent_income": {"min_value": 0.0, "max_value": 0.66, "median": 0.1},
    "cb_person_cred_hist_length": {"min_value": 2.0, "max_value": 30.0, "median": 5.0},
    "credit_score": {"min_value": 390, "max_value": 850, "median": 650}
}

CATEGORICAL_OPTIONS = {
    "person_gender": ["female", "male"],
    "person_education": ["Master", "High School", "Bachelor", "Associate", "Doctorate"],
    "person_home_ownership": ["RENT", "OWN", "MORTGAGE", "OTHER"],
    "loan_intent": ["PERSONAL", "EDUCATION", "MEDICAL", "VENTURE", "HOMEIMPROVEMENT", "DEBTCONSOLIDATION"],
    "previous_loan_defaults_on_file": ["No", "Yes"]
}

FEATURE_ORDER = [
    "person_age", "person_gender", "person_education", "person_income", "person_emp_exp",
    "person_home_ownership", "loan_amnt", "loan_intent", "loan_int_rate",
    "loan_percent_income", "cb_person_cred_hist_length",
    "credit_score", "previous_loan_defaults_on_file"
]

#Session defaults
def _ensure_defaults_in_session():
    defaults = {
        "person_age": NUM_BOUNDS["person_age"]["median"],
        "person_gender": CATEGORICAL_OPTIONS["person_gender"][1],
        "person_education": CATEGORICAL_OPTIONS["person_education"][0],
        "person_income": NUM_BOUNDS["person_income"]["median"],
        "person_emp_exp": NUM_BOUNDS["person_emp_exp"]["median"],
        "person_home_ownership": CATEGORICAL_OPTIONS["person_home_ownership"][0],
        "loan_amnt": NUM_BOUNDS["loan_amnt"]["median"],
        "loan_intent": CATEGORICAL_OPTIONS["loan_intent"][0],
        "loan_int_rate": NUM_BOUNDS["loan_int_rate"]["median"],
        "loan_percent_income": NUM_BOUNDS["loan_percent_income"]["median"],
        "cb_person_cred_hist_length": NUM_BOUNDS["cb_person_cred_hist_length"]["median"],
        "credit_score": NUM_BOUNDS["credit_score"]["median"],
        "previous_loan_defaults_on_file": CATEGORICAL_OPTIONS["previous_loan_defaults_on_file"][0],
        "prediction_made": False,
        "cached_input": None,
        "cached_prediction": None,
        "cached_confidence": None,
        "uploaded_docs": {}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_ensure_defaults_in_session()

#Minimal session flags
if "submission_created" not in st.session_state:
    st.session_state.submission_created = False
if "application_status" not in st.session_state:
    st.session_state.application_status = None
if "admin_decision_note" not in st.session_state:
    st.session_state.admin_decision_note = None
#hide flag to let user clear local display until next submission
if "hide_application_status" not in st.session_state:
    st.session_state.hide_application_status = False

#Reset callback
def reset_to_defaults():
    for key in NUM_BOUNDS:
        st.session_state[key] = NUM_BOUNDS[key]["median"]
    for cat, opts in CATEGORICAL_OPTIONS.items():
        st.session_state[cat] = opts[0]

    st.session_state.prediction_made = False
    st.session_state.cached_input = None
    st.session_state.cached_prediction = None
    st.session_state.cached_confidence = None

    st.session_state.uploaded_docs = {}

    for key in list(st.session_state.keys()):
        if key.endswith("_doc") or key == "loan_intent_doc_file":
            try:
                del st.session_state[key]
            except Exception:
                pass

    if "prediction_df" in st.session_state:
        del st.session_state["prediction_df"]

#Sidebar
st.sidebar.markdown("**📝 Please enter your details below to get a tailored prediction result.**")

with st.sidebar.expander("🧍 Applicant Details", expanded=True):
    st.number_input("person_age", min_value=NUM_BOUNDS["person_age"]["min_value"],
                    max_value=NUM_BOUNDS["person_age"]["max_value"], key="person_age")
    st.selectbox("person_gender", CATEGORICAL_OPTIONS["person_gender"], key="person_gender")
    st.selectbox("person_education", CATEGORICAL_OPTIONS["person_education"], key="person_education")
    st.number_input("person_income", min_value=NUM_BOUNDS["person_income"]["min_value"],
                    max_value=NUM_BOUNDS["person_income"]["max_value"], key="person_income")
    st.number_input("person_emp_exp", min_value=NUM_BOUNDS["person_emp_exp"]["min_value"],
                    max_value=NUM_BOUNDS["person_emp_exp"]["max_value"], key="person_emp_exp")
    st.selectbox("person_home_ownership", CATEGORICAL_OPTIONS["person_home_ownership"], key="person_home_ownership")

with st.sidebar.expander("🏦 Loan Details", expanded=True):
    st.number_input("loan_amnt", min_value=NUM_BOUNDS["loan_amnt"]["min_value"],
                    max_value=NUM_BOUNDS["loan_amnt"]["max_value"], key="loan_amnt")
    loan_intent_selected = st.selectbox("loan_intent", CATEGORICAL_OPTIONS["loan_intent"], key="loan_intent")
    st.number_input("loan_int_rate", min_value=NUM_BOUNDS["loan_int_rate"]["min_value"],
                    max_value=NUM_BOUNDS["loan_int_rate"]["max_value"], key="loan_int_rate")
    st.number_input("loan_percent_income", min_value=NUM_BOUNDS["loan_percent_income"]["min_value"],
                    max_value=NUM_BOUNDS["loan_percent_income"]["max_value"],
                    format="%.3f", key="loan_percent_income")
    st.number_input("cb_person_cred_hist_length",
                    min_value=NUM_BOUNDS["cb_person_cred_hist_length"]["min_value"],
                    max_value=NUM_BOUNDS["cb_person_cred_hist_length"]["max_value"],
                    key="cb_person_cred_hist_length")
    st.number_input("credit_score", min_value=NUM_BOUNDS["credit_score"]["min_value"],
                    max_value=NUM_BOUNDS["credit_score"]["max_value"], key="credit_score")
    st.selectbox("previous_loan_defaults_on_file",
                 CATEGORICAL_OPTIONS["previous_loan_defaults_on_file"],
                 key="previous_loan_defaults_on_file")

#Small-font Required Documents
with st.sidebar.expander("📄 Required Documents", expanded=True):
    st.markdown("<div class='small-docs'>", unsafe_allow_html=True)

    required_docs = {
        "person_income": "Bank Statement",
        "person_emp_exp": "Employment Letter",
        "credit_score": "Credit Bureau Report",
        "previous_loan_defaults_on_file": "Loan Clearance Certificate"
    }

    uploaded_docs = st.session_state.uploaded_docs

    for feature, doc_label in required_docs.items():
        file = st.file_uploader(
            f"{doc_label} (for {feature})",
            type=["pdf", "png", "jpg", "jpeg"],
            key=f"{feature}_doc"
        )
        if file:
            save_path = UPLOADS_DIR / f"{feature}_{file.name}"
            with open(save_path, "wb") as f:
                f.write(file.getbuffer())
            uploaded_docs[feature] = save_path

    intent_doc = None
    if loan_intent_selected == "MEDICAL":
        intent_doc = st.file_uploader("Medical Invoice", type=["pdf", "png", "jpg", "jpeg"],
                                      key="loan_intent_doc_file")
    elif loan_intent_selected == "EDUCATION":
        intent_doc = st.file_uploader("School Admission Letter", type=["pdf", "png", "jpg", "jpeg"],
                                      key="loan_intent_doc_file")
    elif loan_intent_selected == "VENTURE":
        intent_doc = st.file_uploader("Business Plan", type=["pdf", "png", "jpg", "jpeg"],
                                      key="loan_intent_doc_file")

    if intent_doc:
        save_path = UPLOADS_DIR / f"loan_intent_{intent_doc.name}"
        with open(save_path, "wb") as f:
            f.write(intent_doc.getbuffer())
        uploaded_docs["loan_intent_doc"] = save_path

    st.markdown("</div>", unsafe_allow_html=True)

st.session_state.uploaded_docs = uploaded_docs

#Buttons
col1, col2 = st.sidebar.columns([1, 1])
with col1:
    submit = st.button("🔍 Predict")
with col2:
    st.button("Reset 🔄", on_click=reset_to_defaults)

#Prevent prediction if missing docs
all_required_docs = list(required_docs.keys())
if loan_intent_selected in ["MEDICAL", "EDUCATION", "VENTURE"]:
    all_required_docs.append("loan_intent_doc")
missing_docs = [f for f in all_required_docs if f not in st.session_state.uploaded_docs]

if submit and missing_docs:
    # show missing-docs message in the auth/banner color
    st.markdown(f"<div class='msg-blue'>⚠️ Upload all required documents before making a prediction: {missing_docs}</div>", unsafe_allow_html=True)
    submit = False

#Feature Descriptions
FEATURE_DESCRIPTIONS = {
    "person_age": "Applicant's age in years.",
    "person_gender": "Applicant's gender ('female' or 'male').",
    "person_education": "Highest education level.",
    "person_income": "Applicant's annual income.",
    "person_emp_exp": "Years of employment experience.",
    "person_home_ownership": "Home ownership status.",
    "loan_amnt": "Requested loan amount.",
    "loan_intent": "Purpose of the loan.",
    "loan_int_rate": "Loan interest rate (%).",
    "loan_percent_income": "Loan amount as % of income.",
    "cb_person_cred_hist_length": "Credit history length in years.",
    "credit_score": "Numeric credit score.",
    "previous_loan_defaults_on_file": "Whether applicant has prior default records."
}

with st.sidebar.expander("📘 Feature Descriptions", expanded=False):
    for feat in FEATURE_ORDER:
        st.markdown(f"**{feat}** — {FEATURE_DESCRIPTIONS.get(feat)}")

#Prediction
pred = None
confidence = None

if submit:
    row = {k: st.session_state[k] for k in FEATURE_ORDER}
    X = pd.DataFrame([row], columns=FEATURE_ORDER)

    if st.session_state.cached_input is not None and st.session_state.cached_input.equals(X):
        pred = st.session_state.cached_prediction
        confidence = st.session_state.cached_confidence
    else:
        if pipeline is None:
            st.error("❌ Model not available.")
            pred = None
            confidence = None
        else:
            with st.spinner("Analyzing loan details..."):
                try:
                    pred = pipeline.predict(X)[0]
                    if hasattr(pipeline, "predict_proba"):
                        prob = pipeline.predict_proba(X)[0]
                        confidence = prob[int(pred)] * 100
                    else:
                        confidence = None

                    st.session_state.cached_input = X.copy()
                    st.session_state.cached_prediction = pred
                    st.session_state.cached_confidence = confidence

                except Exception as e:
                    st.error("Prediction failed.")
                    logger.exception("Prediction failed: %s", e)
                    pred = None
                    confidence = None

if pred is not None:
    result_label = "✅ Approved" if int(pred) == 1 else "❌ Rejected"
    st.markdown("---")
    st.subheader("Prediction Result")
    st.success(f"**Loan Status:** {result_label}")

    if confidence is not None:
        st.info(f"**Confidence:** {confidence:.2f}%")

    #STORE SUBMISSION (NEW — ADMIN WORKFLOW)
    if not st.session_state.submission_created:
        db.create_submission(
            USER["id"],
            row,
            result_label,
            st.session_state.uploaded_docs,
            confidence  # <-- pass computed confidence to DB
        )

        st.session_state.application_status = "submitted"
        st.session_state.admin_decision_note = None
        st.session_state.submission_created = True
        #Ensure status is visible again (in case user cleared earlier)
        st.session_state.hide_application_status = False
    

    st.session_state.prediction_made = True
    st.session_state.prediction_df = X.copy()
    st.session_state.prediction_df["Prediction"] = result_label

    csv_buffer = BytesIO()
    st.session_state.prediction_df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="📥 Download Prediction as CSV",
        data=csv_buffer.getvalue(),
        file_name="loan_prediction_result.csv",
        mime="text/csv"
    )

    logger.info(
        f"Prediction made: input={row} pred={int(pred)} confidence={confidence}"
    )

#Display Application Status
latest = db.get_latest_submission_for_user(USER["id"])
if not st.session_state.hide_application_status:
    
    if latest:
        db_status = latest.get("status", "")
        #Map internal DB status 'submitted' -> friendly label 'Pending Review'
        if isinstance(db_status, str) and db_status.lower() == "submitted":
            display_label = "Pending Review"
        else:
            display_label = db_status.replace("_", " ").title() if db_status else "Unknown"

        #get admin email for 'reviewed_by'
        reviewed_by_display = ""
        reviewed_by_raw = latest.get("reviewed_by") or latest.get("verified_by") or latest.get("verified_by_email") or latest.get("reviewed_by_email")
        
        if isinstance(reviewed_by_raw, int):
            try:
                admin_user = db.get_user_by_id(reviewed_by_raw)  # use if exists
                if admin_user and admin_user.get("email"):
                    reviewed_by_display = admin_user.get("email")
                else:
                    reviewed_by_display = str(reviewed_by_raw)
            except Exception:
                
                reviewed_by_display = str(reviewed_by_raw)
        else:
            
            if reviewed_by_raw:
                reviewed_by_display = str(reviewed_by_raw)

        admin_note_display = latest.get("admin_decision_note") or latest.get("admin_note") or ""
        
        st.markdown(
            f"""
            <div style="
                background-color:#f0fdf4;
                border-left:6px solid #007a33;
                padding:16px;
                border-radius:10px;
                margin-top:10px;
            ">
                <strong>📄 Application Status</strong><br><br>
                <strong>Status:</strong> {display_label}<br>
                {f"<strong>Reviewed By:</strong> {reviewed_by_display}<br>" if reviewed_by_display else ""}
                {f"<strong>Admin Note:</strong> {admin_note_display}" if admin_note_display else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.session_state.application_status = latest.get("status")
        st.session_state.admin_decision_note = latest.get("admin_decision_note") or latest.get("admin_note")
    else:
        if st.session_state.application_status:
            display_label = st.session_state.application_status
            if isinstance(display_label, str) and display_label.lower() == "submitted":
                display_label = "Pending Review"
            admin_note_display = st.session_state.admin_decision_note or ""
            st.markdown(
                f"""
                <div style="
                    background-color:#f0fdf4;
                    border-left:6px solid #007a33;
                    padding:16px;
                    border-radius:10px;
                    margin-top:10px;
                ">
                    <strong>📄 Application Status</strong><br><br>
                    <strong>Status:</strong> {display_label}<br>
                    {f"<strong>Admin Note:</strong> {admin_note_display}" if admin_note_display else ""}
                </div>
                """,
                unsafe_allow_html=True
            )

#Clear application status button (clears local/session state only)
if (not st.session_state.hide_application_status) and (st.session_state.application_status or (latest and latest.get("status"))):
    if st.button("🗑️ Clear Application Status", key="clear_app"):
        # Clear only the session/local state (does not delete DB rows)
        st.session_state.submission_created = False
        st.session_state.application_status = None
        st.session_state.admin_decision_note = None
        st.session_state.prediction_made = False
        if "prediction_df" in st.session_state:
            del st.session_state["prediction_df"]
        st.session_state.cached_input = None
        st.session_state.cached_prediction = None
        st.session_state.cached_confidence = None
        st.session_state.uploaded_docs = {}
        #remove file uploader keys if present
        for k in list(st.session_state.keys()):
            if k.endswith("_doc") or k == "loan_intent_doc_file":
                try:
                    del st.session_state[k]
                except Exception:
                    pass
        #hide DB-backed display until next submission
        st.session_state.hide_application_status = True
        st.success("Local application status cleared. You can submit a new application now.")
        safe_rerun()

#Footer 
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p class='footer'>© SMARTLEND</p>", unsafe_allow_html=True)





















