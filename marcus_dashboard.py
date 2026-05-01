
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Marcus Weber Electronics - Business Intelligence", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("Online_Retail.xlsx")
    df = df.dropna(subset=['CustomerID'])
    df = df[df['Quantity'] > 0]
    df = df[df['UnitPrice'] > 0]
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Cost'] = df['UnitPrice'] * 0.6
    df['Profit'] = df['Revenue'] - (df['Cost'] * df['Quantity'])
    df['Category'] = df['Description'].str.extract(r'(BAG|HEART|VINTAGE|LIGHT|LUNCH|SET|CHRISTMAS|PARTY)', expand=False).fillna('OTHER')
    return df

df = load_data()

# Header
st.title("🔧 Marcus Weber Electronics")
st.subheader("Business Intelligence Dashboard - 2023 Analysis")

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Revenue", f"£{df['Revenue'].sum():,.0f}")
with col2:
    st.metric("Total Profit", f"£{df['Profit'].sum():,.0f}")
with col3:
    st.metric("Profit Margin", f"{(df['Profit'].sum()/df['Revenue'].sum()*100):.1f}%")
with col4:
    st.metric("Customers", f"{df['CustomerID'].nunique():,}")

st.divider()

# Profitability
st.header("📊 Profitability Analysis")

prof = df.groupby('Category').agg({
    'Revenue': 'sum',
    'Profit': 'sum'
}).reset_index()
prof['Margin_%'] = (prof['Profit'] / prof['Revenue'] * 100).round(2)

fig1 = px.bar(prof.sort_values('Profit', ascending=False), 
              x='Category', y='Profit', 
              title='Profit by Category',
              color='Margin_%',
              color_continuous_scale='RdYlGn')
st.plotly_chart(fig1, use_container_width=True)

# Monthly trend
monthly = df.groupby(df['InvoiceDate'].dt.to_period('M')).agg({
    'Revenue': 'sum',
    'Profit': 'sum'
}).reset_index()
monthly['InvoiceDate'] = monthly['InvoiceDate'].astype(str)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=monthly['InvoiceDate'], y=monthly['Revenue'], name='Revenue', line=dict(color='blue')))
fig2.add_trace(go.Scatter(x=monthly['InvoiceDate'], y=monthly['Profit'], name='Profit', line=dict(color='green')))
fig2.update_layout(title='Monthly Revenue & Profit Trend')
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Returns
st.header("🔄 Returns Analysis")
df_all = pd.read_excel("Online_Retail.xlsx")
df_all = df_all.dropna(subset=['CustomerID'])
returns = df_all[df_all['Quantity'] < 0].copy()
returns['ReturnValue'] = abs(returns['Quantity'] * returns['UnitPrice'])
returns['Category'] = returns['Description'].str.extract(r'(BAG|HEART|VINTAGE|LIGHT|LUNCH|SET|CHRISTMAS|PARTY)', expand=False).fillna('OTHER')

ret_sum = returns.groupby('Category')['ReturnValue'].sum().reset_index()
fig3 = px.pie(ret_sum, values='ReturnValue', names='Category', title='Return Value by Category')
st.plotly_chart(fig3, use_container_width=True)

st.metric("Total Return Loss", f"£{returns['ReturnValue'].sum():,.0f}")

st.divider()

# Customer Segments
st.header("👥 Customer Segmentation")

snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
rfm = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
    'InvoiceNo': 'nunique',
    'Revenue': 'sum'
}).reset_index()
rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']

rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4,3,2,1])
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1,2,3,4])
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1,2,3,4])

def rfm_segment(row):
    score = int(row['R_Score']) + int(row['F_Score']) + int(row['M_Score'])
    if score >= 9: return 'Champions'
    elif score >= 7: return 'Loyal'
    elif score >= 5: return 'Potential'
    else: return 'At Risk'

rfm['Segment'] = rfm.apply(rfm_segment, axis=1)

seg = rfm.groupby('Segment').agg({
    'CustomerID': 'count',
    'Monetary': 'sum'
}).reset_index()
seg.columns = ['Segment', 'Count', 'Revenue']

fig4 = px.bar(seg, x='Segment', y=['Count', 'Revenue'], barmode='group', title='Customer Segments')
st.plotly_chart(fig4, use_container_width=True)

st.dataframe(seg, use_container_width=True)
