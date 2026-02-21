This app collects applicant + loan info, runs a saved ML pipeline (models/loan_approval_model.pkl) to predict loan approval, saves submissions (including model confidence) to MySQL, supports document uploads, and offers an admin dashboard for review/approve/reject with optional email notifications.

Key features (short)

Applicant UI: enter data, upload required docs, get prediction + confidence, download CSV.

Admin UI: view submissions (applicant, status, model result and confidence), download files, approve/reject, leave notes, send email notifications.

MySQL persistence (users + submissions).

Safe DB init (creates DB/tables if missing).

Uses a joblib pipeline that should implement predict and ideally predict_proba.

Quick start (local)

Clone repository

git clone <owino4011>
<cd smartlend_loan_approval_predictor>


Create & activate virtual environment

python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows
.venv\Scripts\activate


Install dependencies (example)

pip install streamlit pandas joblib scikit-learn mysql-connector-python python-dotenv


Ensure MySQL is running and reachable. The app currently reads DB config from the code (auth/db.py). Recommended to change to env vars for production.

Ensure models/loan_approval_model.pkl exists. If you need a quick dummy model for testing, create one (example):

# scripts/create_dummy_model.py
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import joblib, numpy as np
X = np.random.rand(100, 13)
y = np.random.randint(0,2,100)
pipe = make_pipeline(StandardScaler(), LogisticRegression())
pipe.fit(X,y)
joblib.dump(pipe, "models/loan_approval_model.pkl")


Run: python scripts/create_dummy_model.py.

Run the app

python -m streamlit run app.py


Open URL printed in terminal (usually http://localhost:8501 or as shown).

Database notes (essential)

The app uses a smartlend MySQL database with users and submissions tables.

ALTER TABLE submissions ADD COLUMN confidence DOUBLE NULL;


The app's auth/db.py attempts to create DB/tables automatically on startup; verify DB credentials before running.

Model expectations

The saved pipeline must implement:

predict(X) → predicted class (0/1)

Ideally predict_proba(X) → probability vector; the app uses prob[int(pred)] * 100 to compute confidence.

Make sure input feature order matches FEATURE_ORDER in the app.

Admin quick actions

Create an admin user (SQL) if needed:

INSERT INTO users (email, password_hash, salt, role) VALUES ('admin@example.com', '<hash>', '<salt>', 'admin');


Admin dashboard shows all submissions and should display the confidence field from submissions.

File uploads

Uploaded documents are saved to a local uploads/ folder. If admin server runs elsewhere, ensure uploads/ is accessible or switch to shared storage (S3, etc.).

Email notifications

Approval/rejection emails are sent by auth.email_utils. Configure SMTP settings there or via environment variables before enabling in production.

Common troubleshooting

Model not loaded: Verify models/loan_approval_model.pkl exists and is loadable with joblib.

Confidence is None: Your model does not implement predict_proba. Use a classifier that supports probabilities or calibrate probabilities.

DB connection errors: Check host/port/user/password and ensure MySQL server is accessible.

Uploaded files not found in admin: Confirm uploads/ path and that file paths saved in DB match disk locations.

Production & security pointers (brief)

Move DB credentials, SMTP creds, and other secrets to environment variables or a secret manager.

Use secure password hashing (bcrypt/argon2) — do not store plaintext passwords in the DB.

Serve behind HTTPS, and validate/sanitize file uploads before storing or serving.

Project structure (high level)
.
├── app.py
├── dashboards/
│   └── admin_dashboard.py
├── auth/
│   ├── db.py
│   ├── auth.py
│   └── email_utils.py
├── models/
│   └── loan_approval_model.pkl
├── uploads/
├── src/
│   └── utils.py
└── requirements.txt