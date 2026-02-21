#pages/2_Dataset_Insights.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dataset Insights", page_icon="📊")

st.markdown("# Dataset Insights")

# Try load processed train.csv
TRAIN_PATH = "data/processed/train.csv"
try:
    df = pd.read_csv(TRAIN_PATH)
except Exception:
    st.warning("Processed train.csv not found at data/processed/train.csv. Upload or run preprocessing first.")
    df = None

if df is not None:
    st.write("### Sample of processed training data")
    st.dataframe(df.head())

    st.markdown("### Distribution: Loan Status")
    fig, ax = plt.subplots()
    df["loan_status"].value_counts().plot(kind="bar", ax=ax)
    ax.set_xlabel("loan_status (0=Rejected,1=Approved)")
    ax.set_ylabel("count")
    st.pyplot(fig)

    st.markdown("### Correlation Heatmap (numerical features)")
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        cax = ax2.matshow(corr)
        fig2.colorbar(cax)
        ax2.set_xticks(range(len(num_cols)))
        ax2.set_yticks(range(len(num_cols)))
        ax2.set_xticklabels(num_cols, rotation=90)
        ax2.set_yticklabels(num_cols)
        st.pyplot(fig2)

    st.markdown("### Box plots (selected features)")
    features_to_plot = [c for c in ["person_income", "loan_amnt", "credit_score"] if c in df.columns]
    for col in features_to_plot:
        fig, ax = plt.subplots()
        df.boxplot(column=col, by="loan_status", ax=ax)
        ax.set_title(col)
        st.pyplot(fig)
