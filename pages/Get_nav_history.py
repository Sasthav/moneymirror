import requests
import pandas as pd
import streamlit as st

def get_historical_nav(scheme_codes):
    """
    Fetches historical NAV for multiple Indian Mutual Fund scheme codes.
    Example scheme_codes: ['119598', '102885', '118834']
    """
    all_data = []
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
                print(f"No historical data found for scheme {code}")
                continue

            df = pd.DataFrame(nav_list)
            df['scheme_name'] = meta.get('scheme_name', '')
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y').dt.date
            df['nav'] = pd.to_numeric(df['nav'])

            latest_nav = df.loc[df['date'].idxmax(), 'nav']
            df['Profit/Loss'] = latest_nav - df['nav']

            df = df.sort_values(by='date').reset_index(drop=True)
            all_data.append(df)
            metas.append(meta)

            print(f"Successfully fetched data for: {meta.get('scheme_name')}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {code}: {e}")

    # Return all schemes together
    return all_data, metas

 # Define a function to color values
def color_profit_loss(val):
    return 'color: green' if val >= 0 else 'color: red'

# Input box for user
#user_input = st.text_input("Enter scheme name:")

# --- Execution ---
# 127042 - Motilal Oswal Midcap Fund 
# 122639 - Parag Parikh Flexi Cap Fund - Direct Plan - Growth
# 
scheme_codes = ["127042","122639","118668", "140228", "118633", "147943"]  # replace with actual codes
df_nav, metadata = get_historical_nav(scheme_codes)

if df_nav is not None:
    # Preview the historical data
    pd.set_option('display.max_rows', None)      # show all rows
    pd.set_option('display.max_columns', None)  # show all columns
    final_df = pd.concat(df_nav, ignore_index=True)
    df = final_df.sort_values(by="date", ascending=False)
    df = df.reset_index(drop=True)
    # Filter DataFrame if input is provided
    #if user_input:
    # filtered_df = df[df['scheme_name'].str.contains(user_input, case=False)]
   # st.dataframe(filtered_df)
    #option = st.selectbox("Choose scheme:", df['scheme_name'].unique())
    options = ["All"] + df['scheme_name'].unique().tolist()
    option = st.selectbox("Choose scheme:", options)
    if option != "All":
     df = df[df['scheme_name'] == option]
    df = df[['scheme_name', 'date', 'nav', 'Profit/Loss']]
    df = df.rename(columns={"date": "Date", "nav": "NAV", "scheme_name":"Scheme Name"})
    
    styled_df = df.style.map(color_profit_loss, subset=['Profit/Loss'])
    
    #print(df)
    st.title("Mutual Funds NAV Data")
    st.set_page_config(layout="wide")
    st.dataframe(styled_df, use_container_width=True)  # interactive grid with filters/search


def get_allMFs():
    """
    Fetches the complete list of all Indian Mutual Fund schemes
    from the MFAPI open API.
    """
    api_url = "https://api.mfapi.in/mf"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()   # this is a list of dicts

        # Convert list of schemes into a DataFrame
        df = pd.DataFrame(data)

        print(f"Successfully fetched {len(df)} schemes.")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching schemes: {e}")
        return None



    # Example DataFrames
df1 = pd.DataFrame({
    "Scheme": ["A", "B", "C"],
    "NAV": [100, 105, 110]
})

df2 = pd.DataFrame({
    "Scheme": ["X", "Y", "Z"],
    "NAV": [200, 210, 220]
})

#st.title("Mutual Fund Names")

#mf_df = get_allMFs()
#st.subheader("Grid 1: Mutual Funds")
#st.dataframe(mf_df)

#st.subheader("Grid 2: Second set of schemes")
#st.dataframe(df2)
