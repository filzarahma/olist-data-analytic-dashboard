import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import geopandas as gpd
from babel.numbers import format_currency


# MENYIAPKAN DATAFRAME
# create dataframe of 
# create dataframe of daily orders
def create_monthly_orders_df(df):
    # Mengelompokkan berdasarkan 'order_id' dan mengambil baris pertama untuk mengambil payment_value / order
    first_payment_df = df.groupby('order_id').first().reset_index()

    # Menghitung revenue bulanan berdasarkan 'order_approved_at'
    montly_orders_df = first_payment_df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum",
    })

    # Format indeks ke format bulanan
    montly_orders_df.index = montly_orders_df.index.strftime('%Y-%m')

    # Reset index menjadi kolom
    montly_orders_df = montly_orders_df.reset_index()

    # Rename kolom
    montly_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value": "revenue",
    }, inplace=True)
    
    return montly_orders_df

# create dataframe of sum of order items
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby('product_category_name_english').order_item_id.count().sort_values(ascending=False).reset_index()
    sum_order_items_df.rename(columns={
        'product_category_name_english': 'product_category',
        'order_item_id' : 'quantity'
    }, inplace=True)

    return sum_order_items_df

# create dataframe for payment type contribution
def create_payment_type_df(df):
    payment_type_df = df.groupby('order_id').first().groupby('payment_type').payment_value.sum().sort_values(ascending=False).reset_index()
    
    return payment_type_df

# create dataframe for on time delivery rate
def create_delivery_status_df(df):
    delivery_data = df.loc[df['order_status'] == 'delivered'].copy()
    delivery_data = delivery_data.dropna(subset=['on_time_delivery'])
    delivery_data['delivery_group'] = delivery_data.on_time_delivery.apply(lambda x: "on time" if x >=0 else ("late" if x < 0 else "process"))

    delivery_status_df = delivery_data.groupby(by="delivery_group").order_id.nunique().sort_values(ascending=False).reset_index()
    return delivery_status_df

# create dataframe for customer demography
def create_customer_demography_df(df):
    customer_data = df.groupby(by='customer_state').customer_id.nunique().sort_values(ascending=False).reset_index()
    return customer_data

# create dataframe for rfm
def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
    "order_purchase_timestamp": "max", # mengambil tanggal order terakhir
    "order_id": "nunique", # menghitung jumlah order
    "payment_value": "sum" # menghitung jumlah revenue yang dihasilkan
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

# LOAD DATASET
all_df = pd.read_csv('./dashboard/all_data.csv')

# format data to datetime
all_df.sort_values(by='order_approved_at', inplace=True)
all_df.reset_index(inplace=True)

datetime_column = ['order_purchase_timestamp', 'order_approved_at']
for col in datetime_column:
    all_df[col] = pd.to_datetime(all_df[col])

# MEMBUAT KOMPONEN FILTER -> sidebar
min_date = all_df['order_approved_at'].min()
max_date = all_df['order_approved_at'].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image('./image/olist-logo.png', clamp=True)
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_approved_at"] >= str(start_date)) & (all_df["order_approved_at"] <= str(end_date))]

monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
payment_type_df = create_payment_type_df(main_df)
delivery_status_df = create_delivery_status_df(main_df)
customer_demography_df = create_customer_demography_df(main_df)
rfm_df = create_rfm_df(main_df)

# MELENGKAPI DASHBOARD DENGAN BERBAGAI VISUALISASI DATA
st.header('Olist E-Commerce Dashboard 🛍️')

# 1. Monthly Orders
st.subheader('🛒 Monthly Orders')
col1, col2 = st.columns(2)

with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric('📦 Total orders', value=total_orders)

with col2:
    total_revenue = format_currency(monthly_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric('💰 Total Revenue', value=total_revenue)


fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_orders_df['order_approved_at'],
    monthly_orders_df['order_count'],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', rotation=45, labelsize=15)

st.pyplot(fig)

# 2. Best and Worst Performing Products
st.subheader("🚀 Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
 
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
 
sns.barplot(x="quantity", y="product_category", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="quantity", y="product_category", data=sum_order_items_df.sort_values(by="quantity", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
 
st.pyplot(fig)

# 3. Payment Type Contribution
st.subheader('💳 Payment Type Contribution')

labels = payment_type_df['payment_type'].tolist()
sizes = payment_type_df['payment_value'].tolist()
colors = ['#0f3352', '#1b5d97', '#2c88d8', '#71afe5']

fig = go.Figure(data=[go.Pie(
    labels=labels,
    values=sizes,
    hole=0.7,
    marker=dict(colors=colors),
    textinfo='percent+label',
    textfont_size=12,
    pull=[0.3, 0, 0, 0, 0]
)])

# Menambahkan judul ke chart
fig.update_layout(
    title={
        'text': '',
        'y': 0.5,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    annotations=[dict(
        text=f'{sum(sizes):,}',  # Menambahkan jumlah total di tengah
        x=0.5, y=0.5, font_size=18, showarrow=False
    )]
)

# Menampilkan Donut Chart di Streamlit
st.plotly_chart(fig)

# 4. On-Time Delivery Rate
st.subheader('⏰ On-Time Delivery Rate')
labels = delivery_status_df['delivery_group'].tolist()
sizes = delivery_status_df['order_id'].tolist()
colors = ['#003f7f', '#e97d1c']

fig = go.Figure(data=[go.Pie(
    labels=labels,
    values=sizes,
    hole=0.7,
    marker=dict(colors=colors),
    textinfo='percent+label',
    textfont_size=12,
    pull=[0.3, 0, 0, 0, 0]
)])

# Menambahkan judul ke chart
fig.update_layout(
    title={
        'text': '',
        'y': 0.5,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    annotations=[dict(
        text=f'{sum(sizes):,}',  # Menambahkan jumlah total di tengah
        x=0.5, y=0.5, font_size=18, showarrow=False
    )]
)   

# Menampilkan Donut Chart di Streamlit
st.plotly_chart(fig)

# 5. Customer Demographics
st.subheader('🗺️ Customer Demography')

gdf = gpd.read_file('./geojson/brazil_geo.json')

# 2. Data pelanggan (contoh sederhana)
customer_data = customer_demography_df

# 3. Gabungkan data pelanggan dengan data geografis
gdf = gdf.merge(customer_data, left_on='id', right_on='customer_state', how='left')

# 4. Plot peta
fig, ax = plt.subplots(1, 1, figsize=(16, 8))
gdf.plot(column='customer_id', cmap='Blues', legend=True, ax=ax)

ax.axis('off')  # Hilangkan sumbu

# Menambahkan label untuk 'customer_state'
for idx, row in gdf.iterrows():
    # Ambil koordinat tengah negara bagian (centroid)
    x, y = row['geometry'].centroid.coords[0]
    ax.text(x, y, row['id'], fontsize=10, ha='center', color='grey')

# Tampilkan peta di Streamlit
st.pyplot(fig)

# 6. Best Customer Based on RFM Parameters
st.subheader("🔝 Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3) 
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis ='x', labelsize=15, rotation=45)

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15, rotation=45)

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15, rotation=45)

st.pyplot(fig)

st.caption('Copyright (c) filzarahma')
