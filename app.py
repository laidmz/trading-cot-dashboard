import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION & ASSET MAPPING ---
# Maps user-friendly names to CFTC Market Names
ASSET_MAP = {
    "EUR/USD": "EURO CURRENCY - CHICAGO MERCANTILE EXCHANGE",
    "GBP/USD": "BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE",
    "USD/JPY": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
    "USD/CHF": "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE",
    "USD/CAD": "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "AUD/USD": "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "NZD/USD": "NEW ZEALAND DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "Gold (XAU/USD)": "GOLD - COMMODITY EXCHANGE INC.",
    "Nasdaq 100": "NASDAQ-100 STOCK INDEX (MINI) - CHICAGO MERCANTILE EXCHANGE",
    "Dow Jones": "DJIA CONSOLIDATED - CHICAGO BOARD OF TRADE"
}

st.set_page_config(page_title="Pro COT Dashboard", layout="wide")

# --- DATA ENGINE ---
@st.cache_data(ttl=86400) # Cache for 24 hours
def fetch_cot_data():
    """Fetches the current year's Financial/Legacy COT data from CFTC."""
    year = datetime.now().year
    # For Financial Futures (Currencies/Indices)
    url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
    
    try:
        response = requests.get(url)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # The file inside the zip is usually 'fin_fut.txt' (comma delimited)
            with z.open(z.namelist()[0]) as f:
                df = pd.read_csv(f, low_memory=False)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def process_asset_data(df, market_name, weeks):
    """Filters data for a specific asset and calculates metrics."""
    # Filter for market
    asset_df = df[df['Market_and_Exchange_Names'].str.contains(market_name, case=False, na=False)].copy()
    asset_df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(asset_df['Report_Date_as_MM_DD_YYYY'])
    asset_df = asset_df.sort_values('Report_Date_as_MM_DD_YYYY', ascending=False).head(weeks)
    
    # Financial Report column names (TFF)
    # Asset Manager (Commercial-ish), Leveraged Funds (Non-Commercial/Speculators)
    res = {
        "Date": asset_df['Report_Date_as_MM_DD_YYYY'].iloc[0],
        "Long": asset_df['Lev_Money_Positions_Long_All'].iloc[0],
        "Short": asset_df['Lev_Money_Positions_Short_All'].iloc[0],
        "Net": asset_df['Lev_Money_Positions_Long_All'].iloc[0] - asset_df['Lev_Money_Positions_Short_All'].iloc[0],
        "Prev_Net": asset_df['Lev_Money_Positions_Long_All'].iloc[1] - asset_df['Lev_Money_Positions_Short_All'].iloc[1],
        "OI": asset_df['Open_Interest_All'].iloc[0]
    }
    
    # Trend Logic
    change = res['Net'] - res['Prev_Net']
    if change > 0: res['Trend'] = "Rising 📈"
    elif change < 0: res['Trend'] = "Falling 📉"
    else: res['Trend'] = "Sideways ↔️"
    
    # Scoring (0-100 based on Net position relative to history)
    max_net = (asset_df['Lev_Money_Positions_Long_All'] - asset_df['Lev_Money_Positions_Short_All']).max()
    min_net = (asset_df['Lev_Money_Positions_Long_All'] - asset_df['Lev_Money_Positions_Short_All']).min()
    res['Score'] = round(((res['Net'] - min_net) / (max_net - min_net + 1)) * 100, 2)
    
    return res

# --- UI IMPLEMENTATION ---
def main():
    st.title("🏛️ Institutional Commitment of Traders (COT)")
    st.markdown("Analyzing **Leveraged Funds** positioning from the CFTC TFF Report.")

    # Sidebar Filters
    st.sidebar.header("Settings")
    lookback = st.sidebar.slider("Analysis Period (Weeks)", 4, 52, 12)
    selected_assets = st.sidebar.multiselect("Select Assets", list(ASSET_MAP.keys()), default=list(ASSET_MAP.keys()))

    raw_data = fetch_cot_data()

    if raw_data is not None:
        table_data = []
        for asset in selected_assets:
            try:
                stats = process_asset_data(raw_data, ASSET_MAP[asset], lookback)
                stats['Asset'] = asset
                table_data.append(stats)
            except:
                continue

        # Display Summary Table
        summary_df = pd.DataFrame(table_data)
        summary_df = summary_df[['Asset', 'Trend', 'Net', 'Score', 'OI', 'Date']]
        
        st.subheader("Market Sentiment Overview")
        st.dataframe(summary_df.sort_values('Score', ascending=False), use_container_width=True)

        # CSV Export
        csv = summary_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "cot_report.csv", "text/csv")

        # Visual Chart for single asset
        st.divider()
        target = st.selectbox("View Detailed Trend", selected_assets)
        # (Plotly chart implementation would go here fetching historical net positions)
        st.info(f"Visualizing institutional bias for {target} over {lookback} weeks.")

if __name__ == "__main__":
    main()
