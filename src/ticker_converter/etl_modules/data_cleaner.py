"""Data cleaning module for market data."""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ..data_models.market_data import CleanedMarketData, RawMarketData

logger = logging.getLogger(__name__)


class CleaningConfig(BaseModel):
    """Configuration for data cleaning operations."""
    
    remove_duplicates: bool = Field(default=True, description="Remove duplicate records")
    fill_missing_values: bool = Field(default=True, description="Fill missing values")
    missing_value_method: str = Field(default="forward_fill", description="Method for filling missing values")
    remove_outliers: bool = Field(default=True, description="Remove statistical outliers")
    outlier_method: str = Field(default="iqr", description="Outlier detection method")
    outlier_threshold: float = Field(default=1.5, description="Outlier threshold multiplier")
    validate_price_relationships: bool = Field(default=True, description="Validate price relationships")
    ensure_consistent_types: bool = Field(default=True, description="Ensure consistent data types")
    sort_by_date: bool = Field(default=True, description="Sort data by date")


class DataCleaner:
    """Cleans and validates market data for analysis."""
    
    def __init__(self, config: Optional[CleaningConfig] = None):
        """Initialize the data cleaner.
        
        Args:
            config: Cleaning configuration options
        """
        self.config = config or CleaningConfig()
        self.cleaning_operations: List[str] = []
        self.outliers_removed = 0
        self.missing_values_filled = 0
    
    def clean(self, raw_data: RawMarketData) -> CleanedMarketData:
        """Clean raw market data.
        
        Args:
            raw_data: Raw market data to clean
            
        Returns:
            CleanedMarketData with cleaned DataFrame
        """
        logger.info(f"Starting data cleaning for {raw_data.symbol}")
        
        # Reset counters
        self.cleaning_operations = []
        self.outliers_removed = 0
        self.missing_values_filled = 0
        
        # Convert to DataFrame
        df = raw_data.to_dataframe()
        original_count = len(df)
        
        logger.info(f"Original data shape: {df.shape}")
        
        # Apply cleaning operations
        df = self._ensure_consistent_types(df)
        df = self._sort_by_date(df)
        df = self._remove_duplicates(df)
        df = self._validate_price_relationships(df)
        df = self._fill_missing_values(df)
        df = self._remove_outliers(df)
        
        logger.info(f"Cleaned data shape: {df.shape}")
        logger.info(f"Records removed: {original_count - len(df)}")
        logger.info(f"Cleaning operations applied: {self.cleaning_operations}")
        
        # Create cleaned data object
        cleaned_data = CleanedMarketData(
            raw_data=raw_data,
            cleaning_applied=self.cleaning_operations.copy(),
            outliers_removed=self.outliers_removed,
            missing_values_filled=self.missing_values_filled,
        )
        
        return cleaned_data
    
    def _ensure_consistent_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure consistent data types across columns."""
        if not self.config.ensure_consistent_types:
            return df
        
        try:
            # Ensure numeric columns are proper types
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Ensure Volume is integer
            if 'Volume' in df.columns:
                df['Volume'] = df['Volume'].fillna(0).astype('int64')
            
            # Ensure Symbol is string
            if 'Symbol' in df.columns:
                df['Symbol'] = df['Symbol'].astype(str)
            
            self.cleaning_operations.append("ensure_consistent_types")
            logger.debug("Data types standardized")
            
        except Exception as e:
            logger.warning(f"Error ensuring consistent types: {e}")
        
        return df
    
    def _sort_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sort DataFrame by date index."""
        if not self.config.sort_by_date:
            return df
        
        try:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.sort_index()
                self.cleaning_operations.append("sort_by_date")
                logger.debug("Data sorted by date")
        except Exception as e:
            logger.warning(f"Error sorting by date: {e}")
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records based on date and symbol."""
        if not self.config.remove_duplicates:
            return df
        
        initial_count = len(df)
        
        try:
            # Remove duplicates based on index (date) and Symbol
            df = df.reset_index().drop_duplicates(subset=['Date', 'Symbol'], keep='first').set_index('Date')
            
            duplicates_removed = initial_count - len(df)
            if duplicates_removed > 0:
                self.cleaning_operations.append(f"remove_duplicates_{duplicates_removed}")
                logger.info(f"Removed {duplicates_removed} duplicate records")
                
        except Exception as e:
            logger.warning(f"Error removing duplicates: {e}")
        
        return df
    
    def _validate_price_relationships(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate price relationships (High >= Low, Close within range)."""
        if not self.config.validate_price_relationships:
            return df
        
        try:
            initial_count = len(df)
            
            # Remove rows where High < Low
            invalid_high_low = df['High'] < df['Low']
            if invalid_high_low.any():
                df = df[~invalid_high_low]
                logger.warning(f"Removed {invalid_high_low.sum()} rows with High < Low")
            
            # Remove rows where Close is outside High/Low range
            invalid_close = (df['Close'] > df['High']) | (df['Close'] < df['Low'])
            if invalid_close.any():
                df = df[~invalid_close]
                logger.warning(f"Removed {invalid_close.sum()} rows with Close outside High/Low range")
            
            # Remove rows with non-positive prices
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                if col in df.columns:
                    invalid_prices = df[col] <= 0
                    if invalid_prices.any():
                        df = df[~invalid_prices]
                        logger.warning(f"Removed {invalid_prices.sum()} rows with non-positive {col} prices")
            
            removed_count = initial_count - len(df)
            if removed_count > 0:
                self.cleaning_operations.append(f"validate_price_relationships_{removed_count}")
                
        except Exception as e:
            logger.warning(f"Error validating price relationships: {e}")
        
        return df
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values in the DataFrame."""
        if not self.config.fill_missing_values:
            return df
        
        try:
            missing_before = df.isnull().sum().sum()
            
            if missing_before == 0:
                return df
            
            if self.config.missing_value_method == "forward_fill":
                df = df.fillna(method='ffill')
            elif self.config.missing_value_method == "backward_fill":
                df = df.fillna(method='bfill')
            elif self.config.missing_value_method == "interpolate":
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                df[numeric_columns] = df[numeric_columns].interpolate(method='linear')
            elif self.config.missing_value_method == "mean":
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].mean())
            
            missing_after = df.isnull().sum().sum()
            filled_count = missing_before - missing_after
            
            if filled_count > 0:
                self.missing_values_filled = filled_count
                self.cleaning_operations.append(f"fill_missing_values_{self.config.missing_value_method}_{filled_count}")
                logger.info(f"Filled {filled_count} missing values using {self.config.missing_value_method}")
            
        except Exception as e:
            logger.warning(f"Error filling missing values: {e}")
        
        return df
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove statistical outliers from price data."""
        if not self.config.remove_outliers:
            return df
        
        try:
            initial_count = len(df)
            price_columns = ['Open', 'High', 'Low', 'Close']
            
            for col in price_columns:
                if col not in df.columns:
                    continue
                
                if self.config.outlier_method == "iqr":
                    df, removed = self._remove_outliers_iqr(df, col)
                elif self.config.outlier_method == "zscore":
                    df, removed = self._remove_outliers_zscore(df, col)
                
                if removed > 0:
                    logger.info(f"Removed {removed} outliers from {col} using {self.config.outlier_method}")
            
            total_removed = initial_count - len(df)
            if total_removed > 0:
                self.outliers_removed = total_removed
                self.cleaning_operations.append(f"remove_outliers_{self.config.outlier_method}_{total_removed}")
                
        except Exception as e:
            logger.warning(f"Error removing outliers: {e}")
        
        return df
    
    def _remove_outliers_iqr(self, df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, int]:
        """Remove outliers using IQR method."""
        initial_count = len(df)
        
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - self.config.outlier_threshold * IQR
        upper_bound = Q3 + self.config.outlier_threshold * IQR
        
        outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
        df = df[~outliers]
        
        removed = initial_count - len(df)
        return df, removed
    
    def _remove_outliers_zscore(self, df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, int]:
        """Remove outliers using Z-score method."""
        initial_count = len(df)
        
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        outliers = z_scores > self.config.outlier_threshold
        df = df[~outliers]
        
        removed = initial_count - len(df)
        return df, removed
