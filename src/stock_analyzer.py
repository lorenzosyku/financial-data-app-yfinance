import yfinance as yf
from typing import Dict, Any, Optional
import argparse
import sys

def categorize_info(info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Categorizes stock information into predefined groups for better organization.
    
    Args:
        info: Dictionary containing stock information from yfinance
        
    Returns:
        Nested dictionary with categorized financial data
    """
    category_map = {
        "price": ["regularMarketPreviousClose", "regularMarketOpen", 
                 "regularMarketDayHigh", "regularMarketDayLow", "currentPrice"],
        "shares": ["sharesOutstanding", "floatShares", "sharesShort"],
        "valuation": ["marketCap", "enterpriseValue", "priceToBook", "enterpriseToRevenue"],
        "financials": ["totalCash", "totalDebt", "totalRevenue", "grossProfits", "ebitda"],
        "location": ["address1", "address2", "city", "state", "zip", "country", "phone"],
        "company_info": ["sector", "industry", "longName", "website", "employees"]
    }
    
    # Create reverse mapping for O(1) lookups
    key_to_category = {}
    for category, keys in category_map.items():
        for key in keys:
            key_to_category[key] = category
    
    categorized_data = {category: {} for category in category_map}
    categorized_data["other"] = {}
    
    for key, value in info.items():
        if key in key_to_category:
            categorized_data[key_to_category[key]][key] = value
        else:
            categorized_data["other"][key] = value
    
    return categorized_data

def get_financial_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves and organizes financial data for a given ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        Dictionary containing categorized financial data or None if error occurs
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            print(f"No data found for ticker: {ticker}")
            return None
        
        # Get additional data
        institutional_holders = stock.institutional_holders
        recommendations = stock.recommendations
        
        # Categorize fundamental data
        categorized_data = categorize_info(info)
        
        return {
            "fundamentals": categorized_data,
            "institutional_holders": institutional_holders,
            "recommendations": recommendations.tail(5) if recommendations is not None else None
        }
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None

def format_output(data: Dict[str, Any]) -> str:
    """
    Formats the financial data for human-readable display.
    """
    output = []
    for section, content in data.items():
        output.append(f"\n=== {section.upper()} ===")
        if content is None:
            output.append("No data available")
            continue
            
        if isinstance(content, dict):
            for category, values in content.items():
                output.append(f"\n** {category.title()} **")
                for k, v in values.items():
                    output.append(f"{k:>30}: {v}")
        else:
            output.append(str(content))
    
    return "\n".join(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get financial data for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    args = parser.parse_args()
    
    result = get_financial_data(args.ticker)
    if result:
        print(format_output(result))
    else:
        sys.exit(1)