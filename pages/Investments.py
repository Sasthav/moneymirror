import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import requests
from babel.numbers import format_currency
from datetime import datetime, timedelta

def get_historical_nav(scheme_codes):
    all_data = {}
    metas = []

    for code in scheme_codes:
        api_url = f"https://api.mfapi.in/mf/{code}"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            meta = data.get('meta', {})
            nav_list = data.get('data', [])

            if not nav_list:
                continue

            df = pd.DataFrame(nav_list)
            df['scheme_name'] = meta.get('scheme_name', '')
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y').dt.date
            df['nav'] = pd.to_numeric(df['nav'])

            all_data[code] = df
            metas.append(meta)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {code}: {e}")

    return all_data, metas

def fetch_investments():
    conn = sqlite3.connect("SQLite/mf.db")
    cursor = conn.cursor()
    cursor.execute("SELECT scheme_code, scheme_name, amount, date FROM investments order by date desc")
    rows = cursor.fetchall()
    conn.close()
    return rows

def calculate_units_and_profit(all_data):
    investments = fetch_investments()
    results = []

    for scheme_code, scheme_name, amount, invest_date in investments:
        df = all_data.get(scheme_code)
        if df is None:
            continue

        # NAV on investment date
        nav_row = df[df['date'] == pd.to_datetime(invest_date).date()]
        if nav_row.empty:
            nav_row = df[df['date'] <= pd.to_datetime(invest_date).date()].tail(1)

        if not nav_row.empty:
         nav_value = truncate(nav_row['nav'].values[0], 2)
         units = round(amount / nav_value, 2)   # 4-decimal precision
         allotted = truncate(units,2) * truncate(nav_value,2) # currency precision

         # Try to get NAV for today
         yesterday = pd.Timestamp.today().date() - timedelta(days=1)
         dayBefore = df['date'][0]
         #st.success(dayBefore)
         today_row = df[df['date'] == yesterday]
         today_row = df[df['date'] == dayBefore] if today_row.empty else today_row
         #latest_nav = df.loc[df['date'].idxmax(), 'nav']
         latest_nav = today_row['nav'].values[0]
         #st.success(today_row)
         
         current_value = units * latest_nav
         profit_loss = current_value - amount

         results.append({
            "Scheme Code": scheme_code,
            "Scheme Name": scheme_name,
            "Date": invest_date,
            "Invested": amount,
            "Allotted": allotted,
            "NAV on Date": nav_value,
            "Units": units,
            "Latest NAV": latest_nav,
            "Profit/Loss": round(profit_loss, 2)
        })


    return pd.DataFrame(results)
def truncate(value, decimals=2):
    factor = 10 ** decimals
    return int(value * factor) / factor

def color_profit_loss(val):
    if val > 0:
        return "color: green"
    elif val < 0:
        return "color: red"
    else:
        return ""

def showInvestments():
    if st.button("Logout"):
        st.session_state.clear()   # clears all session data
        st.rerun()    # forces app to reload → goes to home_screen
    # --- Example usage ---
    scheme_codes = ["127042","122639","118668", "140228", "118633", "147943"]  # replace with your codes
    all_data, metas = get_historical_nav(scheme_codes)

    st.subheader("📊 Portfolio with Profit/Loss")
    st.set_page_config(page_title="Investments", layout="wide")
    df_units = calculate_units_and_profit(all_data)
    if not df_units.empty:
        combined_list = (df_units["Scheme Code"] + "--" + df_units["Scheme Name"]).unique().tolist()
        options = ["All"] + combined_list  
        option = st.selectbox("Choose scheme:", options)
        parts = option.split('--')
        scheme_name = parts[1] if len(parts) > 1 else "All"
        scheme_code = parts[0] if len(parts) > 1 else "122639"
        #st.success(scheme_code)
        if scheme_name != "All":
         df_units = df_units[df_units['Scheme Name'] == scheme_name]
        styled_df = (
        df_units
        .reset_index(drop=True)   # remove index column
        .style
        .format({
            "Invested": "{:.2f}",
            "Allotted": "{:.2f}",
            "Current Value": "{:.2f}",
            "Profit/Loss": "{:.2f}",
            "Latest NAV": "{:.2f}",
            "NAV on Date": "{:.2f}",
            "Units": "{:.2f}"
        })
        .map(color_profit_loss, subset=["Profit/Loss"])  # use applymap for cell-wise styling
    )    
    
        # --- Totals ---
        total_amount = df_units["Allotted"].sum().round(2)
        total_units = df_units["Units"].sum().round(2)
        total_profit_loss = df_units["Profit/Loss"].sum().round(2)
        current = total_amount + total_profit_loss 
        filteredeach = all_data[scheme_code]
        
        sort1 = filteredeach.sort_values('date')
        firstNav = sort1.iloc[-1]['nav']
        nexNav = sort1.iloc[-2]['nav']
        navDiff = firstNav - nexNav
        singleTot = total_units * navDiff
        # Get today's date
        today = date.today() - timedelta(days=1)

        # Collect today's NAVs for each scheme
        today_navs = {}
        current_value = 0
        today_profit_loss = 0
        todayLS = 0
        for scheme_code, df in all_data.items():
         sort = df.sort_values('date')
         scheme_navs = all_data.get(scheme_code, [])
         sort = scheme_navs.sort_values('date')
         currNav = sort.iloc[-1]['nav']
         prevNav = sort.iloc[-2]['nav']    
         current_value = currNav - prevNav
         currentUnits = df_units["Units"].sum().round(4)
         units_sum = df_units.groupby('Scheme Code')["Units"].sum().reset_index()
         filtered = units_sum[units_sum["Scheme Code"] == scheme_code]
        if filtered.empty:
         units = total_profit_loss #units_sum['Units'].iloc[-1]
        else:
         units = filtered["Units"].iloc[-1]

        #st.success(units)
        today_profit_loss += current_value*units
        
        nav_row = df[df['date'] == today]
        if not nav_row.empty:
            today_navs[scheme_code] = float(nav_row['nav'].values[0])
        else:
            # fallback: last available NAV
            latest_row = df.tail(1)
            today_navs[scheme_code] = float(latest_row['nav'].values[0])
        # Now calculate portfolio totals
        total_amount = df_units["Allotted"].sum().round(2)
        total_units = df_units["Units"].sum().round(4)
        today_profit_loss = today_profit_loss if scheme_name == "All" else singleTot

        if total_profit_loss < 0:
         color = "red"
        else:
         color = "green"
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
         st.markdown(f"**Total Amount:** {format_currency(total_amount, 'INR', locale='en_IN')}")
        with col2:
         st.markdown(f"**Current Value:** {format_currency(current, 'INR', locale='en_IN')}")
        with col3:
         st.markdown(f"**Total Units:** {format_currency(total_units, 'INR', locale='en_IN')}")
        with col4:
            st.markdown(
                    f"<div>"
                    f"<strong>Today P/L:</strong> <span style='color:{color};padding:8px;border-radius:5px;font-weight:bold'> {format_currency(today_profit_loss, 'INR', locale='en_IN')}</span>"
                    "</div>",
                    unsafe_allow_html=True
                    ) 
        with col5:
         st.markdown(
            f"<div>"
            f"<strong>Total P/L:</strong> <span style='color:{color};padding:8px;border-radius:5px;font-weight:bold'> {format_currency(total_profit_loss, 'INR', locale='en_IN')}</span>"
            "</div>",
            unsafe_allow_html=True
            )   
    
        st.dataframe(styled_df, use_container_width=True) 
    else:
        st.info("No investments found or NAV data missing.")

def home_screen():
    st.title("Welcome to Mutual Fund Tracker")
    st.write("Please log in to view your investments.")

# --- Main app logic ---
if "user_id" not in st.session_state or st.session_state["user_id"] is None:
    # Redirect to home/login screen
    home_screen()
else:
    # Show investments only for logged-in user
    showInvestments()