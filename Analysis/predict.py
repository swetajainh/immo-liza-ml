import pandas as pd
import numpy as np
import sklearn
import matplotlib.pyplot as plt
#libraries for preprocessing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import KNNImputer
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
# Libraries for the different models
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
#from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.ensemble import StackingRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error



df=pd.read_csv(r'Data\properties.csv')
df.head()


def calculate_missing_percentage(df):
    # Calculate the total number of missing values in each column
    missing_values = df.isnull().sum().sort_values()

    # Calculate the total number of rows in the DataFrame
    total_rows = df.shape[0]

    # Calculate the percentage of missing values in each column
    percentage_missing_values = (missing_values / total_rows) * 100

    # Display the percentage of missing values in each column
    print("Percentage of missing values in each column:")
    print(percentage_missing_values)

def filter_dataframe(df, column, value):
    # Filter the DataFrame based on a specific column and value
    return df[df[column] == value]

def identify_column_types(df):
    # Define lists to store numerical and categorical column names
    numerical_cols = []
    categorical_cols = []

    # Loop through DataFrame columns
    for column in df.columns:
        # Check if the column is numerical
        if df[column].dtype in [np.int64, np.float64]:
            numerical_cols.append(column)
        else:
            categorical_cols.append(column)

    return numerical_cols, categorical_cols

def split_data(X, y, n_splits=5, random_state=None):
    # Define the number of splits for Stratified K-Fold Cross-Validation
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    # Iterate over the splits and obtain the training and testing indices
    for train_index, test_index in kfold.split(X, y):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        # Printing the shapes of the training and testing sets for each fold
        print("Shape of X_train:", X_train.shape)
        print("Shape of X_test:", X_test.shape)
        print("Shape of y_train:", y_train.shape)
        print("Shape of y_test:", y_test.shape)

def preprocess_data(X_train, X_test, y_train, y_test):
    # Define numerical and categorical columns
    numerical_columns = ['zip_code', 'latitude', 'longitude', 'construction_year', 
                         'total_area_sqm', 'surface_land_sqm', 'nbr_frontages', 
                         'nbr_bedrooms', 'terrace_sqm', 'garden_sqm', 
                         'primary_energy_consumption_sqm', 'cadastral_income']  
    categorical_columns = ['region', 'province', 'equipped_kitchen', 'heating_type',
                            'state_building', 'epc']

    # Imputation
    imputer = KNNImputer(n_neighbors=5)
    X_train_imputed = X_train.copy()
    X_test_imputed = X_test.copy()
    X_train_imputed[numerical_columns] = imputer.fit_transform(X_train[numerical_columns])
    X_test_imputed[numerical_columns] = imputer.transform(X_test[numerical_columns])

    # Scaling
    scaler = StandardScaler()
    X_train_scaled = X_train_imputed.copy()
    X_test_scaled = X_test_imputed.copy()
    X_train_scaled[numerical_columns] = scaler.fit_transform(X_train_imputed[numerical_columns])
    X_test_scaled[numerical_columns] = scaler.transform(X_test_imputed[numerical_columns])

    # One-hot encoding
    one_hot_encoder = OneHotEncoder(drop='first')
    X_train_encoded = one_hot_encoder.fit_transform(X_train[categorical_columns])
    X_test_encoded = one_hot_encoder.transform(X_test[categorical_columns])

    # Convert encoded arrays to DataFrames
    encoded_columns = one_hot_encoder.get_feature_names_out(input_features=categorical_columns)
    X_train_encoded_df = pd.DataFrame(X_train_encoded.toarray(), columns=encoded_columns)
    X_test_encoded_df = pd.DataFrame(X_test_encoded.toarray(), columns=encoded_columns)

    # Combine the scaled numerical features with the encoded categorical features
    X_train_concatenated = pd.concat([X_train_scaled, X_train_encoded_df], axis=1)
    X_test_concatenated = pd.concat([X_test_scaled, X_test_encoded_df], axis=1)

    # Scale the target variable
    y_scaler = StandardScaler()
    y_train_scaled = y_scaler.fit_transform(y_train.values.reshape(-1, 1))
    y_test_scaled = y_scaler.transform(y_test.values.reshape(-1, 1))

    return X_train_concatenated, X_test_concatenated, y_train_scaled, y_test_scaled

from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import LinearRegression

def train_stacking_regressor(base_models, X_train, y_train, X_test, y_test):
    # Preprocess the data
    X_train_concatenated, X_test_concatenated, y_train_scaled, y_test_scaled = preprocess_data(X_train, X_test, y_train, y_test)

    # Initialize stacking regressor with meta-model
    stacking_regressor = StackingRegressor(estimators=base_models, final_estimator=LinearRegression())

    # Train stacking regressor
    stacking_regressor.fit(X_train_concatenated, y_train_scaled)

    # Evaluate on training set
    train_score = stacking_regressor.score(X_train_concatenated, y_train_scaled)
    print("Training Score (R-squared):", train_score)

    # Evaluate on test set
    test_score = stacking_regressor.score(X_test_concatenated, y_test_scaled)
    print("Testing Score (R-squared):", test_score)

    return stacking_regressor, train_score, test_score

# Split data into features (X) and target (y)
X = df.drop(columns=['price'])
y = df['price']

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define base models
base_models = [
    ('random_forest', RandomForestRegressor(n_estimators=100, random_state=42)),
    ('linear_regression', LinearRegression()),
    ('catboost', CatBoostRegressor(iterations=100, random_state=42, verbose=False))
]

# Train stacking regressor
stacking_regressor, train_score, test_score = train_stacking_regressor(base_models, X_train, y_train, X_test, y_test)

'''def calculate_errors(y_true, y_pred):
  X_train_concatenated, X_test_concatenated = preprocess_data(X_train, X_test)
  y_train_scaled, y_test_scaled = scale_target(y_train, y_test)
    # Calculate mean absolute error (MAE)
  mae = mean_absolute_error(y_true, y_pred)
  print("Mean Absolute Error (MAE):", mae)

    # Calculate mean squared error (MSE)
  mse = mean_squared_error(y_true, y_pred)
  print("Mean Squared Error (MSE):", mse)

# Predict on the test set
  y_pred = stacking_regressor.predict(X_test_concatenated)

# Call the function to calculate errors
calculate_errors(y_test_scaled, y_pred)

import pickle

def predictions(predictions=None, file_path=None):
    """
    Save or load predictions using pickle.

    Args:
    - predictions: The predictions to be saved (if saving) or None (if loading).
    - file_path: The file path where the predictions will be saved (if saving) or loaded (if loading).

    Returns:
    - If saving: None
    - If loading: The loaded predictions
    """
    if predictions is not None and file_path is not None:
        # Save predictions
        with open(file_path, 'wb') as f:
            pickle.dump(predictions, f)
        print("Predictions saved to", file_path)
    elif predictions is None and file_path is not None:
        # Load predictions
        with open(file_path, 'rb') as f:
            loaded_predictions = pickle.load(f)
        print("Predictions loaded from", file_path)
        return loaded_predictions
    else:
        print("Please provide predictions and file_path for saving or file_path for loading.")

# Example usage:

# Save predictions
predictions(train_predictions, 'train_predictions.pkl')
predictions(test_predictions, 'test_predictions.pkl')

# Load predictions
loaded_train_predictions = predictions(file_path='train_predictions.pkl')
loaded_test_predictions = predictions(file_path='test_predictions.pkl')'''
