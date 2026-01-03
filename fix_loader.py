
import os

target_file = '/Users/pfay01/Projects/kie-v3/kie/data/loader.py'

# The complete valid function body logic that was corrupted
new_logic = """                    # If no fuzzy match, fallback to intelligent guessing
                    if prefer_categorical and unused_categorical:
                        # If requesting a category but no fuzzy match found, pick best categorical
                        # Avoid high cardinality (like IDs) and constants
                        best_cat = None
                        best_score = -1
                        for cat_col in unused_categorical:
                            cardinality = self.last_loaded[cat_col].nunique()
                            total_rows = len(self.last_loaded)

                            # Score: prefer moderate cardinality
                            # Penalize high cardinality (ID-like columns)
                            if cardinality >= total_rows * 0.9:
                                score = 1   # Nearly all unique (ID column)
                            elif cardinality < 2:
                                score = 0   # Constant, useless
                            elif 2 <= cardinality <= 20:
                                score = 10  # Ideal for grouping
                            else:
                                score = 5   # Moderate

                            if score > best_score:
                                best_score = score
                                best_cat = cat_col

                        candidate = best_cat if best_cat else unused_categorical[0]

                    elif unused_numeric:
                        # Score by: (1) Semantic Match (Highest Priority), (2) ID Avoidance, (3) Statistical Interest
                        scores = {}
                        for col in unused_numeric:
                            try:
                                col_lower = col.lower()
                                mean = self.last_loaded[col].mean()
                                std = self.last_loaded[col].std()

                                # Coefficient of variation
                                cv = (std / mean) if mean > 0 and not pd.isna(std) else 0

                                # 1. Semantic Detection (High Confidence)
                                id_keywords = ['id', 'code', 'zip', 'postal', 'ssn', 'key', 'index']
                                is_likely_id = any(keyword in col_lower for keyword in id_keywords)

                                revenue_keywords = ['revenue', 'sales', 'price', 'cost', 'amount', 'value', 'million', 'dollar', 'usd', 'budget', 'profit', 'margin']
                                is_likely_revenue = any(keyword in col_lower for keyword in revenue_keywords)

                                count_keywords = ['count', 'number', 'quantity', 'qty', 'volume']
                                is_likely_count = any(keyword in col_lower for keyword in count_keywords)

                                # 2. ID/Code Detection (Statistical penalty)
                                # Heavy penalty for explicit ID names or very high uniqueness + sequentiality
                                if is_likely_id:
                                    scores[col] = 0.0001
                                    continue
                                
                                # Heuristic: High cardinality integers with low variance relative to mean are often IDs
                                if mean > 10000 and cv < 0.01:
                                    scores[col] = 0.001
                                    continue

                                # 3. Scoring (Good metrics have variance)
                                # Base score is CV (Coefficient of Variation)
                                # This naturally prefers metrics that move vs constants
                                base_score = cv

                                # Apply Semantic Boosts
                                if prefer_revenue:
                                    if is_likely_revenue:
                                        base_score *= 5.0  # Huge boost for semantic match
                                    elif is_likely_count:
                                        base_score *= 0.5  # Penalty if we want $, not #
                                
                                # Neutralize Scale Bias:
                                # We do NOT simply multiply by magnitude. 
                                # A profit margin (0.15) is as valid as Revenue (1M).
                                # However, we give a tiny nudge to non-tiny numbers to avoid noise/rounding errors
                                if mean > 100:
                                    base_score *= 1.1
                                
                                scores[col] = base_score

                            except:
                                scores[col] = 0

                        # Pick column with highest score
                        if scores:
                            candidate = max(scores, key=scores.get)

                    mapping[req_col] = candidate
                    if candidate:
                        used_columns.add(candidate)
"""

# Read original lines
with open(target_file, 'r') as f:
    lines = f.readlines()

output_lines = []
inside_loop = False
cut_mode = False

# We rebuild the file:
# 1. Keep everything until the line `candidate = None` (around 380)
# 2. Insert new block
# 3. Skip existing broken/old logic lines until we hit `def get_summary`
# 4. Keep remaining lines

for line in lines:
    if 'def get_summary' in line:
        cut_mode = False  # Stop cutting, resume normal copying
    
    if cut_mode:
        continue # Skip the broken lines
        
    if 'candidate = None' in line:
        output_lines.append(line) # Keep the initialization
        output_lines.append(new_logic) # Insert our fix
        output_lines.append("\n        return mapping\n\n") # Close the function
        cut_mode = True # Start skipping the old corrupted body
        continue

    output_lines.append(line)

with open(target_file, 'w') as f:
    f.writelines(output_lines)

print("Successfully patched loader.py")
