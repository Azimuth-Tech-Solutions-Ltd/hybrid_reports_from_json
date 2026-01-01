"""
Pipeline script to enrich addresses with Google Maps data.
Supports processing addresses from file, command line, or stdin.
"""
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from enrichment import analyze_property


def load_addresses_from_file(file_path: str) -> List[str]:
    """Load addresses from a text file (one address per line)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            addresses = [line.strip() for line in f if line.strip()]
        return addresses
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def load_addresses_from_json(file_path: str) -> List[str]:
    """Load addresses from a JSON file (array of strings or array of objects with 'address' field)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, list):
            addresses = []
            for item in data:
                if isinstance(item, str):
                    addresses.append(item)
                elif isinstance(item, dict) and 'address' in item:
                    addresses.append(item['address'])
                else:
                    print(f"Warning: Skipping invalid item: {item}")
            return addresses
        else:
            print("Error: JSON file must contain an array of addresses.")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)


def process_addresses(
    addresses: List[str],
    commute_destination: str = "Charing Cross, London",
    output_file: Optional[str] = None,
    pretty: bool = True
) -> List[Dict[str, Any]]:
    """
    Process a list of addresses and return enriched data.
    
    Args:
        addresses: List of address strings to process
        commute_destination: Destination for commute calculations
        output_file: Optional path to write JSON output
        pretty: Whether to format JSON output nicely
        
    Returns:
        List of enriched property data dictionaries
    """
    results = []
    
    print(f"Processing {len(addresses)} address(es)...")
    for idx, address in enumerate(addresses, 1):
        print(f"\n[{idx}/{len(addresses)}] Processing: {address}")
        result = analyze_property(address, commute_destination)
        results.append(result)
    
    # Write to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                json.dump(results, f, ensure_ascii=False)
        
        print(f"\n[SUCCESS] Results written to: {output_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Enrich addresses with Google Maps data (geocoding, amenities, transport, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single address from command line
  python pipeline.py --address "10 Macaulay Road, London, SW4 0QX"
  
  # Process addresses from a text file
  python pipeline.py --input addresses.txt --output results.json
  
  # Process addresses from a JSON file
  python pipeline.py --input addresses.json --output results.json
  
  # Process addresses from stdin (one per line)
  echo "Address 1" | python pipeline.py --stdin --output results.json
  
  # Custom commute destination
  python pipeline.py --input addresses.txt --commute-dest "Oxford Street, London"
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--address',
        type=str,
        help='Single address to process'
    )
    input_group.add_argument(
        '--input',
        type=str,
        help='Input file path (text file with one address per line, or JSON array)'
    )
    input_group.add_argument(
        '--stdin',
        action='store_true',
        help='Read addresses from stdin (one per line)'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (default: print to stdout)'
    )
    parser.add_argument(
        '--commute-dest',
        type=str,
        default="Charing Cross, London",
        help='Destination for commute time calculation (default: "Charing Cross, London")'
    )
    parser.add_argument(
        '--compact',
        action='store_true',
        help='Output compact JSON (no indentation)'
    )
    
    args = parser.parse_args()
    
    # Load addresses
    addresses = []
    if args.address:
        addresses = [args.address]
    elif args.stdin:
        addresses = [line.strip() for line in sys.stdin if line.strip()]
        if not addresses:
            print("Error: No addresses provided via stdin")
            sys.exit(1)
    elif args.input:
        input_path = Path(args.input)
        if input_path.suffix.lower() == '.json':
            addresses = load_addresses_from_json(args.input)
        else:
            addresses = load_addresses_from_file(args.input)
    
    if not addresses:
        print("Error: No addresses to process")
        sys.exit(1)
    
    # Process addresses
    results = process_addresses(
        addresses,
        commute_destination=args.commute_dest,
        output_file=args.output,
        pretty=not args.compact
    )
    
    # Print to stdout if no output file specified
    if not args.output:
        if args.compact:
            print(json.dumps(results, ensure_ascii=False))
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
    
    print(f"\n[SUCCESS] Successfully processed {len(results)} address(es)")


if __name__ == "__main__":
    main()

