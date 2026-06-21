#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import sqlite3
from scipy.stats import ttest_ind
import scipy.stats as stats
warnings.filterwarnings('ignore')


# ## Loading the dataset

# In[2]:


#creating database connection
conn=sqlite3.connect('inventory.db')

#fetching vendor summary data
df=pd.read_sql_query("select * from vendor_sales_summary",conn)
df.head()


# ## Exploratory Data Analysis

# - Previously, we examined various tables in the database to identify key variables, understand their relationships, and determine which ones should be included in the final analysis.
# - In this phase of EDA, we will analyze the resultant table to gain insights into the distribution of each column. This will help us understand the data patterns, identify anomalies, and ensure data quality before proceeding with further analysis.

# In[3]:


#summary statistics
df.describe().T


# In[4]:


#Distribution plots for numerical columns
numerical_cols = df.select_dtypes(include=np.number).columns

plt.figure(figsize=(15,10))
for i,col in enumerate(numerical_cols):
    plt.subplot(4,4,i+1) #adjust grid layout as needed
    sns.histplot(df[col], kde=True, bins=30)
    plt.title(col)
plt.tight_layout()
plt.show()


# In[5]:


#Outlier detection with boxplots
plt.figure(figsize=(15,10))
for i,col in enumerate(numerical_cols):
    plt.subplot(4,4,i+1)
    sns.boxplot(y=df[col])
    plt.title(col)
plt.tight_layout()
plt.show()


# ## Summary Statistics Insights:
# 
# ### Negative and zero values:
# - Gross Profit: Minimum value is -52002.78, indicating losses. Some products or transactions may be selling at a loss due to high costs or selling at discounts lower than the purchase price.
# - Profit Margin: Has a minimum of -inf, which suggests cases where revenue is zero or even lower than costs.
# - Total Sales Quantity and Sales Dollars: Minimum values are 0, meaning some products were purchased but never sold. These could be slow-moving or obsolete stock.
# 
# ### Outliers indicated by high standard deviations:
# - Purchase and Actual Prices: The max values (5,681.81 & 7,499.99) are significantly higher than the mean (24.39 & 35.64), indicating potential premium products.
# - Freight Cost: Huge variation, from 0.09 to 257,032.07, suggests logistics inefficiencies or bulk shipments.
# - Stock Turnover: Ranges from 0 to 274.5, implying some products sell extremely fast while others remain in stock indefinitely. A value greater than one means that sales are being fulfilled from older stock, which means that the sold quantity of that product is greater than the purchased quantity.

# In[6]:


#lets filter the data by removing inconsistencies
df = pd.read_sql_query("""SELECT * FROM vendor_sales_summary
WHERE GrossProfit > 0
AND ProfitMargin > 0
AND TotalSalesQuantity > 0""", conn)


# In[7]:


df


# In[8]:


#Distribution plots for numerical columns
numerical_cols = df.select_dtypes(include=np.number).columns

plt.figure(figsize=(15,10))
for i,col in enumerate(numerical_cols):
    plt.subplot(4,4,i+1) #adjust grid layout as needed
    sns.histplot(df[col], kde=True, bins=30)
    plt.title(col)
plt.tight_layout()
plt.show()


# In[9]:


#Count plots for categorical columns
categorical_cols = ["VendorName", "Description"]
plt.figure(figsize=(12,5))
for i, col in enumerate(categorical_cols):
    plt.subplot(1,2,i+1)
    sns.countplot(y=df[col], order=df[col].value_counts().index[:10]) #Top 10 categories
    plt.title(f"Count plot of {col}")
plt.tight_layout()
plt.show()


# In[10]:


#Correlation Heatmap
plt.figure(figsize=(12,8))
correlation_matrix=df[numerical_cols].corr()
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
plt.title("Correlation Heatmap")
plt.show()


# ## Correlation Insights
# - PurchasePrice has weak correlations with TotalSalesDollars (-0.012) and GrossProfit (-0.016), suggesting that price variations do not significantly impact sales revenue or profit.
# - Strong correlation between total purchase quantity and total sales quantity (0.999), confirming efficient inventory turnover.
# - Negative correlation between profit margin and total sales price (-0.179) suggests that as sales price increases, margins decrease, possibly due to competitive pricing pressures.
# - StockTurnover has weak negative correlations with both GrossProfit (-0.038) and ProfitMargin (-0.055), indicating that faster turnover does not necessarily result in higher profitability.

# # Data Analysis
# 
# #### Identify brands that needs promotional or pricing adjustments, which exhibit lower sales performance but higher profit margins.

# In[11]:


brand_performance = df.groupby('Description').agg({'TotalSalesDollars':'sum', 'ProfitMargin':'mean'}).reset_index()


# In[12]:


low_sales_threshold=brand_performance['TotalSalesDollars'].quantile(0.15)
high_margin_threshold=brand_performance['ProfitMargin'].quantile(0.85)


# In[13]:


low_sales_threshold


# In[14]:


high_margin_threshold


# In[15]:


# Filter brands with low sales but high profit margins
target_brands = brand_performance[
    (brand_performance['TotalSalesDollars'] <= low_sales_threshold) & 
    (brand_performance['ProfitMargin'] >= high_margin_threshold)
]
print("Brands with Low Sales but High Profit Margins:")
display(target_brands.sort_values('TotalSalesDollars'))


# In[16]:


brand_performance=brand_performance[brand_performance['TotalSalesDollars']<10000] #for better visualization


# In[17]:


plt.figure(figsize=(10, 6))
sns.scatterplot(data=brand_performance, x='TotalSalesDollars', y='ProfitMargin', color="blue", label="All Brands", alpha = 0.2)
sns.scatterplot(data=target_brands, x='TotalSalesDollars', y='ProfitMargin', color="red", label="Target Brands")

plt.axhline(high_margin_threshold, linestyle='--', color='black', label="High Margin Threshold")
plt.axvline(low_sales_threshold, linestyle='--', color='black', label="Low Sales Threshold")

plt.xlabel("Total Sales ($)")
plt.ylabel("Profit Margin (%)")
plt.title("Brands for Promotional or Pricing Adjustments")
plt.legend()
plt.grid(True)
plt.show()


# #### Which vendors and brands demonstrate the highest sales performance?

# In[18]:


def format_dollars(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return str(value)


# In[19]:


#Top Vendors & Brands by Sales Performance
top_vendors = df.groupby("VendorName")["TotalSalesDollars"].sum().nlargest(10)
top_brands= df.groupby ("Description")["TotalSalesDollars"].sum().nlargest(10)
top_vendors


# In[20]:


top_brands


# In[21]:


top_brands.apply(lambda x: format_dollars(x))


# In[22]:


plt.figure(figsize=(15, 5))

#Plot for Top Vendors
plt.subplot(1, 2, 1)
ax1=sns.barplot(y=top_vendors.index, x=top_vendors.values, palette="Blues_r") 
plt.title("Top 10 Vendors by Sales")

for bar in ax1.patches:
    ax1.text(bar.get_width() + (bar.get_width()*0.02), 
             bar.get_y() + bar.get_height() / 2, 
             format_dollars(bar.get_width()), 
             ha='left', va='center', fontsize=10, color='black')

#Plot for Top Brands
plt.subplot(1, 2, 2)
ax2=sns.barplot(y=top_brands.index.astype(str), x=top_brands.values, palette="Reds_r") 
plt.title("Top 10 Brands by Sales")

for bar in ax2.patches:
    ax2.text(bar.get_width() + (bar.get_width() * 0.02), 
             bar.get_y() + bar.get_height() / 2, 
             format_dollars(bar.get_width()), 
             ha='left', va='center', fontsize=10, color='black')

plt.tight_layout()
plt.show()


# #### Which vendors contribute the most to total purchase dollars?

# In[23]:


vendor_performance = df.groupby('VendorName').agg({
    'TotalPurchaseDollars':'sum',
    'GrossProfit':'sum', 
    'TotalSalesDollars':'sum'
}).reset_index()
vendor_performance.shape


# In[24]:


vendor_performance['PurchaseContribution%']=vendor_performance['TotalPurchaseDollars']/vendor_performance['TotalPurchaseDollars'].sum()*100
vendor_performance=round(vendor_performance.sort_values('PurchaseContribution%', ascending=False),2)


# In[25]:


#Display Top 10 Vendors
top_vendors=vendor_performance.head(10)
top_vendors['TotalSalesDollars'] = top_vendors['TotalSalesDollars'].apply(format_dollars)
top_vendors['TotalPurchaseDollars'] = top_vendors['TotalPurchaseDollars'].apply(format_dollars)
top_vendors['GrossProfit'] = top_vendors['GrossProfit'].apply(format_dollars)

top_vendors


# In[26]:


top_vendors['Cummulative_Contribution%']=top_vendors['PurchaseContribution%'].cumsum()
top_vendors


# In[27]:


fig, ax1 = plt.subplots(figsize=(10, 6))

#Bar plot for Purchase Contribution%
sns.barplot(x=top_vendors['VendorName'], y=top_vendors['PurchaseContribution%'], palette="mako", ax=ax1)

for i, value in enumerate(top_vendors['PurchaseContribution%']):
    ax1.text(i, value - 1, str(value)+'%', ha='center', fontsize=10, color='white')

#Line Plot for Cumulative Contribution%
ax2=ax1.twinx()
ax2.plot(top_vendors['VendorName'], top_vendors['Cummulative_Contribution%'], color='red', marker='o', linestyle='dashed', label='Cummulative Contribution %')

ax1.set_xticklabels(top_vendors['VendorName'], rotation=90)
ax1.set_ylabel('Purchase Contribution %', color='blue')
ax2.set_ylabel('Cummulative Contribution %', color='red')
ax1.set_xlabel('Vendors')
ax1.set_title('Pareto Chart: Vendor Contribution to Total Purchases')

ax2.axhline(y=100, color='gray', linestyle='dashed', alpha=0.7)
ax2.legend(loc='upper right')

plt.show()


# #### How much of total procurement is dependent on the top vendors?

# In[28]:


print(f"Total purchase contribution of top 10 vendors is {round(top_vendors['PurchaseContribution%'].sum(),2)}%")


# In[29]:


vendors = list(top_vendors['VendorName'].values)
purchase_contributions = list(top_vendors['PurchaseContribution%'].values)
total_contribution = sum(purchase_contributions)
remaining_contribution = 100 - total_contribution

#Append "Other Vendors" category I
vendors.append("Other Vendors")
purchase_contributions.append(remaining_contribution)

#Donut Chart
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(purchase_contributions, labels=vendors, autopct='%1.1f%%', 
                                  startangle=140, pctdistance=0.85, colors=plt.cm.Paired.colors)

#Draw a white circle in the center to create a "donut" effect
centre_circle = plt.Circle((0, 0), 0.70, fc='white')
fig.gca().add_artist(centre_circle)

#Add Total Contribution annotation in the center
plt.text(0, 0, f"Top 10 Total:\n{total_contribution:.2f}%", fontsize=14, fontweight='bold', ha='center', va='center')

plt.title("Top 10 Vendor's Purchase Contribution (%)")
plt.show()


# #### Does purchasing in bulk reduce the unit price, and what is the optimal purchase volume for cost savings?

# In[30]:


df['UnitPurchasePrice']=df['TotalPurchaseDollars']/df['TotalPurchaseQuantity']


# In[31]:


df['OrderSize']=pd.qcut(df['TotalPurchaseQuantity'], q=3, labels=['Small','Medium','Large'])


# In[32]:


df[['OrderSize','TotalPurchaseQuantity']]


# In[33]:


df.groupby('OrderSize')[['UnitPurchasePrice']].mean()


# In[34]:


plt.figure(figsize=(10,6))
sns.boxplot(data=df, x='OrderSize', y='UnitPurchasePrice', palette='Set2')
plt.title('Impact of bulk purchasing on unit price')
plt.xlabel('Order size')
plt.ylabel('Average unit purchase price')
plt.show()


# - Vendors buying in bulk (Large order size) get the lowest unit price ($10.78 per unit), meaning higher margins if they can manage inventory efficiently.
# - The price difference between small and large orders is substantial (~72% reduction in unit cost).
# - This suggests that bulk pricing strategies successfully encourage vendors to purchase in large volumes, leading to higher overall sales despite lower per-unit revenue.

# #### Which vendors have low inventory turnover, indicating excess stock and slow-moving products?

# In[35]:


df[df['StockTurnover']<1].groupby('VendorName')[['StockTurnover']].mean().sort_values('StockTurnover', ascending=True).head(10)


# #### How much capital is locked in unsold inventory per vendor, and which vendors contribute the most to it?

# In[36]:


df['UnsoldInventoryValue']=(df['TotalPurchaseQuantity']-df['TotalSalesQuantity'])*df['PurchasePrice']
print('Total unsold capital: ', format_dollars(df['UnsoldInventoryValue'].sum()))


# In[37]:


#Aggregate capital locked per vendor
inventory_value_per_vendor=df.groupby('VendorName')['UnsoldInventoryValue'].sum().reset_index()

#Sort vendors with the highest locked capital
inventory_value_per_vendor=inventory_value_per_vendor.sort_values(by='UnsoldInventoryValue', ascending=False)
inventory_value_per_vendor['UnsoldInventoryValue']=inventory_value_per_vendor['UnsoldInventoryValue'].apply(format_dollars)
inventory_value_per_vendor.head(10)


# #### What is the 95% confidence intervals for profit margins of top-performing and low-performing vendors?

# In[38]:


top_threshold=df['TotalSalesDollars'].quantile(0.75)
low_threshold=df['TotalSalesDollars'].quantile(0.25)


# In[39]:


top_vendors=df[df['TotalSalesDollars'] >= top_threshold]['ProfitMargin'].dropna()
low_vendors=df[df['TotalSalesDollars'] <= low_threshold]['ProfitMargin'].dropna()


# In[40]:


top_vendors


# In[41]:


def confidence_interval(data, confidence=0.95):
    mean_val=np.mean(data)
    std_err=np.std(data, ddof=1)/np.sqrt(len(data)) #Standard error
    t_critical=stats.t.ppf((1+confidence)/2, df=len(data)-1)
    margin_of_error=t_critical*std_err
    return mean_val, mean_val-margin_of_error, mean_val+margin_of_error


# In[42]:


top_mean, top_lower, top_upper=confidence_interval(top_vendors)
low_mean, low_lower, low_upper=confidence_interval(low_vendors)

print(f"Top Vendors 95% CI: ({top_lower:.2f}, {top_upper:.2f}), Mean: {top_mean:.2f}") 
print(f"Low Vendors 95% CI: ({low_lower:.2f}, {low_upper:.2f}), Mean: {low_mean:.2f}")

plt.figure(figsize=(12, 6))

#Top Vendors Plot
sns.histplot(top_vendors, kde=True, color="blue", bins=30, alpha=0.5, label="Top Vendors")
plt.axvline(top_lower, color="blue", linestyle="--", label=f"Top Lower: {top_lower:.2f}")
plt.axvline(top_upper, color="blue", linestyle="--", label=f"Top Upper: {top_upper:.2f}") 
plt.axvline(top_mean, color="blue", linestyle="-", label=f"Top Mean: {top_mean:.2f}")

#Low Vendors Plot
sns.histplot(low_vendors, kde=True, color="red", bins=30, alpha=0.5, label="Low Vendors")
plt.axvline(low_lower, color="red", linestyle="--", label=f"Low Lower: {low_lower:.2f}")
plt.axvline(low_upper, color="red", linestyle="--", label=f"Low Upper: {low_upper:.2f}")
plt.axvline(low_mean, color="red", linestyle="-", label=f"Low Mean: {low_mean:.2f}")

#Finalize Plot
plt.title('Confidence interval comparison: Top vs. Low Vendors (Profit Margin)')
plt.xlabel('Profit Margin(%)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True)
plt.show()


# - The confidence interval for low-performing vendors (40.48% to 42.62%) is significantly higher than that of top-performing vendors (30.74% to 31.61%).
# - This suggests that vendors with lower sales tend to maintain higher profit margins, potentially due to premium pricing or lower operational costs.
# - For High-Performing Vendors: If they aim to improve profitability, they could explore selective price adjustments, cost optimization, or bundling strategies.
# - For Low-Performing Vendors: Despite higher margins, their low sales volume might indicate a need for better marketing, competitive pricing, or improved distribution strategies.

# #### Is there a significant difference in profit margins between top-performing and low-performing vendors?

# Hypothesis:
# 
# $H_{0}$ (Null Hypothesis): There is no significant difference in the mean profit margins of top-performing and low-performing vendors.
# 
# $H_{1}$ (Alternative Hypothesis): The mean profit margins of top-performing and low-performing vendors are significantly different.

# In[43]:


top_threshold = df["TotalSalesDollars"].quantile(0.75)
low_threshold = df["TotalSalesDollars"].quantile(0.25)

top_vendors = df[df["TotalSalesDollars"] >= top_threshold]["ProfitMargin"].dropna()
low_vendors = df[df["TotalSalesDollars"] <= low_threshold]["ProfitMargin"].dropna()

#Perform Two-Sample T-Test
t_stat, p_value = ttest_ind(top_vendors, low_vendors, equal_var=False)

#Print results
print(f"T-Statistic: {t_stat:.4f}, P-Value: {p_value:.4f}")
if p_value < 0.05:
    print("Reject Ho: There is a significant difference in profit margins between top and low-performing vendors.")
else:
    print("Fail to Reject Ho: No significant difference in profit margins.")


# In[44]:


df.to_csv("vendor_sales_summary.csv", index=False)

