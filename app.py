import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuration
ASSETS = {
    "EUR/USD": ["EURO CURRENCY", "EURO FX"],
    "GBP/USD": ["BRITISH POUND"],
    "USD/JPY": ["JAPANESE YEN"],
    "Gold (XAU/USD)": ["GOLD - COMMODITY EXCHANGE", "GOLD - COMEX"],
    "Nasdaq 100": ["NASDAQ-100", "NASDAQ 100 STOCK INDEX"]
}

st.set_page_config(page_title="COT Pro", layout="wide")

# 2. Data Fetching
@st.cache_data(ttl=3600)
def fetch_data():
    url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{datetime.now().year}.zip"
    try:
        r = requests.get(url, timeout=20)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return None

# 3. Processing Logic
def process_asset(df, search_terms, weeks):
    try:
        mask = df.iloc[:, 0].str.contains('|'.join(search_terms), case=False, na=False)
        asset_df = df[mask].copy()
        if asset_df.empty: return None
        
        d_col = [c for c in asset_df.columns if 'Date' in c][0]
        asset_df[d_col] = pd.to_datetime(asset_df[d_col])
        asset_df = asset_df.sort_values(d_col, ascending=False).head(weeks)
        
        l_col = [c for c in asset_df.columns if 'Lev_Money_Positions_Long' in c][0]
        s_col = [c for c in asset_df.columns if 'Lev_Money_Positions_Short' in c][0]
        
        curr_net = asset_df[l_col].iloc[0] - asset_df[s_col].iloc[0]
        change = curr_net - (asset_df[l_col].iloc[1] - asset_df[s_col].iloc[1])
        
        return {
            "Asset": "",
            "Trend": "UP 📈" if change > 0 else "DOWN 📉",
            "Net": int(curr_net),
            "Date": asset_df[d_col].iloc[0].strftime('%Y-%m-%d')
        }
    except: return None

# 4. Main App
def main():
    st.title("🏛️ COT Dashboard")
    df = fetch_data()
    if df is not None:
        selected = st.sidebar.multiselect("Select", list(ASSETS.keys()), default=["EUR/USD"])
        results = []
        for a in selected:
            res = process_asset(df, ASSETS[a], 12)
            if res:
                res["Asset"] = a
                results.append(res)
        if results:
            st.table(pd.DataFrame(results).set_index("Asset"))
        else:
            st.error("Processing error. Try again.")
    else:
        st.error("Could not fetch data.")

if __name__ == "__main__":
    main()

