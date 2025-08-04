import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Union, List
from urllib.parse import urlparse
import hashlib
import base64

def process_text(text: str, operation: str) -> Dict[str, Union[str, int]]:
    """
    Process text with various operations like counting, formatting, and transforming.
    
    Use this function when users need text processing, formatting, or analysis.
    Available operations: count_words, count_chars, uppercase, lowercase, title_case, 
    reverse, remove_spaces, extract_emails, extract_urls, word_frequency.
    
    Args:
        text: Input text to process
        operation: Type of operation to perform
    
    Returns:
        Dictionary with processed text results
    """
    try:
        if not text:
            return {"error": "Empty text provided", "status": "error"}
        
        operations = {
            "count_words": lambda t: {"word_count": len(t.split()), "text": t},
            "count_chars": lambda t: {"char_count": len(t), "char_count_no_spaces": len(t.replace(" ", "")), "text": t},
            "uppercase": lambda t: {"result": t.upper(), "original": t},
            "lowercase": lambda t: {"result": t.lower(), "original": t},
            "title_case": lambda t: {"result": t.title(), "original": t},
            "reverse": lambda t: {"result": t[::-1], "original": t},
            "remove_spaces": lambda t: {"result": re.sub(r'\s+', '', t), "original": t},
            "extract_emails": lambda t: {"emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', t), "original": t},
            "extract_urls": lambda t: {"urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', t), "original": t},
            "word_frequency": lambda t: {"word_frequency": dict(sorted([(word.lower(), t.lower().split().count(word.lower())) for word in set(t.split())], key=lambda x: x[1], reverse=True)), "original": t}
        }
        
        if operation not in operations:
            return {
                "error": f"Invalid operation. Available: {', '.join(operations.keys())}", 
                "status": "error"
            }
        
        result = operations[operation](text)
        result["operation"] = operation
        result["status"] = "success"
        return result
        
    except Exception as e:
        return {
            "error": f"Error processing text: {str(e)}",
            "status": "error"
        }

def format_datetime(date_input: str, input_format: str, output_format: str) -> Dict[str, Union[str, Dict]]:
    """
    Format and convert datetime strings between different formats.
    
    Use this function when users need to convert date/time formats or parse dates.
    Common formats: '%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%B %d, %Y'
    
    Args:
        date_input: Input date string
        input_format: Format of the input date (Python strftime format)
        output_format: Desired output format (Python strftime format)
    
    Returns:
        Dictionary with formatted date results
    """
    try:
        # Parse the input date
        parsed_date = datetime.strptime(date_input, input_format)
        
        # Format to output format
        formatted_date = parsed_date.strftime(output_format)
        
        return {
            "formatted_date": formatted_date,
            "original": date_input,
            "input_format": input_format,
            "output_format": output_format,
            "parsed_info": {
                "year": parsed_date.year,
                "month": parsed_date.month,
                "day": parsed_date.day,
                "weekday": parsed_date.strftime("%A"),
                "month_name": parsed_date.strftime("%B")
            },
            "status": "success"
        }
        
    except ValueError as e:
        return {
            "error": f"Date parsing error: {str(e)}",
            "date_input": date_input,
            "input_format": input_format,
            "status": "error"
        }
    except Exception as e:
        return {
            "error": f"Error formatting date: {str(e)}",
            "status": "error"
        }

def calculate_date_difference(date1: str, date2: str, date_format: str) -> Dict[str, Union[str, int, Dict]]:
    """
    Calculate the difference between two dates.
    
    Use this function when users need to find the time difference between dates,
    calculate age, or determine duration between events.
    
    Args:
        date1: First date string
        date2: Second date string
        date_format: Format of both dates (Python strftime format)
    
    Returns:
        Dictionary with date difference calculations
    """
    try:
        # Parse both dates
        parsed_date1 = datetime.strptime(date1, date_format)
        parsed_date2 = datetime.strptime(date2, date_format)
        
        # Calculate difference
        diff = parsed_date2 - parsed_date1
        
        # Calculate various difference formats
        total_seconds = int(diff.total_seconds())
        days = diff.days
        hours = total_seconds // 3600
        minutes = total_seconds // 60
        
        # Calculate years, months, days breakdown
        years = days // 365
        remaining_days = days % 365
        months = remaining_days // 30
        remaining_days = remaining_days % 30
        
        return {
            "difference": {
                "total_days": days,
                "total_hours": hours,
                "total_minutes": minutes,
                "total_seconds": total_seconds,
                "breakdown": {
                    "years": years,
                    "months": months,
                    "days": remaining_days
                }
            },
            "date1": date1,
            "date2": date2,
            "date_format": date_format,
            "status": "success"
        }
        
    except ValueError as e:
        return {
            "error": f"Date parsing error: {str(e)}",
            "date1": date1,
            "date2": date2,
            "status": "error"
        }
    except Exception as e:
        return {
            "error": f"Error calculating date difference: {str(e)}",
            "status": "error"
        }

def generate_uuid(version: int = 4) -> Dict[str, Union[str, int]]:
    """
    Generate a UUID (Universally Unique Identifier).
    
    Use this function when users need unique identifiers for databases,
    sessions, or any application requiring unique IDs.
    
    Args:
        version: UUID version (1, 4, or 5). Default is 4 (random)
    
    Returns:
        Dictionary with generated UUID information
    """
    try:
        if version == 1:
            generated_uuid = str(uuid.uuid1())
        elif version == 4:
            generated_uuid = str(uuid.uuid4())
        elif version == 5:
            # UUID5 requires a namespace and name, using default
            generated_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com'))
        else:
            return {
                "error": "Invalid UUID version. Use 1, 4, or 5",
                "status": "error"
            }
        
        return {
            "uuid": generated_uuid,
            "version": version,
            "format": "8-4-4-4-12 hexadecimal digits",
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": f"Error generating UUID: {str(e)}",
            "status": "error"
        }

def hash_text(text: str, algorithm: str = "sha256") -> Dict[str, Union[str, Dict]]:
    """
    Generate hash values for text using various algorithms.
    
    Use this function when users need to hash passwords, create checksums,
    or generate unique fingerprints for text.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
    
    Returns:
        Dictionary with hash results
    """
    try:
        if not text:
            return {"error": "Empty text provided", "status": "error"}
        
        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512
        }
        
        if algorithm not in algorithms:
            return {
                "error": f"Invalid algorithm. Available: {', '.join(algorithms.keys())}", 
                "status": "error"
            }
        
        hash_object = algorithms[algorithm]()
        hash_object.update(text.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        
        return {
            "hash": hash_hex,
            "algorithm": algorithm,
            "text_length": len(text),
            "hash_length": len(hash_hex),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": f"Error hashing text: {str(e)}",
            "status": "error"
        }

def encode_decode_base64(text: str, operation: str) -> Dict[str, Union[str, int]]:
    """
    Encode or decode text using Base64 encoding.
    
    Use this function when users need to encode data for transmission
    or decode Base64 encoded strings.
    
    Args:
        text: Text to encode/decode
        operation: 'encode' to encode, 'decode' to decode
    
    Returns:
        Dictionary with encoding/decoding results
    """
    try:
        if not text:
            return {"error": "Empty text provided", "status": "error"}
        
        if operation == "encode":
            encoded_bytes = base64.b64encode(text.encode('utf-8'))
            result = encoded_bytes.decode('utf-8')
            return {
                "result": result,
                "operation": "encode",
                "original": text,
                "original_length": len(text),
                "result_length": len(result),
                "status": "success"
            }
        elif operation == "decode":
            try:
                decoded_bytes = base64.b64decode(text)
                result = decoded_bytes.decode('utf-8')
                return {
                    "result": result,
                    "operation": "decode",
                    "original": text,
                    "original_length": len(text),
                    "result_length": len(result),
                    "status": "success"
                }
            except Exception as decode_error:
                return {
                    "error": f"Invalid Base64 string: {str(decode_error)}",
                    "operation": "decode",
                    "status": "error"
                }
        else:
            return {
                "error": "Invalid operation. Use 'encode' or 'decode'",
                "status": "error"
            }
        
    except Exception as e:
        return {
            "error": f"Error in Base64 operation: {str(e)}",
            "status": "error"
        }

def validate_url(url: str) -> Dict[str, Union[str, bool, Dict]]:
    """
    Validate and parse URL components.
    
    Use this function when users need to validate URLs or extract
    URL components like domain, path, parameters.
    
    Args:
        url: URL to validate and parse
    
    Returns:
        Dictionary with URL validation and parsing results
    """
    try:
        if not url:
            return {"error": "Empty URL provided", "status": "error"}
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        
        # Basic validation
        is_valid = bool(parsed.netloc and parsed.scheme)
        
        return {
            "is_valid": is_valid,
            "original_url": url,
            "components": {
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "domain": parsed.netloc.split(':')[0],
                "path": parsed.path,
                "params": parsed.params,
                "query": parsed.query,
                "fragment": parsed.fragment,
                "port": parsed.port
            },
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": f"Error validating URL: {str(e)}",
            "url": url,
            "status": "error"
        }

def format_json(json_string: str, indent: int = 2) -> Dict[str, Union[str, Dict]]:
    """
    Format and validate JSON strings.
    
    Use this function when users need to format JSON data,
    validate JSON syntax, or make JSON more readable.
    
    Args:
        json_string: JSON string to format
        indent: Number of spaces for indentation
    
    Returns:
        Dictionary with formatted JSON results
    """
    try:
        if not json_string:
            return {"error": "Empty JSON string provided", "status": "error"}
        
        # Parse JSON to validate
        parsed_json = json.loads(json_string)
        
        # Format with indentation
        formatted_json = json.dumps(parsed_json, indent=indent, ensure_ascii=False)
        
        # Calculate statistics
        minified_json = json.dumps(parsed_json, separators=(',', ':'))
        
        return {
            "formatted_json": formatted_json,
            "minified_json": minified_json,
            "is_valid": True,
            "statistics": {
                "original_length": len(json_string),
                "formatted_length": len(formatted_json),
                "minified_length": len(minified_json),
                "indent_spaces": indent
            },
            "status": "success"
        }
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON: {str(e)}",
            "is_valid": False,
            "original": json_string,
            "status": "error"
        }
    except Exception as e:
        return {
            "error": f"Error formatting JSON: {str(e)}",
            "status": "error"
        } 