import pandas as pd
import pdfplumber
from pathlib import Path
import io
import re
from datetime import datetime
import json
import sys
import argparse
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatementParser:
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.filename = file_obj.name if hasattr(file_obj, 'name') else 'statement.pdf'

    def parse(self):
        """Parse the file into a standardized DataFrame"""
        if self.filename.endswith('.pdf'):
            return self._parse_pdf()
        else:
            raise ValueError("Unsupported file format")

    def _parse_pdf(self):
        """Handle PDF parsing with comprehensive extraction"""
        try:
            transactions = []
            with pdfplumber.open(self.file_obj) as pdf:
                # Transaction patterns
                transaction_patterns = [
                    # Kotak Format: Date Narration Chq/RefNo Withdrawal(Dr)/Deposit(Cr) Balance
                    re.compile(
                        r'(?P<date>\d{2}-\d{2}-\d{4})\s+'  # Date (DD-MM-YYYY)
                        r'(?P<narration>.*?)\s+' # Narration/Description (non-greedy match)
                        r'(?:.*?)\s+' # Skip Chq/Ref No column (non-capturing, non-greedy)
                        r'(?P<amount>[\d,]+\.?\d{2})\((?P<type>Cr|Dr)\)', # Amount with Dr/Cr type
                        re.IGNORECASE
                    ),
                    # Pattern 1: Standard format
                    re.compile(
                        r'(?P<date>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{1,2},\s*\d{4})\s*'
                        r'(?P<description>.*?)'
                        r'(?P<type>DEBIT|CREDIT|Dr|Cr)?\s*'
                        r'(?:₹|Rs\.?)\s*(?P<amount>[\d,]+\.?\d*)',
                        re.IGNORECASE | re.MULTILINE | re.DOTALL
                    ),
                    # Pattern 2: Alternative format
                    re.compile(
                        r'(?P<date>\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4})\s*'
                        r'(?P<description>.*?)'
                        r'(?P<amount>[-+]?₹?\s*[\d,]+\.?\d*)',
                        re.IGNORECASE | re.MULTILINE | re.DOTALL
                    )
                ]

                # Process each page individually
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        # Apply patterns to the current page's text
                        for pattern in transaction_patterns:
                            for match in pattern.finditer(text):
                                try:
                                    date_str = match.group('date').strip()
                                    date = self._parse_date(date_str)
                                    
                                    # Use 'narration' group for the new pattern, 'description' for others
                                    if 'narration' in match.groupdict():
                                        description = match.group('narration').strip()
                                    else:
                                        description = match.group('description').strip()

                                    amount_str = match.group('amount')
                                    amount_str = re.sub(r'[₹,\s]', '', amount_str)
                                    amount = float(amount_str)
                                    
                                    # Determine transaction type and adjust amount
                                    if 'type' in match.groupdict():
                                        txn_type = match.group('type').upper()
                                        if txn_type in ['DR', 'DEBIT']:
                                            amount = -abs(amount)
                                    elif amount < 0:
                                         txn_type = 'DR'
                                    else:
                                         txn_type = 'CR'

                                    transactions.append({
                                        'date': date,
                                        'amount': amount,
                                        'description': description,
                                        'category': self._categorize_transaction(description)
                                    })
                                except Exception as e:
                                    logger.warning(f"Could not process transaction on page {page.page_number} with pattern {pattern.pattern}: {e}")

            if transactions:
                df = pd.DataFrame(transactions)
                df = df[df['amount'].abs() > 0]
                df = df.drop_duplicates(subset=['date', 'amount', 'description'])
                df = df.sort_values('date')
                return df
            else:
                logger.warning("No transactions found after parsing all pages.")
                return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])

        except Exception as e:
            logger.error(f"PDF parsing error: {str(e)}\n{traceback.format_exc()}")
            return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])

    def _parse_date(self, date_str):
        """Parse date string into datetime object"""
        try:
            if not date_str:
                return datetime.now()

            date_str = date_str.strip()
            date_formats = [
                '%d %b %Y',      # 06 Nov 2024
                '%b %d %Y',      # Nov 06 2024
                '%d %B %Y',      # 06 November 2024
                '%B %d %Y',      # November 06 2024
                '%m/%d/%Y',      # 11/06/2024
                '%d/%m/%Y',      # 06/11/2024
                '%Y-%m-%d',      # 2024-11-06
                '%d-%m-%Y',      # 06-11-2024
                '%b %d, %Y',     # Nov 06, 2024
                '%d %b, %Y',     # 06 Nov, 2024
                '%d-%b-%Y',      # 06-Nov-2024
                '%b-%d-%Y'       # Nov-06-2024
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    if parsed_date.year > datetime.now().year:
                        parsed_date = parsed_date.replace(year=datetime.now().year)
                    return parsed_date
                except ValueError:
                    continue
            
            # Fallback: try to extract components
            components = re.findall(r'\d+', date_str)
            if len(components) >= 3:
                day, month, year = map(int, components[:3])
                if year < 100:
                    year += 2000 if year < 50 else 1900
                return datetime(year, month, day)
            
            return datetime.now()
            
        except Exception as e:
            logger.error(f"Date parsing error: {str(e)}")
            return datetime.now()

    def _categorize_transaction(self, description):
        """Categorize transaction based on description"""
        description = description.lower()
        
        # Basic categories for now
        categories = {
            'food': ['restaurant', 'food', 'cafe', 'coffee', 'swiggy', 'zomato'],
            'shopping': ['amazon', 'flipkart', 'myntra', 'shop', 'store'],
            'transport': ['uber', 'ola', 'metro', 'bus', 'train', 'flight'],
            'utilities': ['electricity', 'water', 'gas', 'internet', 'mobile'],
            'entertainment': ['movie', 'theatre', 'concert', 'netflix', 'prime'],
            'health': ['hospital', 'doctor', 'pharmacy', 'medical'],
            'education': ['school', 'college', 'university', 'course'],
            'investment': ['mutual fund', 'stock', 'investment', 'sip'],
            'salary': ['salary', 'income', 'credit'],
            'transfer': ['transfer', 'neft', 'imps', 'rtgs']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                return category
        
        return 'other' 