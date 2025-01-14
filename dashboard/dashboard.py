import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import geopandas as gpd
from babel.numbers import format_currency
import json

#######################
# Page configuration
st.set_page_config(
    page_title="Olist Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #F0F2F6; /* Warna latar belakang */
    text-align: center;
    padding: 15px 0;
    border-radius: 5px 5px 5px 5px; /* Mengatur radius pada sudut */
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################

# MENYIAPKAN DATAFRAME
# create dataframe of 
# create dataframe of daily orders
def create_daily_orders_df(df):
    # Mengelompokkan berdasarkan 'order_id' dan mengambil baris pertama untuk mengambil payment_value / order
    first_payment_df = df.groupby('order_id').first().reset_index()

    # Menghitung revenue harian berdasarkan 'order_approved_at'
    daily_orders_df = first_payment_df.resample(rule='D', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum",
        "review_score": "mean"
    })
    # Reset index menjadi kolom
    daily_orders_df = daily_orders_df.reset_index()

    # Rename kolom
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value": "revenue",
        "review_score": "rating"
    }, inplace=True)
    
    return daily_orders_df

# create dataframe of sum of order items
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby('product_category_name_english').order_item_id.count().sort_values(ascending=False).reset_index()
    sum_order_items_df.rename(columns={
        'product_category_name_english': 'product_category',
        'order_item_id' : 'quantity',
    }, inplace=True)

    return sum_order_items_df

# create dataframe for customer demography
def create_customer_demography_df(df):
    customer_data = df.groupby(by='customer_state').customer_id.nunique().sort_values(ascending=True).reset_index()
    customer_data.rename(columns={
        'customer_id': 'customer_count'
    }, inplace=True)
    return customer_data

# create dataframe for status count
def create_status_count_df(df):
    status_count_df = df.groupby(by='order_status').order_id.nunique().reset_index()
    status_count_df.rename(columns={
        'order_id': 'order_count'
    }, inplace=True)
    return status_count_df

# create dataframe for payment type contribution
def create_payment_type_df(df):
    payment_type_df = df.groupby('order_id').first().groupby('payment_type').payment_value.sum().sort_values(ascending=False).reset_index()
    payment_type_df['payment_type'] = payment_type_df['payment_type'].str.replace('_', ' ')
    return payment_type_df

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
all_df = pd.read_csv('./dashboard/all data.csv', sep=",")

# format data to datetime
all_df.sort_values(by="order_approved_at", inplace=True)
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
    
    try:
        # Mengambil start_date & end_date dari date_input
        start_date, end_date = st.date_input(
            label='Date Range', min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )
        # Jika end_date tidak diinput, gunakan max_date sebagai default
        if not end_date:
            end_date = max_date

        # Validasi rentang waktu
        if start_date < min_date or end_date > max_date:
            raise ValueError("Tanggal berada di luar rentang yang diizinkan.")
        if start_date > end_date:
            raise ValueError("Tanggal mulai harus lebih awal dari tanggal akhir.")
    
    except ValueError as e:
        print(f"Input tidak valid: {e}")
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")


    # Menambahkan filter kategori produk
    category = st.multiselect(
        label="Product Category",
        options=sorted(all_df['product_category_name_english'].unique())
    )

    # Menambahkan filter negara
    state = st.multiselect(
        label="Customer State",
        options=sorted(all_df['customer_state'].unique())
    )

    st.caption('Copyright (c) filzarahma')

# KONFIGURASI MAIN DATAFRAME
main_df = all_df[(all_df["order_approved_at"] >= str(start_date)) & (all_df["order_approved_at"] <= str(end_date))]
if len(category) > 0:
    main_df = main_df[main_df['product_category_name_english'].isin(category)]

if len(state) > 0:
    main_df = main_df[main_df['customer_state'].isin(state)]

# KONFIGURASI SUB DATAFRAME
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
customer_demography_df = create_customer_demography_df(main_df)
order_status_df = create_status_count_df(main_df)
payment_type_df = create_payment_type_df(main_df)
rfm_df = create_rfm_df(main_df)

# MELENGKAPI DASHBOARD DENGAN BERBAGAI VISUALISASI DATA
st.header('Olist E-Commerce Dashboard 🛍️')

# OVERVIEW
col1 = st.columns([2, 1])

with col1[0]:
# 1. Daily Orders
    st.subheader('🛒 Daily Orders')
    order_col = st.columns((1.5, 4.5, 2), gap='medium')

    with order_col[0]:
        total_orders = daily_orders_df.order_count.sum()
        st.metric('📦 Total Orders    ', value=total_orders)

    with order_col[1]:
        total_revenue = format_currency(round(daily_orders_df.revenue.sum(),2), "BRL", locale='pt_BR')
        st.metric('💰 Total Revenue', value=total_revenue)

    with order_col[2]:
        avg_rating = round(daily_orders_df.rating.mean(), 2)
        st.metric('⭐ Average Rating', value=avg_rating)


    # Membuat plot dengan Plotly
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_orders_df['order_approved_at'],
            y=daily_orders_df['order_count'],
            mode='lines+markers',
            marker=dict(color="#90CAF9"),
            line=dict(width=2, color="#90CAF9"),
        )
    )

    # Menyesuaikan tata letak
    fig.update_layout(
        # title="Order Count Over Time",
        xaxis=dict(
            title="Order Date",
            tickangle=45,
            tickfont=dict(size=15),
        ),
        yaxis=dict(
            title="Order Count",
            tickfont=dict(size=15),
        ),
        template="plotly_white",
        height=450,
        width=1000,
    )

    st.plotly_chart(fig)

with col1[1]:
    st.subheader('📈 Top Selling')
    top_selling_df = sum_order_items_df.sort_values(by='quantity', ascending=False).head(5).copy()
    st.dataframe(top_selling_df,
                 column_order=("product_category", "quantity"),
                 hide_index=True,
                 width=500,
                 column_config={
                    "product_category": st.column_config.TextColumn(
                        "Product Category",
                    ),
                    "quantity": st.column_config.TextColumn(
                        "Quantity",
                    )
                    # "quantity": st.column_config.ProgressColumn(
                    #     "Quantity",
                    #     format="%f",
                    #     min_value=0,
                    #     max_value=sum_order_items_df['quantity'].max(),
                    #  )
                     }
                 )
    
    st.subheader('📉 Worst Selling')
    worst_selling_df = sum_order_items_df.sort_values(by='quantity', ascending=True).head(5).copy()
    st.dataframe(worst_selling_df,
                 column_order=("product_category", "quantity"),
                 hide_index=True,
                 width=500,
                 column_config={
                    "product_category": st.column_config.TextColumn(
                        "Product Category",
                    ),
                    "quantity": st.column_config.TextColumn(
                        "Quantity",
                    )
                    # "quantity": st.column_config.ProgressColumn(
                    #     "Quantity",
                    #     format="%f",
                    #     min_value=0,
                    #     max_value=sum_order_items_df['quantity'].max(),
                    #  )
                     }
                 )
# ORDER COUNT
col2 = st.columns(8)

with col2[0]:
    st.metric("Created", value=order_status_df[order_status_df['order_status'] == 'created']['order_count'].sum())

with col2[1]:
    st.metric("Approved", value=order_status_df[order_status_df['order_status'] == 'approved']['order_count'].sum())

with col2[2]:
    st.metric("Processing", value=order_status_df[order_status_df['order_status'] == 'processing']['order_count'].sum())

with col2[3]:
    st.metric("Invoiced", value=order_status_df[order_status_df['order_status'] == 'invoiced']['order_count'].sum())

with col2[4]:
    st.metric("Shipped", value=order_status_df[order_status_df['order_status'] == 'shipped']['order_count'].sum())

with col2[5]:
    st.metric("Delivered", value=order_status_df[order_status_df['order_status'] == 'delivered']['order_count'].sum())

with col2[6]:
    st.metric("Canceled", value=order_status_df[order_status_df['order_status'] == 'canceled']['order_count'].sum())

with col2[7]:
    st.metric("Unavailable", value=order_status_df[order_status_df['order_status'] == 'unavailable']['order_count'].sum())

# DEMOGRAPHY
col3 = st.columns([1, 1])

customer_data = customer_demography_df

with col3[0]:
    st.subheader('🚀 Top States')
    # Membuat barplot horizontal menggunakan Plotly
    fig = px.bar(customer_data, 
                 x='customer_count', 
                 y='customer_state', 
                 orientation='h', 
                 title=' ') 
                 
    # Menampilkan plot
    st.plotly_chart(fig)

with col3[1]:
    st.subheader('🗺️ Customer Demography')

    # Load the geographic data (assuming GeoJSON file)
    gdf = gpd.read_file('./geojson/brazil_geo.json')

    # Merge geographic data with customer data based on 'id' and 'customer_state'
    gdf = gdf.merge(customer_data, left_on='id', right_on='customer_state', how='left')

    # Convert GeoDataFrame to a format suitable for Plotly
    # Convert geometry to GeoJSON format and create a valid GeoJSON dictionary for Plotly
    geojson_data = json.loads(gdf.to_json())

    # Create a Plotly Choropleth map
    fig = px.choropleth(
        gdf,
        geojson=geojson_data,
        locations=gdf.index,  # Use the index of gdf as location
        color='customer_count',  # Color based on customer_id or another column you want to visualize
        hover_name='id',  # Hover over info to show 'id'
        hover_data=['customer_state'],  # Add any additional data to show on hover
        color_continuous_scale="Blues",  # Adjust color scale as needed
        title=" "
    )

    # Update layout for better presentation
    fig.update_geos(fitbounds="locations", visible=False)  # Fit the map to the locations and hide borders
    fig.update_layout(
        geo=dict(showland=True, landcolor='white'),
        showlegend=False,  # Hide legend if not needed
        title_x=0.5,
        title_font_size=24
    )

    # Display the Plotly map in Streamlit
    st.plotly_chart(fig)

col4 = st.columns([1.5, 2.5])

with col4[0]:
    # 3. Payment Type Contribution
    st.subheader('💳 Payment Type Contribution')

    labels = payment_type_df['payment_type'].tolist()
    sizes = payment_type_df['payment_value'].tolist()
    colors = ['#0f3352', '#1b5d97', '#2c88d8', '#71afe5']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=sizes,
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

with col4[1]:
    # 6. Best Customer Based on RFM Parameters
    st.subheader("👑 Best Customer Based on RFM Parameters")

    rfm_col1, rfm_col2, rfm_col3 = st.columns(3) 
    with rfm_col1:
        avg_recency = round(rfm_df.recency.mean(), 1)
        st.metric("Average Recency (days)", value=avg_recency)
    
    with rfm_col2:
        avg_frequency = round(rfm_df.frequency.mean(), 2)
        st.metric("Average Frequency", value=avg_frequency)
    
    with rfm_col3:
        avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR') 
        st.metric("Average Monetary", value=avg_frequency)

    # Mengambil 5 teratas berdasarkan recency, frequency, dan monetary
    top_recency = rfm_df.sort_values(by="recency", ascending=True).head(5)
    top_frequency = rfm_df.sort_values(by="frequency", ascending=False).head(5)
    top_monetary = rfm_df.sort_values(by="monetary", ascending=False).head(5)

    # Membuat subplots dengan Plotly dan memastikan setiap subplot memiliki sumbu Y yang terpisah
    fig = make_subplots(
        rows=1, cols=3, 
        shared_yaxes=False,  # Memastikan sumbu Y terpisah
        vertical_spacing=0.1
    )

    # Menambahkan trace untuk recency plot
    fig.add_trace(
        go.Bar(x=top_recency['customer_id'], y=top_recency['recency'], marker=dict(color='#90CAF9')),
        row=1, col=1
    )

    # Menambahkan trace untuk frequency plot
    fig.add_trace(
        go.Bar(x=top_frequency['customer_id'], y=top_frequency['frequency'], marker=dict(color='#90CAF9')),
        row=1, col=2
    )

    # Menambahkan trace untuk monetary plot
    fig.add_trace(
        go.Bar(x=top_monetary['customer_id'], y=top_monetary['monetary'], marker=dict(color='#90CAF9')),
        row=1, col=3
    )

    # Menambahkan label di atas setiap grafik
    fig.update_layout(
        title="Top 5 Customers Based on RFM Metrics",
        xaxis_title="Customer ID",
        yaxis_title="Value",
        height=600,
        width=1200,
        showlegend=False,
        annotations=[
            dict(text="Recency (days)", x=0.1, y=1.05, showarrow=False, xref='paper', yref='paper'),
            dict(text="Frequency", x=0.5, y=1.05, showarrow=False, xref='paper', yref='paper'),
            dict(text="Monetary", x=0.9, y=1.05, showarrow=False, xref='paper', yref='paper')
        ]
    )

    # Mengupdate axis labels dan tick sizes
    fig.update_xaxes(tickangle=45, tickfont=dict(size=15))
    fig.update_yaxes(tickfont=dict(size=15))
    
    st.plotly_chart(fig)


