import streamlit as st
from auth import db
from auth.email_utils import send_email, approval_template, rejection_template
import json
from pathlib import Path

def show_admin():

    # ===== CONSISTENT BUTTON + TITLE STYLING (ADMIN ONLY) =====
    st.markdown(
        """
        <style>
        /* ALL buttons inside admin dashboard */
        div.stButton > button {
            background-color: #007a33 !important;
            color: white !important;
            border-radius: 10px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
            border: none;
            transition: 0.2s ease-in-out;
        }

        div.stButton > button:hover {
            background-color: #00b37e !important;
            color: white !important;
        }

        /* Admin dashboard title box */
        .admin-title-box {
            background-color: #007a33;
            border-radius: 16px;
            padding: 16px 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }

        .admin-title-box h1 {
            color: white;
            margin: 0;
            font-size: 28px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # ==========================================================

    # ===== WELCOME MESSAGE =====
    admin_email = st.session_state.user["email"]
    st.success(f"👋 Welcome back, {admin_email}")

    # ===== TITLE IN ROUNDED RECTANGLE =====
    st.markdown(
        """
        <div class="admin-title-box">
            <h1>💰SmartLend:Admin Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # NOTE: "Clear backlog" UI removed as requested.

    submissions = db.get_all_submissions()

    if not submissions:
        st.info("No submissions available.")
        return

    # helper to map reviewed_by id -> email (uses db.get_conn from auth.db)
    def _get_user_email_by_id(uid):
        try:
            conn = db.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT email FROM users WHERE id=%s", (uid,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                # row is a tuple (email,)
                return row[0]
        except Exception:
            # safe-fail
            try:
                cur.close()
                conn.close()
            except Exception:
                pass
        return None

    for s in submissions:
        st.markdown("---")
        st.subheader(f"Applicant: {s['applicant_email'] if s.get('applicant_email') else s.get('email', '')}")
        st.write("**Status:**", s.get("status"))
        st.write("**Model Result:**", s.get("prediction_result"))

        # --- NEW: display model confidence if available ---
        conf_val = s.get("confidence")
        if conf_val is not None:
            try:
                conf_num = float(conf_val)
                # If stored as fraction (0-1) convert to percent; heuristic:
                if 0 <= conf_num <= 1:
                    conf_display = conf_num * 100
                else:
                    conf_display = conf_num
                st.write("**Model Confidence:**", f"{conf_display:.2f}%")
            except Exception:
                # fallback to raw display
                st.write("**Model Confidence:**", conf_val)

        # Show model inputs
        try:
            st.json(json.loads(s.get("inputs") or "{}"))
        except Exception:
            st.write("Could not parse inputs.")

        # ===== Uploaded files =====
        uploaded_files = s.get("uploaded_file_path")
        if uploaded_files:
            try:
                files = json.loads(uploaded_files)
                st.markdown("### 📂 Uploaded Documents")
                for fname, fpath in files.items():
                    file_path = Path(fpath)
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"📄 {fname}",
                                data=f,
                                file_name=fname,
                                mime="application/octet-stream",
                                key=f"download_{s['id']}_{fname}"
                            )
                    else:
                        st.warning(f"File not found: {fname}")
            except Exception as e:
                st.warning(f"Unable to load uploaded files: {e}")

        # ===== Admin decision note =====
        existing_note = s.get("admin_note") or s.get("admin_decision_note") or ""
        note = st.text_area(
            "Admin decision note",
            value=existing_note,
            key=f"note_{s['id']}"
        )

        # Show Reviewed By email (if available) inside admin UI (read-only)
        reviewed_by_display = s.get("reviewed_by")
        reviewed_by_email = None
        if reviewed_by_display:
            # If reviewed_by already contains an email string, use it;
            # otherwise treat it as an id and look up the email.
            if isinstance(reviewed_by_display, str) and "@" in reviewed_by_display:
                reviewed_by_email = reviewed_by_display
            else:
                try:
                    # try to convert to int id
                    rid = int(reviewed_by_display)
                    reviewed_by_email = _get_user_email_by_id(rid)
                except Exception:
                    reviewed_by_email = None

        if reviewed_by_email:
            st.write("**Reviewed By:**", reviewed_by_email)
        elif reviewed_by_display:
            # fallback to whatever is present
            st.write("**Reviewed By:**", reviewed_by_display)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{s['id']}"):
                # update DB (keeps your existing DB logic unchanged)
                db.update_submission_status(
                    s["id"],
                    "approved",
                    st.session_state.user["id"],
                    note
                )

                # prepare/send email
                applicant_email = s.get("email") or s.get("applicant_email")
                admin_email_local = st.session_state.user.get("email", "SmartLend Admin")
                try:
                    subject, body = approval_template(applicant_email, admin_email_local, note)
                    send_email(applicant_email, subject, body)
                except Exception as e:
                    # don't let email issues break the UI — log to console and continue
                    print("Email send failed (approve):", e)

                st.success("Approved — applicant notified by email (if configured).")
                st.rerun()

        with col2:
            if st.button("❌ Reject", key=f"reject_{s['id']}"):
                db.update_submission_status(
                    s["id"],
                    "rejected",
                    st.session_state.user["id"],
                    note
                )

                # prepare/send email
                applicant_email = s.get("email") or s.get("applicant_email")
                admin_email_local = st.session_state.user.get("email", "SmartLend Admin")
                try:
                    subject, body = rejection_template(applicant_email, admin_email_local, note)
                    send_email(applicant_email, subject, body)
                except Exception as e:
                    print("Email send failed (reject):", e)

                st.error("Rejected — applicant notified by email (if configured).")
                st.rerun()











