import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION ---
# Assets and their potential naming in both TFF and Legacy reports
ASSETS = {
    "EUR/USD": ["EURO CURRENCY", "EURO FX"],
    "GBP/USD": ["BRITISH POUND", "BRITISH POUND STERLING"],
    "USD/JPY": ["JAPANESE YEN"],
    "USD/CHF": ["SWISS FRANC"],
    "USD/CAD": ["CANADIAN DOLLAR"],
    "AUD/USD": ["AUSTRALIAN DOLLAR"],
    "NZD/USD": ["NEW ZEALAND DOLLAR"],
    "Gold (XAU/USD)": ["GOLD - COMMODITY EXCHANGE", "GOLD - COMEX"],
    "Nasdaq 100": ["NASDAQ-100", "NASDAQ 100 STOCK INDEX"],
    "Dow Jones": ["DJIA", "DOW JONES INDUSTRIAL AVERAGE"]
}

st.set_page_config(page_title="Professional COT Dashboard", layout="wide")

@st.cache_data(ttl=3600) # Cache for 1 hour to stay updated
def fetch_all_cot_data():
    """Fetches both Financial and Legacy data to ensure coverage."""
    year = datetime.now().year
    urls = {
        "fin": f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip",
        "leg": f"https://www.cftc.gov/files/dea/history/deahistfo{year}.zip"
    }
    
    combined_df = pd.DataFrame()
    
    for key, url in urls.items():
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    with z.open(z.namelist()[0]) as f:
                        df = pd.read_csv(f, low_memory=False)
                        combined_df = pd.concat([combined_df, df], axis=0, ignore_index=True)
        except:
            continue
    return combined_df

def process_asset(df, search_terms, weeks):
    """Smart search for assets across different report formats."""
    # Find rows where Market Name contains any of the search terms
    mask = df['Market_and_Exchange_Names'].str.contains('|'.join(search_terms), case=False, na=False)
    asset_df = df[mask].copy()
    
    if asset_df.empty:
        return None

    asset_df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(asset_df['Report_Date_as_MM_DD_YYYY'])
    asset_df = asset_df.sort_values('Report_Date_as_MM_DD_YYYY', ascending=False).head(weeks)
    
    if len(asset_df) < 2:
        return None

    # Identify if it's TFF (Financial) or Legacy (Commodity) report by checking column names
    # and map 'Non-Commercial' or 'Leveraged' to a unified 'Speculators' view
    try:
        if 'Lev_Money_Positions_Long_All' in asset_df.columns:
            l, s = 'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All'
        else:
            l, s = 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All'
            
        curr_l, curr_s = asset_df[l].iloc[0], asset_df[s].iloc[0]
        prev_l, prev_s = asset_df[l].iloc[1], asset_df[s].iloc[1]
        
        net = curr_l - curr_s
        change = net - (prev_l - prev_s)
        
        # Scoring
        history = asset_df[l] - asset_df[s]
        score = round(((net - history.min()) / (history.max() - history.min() + 1)) * 100, 2)
        
        return {
            "Asset": "", 
            "Trend": "Rising 📈" if change > 0 else "Falling 📉",
            "Net Position": int(net),
            "Score (0-100)": score,
            "Date": asset_df['Report_Date_as_MM_DD_YYYY'].iloc[0].strftime('%Y-%m-%d')
        }
    except:
        return None

def main():
    st.header("🏛️ Multi-Source COT Dashboard")
    st.sidebar.title("Filters")
    lookback = st.sidebar.slider("Analysis Period (Weeks)", 4, 52, 12)
    selected = st.sidebar.multiselect("Assets", list(ASSETS.keys()), default=["EUR/USD", "Gold (XAU/USD)"])

    with st.spinner("Fetching latest CFTC reports..."):
        df = fetch_all_cot_data()

    if not df.empty:
        results = []
        for asset_name in selected:
            data = process_asset(df, ASSETS[asset_name], lookback)
            if data:
                data["Asset"] = asset_name
                results.append(data)
        
        if results:
            res_df = pd.DataFrame(results)
            st.subheader("Smart Money Sentiment")
            st.table(res_df.set_index("Asset"))
            
            # Simple Chart for the first selected asset
            st.divider()
            target = selected[0]
            st.info(f"Visualizing trend for {target} over {lookback} weeks...")
        else:
            st.error("Could not find matching data. The CFTC server might be updating or the search terms need refinement.")
    else:
        st.error("Failed to fetch data from CFTC. Please check your internet connection or try again later.")

if __name__ == "__main__":
    main()
