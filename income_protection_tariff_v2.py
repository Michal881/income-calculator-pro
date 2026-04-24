
import pandas as pd
import numpy as np
import re

INPUT_CSV = "ML Income protection.csv"
SEP = ";"

COLUMN_MAP = {
    "death": ("Śmierć świadczenie", "Śmierć składka"),
    "disability": ("Inwalidztwo świadczenie", "Inwalidztwo składka"),
    "ptd_accident": ("PTD wypadek świadczenie", "PTD wypadek składka"),
    "ptd_sickness": ("PTD choroba świadczenie", "PTD choroba składka"),
    "ttd_accident": ("TTD wypadek świadczenie", "TTD wypadek składka"),
    "ttd_sickness": ("TTD choroba świadczenie", "TTD choroba składka"),
    "hiv_hbv_hcv": ("HIV/WZW świadczenie", "HIV/WZW składka"),
}

BASE_COLS = {
    "sex": "Płeć",
    "risk_class": "Klasa ryzyka",
    "age": "Wiek w dniu początku okresu (lat)",
    "assigned_premium": "Składka przypisana",
    "reference_premium": "Składka referencyjna",
    "installments": "Liczba rat",
    "distribution_fee": "Opłata dystrybucyjna",
    "waiting_sickness": "Okres wyczekiwania choroba",
    "waiting_accident": "Okres wyczekiwania wypadek",
    "benefit_period_sickness": "Okres odszkodowawczy choroba",
    "benefit_period_accident": "Okres odszkodowawczy wypadek",
    "active_life_risk": "Ryzyko/a aktywnego życia",
    "additional_benefits": "Świadczenie/a dodatkowe",
    "hiv_wzw_flag": "HIV/WZW",
}

# Ryzyka, dla których klasa zawodowa ma sens underwritingowy.
CLASS_SENSITIVE_RISKS = {
    "death",
    "disability",
    "ptd_accident",
    "ptd_sickness",
    "ttd_accident",
}

# Ryzyka chorobowe / dodatki, gdzie klasa ryzyka w danych nie daje stabilnej monotoniczności.
CLASS_NEUTRAL_RISKS = {
    "ttd_sickness",
    "hiv_hbv_hcv",
}

def clean_text(x):
    if pd.isna(x):
        return np.nan
    x = str(x).replace("\xa0", " ").strip()
    return np.nan if x == "" else x

def parse_money(x):
    if pd.isna(x):
        return np.nan
    x = str(x).replace("\xa0", "").replace(" ", "").strip()
    if x == "":
        return np.nan
    x = x.replace(",", "")
    try:
        return float(x)
    except ValueError:
        return np.nan

def parse_period_number(x):
    x = clean_text(x)
    if pd.isna(x):
        return np.nan
    m = re.search(r"(\d+)", x)
    return float(m.group(1)) if m else np.nan

def normalize_risk_class(x):
    x = clean_text(x)
    if pd.isna(x):
        return "KLASA II"
    return x.upper().replace("  ", " ")

def risk_class_num(x):
    mapping = {"KLASA I": 1, "KLASA II": 2, "KLASA III": 3, "KLASA IV": 4, "KLASA V": 5}
    return mapping.get(str(x).upper().strip(), np.nan)

def yes_no(x):
    x = clean_text(x)
    if pd.isna(x):
        return 0
    return 1 if str(x).upper().startswith("T") else 0

def age_band(age):
    if pd.isna(age):
        return "unknown"
    if age < 35:
        return "<35"
    if age <= 45:
        return "35-45"
    if age <= 55:
        return "46-55"
    return "56+"

def load_data(path):
    df = pd.read_csv(path, sep=SEP, encoding="utf-8-sig")
    df.columns = [clean_text(c) for c in df.columns]
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].map(clean_text)
    return df

def build_policy_dataset(df):
    out = pd.DataFrame()
    for new, old in BASE_COLS.items():
        out[new] = df[old] if old in df.columns else np.nan

    for c in ["assigned_premium", "reference_premium", "distribution_fee"]:
        out[c] = out[c].map(parse_money)

    out["age"] = pd.to_numeric(out["age"], errors="coerce")
    out["installments"] = pd.to_numeric(out["installments"], errors="coerce")
    out["risk_class"] = out["risk_class"].map(normalize_risk_class)
    out["risk_class_num"] = out["risk_class"].map(risk_class_num)
    out["sex_male"] = out["sex"].map(lambda x: 1 if clean_text(x) == "Mężczyzna" else 0)
    out["sex_female"] = out["sex"].map(lambda x: 1 if clean_text(x) == "Kobieta" else 0)
    out["age_band"] = out["age"].map(age_band)
    out["waiting_sickness_days"] = out["waiting_sickness"].map(parse_period_number)
    out["waiting_accident_days"] = out["waiting_accident"].map(parse_period_number)
    out["benefit_period_sickness_months"] = out["benefit_period_sickness"].map(parse_period_number)
    out["benefit_period_accident_months"] = out["benefit_period_accident"].map(parse_period_number)
    out["active_life_risk_flag"] = out["active_life_risk"].map(yes_no)
    out["additional_benefits_flag"] = out["additional_benefits"].map(yes_no)
    out["hiv_wzw_flag_num"] = out["hiv_wzw_flag"].map(yes_no)
    return out

def build_component_dataset(df, policy):
    rows = []
    for idx, row in df.iterrows():
        for risk_type, (benefit_col, premium_col) in COLUMN_MAP.items():
            if benefit_col not in df.columns or premium_col not in df.columns:
                continue
            benefit = parse_money(row.get(benefit_col))
            premium = parse_money(row.get(premium_col))
            if pd.notna(benefit) and benefit > 0 and pd.notna(premium) and premium > 0:
                rows.append({
                    "policy_row": idx,
                    "risk_type": risk_type,
                    "sex": policy.loc[idx, "sex"],
                    "sex_male": policy.loc[idx, "sex_male"],
                    "sex_female": policy.loc[idx, "sex_female"],
                    "risk_class": policy.loc[idx, "risk_class"],
                    "risk_class_num": policy.loc[idx, "risk_class_num"],
                    "age": policy.loc[idx, "age"],
                    "age_band": policy.loc[idx, "age_band"],
                    "benefit": benefit,
                    "component_premium": premium,
                    "component_rate": premium / benefit,
                    "waiting_sickness_days": policy.loc[idx, "waiting_sickness_days"],
                    "waiting_accident_days": policy.loc[idx, "waiting_accident_days"],
                    "benefit_period_sickness_months": policy.loc[idx, "benefit_period_sickness_months"],
                    "benefit_period_accident_months": policy.loc[idx, "benefit_period_accident_months"],
                    "active_life_risk_flag": policy.loc[idx, "active_life_risk_flag"],
                    "additional_benefits_flag": policy.loc[idx, "additional_benefits_flag"],
                    "hiv_wzw_flag_num": policy.loc[idx, "hiv_wzw_flag_num"],
                })
    return pd.DataFrame(rows)

def smooth_monotonic_class_factors(raw):
    """
    Wersja v2:
    - dla ryzyk accident / kapitałowych wymuszamy łagodną monotoniczność po klasie,
    - dla TTD sickness oraz HIV/WZW klasa = neutralna, bo dane nie pokazują stabilnego wpływu.
    """
    rows = []
    all_classes = ["KLASA I", "KLASA II", "KLASA III", "KLASA IV", "KLASA V"]

    for risk_type in sorted(raw["risk_type"].unique()):
        if risk_type in CLASS_NEUTRAL_RISKS:
            for rc in all_classes:
                rows.append({
                    "risk_type": risk_type,
                    "risk_class": rc,
                    "risk_class_factor_v2": 1.0,
                    "method": "class_neutral"
                })
            continue

        sub = raw[raw["risk_type"] == risk_type].copy()
        class_to_factor = dict(zip(sub["risk_class"], sub["raw_risk_class_factor"]))

        # domyślna ścieżka, jeśli którejś klasy brakuje: użyj rozsądnej drabinki bazowej
        fallback = {
            "KLASA I": 0.80,
            "KLASA II": 1.00,
            "KLASA III": 1.20,
            "KLASA IV": 1.50,
            "KLASA V": 1.80,
        }

        factors = []
        for rc in all_classes:
            factors.append(float(class_to_factor.get(rc, fallback[rc])))

        # wygładzenie: klasa II jako okolice 1.00
        # monotoniczność: każda kolejna klasa nie może być niższa od poprzedniej
        smoothed = []
        for i, f in enumerate(factors):
            if i == 0:
                smoothed.append(min(f, 1.0))
            else:
                smoothed.append(max(f, smoothed[-1]))

        # lekkie ograniczenia, żeby nie mieć dzikich faktorów z małych próbek
        capped = [min(max(f, 0.70), 2.50) for f in smoothed]

        for rc, f in zip(all_classes, capped):
            rows.append({
                "risk_type": risk_type,
                "risk_class": rc,
                "risk_class_factor_v2": f,
                "method": "monotonic_smoothed"
            })

    return pd.DataFrame(rows)

def build_tariff_v2(components):
    c = components.copy()

    base = (
        c.groupby("risk_type", dropna=False)["component_rate"]
        .median()
        .reset_index()
        .rename(columns={"component_rate": "base_rate_median"})
    )

    raw_class = (
        c.groupby(["risk_type", "risk_class"], dropna=False)["component_rate"]
        .median()
        .reset_index()
        .merge(base, on="risk_type", how="left")
    )
    raw_class["raw_risk_class_factor"] = raw_class["component_rate"] / raw_class["base_rate_median"]

    class_v2 = smooth_monotonic_class_factors(raw_class)

    raw_age = (
        c.groupby(["risk_type", "age_band"], dropna=False)["component_rate"]
        .median()
        .reset_index()
        .merge(base, on="risk_type", how="left")
    )
    raw_age["raw_age_factor"] = raw_age["component_rate"] / raw_age["base_rate_median"]

    # v2: wiek stosujemy głównie do chorobowego TTD, a dla reszty zostawiamy neutralnie,
    # chyba że dane pokażą stabilny wzorzec.
    all_bands = ["<35", "35-45", "46-55", "56+"]
    age_rows = []
    for risk_type in sorted(c["risk_type"].unique()):
        sub = raw_age[raw_age["risk_type"] == risk_type]
        lookup = dict(zip(sub["age_band"], sub["raw_age_factor"]))

        for band in all_bands:
            if risk_type == "ttd_sickness":
                f = float(lookup.get(band, 1.0))
                f = min(max(f, 0.70), 1.60)
                method = "age_sensitive"
            else:
                f = 1.0
                method = "age_neutral_v2"
            age_rows.append({
                "risk_type": risk_type,
                "age_band": band,
                "age_factor_v2": f,
                "method": method
            })

    age_v2 = pd.DataFrame(age_rows)
    return base, raw_class, class_v2, raw_age, age_v2

def lookup_value(table, conditions, value_col, default=1.0):
    sub = table.copy()
    for col, val in conditions.items():
        sub = sub[sub[col] == val]
    if len(sub) == 0:
        return default
    return float(sub[value_col].iloc[0])

def price_component_v2(benefit, risk_type, risk_class, age, base, class_v2, age_v2):
    if benefit is None or pd.isna(benefit) or benefit <= 0:
        return 0.0

    base_rate = lookup_value(base, {"risk_type": risk_type}, "base_rate_median", default=0.0)
    class_factor = lookup_value(
        class_v2,
        {"risk_type": risk_type, "risk_class": risk_class},
        "risk_class_factor_v2",
        default=1.0
    )
    age_factor = lookup_value(
        age_v2,
        {"risk_type": risk_type, "age_band": age_band(age)},
        "age_factor_v2",
        default=1.0
    )

    return benefit * base_rate * class_factor * age_factor

def price_policy_v2(input_dict, base, class_v2, age_v2, distribution_fee_rate=0.10):
    age = input_dict.get("age", 40)
    risk_class = input_dict.get("risk_class", "KLASA II")

    details = {}
    total = 0.0

    for risk_type in COLUMN_MAP.keys():
        benefit = input_dict.get(risk_type, 0)
        premium = price_component_v2(
            benefit=benefit,
            risk_type=risk_type,
            risk_class=risk_class,
            age=age,
            base=base,
            class_v2=class_v2,
            age_v2=age_v2,
        )
        details[risk_type] = premium
        total += premium

    fee = total * distribution_fee_rate
    return {
        "component_premiums": details,
        "components_total": total,
        "distribution_fee": fee,
        "total_premium": total + fee,
    }

def main():
    df = load_data(INPUT_CSV)
    policy = build_policy_dataset(df)
    components = build_component_dataset(df, policy)
    base, raw_class, class_v2, raw_age, age_v2 = build_tariff_v2(components)

    policy.to_csv("v2_policy_dataset_clean.csv", index=False, encoding="utf-8-sig")
    components.to_csv("v2_component_dataset_for_tariff.csv", index=False, encoding="utf-8-sig")
    base.to_csv("v2_tariff_base_rates.csv", index=False, encoding="utf-8-sig")
    raw_class.to_csv("v2_raw_risk_class_factors.csv", index=False, encoding="utf-8-sig")
    class_v2.to_csv("v2_final_risk_class_factors.csv", index=False, encoding="utf-8-sig")
    raw_age.to_csv("v2_raw_age_factors.csv", index=False, encoding="utf-8-sig")
    age_v2.to_csv("v2_final_age_factors.csv", index=False, encoding="utf-8-sig")

    example = {
        "age": 42,
        "risk_class": "KLASA II",
        "death": 0,
        "disability": 0,
        "ptd_accident": 100000,
        "ptd_sickness": 100000,
        "ttd_accident": 15000,
        "ttd_sickness": 15000,
        "hiv_hbv_hcv": 200000,
    }

    result = price_policy_v2(example, base, class_v2, age_v2)
    print("Przykładowa kalkulacja v2:")
    print(result)

    print("\nZapisano pliki v2:")
    print("- v2_tariff_base_rates.csv")
    print("- v2_raw_risk_class_factors.csv")
    print("- v2_final_risk_class_factors.csv")
    print("- v2_raw_age_factors.csv")
    print("- v2_final_age_factors.csv")
    print("- v2_component_dataset_for_tariff.csv")
    print("- v2_policy_dataset_clean.csv")

if __name__ == "__main__":
    main()
