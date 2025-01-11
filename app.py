import streamlit as st
import requests
import json
import math
import pandas as pd
import time

# Page config with light theme
st.set_page_config(
    page_title="NSE Options Chain Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",

)

# Custom CSS for light mode styling
st.markdown("""
    <style>

    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        background-color: white;
    }
    div[data-testid="stTable"] {
        font-size: 14px;
    }
    thead tr th {
        background-color: #f8f9fa !important;
        color: #1f2937 !important;
    }
    tbody tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .header {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }
    </style>
""", unsafe_allow_html=True)

# Automatic refresh every 60 seconds using JavaScript
st.markdown("""
    <script>
        function reload() {
            setTimeout(function () {
                window.location.reload();
            }, 60);
        }
        reload();
    </script>
""", unsafe_allow_html=True)

# Define functions to fetch data
def round_nearest(x, num=50):
    return int(math.ceil(float(x) / num) * num)

def nearest_strike_bnf(x):
    return round_nearest(x, 100)

def nearest_strike_nf(x):
    return round_nearest(x, 50)

# API URLs and headers
url_oc = "https://www.nseindia.com/"
url_bnf = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
url_nf = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
url_indices = "https://www.nseindia.com/api/allIndices"

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'referer': 'https://www.nseindia.com/option-chain',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
}

sess = requests.Session()

def set_cookie():
    sess.get(url_oc, headers=headers, timeout=5)

def get_data(url):
    set_cookie()
    time.sleep(2)
    response = sess.get(url, headers=headers, timeout=5)
    if response.status_code == 401:
        set_cookie()
        response = sess.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
        return response.text
    return ""

def fetch_indices_data():
    response_text = get_data(url_indices)
    data = json.loads(response_text)
    nifty_last = None
    banknifty_last = None
    for index in data["data"]:
        if index["index"] == "NIFTY 50":
            nifty_last = index["last"]
        if index["index"] == "NIFTY BANK":
            banknifty_last = index["last"]
    return nifty_last, banknifty_last

def fetch_oi_data(num, step, nearest, url):
    strike = nearest - (step * num)
    data_list = []
    response_text = get_data(url)
    data = json.loads(response_text)
    currExpiryDate = data["records"]["expiryDates"][0]
    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            if strike <= item["strikePrice"] < strike + (step * num * 2):
                data_list.append({
                    "Strike Price": item["strikePrice"],
                    "CE Last Price": item["CE"]["lastPrice"],
                    "PE Last Price": item["PE"]["lastPrice"],
                    "Expiry Date": currExpiryDate
                })
    return data_list

def highest_oi_ce(num, step, nearest, url):
    strike = nearest - (step * num)
    response_text = get_data(url)
    data = json.loads(response_text)
    currExpiryDate = data["records"]["expiryDates"][0]
    max_oi = 0
    max_oi_strike = 0
    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate and strike <= item["strikePrice"] < strike + (step * num * 2):
            if item["CE"]["openInterest"] > max_oi:
                max_oi = item["CE"]["openInterest"]
                max_oi_strike = item["strikePrice"]
    return max_oi_strike

def highest_oi_pe(num, step, nearest, url):
    strike = nearest - (step * num)
    response_text = get_data(url)
    data = json.loads(response_text)
    currExpiryDate = data["records"]["expiryDates"][0]
    max_oi = 0
    max_oi_strike = 0
    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate and strike <= item["strikePrice"] < strike + (step * num * 2):
            if item["PE"]["openInterest"] > max_oi:
                max_oi = item["PE"]["openInterest"]
                max_oi_strike = item["strikePrice"]
    return max_oi_strike

# Display header with refresh time
current_time = time.strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"""
    <div class='header'>
        <h1 style='text-align: center; margin: 0; color: #1f2937;'>📈 NSE Option Chain Analysis</h1>
        <p style='text-align: center; margin: 10px 0 0 0; color: #6b7280;'>Last Updated: {current_time}</p>
    </div>
""", unsafe_allow_html=True)

# Fetch data
nifty_last, banknifty_last = fetch_indices_data()
nifty_nearest = nearest_strike_nf(nifty_last)
banknifty_nearest = nearest_strike_bnf(banknifty_last)

# Major support and resistance levels
nf_highestoi_ce = highest_oi_ce(10, 50, nifty_nearest, url_nf)
nf_highestoi_pe = highest_oi_pe(10, 50, nifty_nearest, url_nf)
bnf_highestoi_ce = highest_oi_ce(10, 100, banknifty_nearest, url_bnf)
bnf_highestoi_pe = highest_oi_pe(10, 100, banknifty_nearest, url_bnf)

# Display metrics in columns
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
        <div class='metric-card'>
            <h3 style='color: #1f2937; margin: 0;'>NIFTY</h3>
            <h2 style='color: #1f2937; margin: 10px 0;'>{nifty_last:,.2f}</h2>
            <p style='color: #6b7280; margin: 0;'>Support: {nf_highestoi_ce:,.2f} | Resistance: {nf_highestoi_pe:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class='metric-card'>
            <h3 style='color: #1f2937; margin: 0;'>BANKNIFTY</h3>
            <h2 style='color: #1f2937; margin: 10px 0;'>{banknifty_last:,.2f}</h2>
            <p style='color: #6b7280; margin: 0;'>Support: {bnf_highestoi_ce:,.2f} | Resistance: {bnf_highestoi_pe:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)

# Display Option Chain Data
st.markdown("### NIFTY Option Chain")
nifty_oi_data = fetch_oi_data(10, 50, nifty_nearest, url_nf)
st.table(pd.DataFrame(nifty_oi_data))

st.markdown("### BANKNIFTY Option Chain")
banknifty_oi_data = fetch_oi_data(10, 100, banknifty_nearest, url_bnf)
st.table(pd.DataFrame(banknifty_oi_data))
