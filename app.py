import streamlit as st
import pandas as pd
import requests
import io
import zipfile
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION & ASSET MAPPING ---
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

st.set_page_config(page_title="Professional COT Dashboard", layout="wide")

# --- DATA ENGINE ---
@st.cache_data(ttl=86400)
def fetch_cot_data():
    """Fetches the current year's COT data from CFTC."""
    year = datetime.now().year
    url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open(z.namelist()[0]) as f:
                    df = pd.read_csv(f, low_memory=False)
            return df
        else:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to CFTC: {e}")
        return None

def process_asset_data(df, market_name, weeks):
    """Filters data for a specific asset and calculates metrics."""
    # Search for the market name in the dataframe
    asset_df = df[df['Market_and_Exchange_Names'].str.contains(market_name, case=False, na=False)].copy()
    
    if asset_df.empty:
        return None
        
    asset_df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(asset_df['Report_Date_as_MM_DD_YYYY'])
    asset_df = asset_df.sort_values('Report_Date_as_MM_DD_YYYY', ascending=False).head(weeks)
    
    if len(asset_df) < 2:
        return None

    # Calculate metrics for Leveraged Funds (Speculators)
    current_long = asset_df['Lev_Money_Positions_Long_All'].iloc[0]
    current_short = asset_df['Lev_Money_Positions_Short_All'].iloc[0]
    current_net = current_long - current_short
    
    prev_long = asset_df['Lev_Money_Positions_Long_All'].iloc[1]
    prev_short = asset_df['Lev_Money_Positions_Short_All'].iloc[1]
    prev_net = prev_long - prev_short
    
    # Trend logic
    change = current_net - prev_net
    trend = "Rising 📈" if change > 0 else "Falling 📉" if change < 0 else "Sideways ↔️"
    
    # COT Index Score (0-100)
    net_history = asset_df['Lev_Money_Positions_Long_All'] - asset_df['Lev_Money_Positions_Short_All']
    max_net = net_history.max()
    min_net = net_history.min()
    score = round(((current_net - min_net) / (max_net - min_net + 1)) * 100, 2)
    
    return {
        "Asset": "", # Will be filled in main
        "Trend": trend,
        "Net Position": current_net,
        "Weekly Change": change,
        "COT Score": score,
        "Open Interest": asset_df['Open_Interest_All'].iloc[0],
        "Date": asset_df['Report_Date_as_MM_DD_YYYY'].iloc[0].strftime('%Y-%m-%d')
    }

# --- UI MAIN ---
def main():
    st.title("🏛️ Institutional COT Dashboard")
    st.markdown("Analyzing **Leveraged Funds** (Smart Money) positioning from CFTC reports.")

    # Sidebar
    st.sidebar.header("Settings")
    lookback = st.sidebar.slider("Analysis Period (Weeks)", 4, 52, 12)
    selected_assets = st.sidebar.multiselect("Select Assets", list(ASSET_MAP.keys()), default=["EUR/USD", "Gold (XAU/USD)", "Nasdaq 100"])

    raw_data = fetch_cot_data()

    if raw_data is not None:
        table_data = []
        for asset in selected_assets:
            stats = process_asset_data(raw_data, ASSET_MAP[asset], lookback)
            if stats:
                stats['Asset'] = asset
                table_data.append(stats)

        # Check if we have data to display
        if table_data:
            summary_df = pd.DataFrame(table_data)
            
            # Display Metrics Table
            st.subheader("Market Sentiment Overview")
            st.dataframe(summary_df.sort_values('COT Score', ascending=False), use_container_width=True, hide_index=True)

            # Export CSV
            csv = summary_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Data as CSV", csv, "cot_analysis.csv", "text/csv")
            
            # Detailed Chart
            st.divider()
            target = st.selectbox("Select Asset for Detailed Trend", selected_assets)
            
            # Historical Plot
            hist_df = raw_data[raw_data['Market_and_Exchange_Names'].str.contains(ASSET_MAP[target], case=False, na=False)].copy()
            hist_df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(hist_df['Report_Date_as_MM_DD_YYYY'])
            hist_df = hist_df.sort_values('Report_Date_as_MM_DD_YYYY').tail(lookback)
            hist_df['Net'] = hist_df['Lev_Money_Positions_Long_All'] - hist_df['Lev_Money_Positions_Short_All']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_df['Report_Date_as_MM_DD_YYYY'], y=hist_df['Net'],
                                     mode='lines+markers', name='Net Position',
                                     line=dict(color='#1f77b4', width=3)))
            
            fig.update_layout(title=f"Net Position Trend: {target}", xaxis_title="Date", yaxis_title="Contracts")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("No data found for the selected assets. Try increasing the analysis period or checking other assets.")

if __name__ == "__main__":
    main()
