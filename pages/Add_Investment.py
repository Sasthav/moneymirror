import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- Database setup ---
def init_db():
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            scheme_code TEXT NOT NULL,
            scheme_name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_investment(scheme_code, scheme_name, amount, date_value):
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO investments (scheme_code, scheme_name, amount, date)
        VALUES (?, ?, ?, ?)
    """, (scheme_code, scheme_name, amount, date_value))
    conn.commit()
    conn.close()

def fetch_investments():
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, * FROM investments")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_investment(rowid, amount, date_value):
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE investments
        SET amount=?, date=?
        WHERE rowid=?
    """, (amount, date_value, rowid))
    conn.commit()
    conn.close()

def delete_investment(rowid):
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investments WHERE rowid=?", (rowid,))
    conn.commit()
    conn.close()

# --- Initialize DB ---
init_db()

# --- Example scheme list ---
schemes = {
    "": "Select -",
    "127042": "Motilal Oswal Midcap Fund",
    "122639": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
    "118668": "Nippon India Growth Mid Cap Fund - Direct Plan - Growth Option",
    "140228": "Edelweiss Mid Cap Fund - Direct Plan - Growth",
    "118633": "Nippon India Large Cap Fund - Direct Plan - Bonus Option",
    "147943": "BANDHAN Small Cap Fund - Direct Plan - IDCW",
}

# --- Add new investment ---
st.title("💰 Investment Entry Form")

with st.form("investment_form"):
    selected = st.selectbox(
        "Choose Scheme",
        options=[f"{code} - {name}" for code, name in schemes.items()]
    )
    scheme_code, scheme_name = selected.split(" - ", 1)

    amount = st.number_input("Amount Invested", min_value=0.0)
    date_value = st.date_input("Date", value=date.today())
    
    submitted = st.form_submit_button("Save Investment")
    if submitted:
        save_investment(scheme_code, scheme_name, amount, str(date_value))
        st.success(f"Saved {scheme_name} ({scheme_code}) with amount {amount}")

# --- Display & manage investments ---
st.subheader("📊 Saved Investments")
rows = fetch_investments()
if rows:
    df = pd.DataFrame(rows, columns=["RowID", "Scheme Code", "Scheme Name", "Amount", "Date"])
    st.dataframe(df, use_container_width=True)

    # Select a row to edit/delete
    rowid = st.selectbox("Select investment to manage:", df["RowID"])

    if rowid:
        selected_row = df[df["RowID"] == rowid].iloc[0]

        st.write(f"Editing: {selected_row['Scheme Name']} ({selected_row['Scheme Code']})")

        new_amount = st.number_input("Update Amount", value=float(selected_row["Amount"]))
        new_date = st.date_input("Update Date", value=pd.to_datetime(selected_row["Date"]).date())

        if st.button("Update Investment"):
            update_investment(rowid, new_amount, str(new_date))
            st.success("Investment updated successfully!")

        if st.button("Delete Investment"):
            delete_investment(rowid)
            st.warning("Investment deleted successfully!")
else:
    st.info("No investments saved yet.")
