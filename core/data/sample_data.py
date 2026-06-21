# core/data/sample_data.py
"""
Sample data generators for Data Explorer Pro.
Provides realistic sales and housing datasets for demonstration and testing.
"""

import numpy as np
import pandas as pd
from typing import Optional

# Optional dependency: Faker for realistic fake data
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False


def _make_fake_data(n_rows: int, fields: list, seed: int = 42) -> dict:
    """
    Generate fake data for given fields using Faker if available, otherwise fallback.

    Args:
        n_rows: Number of rows to generate
        fields: List of field names ('name', 'email', 'company', 'address', 'phone')
        seed: Random seed for reproducibility

    Returns:
        Dictionary mapping field name to list of values
    """
    result = {}

    if not FAKER_AVAILABLE:
        # Fallback: generate simple synthetic data
        for field in fields:
            if field == 'name':
                result[field] = [f"Customer {i:04d}" for i in range(1, n_rows + 1)]
            elif field == 'email':
                result[field] = [f"user{i:04d}@example.com" for i in range(1, n_rows + 1)]
            elif field == 'company':
                companies = ['Acme Corp', 'Globex Inc', 'Initech', 'Umbrella Corp', 'Stark Industries']
                result[field] = [np.random.choice(companies) for _ in range(n_rows)]
            elif field == 'address':
                result[field] = [f"{i} Main St, City {i % 100}, USA" for i in range(1, n_rows + 1)]
            elif field == 'phone':
                result[field] = [f"(555) 555-{i:04d}" for i in range(1, n_rows + 1)]
            else:
                result[field] = [None] * n_rows
        return result

    # Use Faker
    faker = Faker()
    faker.seed_instance(seed)

    for field in fields:
        if field == 'name':
            result[field] = [faker.name() for _ in range(n_rows)]
        elif field == 'email':
            result[field] = [faker.email() for _ in range(n_rows)]
        elif field == 'company':
            result[field] = [faker.company() for _ in range(n_rows)]
        elif field == 'address':
            result[field] = [faker.address().replace('\n', ', ') for _ in range(n_rows)]
        elif field == 'phone':
            result[field] = [faker.phone_number() for _ in range(n_rows)]
        else:
            result[field] = [None] * n_rows

    return result


def generate_sample_sales_data(n_rows: int = 5000, heavy_fields: bool = False) -> pd.DataFrame:
    """
    Generate realistic sales transaction data with business metrics.

    Args:
        n_rows: Number of rows to generate
        heavy_fields: If True, include additional columns (address, phone)

    Returns:
        DataFrame with sales data columns:
        - date: transaction date
        - sales: revenue amount
        - quantity: units sold
        - unit_price: price per unit
        - discount: discount percentage
        - region: sales region
        - product_category: product category
        - sales_stage: pipeline stage
        - customer_segment: customer tier
        - latitude, longitude: geographic coordinates
        - satisfaction_score: customer rating
        - return_rate: return percentage
        - customer_name, sales_rep_name, customer_email, company_name
        - profit, profit_margin
        - (optional) customer_address, customer_phone
    """
    rng = np.random.default_rng(42)
    fields = ['name', 'email', 'company'] + (['address', 'phone'] if heavy_fields else [])

    fake_data = _make_fake_data(n_rows, fields, seed=42)

    # Generate core sales metrics
    base_sales = rng.lognormal(mean=np.log(5000), sigma=0.8, size=n_rows)
    sales = np.round(base_sales).astype(int)
    sales = np.clip(sales, 100, 1_000_000)

    df = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=n_rows, freq='D'),
        'sales': sales,
        'quantity': rng.poisson(25, n_rows) + rng.integers(1, 10, n_rows),
        'unit_price': np.abs(rng.normal(45, 15, n_rows)).round(2).clip(min=0.5),
        'discount': rng.choice([0, 5, 10, 15, 20], n_rows, p=[0.6, 0.2, 0.1, 0.05, 0.05]),
        'region': rng.choice(['East', 'West', 'North', 'South'], n_rows, p=[0.3, 0.3, 0.2, 0.2]),
        'product_category': rng.choice(['Electronics', 'Clothing', 'Home Goods', 'Books', 'Sports'], n_rows),
        'sales_stage': rng.choice(['Lead', 'Proposal', 'Negotiation', 'Closed', 'Lost'], n_rows, p=[0.2, 0.2, 0.2, 0.3, 0.1]),
        'customer_segment': rng.choice(['Premium', 'Standard', 'Basic'], n_rows, p=[0.2, 0.6, 0.2]),
        'latitude': rng.uniform(35.0, 45.0, n_rows),
        'longitude': rng.uniform(-120.0, -75.0, n_rows),
        'satisfaction_score': rng.integers(1, 11, n_rows),
        'return_rate': rng.beta(2, 50, n_rows).round(3),
    })

    # Add customer data from fake_data
    if fake_data:
        df['customer_name'] = fake_data['name']
        df['sales_rep_name'] = _make_fake_data(n_rows, ['name'], seed=43)['name']
        df['customer_email'] = fake_data['email']
        df['company_name'] = fake_data['company']
        if heavy_fields:
            df['customer_address'] = fake_data['address']
            df['customer_phone'] = fake_data['phone']
    else:
        df['customer_name'] = [f"Customer {i:04d}" for i in range(1, n_rows + 1)]
        df['sales_rep_name'] = rng.choice([f'SR{i:03d}' for i in range(1, 21)], n_rows)
        df['customer_email'] = [f"customer{i}@example.com" for i in range(1, n_rows + 1)]
        df['company_name'] = rng.choice(['Acme Corp', 'Globex Inc', 'Initech', 'Umbrella Corp'], n_rows)
        if heavy_fields:
            df['customer_address'] = [f"{i} Main St, USA" for i in range(1, n_rows + 1)]
            df['customer_phone'] = [f"(555) 555-{i:04d}" for i in range(1, n_rows + 1)]

    # Apply realistic business patterns
    west_mask = df['region'] == 'West'
    df.loc[west_mask, 'sales'] = (df.loc[west_mask, 'sales'] * 1.3).astype(int)

    electronics_mask = df['product_category'] == 'Electronics'
    df.loc[electronics_mask, 'unit_price'] = (df.loc[electronics_mask, 'unit_price'] * 1.5).round(2)

    # Add seasonality
    day_of_year = df['date'].dt.dayofyear
    seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * day_of_year / 365)
    df['sales'] = (df['sales'] * seasonal_factor).astype(int)

    # Calculate profit
    margins = rng.normal(0.22, 0.05, n_rows).clip(0.01, 0.5)
    df['profit'] = (df['sales'] * margins).round().astype(int)
    df['profit_margin'] = (df['profit'] / df['sales']).round(3)

    # Add some missing values (5% discount, 3% satisfaction)
    missing_indices = rng.choice(n_rows, size=int(n_rows * 0.05), replace=False)
    df.loc[missing_indices, 'discount'] = np.nan
    missing_indices = rng.choice(n_rows, size=int(n_rows * 0.03), replace=False)
    df.loc[missing_indices, 'satisfaction_score'] = np.nan

    # Add a few outliers (0.5% sales spikes)
    outlier_idx = rng.choice(n_rows, size=max(1, int(n_rows * 0.005)), replace=False)
    df.loc[outlier_idx, 'sales'] = (df.loc[outlier_idx, 'sales'] * 10).astype(int)

    # Add some duplicate rows (1%)
    dup_idx = rng.choice(n_rows, size=max(1, int(n_rows * 0.01)), replace=False)
    duplicates = df.loc[dup_idx].copy()
    duplicates['date'] = duplicates['date'] + pd.Timedelta(days=1)  # slight variation
    df = pd.concat([df, duplicates], ignore_index=True)

    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    df['date'] = pd.to_datetime(df['date'])

    # Optimize data types (basic)
    for col in df.select_dtypes(include=['object']):
        if df[col].nunique() < 50:
            df[col] = df[col].astype('category')

    return df


def generate_sample_housing_data(n_rows: int = 3000, heavy_fields: bool = False) -> pd.DataFrame:
    """
    Generate realistic real estate / housing data.

    Args:
        n_rows: Number of rows to generate
        heavy_fields: If True, include additional columns (address, phone)

    Returns:
        DataFrame with housing data columns:
        - date: listing date
        - price: listing price
        - sqft: square footage
        - bedrooms, bathrooms: room counts
        - lot_size: lot size (acres)
        - year_built: construction year
        - city, neighborhood: location
        - condition: property condition
        - property_type: type of property
        - latitude, longitude: coordinates
        - days_on_market: listing duration
        - open_house_count: number of open houses
        - price_reduced: boolean flag
        - owner_name, realtor_name
        - price_per_sqft: calculated ratio
        - (optional) address, phone_number
    """
    rng = np.random.default_rng(42)
    fields = ['name', 'email', 'company'] + (['address', 'phone'] if heavy_fields else [])

    fake_data = _make_fake_data(n_rows, fields, seed=42)

    # Generate housing metrics
    base_prices = rng.lognormal(mean=np.log(300_000), sigma=0.4, size=n_rows)
    prices = np.round(base_prices).astype(int)
    prices = np.clip(prices, 50_000, 10_000_000)

    sqft = np.abs(rng.normal(2000, 500, n_rows)).round().astype(int).clip(min=200)

    df = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=n_rows, freq='D'),
        'price': prices,
        'sqft': sqft,
        'bedrooms': rng.choice([1, 2, 3, 4, 5], n_rows, p=[0.1, 0.2, 0.4, 0.2, 0.1]),
        'bathrooms': rng.choice([1, 1.5, 2, 2.5, 3, 3.5], n_rows, p=[0.2, 0.2, 0.3, 0.15, 0.1, 0.05]),
        'lot_size': np.abs(rng.normal(0.25, 0.1, n_rows)).round(2).clip(min=0.01),
        'year_built': rng.integers(1950, 2023, n_rows),
        'city': rng.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia'], n_rows),
        'neighborhood': rng.choice(['Downtown', 'Suburban', 'Rural', 'Waterfront'], n_rows),
        'condition': rng.choice(['Excellent', 'Good', 'Fair', 'Poor'], n_rows, p=[0.3, 0.4, 0.2, 0.1]),
        'property_type': rng.choice(['Single Family', 'Condo', 'Townhouse', 'Multi-Family'], n_rows),
        'latitude': rng.uniform(40.5, 40.9, n_rows),
        'longitude': rng.uniform(-74.1, -73.7, n_rows),
        'days_on_market': rng.poisson(30, n_rows) + rng.integers(0, 30, n_rows),
        'open_house_count': rng.poisson(3, n_rows),
        'price_reduced': rng.choice([0, 1], n_rows, p=[0.7, 0.3]),
    })

    # Add owner/realtor data
    if fake_data:
        df['owner_name'] = fake_data['name']
        df['realtor_name'] = _make_fake_data(n_rows, ['name'], seed=43)['name']
        if heavy_fields:
            df['address'] = fake_data['address']
            df['phone_number'] = fake_data['phone']
    else:
        df['owner_name'] = [f"Owner {i:04d}" for i in range(1, n_rows + 1)]
        df['realtor_name'] = rng.choice(['John Doe', 'Jane Smith', 'Bob Johnson'], n_rows)
        if heavy_fields:
            df['address'] = [f"{i} Main St, {df['city'].iloc[i-1]}, USA" for i in range(1, n_rows + 1)]
            df['phone_number'] = [f"(555) 555-{i:04d}" for i in range(1, n_rows + 1)]

    # Apply realistic market patterns
    ny_mask = df['city'] == 'New York'
    df.loc[ny_mask, 'price'] = (df.loc[ny_mask, 'price'] * 2.5).astype(int)

    excellent_mask = df['condition'] == 'Excellent'
    df.loc[excellent_mask, 'price'] = (df.loc[excellent_mask, 'price'] * 1.2).astype(int)

    poor_mask = df['condition'] == 'Poor'
    df.loc[poor_mask, 'price'] = (df.loc[poor_mask, 'price'] * 0.8).astype(int)

    condo_mask = df['property_type'] == 'Condo'
    df.loc[condo_mask, 'sqft'] = (df.loc[condo_mask, 'sqft'] * 0.7).astype(int)

    # Add price appreciation over time
    time_factor = (df.index - df.index.min()) / len(df)
    df['price'] = (df['price'] * (1 + 0.001 * time_factor * len(df))).astype(int)

    # Calculate price per sqft
    df['price_per_sqft'] = (df['price'] / df['sqft']).round(2)

    # Add realistic missing data (4% year_built, 2% lot_size)
    missing_indices = rng.choice(n_rows, size=int(n_rows * 0.04), replace=False)
    df.loc[missing_indices, 'year_built'] = np.nan
    missing_indices = rng.choice(n_rows, size=int(n_rows * 0.02), replace=False)
    df.loc[missing_indices, 'lot_size'] = np.nan

    # Add a few luxury outliers (0.5% price spikes)
    outlier_idx = rng.choice(n_rows, size=max(1, int(n_rows * 0.005)), replace=False)
    df.loc[outlier_idx, 'price'] = (df.loc[outlier_idx, 'price'] * 10).astype(int)

    # Add some duplicate rows (1%)
    dup_idx = rng.choice(n_rows, size=max(1, int(n_rows * 0.01)), replace=False)
    duplicates = df.loc[dup_idx].copy()
    duplicates['date'] = duplicates['date'] + pd.Timedelta(days=1)
    df = pd.concat([df, duplicates], ignore_index=True)

    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    df['date'] = pd.to_datetime(df['date'])

    # Optimize data types
    for col in df.select_dtypes(include=['object']):
        if df[col].nunique() < 50:
            df[col] = df[col].astype('category')

    return df