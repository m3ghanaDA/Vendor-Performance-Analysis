#!/usr/bin/env python
# coding: utf-8

# # Exploratory Data Analysis
# 
# Understanding the dataset to explore how the data is present in the database and if there is a need for creating some aggregated tables that can help with:
# 
# - Vendor selection for profitability
# - Product pricing optimization

# In[1]:


import pandas as pd
import sqlite3


# In[2]:


#creating db connection
conn = sqlite3.connect('inventory.db')


# In[3]:


#checking tables present in the db
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
tables


# In[4]:


for table in tables['name']:
    print('-'*50, f'{table}', '-'*50)
    print('Count of records: ', pd.read_sql(f"SELECT count(*) as count from {table}", conn)['count'].values[0])
    display(pd.read_sql(f"select * from {table} limit 5", conn))


# In[5]:


purchases = pd.read_sql_query("select * from purchases where VendorNumber=4466", conn)
purchases


# In[6]:


purchase_prices = pd.read_sql_query(f"select * from purchase_prices where VendorNumber=4466", conn)
purchase_prices


# In[7]:


vendor_invoice = pd.read_sql_query(f"select * from vendor_invoice where VendorNumber=4466", conn)
vendor_invoice


# In[8]:


sales = pd.read_sql_query(f"select * from sales where VendorNo=4466", conn)
sales


# In[9]:


purchases


# In[10]:


purchases.groupby(['Brand', 'PurchasePrice'])[['Quantity','Dollars']].sum()


# In[11]:


sales.groupby('Brand')[['SalesDollars','SalesPrice','SalesQuantity']].sum()


# - The purchases table contains actual purchase data, including the date of purchase, products (brands) purchased by vendors, the amount paid (in dollars), and the quantity purchased.
# - The purchase price column is derived from the purchase_prices table, which provides product-wise actual and purchase prices. The combination of vendor and brand is unique in this table.
# - The vendor_invoice table aggregates data from the purchases table, summarizing quantity and dollar amounts, along with an additional column for freight. This table maintains uniqueness based on vendor and PO number.
# - The sales table captures actual sales transactions, detailing the brands purchased by vendors, the quantity sold, the selling price, and the revenue earned.

# As the data that we need for analysis is distributed in different tables, we need to create a summary table containing:
# 
# - purchase transactions made by vendors
# - sales transaction data
# - freight costs for each vendor
# - actual product prices from vendors

# In[12]:


vendor_invoice.columns


# In[13]:


freight_summary = pd.read_sql_query("""select VendorNumber, SUM(Freight) as FreightCost
                                    FROM vendor_invoice
                                    GROUP BY VendorNumber""", conn)


# In[14]:


freight_summary


# In[15]:


purchases.columns


# In[16]:


purchase_prices.columns


# In[17]:


pd.read_sql_query("""SELECT p.VendorNumber, p.VendorName, p.Brand, p.PurchasePrice,
                    pp.Volume, pp.Price as ActualPrice,
                    SUM(p.Quantity) as TotalPurchaseQuantity,
                    SUM(p.Dollars) as TotalPurchaseDollars
                    FROM purchases p
                    JOIN purchase_prices pp
                    ON p.Brand = pp.Brand
                    WHERE p.PurchasePrice > 0
                    GROUP BY p.VendorNumber, p.VendorName, p.Brand
                    ORDER BY TotalPurchaseDollars""",conn)


# In[18]:


sales.columns


# In[19]:


pd.read_sql_query("""SELECT Brand, VendorNo,
                    SUM(SalesQuantity) AS TotalSalesQuantity,
                    SUM(SalesDollars) AS TotalSalesDollars,
                    SUM(SalesPrice) AS TotalSalesPrice,
                    SUM(ExciseTax) AS TotalExciseTax
                    FROM sales
                    GROUP BY VendorNo, Brand
                    ORDER BY TotalSalesDollars""",conn)


# In[20]:


vendor_sales_summary=pd.read_sql_query("""WITH FreightSummary AS (
    SELECT VendorNumber, SUM(Freight) AS FreightCost
    FROM vendor_invoice
    GROUP BY VendorNumber
),

PurchaseSummary AS (
    SELECT 
        p.VendorNumber,
        p.VendorName,
        p.Brand,
        p.Description,
        p.PurchasePrice,
        pp.Price AS ActualPrice,
        pp.Volume,
        SUM(p.Quantity) AS TotalPurchaseQuantity,
        SUM(p.Dollars) AS TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp
        ON p.Brand = pp.Brand
    WHERE p.PurchasePrice > 0
    GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
),

SalesSummary AS (
    SELECT 
        VendorNo,
        Brand,
        SUM(SalesQuantity) AS TotalSalesQuantity,
        SUM(SalesDollars) AS TotalSalesDollars,
        SUM(SalesPrice) AS TotalSalesPrice,
        SUM(ExciseTax) AS TotalExciseTax
    FROM sales
    GROUP BY VendorNo, Brand
)

SELECT 
    ps.VendorNumber,
    ps.VendorName,
    ps.Brand,
    ps.Description,
    ps.PurchasePrice,
    ps.ActualPrice,
    ps.Volume,
    ps.TotalPurchaseQuantity,
    ps.TotalPurchaseDollars,
    ss.TotalSalesQuantity,
    ss.TotalSalesDollars,
    ss.TotalSalesPrice,
    ss.TotalExciseTax,
    fs.FreightCost
FROM PurchaseSummary ps
LEFT JOIN SalesSummary ss
    ON ps.VendorNumber = ss.VendorNo
    AND ps.Brand = ss.Brand
LEFT JOIN FreightSummary fs
    ON ps.VendorNumber = fs.VendorNumber
ORDER BY ps.TotalPurchaseDollars DESC""", conn)


# In[21]:


vendor_sales_summary


# This query generates a vendor-wise sales and purchase summary, which is valuable for:
# 
# **Performance Optimization:**
# - The query involves heavy joins and aggregations on large datasets like sales and purchases.
# - Storing the pre-aggregated results avoids repeated expensive computations.
# - Helps in analyzing sales, purchases, and pricing for different vendors and brands.
# - Future benefits of storing this data for faster dashboarding and reporting.
# - Instead of running expensive queries each time, dashboards can fetch data quickly from vendor_sales_summary.

# In[22]:


#checking data types of each column
vendor_sales_summary.dtypes


# In[23]:


#checking missing values
vendor_sales_summary.isnull().sum()


# In[24]:


vendor_sales_summary['VendorName'].unique()


# In[25]:


#changing the data type of 'Volume'
vendor_sales_summary['Volume'] = vendor_sales_summary['Volume'].astype('float64')


# In[26]:


#filling missing values
vendor_sales_summary.fillna(0, inplace=True)


# In[27]:


# striping white spaces in VendorName column
vendor_sales_summary['VendorName'] = vendor_sales_summary['VendorName'].str.strip()


# In[28]:


#creating new features
vendor_sales_summary['GrossProfit'] = vendor_sales_summary['TotalSalesDollars'] - vendor_sales_summary['TotalPurchaseDollars']


# In[29]:


vendor_sales_summary['ProfitMargin'] = (vendor_sales_summary['GrossProfit']/vendor_sales_summary['TotalSalesDollars'])*100


# In[30]:


vendor_sales_summary['StockTurnover'] = vendor_sales_summary['TotalSalesQuantity']/vendor_sales_summary['TotalPurchaseQuantity']


# In[31]:


vendor_sales_summary['SalestoPurchaseRatio'] = vendor_sales_summary['TotalSalesDollars']/vendor_sales_summary['TotalPurchaseDollars']


# In[32]:


vendor_sales_summary.columns


# In[33]:


cursor = conn.cursor()


# In[34]:


#creating our final table
cursor.execute("""CREATE TABLE vendor_sales_summary (
    VendorNumber INT,
    VendorName VARCHAR(100),
    Brand INT,
    Description VARCHAR(100),
    PurchasePrice DECIMAL(10,2),
    ActualPrice DECIMAL(10,2),
    Volume ,
    TotalPurchaseQuantity INT,
    TotalPurchaseDollars DECIMAL(15,2),
    TotalSalesQuantity INT,
    TotalSalesDollars DECIMAL(15,2),
    TotalSalesPrice DECIMAL(15,2),
    TotalExciseTax DECIMAL(15,2),
    FreightCost DECIMAL(15,2),
    GrossProfit DECIMAL(15,2),
    ProfitMargin DECIMAL(15,2),
    StockTurnover DECIMAL(15,2),
    SalestoPurchaseRatio DECIMAL(15,2),
    PRIMARY KEY (VendorNumber, Brand)
);
""")


# In[35]:


pd.read_sql_query("SELECT * FROM vendor_sales_summary",conn)


# In[36]:


vendor_sales_summary.to_sql('vendor_sales_summary', conn, if_exists='replace', index=False)


# In[37]:


#adding data into the table
pd.read_sql_query("SELECT * FROM vendor_sales_summary",conn)


# In[48]:


import sqlite3
import pandas as pd
import logging
from ingestion_db import ingest_db

logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s-%(levelname)s-%(message)s",
    filemode="a"
)

def create_vendor_summary(conn):
    '''This function will merge different tables to get the overall vendor summary and adding new columns in the resultant data'''
    vendor_sales_summary=pd.read_sql_query("""WITH FreightSummary AS (
        SELECT VendorNumber, SUM(Freight) AS FreightCost
        FROM vendor_invoice
        GROUP BY VendorNumber
    ),
    
    PurchaseSummary AS (
        SELECT 
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Price AS ActualPrice,
            pp.Volume,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) AS TotalPurchaseDollars
        FROM purchases p
        JOIN purchase_prices pp
            ON p.Brand = pp.Brand
        WHERE p.PurchasePrice > 0
        GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
    ),
    
    SalesSummary AS (
        SELECT 
            VendorNo,
            Brand,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(ExciseTax) AS TotalExciseTax
        FROM sales
        GROUP BY VendorNo, Brand
    )
    
    SELECT 
        ps.VendorNumber,
        ps.VendorName,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.FreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber = ss.VendorNo
        AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""", conn)

    return vendor_sales_summary

def clean_data(df):
    '''This function will clean the data'''
    #changing the data type of 'Volume' to float
    df['Volume'] = df['Volume'].astype('float64')

    #filling missing value with 0
    df.fillna(0, inplace=True)

    #removing spaces from categorical columns
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()

    #creating new columns for better analysis
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = (df['GrossProfit']/df['TotalSalesDollars'])*100
    df['StockTurnover'] = df['TotalSalesQuantity']/df['TotalPurchaseQuantity']
    df['SalestoPurchaseRatio'] = df['TotalSalesDollars']/df['TotalPurchaseDollars']

    return df

if __name__=='__main__':
    #creating db connection
    conn=sqlite3.connect('inventory.db')

    logging.info('Creating vendor summary table...')
    summary_df=create_vendor_summary(conn)
    logging.info(summary_df.head())

    logging.info('Cleaning data...')
    clean_df=clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('Ingesting data...')
    ingest_db(clean_df,'vendor_sales_summary',conn)
    logging.info('Completed')


# In[49]:


vendor_sales_summary.head()

