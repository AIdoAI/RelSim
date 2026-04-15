"""
Special distribution generators.

Implements special-purpose distributions and functions:
- RAND: Random uniform [0,1]
- FIXED: Fixed constant value (not technically a distribution)
- DATE_UNIF: Uniform random ISO date between two date strings
"""

import random
from datetime import datetime, timedelta
import numpy as np
from typing import Optional, Union, Any


class SpecialDistributions:
    """Static class containing special distribution generators and functions."""

    @staticmethod
    def date_unif(start_date: str, end_date: str, size: Optional[int] = None) -> Union[str, list]:
        """
        DATE_UNIF(start, end) - uniform random date between two dates (inclusive).

        Returns ISO date strings in 'YYYY-MM-DD' format so they can be stored
        directly in a DATE column.

        Args:
            start_date: start date in 'YYYY-MM-DD' format
            end_date:   end date in 'YYYY-MM-DD' format
            size:       number of samples

        Returns:
            ISO date string (or list of strings if size is given)
        """
        start = datetime.strptime(str(start_date), '%Y-%m-%d')
        end = datetime.strptime(str(end_date), '%Y-%m-%d')
        days_between = (end - start).days
        if days_between < 0:
            raise ValueError(f"DATE_UNIF start ({start_date}) must be <= end ({end_date})")

        def _one():
            offset = random.randint(0, days_between) if days_between > 0 else 0
            return (start + timedelta(days=offset)).strftime('%Y-%m-%d')

        if size is None:
            return _one()
        return [_one() for _ in range(size)]

    @staticmethod
    def rand(size: Optional[int] = None) -> Union[float, np.ndarray]:
        """
        RAND() - Uniform random number between 0 and 1.
        
        Args:
            size: Number of samples to generate
            
        Returns:
            Random value(s) uniformly distributed in [0, 1]
        """
        return np.random.uniform(0, 1, size)
    
    @staticmethod
    def fixed(value: Any, size: Optional[int] = None) -> Union[Any, np.ndarray]:
        """
        FIXED(value) - Fixed constant value.
        
        Not technically a distribution, but useful for configuration.
        
        Args:
            value: The constant value to return
            size: Number of samples to generate (all will be the same value)
            
        Returns:
            The fixed value, or an array of the fixed value
        """
        if size is None:
            return value
        return np.full(size, value)