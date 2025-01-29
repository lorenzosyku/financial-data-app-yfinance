import yfinance as yf
from typing import Dict, Any, Optional, List
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

def get_financial_data(ticker: str, expiration: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves and organizes financial data for a given ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        expiration: Options expiration date (YYYY-MM-DD). Defaults to nearest available.
        
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
        
        # Get options data
        options_data = None
        try:
            expirations: List[str] = stock.options
        except Exception as e:
            print(f"Warning: Could not retrieve options expirations - {e}")
            expirations = []
        
        if expirations:
            selected_expiration = None
            if expiration:
                if expiration in expirations:
                    selected_expiration = expiration
                else:
                    print(f"Error: Expiration {expiration} not found. Available dates: {', '.join(expirations)}")
            else:
                selected_expiration = expirations[0]  # Use nearest expiration
            
            if selected_expiration:
                try:
                    chain = stock.option_chain(selected_expiration)
                    options_data = {
                        "expiration": selected_expiration,
                        "calls": chain.calls,
                        "puts": chain.puts
                    }
                except Exception as e:
                    print(f"Error retrieving option chain: {e}")
        
        return {
            "fundamentals": categorized_data,
            "institutional_holders": institutional_holders,
            "recommendations": recommendations.tail(5) if recommendations is not None else None,
            "options": options_data
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
            
        if section == "options":
            # Handle options data special case
            output.append(f"Expiration: {content['expiration']}")
            
            # Format calls
            output.append("\n** Calls **")
            if not content["calls"].empty:
                calls = content["calls"][["strike", "lastPrice", "bid", "ask", "volume", "openInterest"]].head(5)
                output.append(calls.to_string(index=False))
            else:
                output.append("No calls data available")
            
            # Format puts
            output.append("\n** Puts **")
            if not content["puts"].empty:
                puts = content["puts"][["strike", "lastPrice", "bid", "ask", "volume", "openInterest"]].head(5)
                output.append(puts.to_string(index=False))
            else:
                output.append("No puts data available")
        elif isinstance(content, dict):
            # Handle nested dictionaries (fundamentals)
            for category, values in content.items():
                output.append(f"\n** {category.title()} **")
                if isinstance(values, dict):
                    for k, v in values.items():
                        output.append(f"{k:>30}: {v}")
                else:
                    output.append(str(values))
        else:
            # Handle DataFrames and other objects
            output.append(str(content))
    
    return "\n".join(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get financial data for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('-e', '--expiration', type=str, help='Options expiration date (YYYY-MM-DD)')
    args = parser.parse_args()
    
    result = get_financial_data(args.ticker, args.expiration)
    if result:
        print(format_output(result))
    else:
        sys.exit(1)