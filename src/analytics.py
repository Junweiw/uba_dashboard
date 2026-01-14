import pandas as pd

def calculate_kpis(df):
    total_events = len(df)
    unique_users = df['user_id'].nunique()
    return total_events, unique_users

def get_trend(df):
    return df.groupby(df['event_time'].dt.date).size().reset_index(name='count')

def get_distribution(df):
    return df['event_type'].value_counts().reset_index()
