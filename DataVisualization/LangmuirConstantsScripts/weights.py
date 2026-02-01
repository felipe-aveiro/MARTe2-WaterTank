import pandas as pd

# score = (regularity * 0.5) + (cicles/duration * 0.3) + (current * 0.2)
""" 
• regularity:

    Excelent = 3

    Good = 2

    Bad = 1

• cicles/duration:

    Many = 3

    Average = 2

    Few = 1

• current:

    Nominal = 3

    Slightly lower = 2

    Very low = 1
"""

shots_data = [
    [45754, "Multiple AC pulses, irregular shape and premature endings", 1, 3, 1],
    [45967, "Several perfect positive pulses, all nominal current", 3, 3, 3],
    [46241, "Best overall, perfect regular AC pulses, ideal case", 3, 3, 3],
    [52856, "Two AC pulses, below nominal and irregular", 1, 2, 1],
    [52857, "Six AC pulses, below nominal and irregular", 1, 3, 1],
    [53058, "One positive + three negatives, nominal current, some irregularity", 2, 2, 3],
    [53071, "One positive + two negatives, good regularity but slight current drop on negatives", 3, 2, 2],
    [53099, "Poor quality pulses, irregular current, below nominal", 2, 2, 2],
    [53105, "Single AC cycle, regular behavior but slightly under nominal current", 3, 1, 2],
    [53197, "Three AC pulses, well below nominal and irregular", 1, 3, 1]
]

# Create DataFrame
df_scores = pd.DataFrame(shots_data, columns=["Shot", "Description", "Regularity", "Cycles", "Current"])

# Apply weights: Regularity (0.5), Cycles (0.3), Current (0.2)
df_scores["Weighted_Score"] = (
    df_scores["Regularity"] * 0.5 +
    df_scores["Cycles"] * 0.3 +
    df_scores["Current"] * 0.2
)

# Normalize scores to range [1, 3]
min_score = df_scores["Weighted_Score"].min()
max_score = df_scores["Weighted_Score"].max()
df_scores["Final_Weight"] = 1 + (df_scores["Weighted_Score"] - min_score) * (2 / (max_score - min_score))

# Sort by final weight
df_sorted = df_scores.sort_values(by="Final_Weight", ascending=False)

# Print the full table
print("\n=== Balanced Shot Weights ===")
print(df_sorted[["Shot", "Description", "Regularity", "Cycles", "Current", "Final_Weight"]].to_string(index=False))

# Generate Python dictionary with final weights
shot_weights = {row["Shot"]: round(row["Final_Weight"], 2) for _, row in df_sorted.iterrows()}

print("\n=== Python Dictionary (shot_weights) ===")
print(shot_weights)