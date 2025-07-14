import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mysql.connector
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

class SalesAnalytics:
    def __init__(self):
        self.connection = None
        self.data = None
        
    def connect_to_database(self, host: str, user: str, password: str, database: str) -> bool:
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="sales_data"
            )
            return True
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            return False
    
    def load_data(self) -> pd.DataFrame:
        """Load data from MySQL database for last 6 months"""
        try:
            # Calculate date range for last 6 months
            end_date = datetime.now().replace(day=31, month=5, year=2025)  # End of May 2025
            start_date = end_date - timedelta(days=180) 
            
            query = f"""
            SELECT * FROM your_table_name 
            WHERE orderDate >= '{start_date.strftime('%Y-%m-%d')}' 
            AND orderDate <= '{end_date.strftime('%Y-%m-%d')}'
            """
            
            self.data = pd.read_sql(query, self.connection)
            
            # Data preprocessing
            self.data['orderDate'] = pd.to_datetime(self.data['orderDate'])
            self.data['totalProductPrice'] = pd.to_numeric(self.data['totalProductPrice'], errors='coerce')
            self.data['quantity'] = pd.to_numeric(self.data['quantity'], errors='coerce')
            self.data['sellingPrice'] = pd.to_numeric(self.data['sellingPrice'], errors='coerce')
            
            # Create month-year column for analysis
            self.data['month_year'] = self.data['orderDate'].dt.to_period('M')
            
            return self.data
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None
    
    def get_brand_wise_sales(self, selected_stores: List[str] = None) -> pd.DataFrame:
        """Analysis 1: Brand wise sales for last 6 months"""
        data = self.data.copy()
        
        if selected_stores:
            data = data[data['storeName'].isin(selected_stores)]
        
        brand_sales = data.groupby(['brandName', 'month_year']).agg({
            'totalProductPrice': 'sum',
            'quantity': 'sum'
        }).reset_index()
        
        return brand_sales
    
    def get_store_brand_growth(self, selected_brands: List[str] = None) -> pd.DataFrame:
        """Analysis 2: Per store brand wise average sales growth over last 6 months"""
        data = self.data.copy()
        
        if selected_brands:
            data = data[data['brandName'].isin(selected_brands)]
        
        # Calculate monthly sales per store-brand combination
        store_brand_monthly = data.groupby(['storeName', 'brandName', 'month_year']).agg({
            'totalProductPrice': 'sum'
        }).reset_index()
        
        # Calculate growth rate
        growth_data = []
        for store in store_brand_monthly['storeName'].unique():
            for brand in store_brand_monthly['brandName'].unique():
                store_brand_data = store_brand_monthly[
                    (store_brand_monthly['storeName'] == store) & 
                    (store_brand_monthly['brandName'] == brand)
                ].sort_values('month_year')
                
                if len(store_brand_data) > 1:
                    # Calculate month-over-month growth
                    store_brand_data['growth_rate'] = store_brand_data['totalProductPrice'].pct_change() * 100
                    avg_growth = store_brand_data['growth_rate'].mean()
                    
                    growth_data.append({
                        'storeName': store,
                        'brandName': brand,
                        'avg_growth_rate': avg_growth,
                        'total_sales': store_brand_data['totalProductPrice'].sum()
                    })
        
        return pd.DataFrame(growth_data)
    
    def get_top_sku_growth(self, selected_brand: str) -> pd.DataFrame:
        """Analysis 3: Top 5 SKU and their growth for selected brand"""
        if not selected_brand:
            return pd.DataFrame()
        
        brand_data = self.data[self.data['brandName'] == selected_brand]
        
        # Get top 5 SKUs by sales volume
        top_skus = brand_data.groupby('productName').agg({
            'totalProductPrice': 'sum',
            'quantity': 'sum'
        }).sort_values('totalProductPrice', ascending=False).head(5)
        
        # Calculate growth for top SKUs
        sku_growth_data = []
        for sku in top_skus.index:
            sku_data = brand_data[brand_data['productName'] == sku]
            monthly_sales = sku_data.groupby('month_year')['totalProductPrice'].sum().sort_index()
            
            if len(monthly_sales) > 1:
                growth_rate = ((monthly_sales.iloc[-1] - monthly_sales.iloc[0]) / monthly_sales.iloc[0]) * 100
            else:
                growth_rate = 0
            
            sku_growth_data.append({
                'productName': sku,
                'total_sales': top_skus.loc[sku, 'totalProductPrice'],
                'total_quantity': top_skus.loc[sku, 'quantity'],
                'growth_rate': growth_rate
            })
        
        return pd.DataFrame(sku_growth_data)
    
    def get_tier_region_breakdown(self, selected_brands: List[str] = None) -> Dict:
        """Analysis 4: Tier wise and region wise breakup of brand sales"""
        data = self.data.copy()
        
        if selected_brands:
            data = data[data['brandName'].isin(selected_brands)]
        
        # Create tier classification based on store sales volume
        store_sales = data.groupby('storeName')['totalProductPrice'].sum()
        
        # Define tiers based on quartiles
        q75 = store_sales.quantile(0.75)
        q50 = store_sales.quantile(0.50)
        q25 = store_sales.quantile(0.25)
        
        def assign_tier(sales):
            if sales >= q75:
                return 'Tier 1'
            elif sales >= q50:
                return 'Tier 2'
            elif sales >= q25:
                return 'Tier 3'
            else:
                return 'Tier 4'
        
        # Add tier information to data
        store_tier_map = store_sales.apply(assign_tier).to_dict()
        data['tier'] = data['storeName'].map(store_tier_map)
        
        # For region, we'll use first part of store name or create dummy regions
        data['region'] = data['storeName'].str.split().str[0]  # Simplified region extraction
        
        # Calculate tier-wise breakdown
        tier_breakdown = data.groupby(['tier', 'brandName'])['totalProductPrice'].sum().reset_index()
        
        # Calculate region-wise breakdown
        region_breakdown = data.groupby(['region', 'brandName'])['totalProductPrice'].sum().reset_index()
        
        return {
            'tier_breakdown': tier_breakdown,
            'region_breakdown': region_breakdown
        }

def create_sample_data():
    """Create sample data for demonstration"""
    np.random.seed(42)
    
    brands = ['Apple', 'Samsung', 'Nike', 'Adidas', 'Coca-Cola', 'Pepsi', 'Nestle', 'Unilever']
    stores = ['Store_Mumbai_1', 'Store_Delhi_1', 'Store_Bangalore_1', 'Store_Chennai_1', 
              'Store_Mumbai_2', 'Store_Delhi_2', 'Store_Kolkata_1', 'Store_Pune_1']
    products = {
        'Apple': ['iPhone 14', 'iPhone 13', 'MacBook Air', 'iPad', 'AirPods'],
        'Samsung': ['Galaxy S23', 'Galaxy Note', 'Galaxy Tab', 'Galaxy Buds', 'Galaxy Watch'],
        'Nike': ['Air Max', 'Air Force 1', 'React', 'Pegasus', 'Dunk'],
        'Adidas': ['Ultraboost', 'Stan Smith', 'Gazelle', 'Superstar', 'NMD'],
        'Coca-Cola': ['Coke Classic', 'Diet Coke', 'Coke Zero', 'Sprite', 'Fanta'],
        'Pepsi': ['Pepsi Classic', 'Diet Pepsi', 'Mountain Dew', '7UP', 'Mirinda'],
        'Nestle': ['KitKat', 'Maggi', 'Nescafe', 'Cerelac', 'Lactogen'],
        'Unilever': ['Dove', 'Lifebuoy', 'Surf Excel', 'Rin', 'Fair & Lovely']
    }
    
    # Generate sample data for last 6 months
    start_date = datetime(2024, 12, 1)
    end_date = datetime(2025, 5, 31)
    
    data = []
    for _ in range(5000):  # Generate 5000 sample records
        brand = np.random.choice(brands)
        store = np.random.choice(stores)
        product = np.random.choice(products[brand])
        
        order_date = start_date + timedelta(days=np.random.randint(0, (end_date - start_date).days))
        quantity = np.random.randint(1, 10)
        price = np.random.uniform(100, 5000)
        total_price = quantity * price
        
        data.append({
            'orderDate': order_date,
            'brandName': brand,
            'storeName': store,
            'productName': product,
            'quantity': quantity,
            'sellingPrice': price,
            'totalProductPrice': total_price
        })
    
    df = pd.DataFrame(data)
    df['month_year'] = df['orderDate'].dt.to_period('M')
    return df

def main():
    st.markdown('<h1 class="main-header">📊 Sales Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize analytics
    analytics = SalesAnalytics()
    
    # Sidebar for database connection
    st.sidebar.header("🔗 Database Connection")
    
    # Database connection toggle
    use_sample_data = st.sidebar.checkbox("Use Sample Data (for demo)", value=True)
    
    if not use_sample_data:
        host = st.sidebar.text_input("Host", value="localhost")
        user = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        database = st.sidebar.text_input("Database Name")
        
        if st.sidebar.button("Connect to Database"):
            if analytics.connect_to_database(host, user, password, database):
                st.sidebar.success("Connected successfully!")
                data = analytics.load_data()
            else:
                st.sidebar.error("Connection failed!")
                return
    else:
        # Use sample data
        data = create_sample_data()
        analytics.data = data
        st.sidebar.success("Using sample data!")
    
    if analytics.data is not None:
        # Sidebar filters
        st.sidebar.header("🎛️ Filters")
        
        # Brand selector
        brands = ['All'] + sorted(analytics.data['brandName'].unique().tolist())
        selected_brands = st.sidebar.multiselect(
            "Select Brands",
            options=brands,
            default=['All']
        )
        
        if 'All' in selected_brands:
            selected_brands = analytics.data['brandName'].unique().tolist()
        
        # Store selector
        stores = ['All'] + sorted(analytics.data['storeName'].unique().tolist())
        selected_stores = st.sidebar.multiselect(
            "Select Stores",
            options=stores,
            default=['All']
        )
        
        if 'All' in selected_stores:
            selected_stores = analytics.data['storeName'].unique().tolist()
        
        # Single brand selector for SKU analysis
        single_brand = st.sidebar.selectbox(
            "Select Brand for SKU Analysis",
            options=sorted(analytics.data['brandName'].unique().tolist())
        )
        
        # Main dashboard
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Brand Sales", 
            "🏪 Store Growth", 
            "🛍️ Top SKUs", 
            "🗺️ Tier & Region"
        ])
        
        with tab1:
            st.header("Brand-wise Sales Analysis (Last 6 Months)")
            
            # Get brand sales data
            brand_sales = analytics.get_brand_wise_sales(selected_stores)
            
            if not brand_sales.empty:
                # Filter by selected brands
                brand_sales_filtered = brand_sales[brand_sales['brandName'].isin(selected_brands)]
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_sales = brand_sales_filtered['totalProductPrice'].sum()
                    st.metric("Total Sales", f"₹{total_sales:,.0f}")
                
                with col2:
                    total_quantity = brand_sales_filtered['quantity'].sum()
                    st.metric("Total Quantity", f"{total_quantity:,.0f}")
                
                with col3:
                    avg_monthly_sales = brand_sales_filtered.groupby('month_year')['totalProductPrice'].sum().mean()
                    st.metric("Avg Monthly Sales", f"₹{avg_monthly_sales:,.0f}")
                
                with col4:
                    unique_brands = brand_sales_filtered['brandName'].nunique()
                    st.metric("Active Brands", unique_brands)
                
                # Monthly trend chart
                monthly_trend = brand_sales_filtered.groupby(['month_year', 'brandName'])['totalProductPrice'].sum().reset_index()
                monthly_trend['month_year_str'] = monthly_trend['month_year'].astype(str)
                
                fig1 = px.line(
                    monthly_trend, 
                    x='month_year_str', 
                    y='totalProductPrice', 
                    color='brandName',
                    title='Monthly Sales Trend by Brand',
                    labels={'totalProductPrice': 'Sales (₹)', 'month_year_str': 'Month'}
                )
                fig1.update_layout(height=500)
                st.plotly_chart(fig1, use_container_width=True)
                
                # Brand comparison bar chart
                brand_total = brand_sales_filtered.groupby('brandName')['totalProductPrice'].sum().sort_values(ascending=True)
                
                fig2 = px.bar(
                    x=brand_total.values,
                    y=brand_total.index,
                    orientation='h',
                    title='Total Sales by Brand (6 Months)',
                    labels={'x': 'Sales (₹)', 'y': 'Brand'}
                )
                fig2.update_layout(height=600)
                st.plotly_chart(fig2, use_container_width=True)
        
        with tab2:
            st.header("Store-wise Brand Growth Analysis")
            
            growth_data = analytics.get_store_brand_growth(selected_brands)
            
            if not growth_data.empty:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_growth = growth_data['avg_growth_rate'].mean()
                    st.metric("Average Growth Rate", f"{avg_growth:.1f}%")
                
                with col2:
                    top_performer = growth_data.loc[growth_data['avg_growth_rate'].idxmax()]
                    st.metric("Top Performer", f"{top_performer['storeName']}")
                
                with col3:
                    total_stores = growth_data['storeName'].nunique()
                    st.metric("Total Stores", total_stores)
                
                # Growth heatmap
                growth_pivot = growth_data.pivot(index='storeName', columns='brandName', values='avg_growth_rate')
                
                fig3 = px.imshow(
                    growth_pivot.values,
                    x=growth_pivot.columns,
                    y=growth_pivot.index,
                    title='Growth Rate Heatmap (Store vs Brand)',
                    labels={'color': 'Growth Rate (%)'},
                    color_continuous_scale='RdYlGn'
                )
                fig3.update_layout(height=600)
                st.plotly_chart(fig3, use_container_width=True)
                
                # Top growing store-brand combinations
                st.subheader("Top 10 Growing Store-Brand Combinations")
                top_growth = growth_data.nlargest(10, 'avg_growth_rate')[
                    ['storeName', 'brandName', 'avg_growth_rate', 'total_sales']
                ]
                st.dataframe(top_growth, use_container_width=True)
        
        with tab3:
            st.header(f"Top SKU Analysis - {single_brand}")
            
            sku_data = analytics.get_top_sku_growth(single_brand)
            
            if not sku_data.empty:
                # SKU performance metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    top_sku = sku_data.loc[sku_data['total_sales'].idxmax(), 'productName']
                    st.metric("Top Selling SKU", top_sku)
                
                with col2:
                    fastest_growing = sku_data.loc[sku_data['growth_rate'].idxmax(), 'productName']
                    st.metric("Fastest Growing SKU", fastest_growing)
                
                # SKU sales chart
                fig4 = px.bar(
                    sku_data,
                    x='productName',
                    y='total_sales',
                    title=f'Top 5 SKUs Sales - {single_brand}',
                    labels={'total_sales': 'Total Sales (₹)', 'productName': 'Product'}
                )
                fig4.update_layout(height=400)
                st.plotly_chart(fig4, use_container_width=True)
                
                # SKU growth chart
                fig5 = px.bar(
                    sku_data,
                    x='productName',
                    y='growth_rate',
                    title=f'SKU Growth Rate - {single_brand}',
                    labels={'growth_rate': 'Growth Rate (%)', 'productName': 'Product'},
                    color='growth_rate',
                    color_continuous_scale='RdYlGn'
                )
                fig5.update_layout(height=400)
                st.plotly_chart(fig5, use_container_width=True)
                
                # Detailed SKU table
                st.subheader("Detailed SKU Performance")
                st.dataframe(sku_data, use_container_width=True)
        
        with tab4:
            st.header("Tier & Region Analysis")
            
            breakdown_data = analytics.get_tier_region_breakdown(selected_brands)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Tier-wise Sales Breakdown")
                tier_data = breakdown_data['tier_breakdown']
                
                if not tier_data.empty:
                    tier_summary = tier_data.groupby('tier')['totalProductPrice'].sum().sort_values(ascending=False)
                    
                    fig6 = px.pie(
                        values=tier_summary.values,
                        names=tier_summary.index,
                        title='Sales Distribution by Tier'
                    )
                    st.plotly_chart(fig6, use_container_width=True)
                    
                    st.dataframe(tier_data, use_container_width=True)
            
            with col2:
                st.subheader("Region-wise Sales Breakdown")
                region_data = breakdown_data['region_breakdown']
                
                if not region_data.empty:
                    region_summary = region_data.groupby('region')['totalProductPrice'].sum().sort_values(ascending=False)
                    
                    fig7 = px.bar(
                        x=region_summary.index,
                        y=region_summary.values,
                        title='Sales by Region'
                    )
                    fig7.update_layout(
                        xaxis_title='Region',
                        yaxis_title='Sales (₹)'
                    )
                    st.plotly_chart(fig7, use_container_width=True)
                    
                    st.dataframe(region_data, use_container_width=True)
        
        # Download section
        st.sidebar.header("📥 Export Data")
        if st.sidebar.button("Generate Excel Report"):
            # Create Excel report with multiple sheets
            from io import BytesIO
            import pandas as pd
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Brand sales
                brand_sales = analytics.get_brand_wise_sales(selected_stores)
                brand_sales.to_excel(writer, sheet_name='Brand_Sales', index=False)
                
                # Store growth
                growth_data = analytics.get_store_brand_growth(selected_brands)
                growth_data.to_excel(writer, sheet_name='Store_Growth', index=False)
                
                # SKU analysis
                sku_data = analytics.get_top_sku_growth(single_brand)
                sku_data.to_excel(writer, sheet_name='Top_SKUs', index=False)
                
                # Tier & Region
                breakdown_data = analytics.get_tier_region_breakdown(selected_brands)
                breakdown_data['tier_breakdown'].to_excel(writer, sheet_name='Tier_Analysis', index=False)
                breakdown_data['region_breakdown'].to_excel(writer, sheet_name='Region_Analysis', index=False)
            
            st.sidebar.download_button(
                label="Download Excel Report",
                data=buffer.getvalue(),
                file_name=f"sales_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()