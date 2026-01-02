"""
FIPS Code Enrichment System

Federal Information Processing Standards (FIPS) codes for US geographic areas.
"""

from typing import Optional, Dict, Tuple
import pandas as pd


# US State FIPS codes (2-digit)
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11", "PR": "72", "VI": "78", "GU": "66", "AS": "60",
    "MP": "69",
}

# Reverse lookup: FIPS code to state abbreviation
FIPS_TO_STATE = {v: k for k, v in STATE_FIPS.items()}

# State names to abbreviations
STATE_NAMES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}


class FIPSEnricher:
    """
    FIPS code enrichment for US geographic data.

    Adds state and county FIPS codes to datasets.
    """

    def __init__(self):
        """Initialize FIPS enricher."""
        self.state_fips = STATE_FIPS
        self.fips_to_state = FIPS_TO_STATE
        self.state_names = STATE_NAMES

    def get_state_fips(self, state: str) -> Optional[str]:
        """
        Get state FIPS code from state abbreviation or name.

        Args:
            state: State abbreviation (e.g., "CA") or name (e.g., "California")

        Returns:
            2-digit FIPS code or None if not found
        """
        # Try as abbreviation
        if state.upper() in self.state_fips:
            return self.state_fips[state.upper()]

        # Try as full name
        if state in self.state_names:
            abbr = self.state_names[state]
            return self.state_fips[abbr]

        return None

    def get_state_from_fips(self, fips_code: str) -> Optional[str]:
        """
        Get state abbreviation from FIPS code.

        Args:
            fips_code: 2-digit state FIPS code

        Returns:
            State abbreviation or None if not found
        """
        # Handle full FIPS (state+county) - extract first 2 digits
        if len(fips_code) > 2:
            fips_code = fips_code[:2]

        return self.fips_to_state.get(fips_code)

    def parse_fips(self, fips_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse full FIPS code into state and county components.

        Args:
            fips_code: Full FIPS code (e.g., "06075" for San Francisco County, CA)

        Returns:
            Tuple of (state_fips, county_fips)
        """
        if not fips_code or len(fips_code) < 2:
            return None, None

        state_fips = fips_code[:2]
        county_fips = fips_code[2:] if len(fips_code) > 2 else None

        return state_fips, county_fips

    def enrich_dataframe(
        self,
        df: pd.DataFrame,
        state_col: str = "state",
        output_col: str = "fips_state",
    ) -> pd.DataFrame:
        """
        Enrich DataFrame with state FIPS codes.

        Args:
            df: Pandas DataFrame
            state_col: Column containing state abbreviations or names
            output_col: Output column name for FIPS codes

        Returns:
            DataFrame with FIPS codes added
        """
        df = df.copy()

        # Add FIPS codes
        df[output_col] = df[state_col].apply(
            lambda x: self.get_state_fips(x) if pd.notna(x) else None
        )

        return df

    def validate_fips(self, fips_code: str) -> bool:
        """
        Validate FIPS code format.

        Args:
            fips_code: FIPS code to validate

        Returns:
            True if valid format
        """
        if not fips_code:
            return False

        # Should be 2 or 5 digits
        if len(fips_code) not in [2, 5]:
            return False

        # Should be numeric
        if not fips_code.isdigit():
            return False

        # State portion should be valid
        state_fips = fips_code[:2]
        if state_fips not in self.fips_to_state:
            return False

        return True

    def get_all_state_fips(self) -> Dict[str, str]:
        """Get dictionary of all state abbreviations to FIPS codes."""
        return self.state_fips.copy()

    def get_all_states(self) -> list:
        """Get list of all state abbreviations."""
        return sorted(self.state_fips.keys())


def zip_to_fips_approximation(zip_code: str) -> Optional[str]:
    """
    Approximate FIPS state code from ZIP code.

    Note: This is a rough approximation based on ZIP code ranges.
    For accurate mapping, use Census geocoding service.

    Args:
        zip_code: 5-digit ZIP code

    Returns:
        2-digit state FIPS code or None
    """
    if not zip_code or len(zip_code) < 5:
        return None

    try:
        zip_int = int(zip_code[:5])
    except ValueError:
        return None

    # Approximate ZIP to state mapping
    if 35000 <= zip_int <= 36999:
        return "01"  # AL
    elif 99500 <= zip_int <= 99999:
        return "02"  # AK
    elif 85000 <= zip_int <= 86999:
        return "04"  # AZ
    elif 71600 <= zip_int <= 72999:
        return "05"  # AR
    elif 90000 <= zip_int <= 96699:
        return "06"  # CA
    elif 80000 <= zip_int <= 81999:
        return "08"  # CO
    elif 6000 <= zip_int <= 6999:
        return "09"  # CT
    elif 19700 <= zip_int <= 19999:
        return "10"  # DE
    elif 32000 <= zip_int <= 34999:
        return "12"  # FL
    elif 30000 <= zip_int <= 31999:
        return "13"  # GA
    elif 96700 <= zip_int <= 96999:
        return "15"  # HI
    elif 83200 <= zip_int <= 83999:
        return "16"  # ID
    elif 60000 <= zip_int <= 62999:
        return "17"  # IL
    elif 46000 <= zip_int <= 47999:
        return "18"  # IN
    elif 50000 <= zip_int <= 52999:
        return "19"  # IA
    elif 66000 <= zip_int <= 67999:
        return "20"  # KS
    elif 40000 <= zip_int <= 42999:
        return "21"  # KY
    elif 70000 <= zip_int <= 71599:
        return "22"  # LA
    elif 3900 <= zip_int <= 4999:
        return "23"  # ME
    elif 20600 <= zip_int <= 21999:
        return "24"  # MD
    elif 1000 <= zip_int <= 2799:
        return "25"  # MA
    elif 48000 <= zip_int <= 49999:
        return "26"  # MI
    elif 55000 <= zip_int <= 56999:
        return "27"  # MN
    elif 38600 <= zip_int <= 39999:
        return "28"  # MS
    elif 63000 <= zip_int <= 65999:
        return "29"  # MO
    elif 59000 <= zip_int <= 59999:
        return "30"  # MT
    elif 68000 <= zip_int <= 69999:
        return "31"  # NE
    elif 88900 <= zip_int <= 89999:
        return "32"  # NV
    elif 3000 <= zip_int <= 3899:
        return "33"  # NH
    elif 7000 <= zip_int <= 8999:
        return "34"  # NJ
    elif 87000 <= zip_int <= 88499:
        return "35"  # NM
    elif 10000 <= zip_int <= 14999:
        return "36"  # NY
    elif 27000 <= zip_int <= 28999:
        return "37"  # NC
    elif 58000 <= zip_int <= 58999:
        return "38"  # ND
    elif 43000 <= zip_int <= 45999:
        return "39"  # OH
    elif 73000 <= zip_int <= 74999:
        return "40"  # OK
    elif 97000 <= zip_int <= 97999:
        return "41"  # OR
    elif 15000 <= zip_int <= 19699:
        return "42"  # PA
    elif 2800 <= zip_int <= 2999:
        return "44"  # RI
    elif 29000 <= zip_int <= 29999:
        return "45"  # SC
    elif 57000 <= zip_int <= 57999:
        return "46"  # SD
    elif 37000 <= zip_int <= 38599:
        return "47"  # TN
    elif 75000 <= zip_int <= 79999 or 88500 <= zip_int <= 88899:
        return "48"  # TX
    elif 84000 <= zip_int <= 84999:
        return "49"  # UT
    elif 5000 <= zip_int <= 5999:
        return "50"  # VT
    elif 20000 <= zip_int <= 20599 or 22000 <= zip_int <= 24699:
        return "51"  # VA
    elif 98000 <= zip_int <= 99499:
        return "53"  # WA
    elif 24700 <= zip_int <= 26999:
        return "54"  # WV
    elif 53000 <= zip_int <= 54999:
        return "55"  # WI
    elif 82000 <= zip_int <= 83199:
        return "56"  # WY
    elif 20000 <= zip_int <= 20599:
        return "11"  # DC

    return None
