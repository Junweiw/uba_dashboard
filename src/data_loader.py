import pandas as pd
import numpy as np
from datetime import datetime

def load_data(uploaded_file):
    if uploaded_file:
        try:
            return pd.read_csv(uploaded_file)
        except:
            return pd.read_excel(uploaded_file)
    return None

def generate_mock_data():
    dates = pd.date_range(end=datetime.now(), periods=30)
    data = []
    for _ in range(1000):
        date = np.random.choice(dates)
        user_id = np.random.randint(1000, 1100)
        event = np.random.choice(['login', 'view', 'click', 'buy'], p=[0.3, 0.4, 0.2, 0.1])
        data.append([date, user_id, event])
    df = pd.DataFrame(data, columns=['event_time', 'user_id', 'event_type'])
    df['event_time'] = pd.to_datetime(df['event_time'])
    return df
