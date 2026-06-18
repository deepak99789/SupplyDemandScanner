import pandas as pd
import numpy as np

# =====================================================
# PROFILE RULES
# =====================================================

PROFILE_RULES = {

    "Good": {
        "legin": 2.0,
        "legout": 4.0,
        "body_ratio": 0.60,
        "min_score": 60
    },

    "Strong": {
        "legin": 3.0,
        "legout": 6.0,
        "body_ratio": 0.70,
        "min_score": 75
    },

    "Best": {
        "legin": 4.0,
        "legout": 8.0,
        "body_ratio": 0.75,
        "min_score": 90
    }

}


# =====================================================
# CANDLE FUNCTIONS
# =====================================================

def body(c):
    return abs(c["Close"]-c["Open"])


def rng(c):
    return c["High"]-c["Low"]


def bullish(c):
    return c["Close"]>c["Open"]


def bearish(c):
    return c["Close"]<c["Open"]


# =====================================================
# BASE DETECTION
# =====================================================

def detect_base(df,start,base_count):

    if start+base_count>=len(df):
        return None

    base=df.iloc[start:start+base_count]

    bodies=(base["Close"]-base["Open"]).abs()

    if len(bodies)==0:
        return None

    X=bodies.max()

    if X==0:
        return None

    # Similar body size
    if bodies.max()>bodies.min()*2.5:
        return None

    # Compact range
    total_range=base["High"].max()-base["Low"].min()

    if total_range>X*3:
        return None

    # Wick filter
    for _,r in base.iterrows():

        b=body(r)

        rr=rng(r)

        if rr==0:
            return None

        if b/rr<0.25:
            return None

    return{

        "start":start,

        "end":start+base_count-1,

        "body":X,

        "high":base["High"].max(),

        "low":base["Low"].min(),

        "base":base

    }


# =====================================================
# LEG-IN
# =====================================================

def detect_legin(df,base,profile):

    idx=base["start"]-1

    if idx<0:
        return None

    candle=df.iloc[idx]

    b=body(candle)

    need=base["body"]*PROFILE_RULES[profile]["legin"]

    if b<need:
        return None

    rr=rng(candle)

    if rr==0:
        return None

    if b/rr<PROFILE_RULES[profile]["body_ratio"]:
        return None

    return{

        "index":idx,

        "body":b,

        "direction":"Bullish" if bullish(candle) else "Bearish",

        "candle":candle

    }


# =====================================================
# LEG-OUT
# =====================================================

def detect_legout(df,base,profile,selected_legout_counts):

    start=base["end"]+1

    if start>=len(df):
        return []

    rule=PROFILE_RULES[profile]

    counts=[]

    for c in selected_legout_counts:

        if c=="More Than 3":

            counts.extend([4,5,6,7,8,9,10])

        else:

            counts.append(int(c))

    counts=sorted(set(counts))

    output=[]

    for count in counts:

        end=start+count

        if end>len(df):
            continue

        leg=df.iloc[start:end]

        if len(leg)!=count:
            continue

        first=leg.iloc[0]

        direction="Bullish" if bullish(first) else "Bearish"

        valid=True

        previous=None

        for _,row in leg.iterrows():

            b=body(row)

            rr=rng(row)

            if rr==0:

                valid=False

                break

            if b<base["body"]*rule["legout"]:

                valid=False

                break

            if b/rr<rule["body_ratio"]:

                valid=False

                break

            d="Bullish" if bullish(row) else "Bearish"

            if d!=direction:

                valid=False

                break

            if previous is not None:

                if direction=="Bullish":

                    if row.Close<=previous:

                        valid=False

                        break

                else:

                    if row.Close>=previous:

                        valid=False

                        break

            previous=row.Close

        if not valid:
            continue

        last=leg.iloc[-1]

        buffer=base["body"]*0.20

        if direction=="Bullish":

            if last.Close<=base["high"]+buffer:
                continue

        else:

            if last.Close>=base["low"]-buffer:
                continue

        output.append({

            "count":count,

            "direction":direction,

            "last":last,

            "candles":leg

        })

    return output

# =====================================================
# PATTERN CLASSIFICATION
# =====================================================

def classify_pattern(legin, legout):

    li = legin["direction"]
    lo = legout["direction"]

    if li == "Bullish" and lo == "Bullish":
        return "RBR", "Demand"

    elif li == "Bearish" and lo == "Bullish":
        return "DBR", "Demand"

    elif li == "Bullish" and lo == "Bearish":
        return "RBD", "Supply"

    elif li == "Bearish" and lo == "Bearish":
        return "DBD", "Supply"

    return None, None


# =====================================================
# CREATE ZONE
# =====================================================

def create_zone(symbol,
                timeframe,
                profile,
                pattern,
                zone_type,
                base,
                legout,
                formed_at):

    base_high = float(base["high"])
    base_low = float(base["low"])

    if zone_type == "Demand":

        proximal = base_high
        distal = base_low
        risk = proximal - distal
        target = proximal + risk * 2

    else:

        proximal = base_low
        distal = base_high
        risk = distal - proximal
        target = proximal - risk * 2

    return {

        "Symbol": symbol,

        "Timeframe": timeframe,

        "Profile": profile,

        "Pattern": pattern,

        "Type": zone_type,

        "Base Count":
            base["end"] - base["start"] + 1,

        "Legout Count":
            legout["count"],

        "Status":
            "FRESH",

        "Proximal":
            round(proximal, 5),

        "Distal":
            round(distal, 5),

        "Target (1:2)":
            round(target, 5),

        "Risk":
            round(risk, 5),

        "Formed At":
            formed_at

    }


# =====================================================
# IMPULSE SCORE
# =====================================================

def impulse_score(base, legin, legout):

    score = 0

    # Leg-In

    if legin["body"] >= base["body"] * 2:
        score += 20

    if legin["body"] >= base["body"] * 3:
        score += 10

    # Leg-Out

    last = legout["last"]

    body = abs(last.Close - last.Open)
    rng = last.High - last.Low

    if rng > 0:

        ratio = body / rng

        if ratio >= 0.60:
            score += 20

        if ratio >= 0.75:
            score += 10

    # Consecutive candles

    if legout["count"] >= 2:
        score += 15

    if legout["count"] >= 3:
        score += 10

    # Breakout

    if legout["direction"] == "Bullish":

        distance = last.Close - base["high"]

    else:

        distance = base["low"] - last.Close

    if distance > base["body"]:
        score += 15

    return min(score, 100)


# =====================================================
# BASE SCORE
# =====================================================

def base_score(base):

    score = 100

    b = (
        base["base"]["Close"] -
        base["base"]["Open"]
    ).abs()

    if b.max() > b.min() * 2:
        score -= 25

    rng = (
        base["base"]["High"].max() -
        base["base"]["Low"].min()
    )

    if rng > base["body"] * 3:
        score -= 25

    return max(score, 0)


# =====================================================
# STATUS CHECK
# =====================================================

def check_zone_status(df, zone, formed_index):

    future = df.iloc[formed_index + 1:]

    if len(future) == 0:
        return "FRESH"

    if zone["Type"] == "Demand":

        for _, row in future.iterrows():

            # SL Hit

            if row.Low < zone["Distal"]:
                return "SL HIT"

            # Target Hit

            if row.High >= zone["Target (1:2)"]:
                return "TARGET HIT"

            # Used

            if row.Low <= zone["Proximal"]:
                return "USED"

        return "FRESH"

    else:

        for _, row in future.iterrows():

            if row.High > zone["Distal"]:
                return "SL HIT"

            if row.Low <= zone["Target (1:2)"]:
                return "TARGET HIT"

            if row.High >= zone["Proximal"]:
                return "USED"

        return "FRESH"

  # =====================================================
# REMOVE DUPLICATE ZONES
# =====================================================

def remove_duplicate_zones(zones):

    final = []

    for zone in zones:

        duplicate = False

        for old in final:

            if old["Symbol"] != zone["Symbol"]:
                continue

            if old["Timeframe"] != zone["Timeframe"]:
                continue

            if old["Type"] != zone["Type"]:
                continue

            if abs(old["Proximal"] - zone["Proximal"]) < 0.0001:

                if zone["Strength"] > old["Strength"]:

                    final.remove(old)
                    final.append(zone)

                duplicate = True
                break

        if not duplicate:
            final.append(zone)

    return final


# =====================================================
# REMOVE NESTED ZONES
# =====================================================

def remove_nested_zones(zones):

    final = []

    for zone in zones:

        keep = True

        for old in final:

            if old["Type"] != zone["Type"]:
                continue

            if zone["Proximal"] >= old["Proximal"] and \
               zone["Distal"] <= old["Distal"]:

                if old["Strength"] >= zone["Strength"]:
                    keep = False
                    break

        if keep:
            final.append(zone)

    return final


# =====================================================
# MAIN SCANNER
# =====================================================

def scan_supply_demand_zones(
    df,
    symbol_name,
    tf_name,
    selected_base_counts=[1,2,3],
    selected_legout_counts=[1,2,3,"More Than 3"],
    profile="Good"
):

    zones = []

    n = len(df)

    for i in range(5, n - 15):

        for base_count in selected_base_counts:

            base = detect_base(df, i, base_count)

            if base is None:
                continue

            legin = detect_legin(df, base, profile)

            if legin is None:
                continue

            legouts = detect_legout(
                df,
                base,
                profile,
                selected_legout_counts
            )

            if len(legouts) == 0:
                continue

            for legout in legouts:

                pattern, zone_type = classify_pattern(
                    legin,
                    legout
                )

                if pattern is None:
                    continue

                zone = create_zone(
                    symbol_name,
                    tf_name,
                    profile,
                    pattern,
                    zone_type,
                    base,
                    legout,
                    df.index[base["end"]]
                )

                impulse = impulse_score(
                    base,
                    legin,
                    legout
                )

                base_quality = base_score(base)

                zone["Strength"] = int(
                    impulse * 0.70 +
                    base_quality * 0.30
                )

                # Profile Quality Filter

                min_score = PROFILE_RULES[profile]["min_score"]

                if zone["Strength"] < min_score:
                    continue

                zone["Status"] = check_zone_status(
                    df,
                    zone,
                    base["end"]
                )

                zones.append(zone)

    zones = remove_duplicate_zones(zones)

    zones = remove_nested_zones(zones)

    zones = sorted(
        zones,
        key=lambda x: (
            x["Strength"],
            x["Base Count"],
            x["Legout Count"]
        ),
        reverse=True
    )

    return zones
