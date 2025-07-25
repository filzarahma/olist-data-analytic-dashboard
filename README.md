# Olist E-Commerce Dashboard ✨

## Project Overview
This project analyzes the Olist E-Commerce dataset to gain insights into sales performance, customer behavior, and operational efficiency. The analysis aims to answer key business questions and provide data-driven recommendations.

## Business Questions Addressed
- How is the company's sales and revenue performance in the last few months?
- Which product categories are the most and least sold?
- How does each payment method contribute to total sales?
- What proportion of orders are delivered on time?
- What is the demographic distribution of our customers?

## Key Findings
- Overall, the number of orders and company revenue have increased over the last 3 years, peaking in November 2017 with 7,309 orders and revenue of 1,143,633.57 Real.
- The most sold product category is bed bath table with 11,988 items. The least sold product category is security and services with only 2 items sold.
- The three most commonly used payment methods are credit card (78.3%), boleto (17.9%), and voucher (2.4%).
- Olist has excellent performance with an on-time delivery rate of 92.1%.
- The highest customer demographics are centered in southeastern Brazil, particularly São Paulo and surrounding areas.

## Data Source
The analysis uses the Olist E-Commerce public dataset, which contains information about orders, products, customers, and sellers from the Brazilian market.

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run steamlit app
```
streamlit run dashboard/dashboard.py
```

## Links
- GitHub Repository: [https://github.com/filzarahma/olist-data-analytic-dashboard/](https://github.com/filzarahma/olist-data-analytic-dashboard/)
- Live Dashboard: [https://olist-ecommerce-analytic-dashboard.streamlit.app/](https://olist-ecommerce-analytic-dashboard.streamlit.app/)
