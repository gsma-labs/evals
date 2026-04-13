#!/usr/bin/env python
# -*-coding:utf-8 -*-

import io
import math
import os
import random

import numpy as np
import pandas as pd
from _types import Scenario
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from utils import (
    df_all_or_none,
    df_first_or_none,
    get_fields_at_time,
    get_fields_before_time,
    load_scenarios,
)

app = FastAPI(title="5G Drive-Test Analysis API", version="1.2.0")

# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------


FASTAPI_HOST = os.environ.get("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.environ.get("FASTAPI_PORT", "7860"))
DATA_SOURCE = os.environ.get("DATA_SOURCE", "data/Phase_1")
DATA_SPLIT = os.environ.get("DATA_SPLIT", "test")  # change to train if needed

# ------------------------------------------------------------------------------
# Load scenarios
# ------------------------------------------------------------------------------

SCENARIOS = load_scenarios(DATA_SOURCE, split=DATA_SPLIT)

# ------------------------------------------------------------------------------
# Middleware (CORS)
# ------------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Scenario context (X-Scenario-Id)
# ------------------------------------------------------------------------------


def get_scenario_by_id(scenario_id: str | None) -> Scenario:
    if not scenario_id:
        raise HTTPException(status_code=400, detail="Missing X-Scenario-Id header")
    for s in SCENARIOS:
        if s.scenario_id == scenario_id:
            return s
    raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")


def resolve_scenario(
    x_scenario_id: str | None = Header(default=None, alias="X-Scenario-Id"),
) -> Scenario:
    return get_scenario_by_id(x_scenario_id)


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def read_config_df(scenario: Scenario) -> pd.DataFrame:
    data = scenario.data.network_configuration_data
    if not data:
        raise HTTPException(
            status_code=404, detail="No network configuration data in scenario"
        )

    df = pd.read_csv(io.StringIO(data), sep="|")
    if "PCI" in df.columns:
        df["PCI"] = pd.to_numeric(df["PCI"], errors="coerce")
    return df


def read_user_plane_df(scenario: Scenario) -> pd.DataFrame:
    data = scenario.data.user_plane_data
    if not data:
        raise HTTPException(status_code=404, detail="No user-plane data in scenario")

    df = pd.read_csv(io.StringIO(data), sep="|")
    if "5G KPI PCell RF Serving PCI" in df.columns:
        df["5G KPI PCell RF Serving PCI"] = pd.to_numeric(
            df["5G KPI PCell RF Serving PCI"], errors="coerce"
        )
    return df


def read_signaling_plane_df(scenario: Scenario) -> pd.DataFrame:
    data = scenario.data.signaling_plane_data
    if not data:
        raise HTTPException(
            status_code=404,
            detail="The signaling-plane data is not available for this scenario",
        )
    df = pd.read_csv(io.StringIO(data), sep="|")
    return df


def read_traffic_df(scenario: Scenario) -> pd.DataFrame:
    data = scenario.data.traffic_data
    if not data:
        raise HTTPException(
            status_code=404,
            detail="The traffic data is not available for this scenario",
        )
    df = pd.read_csv(io.StringIO(data), sep="|")
    return df


def read_mr_df(scenario: Scenario) -> pd.DataFrame:
    data = scenario.data.mr_data
    if not data:
        raise HTTPException(
            status_code=404,
            detail="The traffic data is not available for this scenario",
        )
    df = pd.read_csv(io.StringIO(data), sep="|")
    return df


def gain_pattern(phi, theta):
    phi0 = np.radians(180)
    theta0 = np.radians(90)

    d_phi = np.abs(phi - phi0)
    d_phi = np.minimum(d_phi, 2 * np.pi - d_phi)
    d_theta = theta - theta0

    sigma_phi = np.radians(15)
    sigma_theta = np.radians(15)

    main_lobe = np.exp(
        -0.5 * ((d_phi / sigma_phi) ** 4) - 0.5 * ((d_theta / sigma_theta) ** 4)
    )
    side_lobe_phi = np.abs(phi - (phi0 + np.pi))
    side_lobe_phi = np.minimum(side_lobe_phi, 2 * np.pi - side_lobe_phi)
    side_lobe_theta = theta - theta0
    side_lobe = 0.1 * np.exp(
        -0.5 * (side_lobe_phi / sigma_phi) ** 2
        - 0.5 * (side_lobe_theta / sigma_theta) ** 2
    )

    isotropic = 0.001
    return main_lobe + side_lobe + isotropic


def beam_scenario_to_v_bw(name: str) -> float:
    if name == "DEFAULT":
        return 6.0
    try:
        suffix = int(name.split("_")[-1])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid beam scenario name.")
    if 1 <= suffix <= 5:
        return 6.0
    if 6 <= suffix <= 11:
        return 12.0
    if suffix >= 12:
        return 25.0
    raise HTTPException(status_code=400, detail="Invalid beam scenario index.")


def calculate_overlap_coverage(
    lon1, lat1, azimuth1, lon2, lat2, azimuth2, radius: float = 900.0
) -> float:
    if lon1 == 0 or lat1 == 0 or lon2 == 0 or lat2 == 0:
        return 0.0

    lat_to_meter = 111320.0
    lon_to_meter = 111320.0 * math.cos(math.radians(lat1))

    x2 = (lon2 - lon1) * lon_to_meter
    y2 = (lat2 - lat1) * lat_to_meter

    distance = math.sqrt(x2**2 + y2**2)

    if distance >= 2 * radius:
        return 0.0

    if distance < 0.1:
        return 1.0

    half_circle_area = 0.5 * math.pi * radius**2

    r1 = radius
    r2 = radius
    d = distance

    if d >= r1 + r2:
        overlap_area = 0.0
    elif d <= abs(r1 - r2):
        overlap_area = math.pi * min(r1, r2) ** 2
    else:
        r1_sq = r1**2
        r2_sq = r2**2
        d_sq = d**2

        alpha = math.acos((r1_sq + d_sq - r2_sq) / (2 * r1 * d))
        beta = math.acos((r2_sq + d_sq - r1_sq) / (2 * r2 * d))

        overlap_area = (
            r1_sq * alpha
            + r2_sq * beta
            - 0.5
            * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
        )

    azimuth_diff = abs(azimuth1 - azimuth2)
    azimuth_diff = min(azimuth_diff, 360 - azimuth_diff)
    if azimuth_diff > 180:
        azimuth_diff = 360 - azimuth_diff

    azimuth_factor = max(0, 1 - azimuth_diff / 180)

    overlap_coverage = (overlap_area / half_circle_area) * azimuth_factor

    return min(1.0, max(0.0, overlap_coverage))


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
        lat2_rad
    ) * math.cos(delta_lon)
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing


def calculate_angle_between_user_and_cell(
    user_lon: float,
    user_lat: float,
    cell_lon: float,
    cell_lat: float,
    cell_azimuth: int,
) -> float:
    bearing_to_user = calculate_bearing(cell_lat, cell_lon, user_lat, user_lon)
    angle_diff = abs(bearing_to_user - cell_azimuth)
    angle_diff = angle_diff % 360
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    return angle_diff


def haversine_distance(point_lon, point_lat, cell_lon, cell_lat):
    """
    Haversine Formula

    """
    R = 6371.0

    lat1 = math.radians(point_lat)
    lon1 = math.radians(point_lon)
    lat2 = math.radians(cell_lat)
    lon2 = math.radians(cell_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    distance = R * c

    return distance


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scenario")
def get_scenario(scenario: Scenario = Depends(resolve_scenario)):
    # Return as dict for JSON serialization (keeps "no other types" promise)
    return scenario.model_dump()


@app.get("/scenario/random")
def get_random_scenario():
    return random.choice(SCENARIOS).model_dump()


@app.get("/scenario/all")
def get_all_scenario():
    return [s.model_dump() for s in SCENARIOS]


@app.get("/config-data/json")
def get_config_data_json(scenario: Scenario = Depends(resolve_scenario)):
    df = read_config_df(scenario)
    return {"rows": df.to_dict(orient="records")}


@app.get("/config-data")
def get_config_data(scenario: Scenario = Depends(resolve_scenario)):
    data = scenario.data.network_configuration_data
    if not data:
        raise HTTPException(
            status_code=404, detail="No network configuration data in scenario"
        )
    return {"Network Configuration Data": data}


@app.get("/user-plane-data/json")
def get_user_plane_data_json(scenario: Scenario = Depends(resolve_scenario)):
    df = read_user_plane_df(scenario)
    return {"rows": df.to_dict(orient="records")}


@app.get("/user-plane-data")
def get_user_plane_data(scenario: Scenario = Depends(resolve_scenario)):
    data = scenario.data.user_plane_data
    if not data:
        raise HTTPException(status_code=404, detail="No user-plane data in scenario")
    return {"User Plane Data": data}


@app.get("/get_kpi_data")
def get_kpi_data(scenario: Scenario = Depends(resolve_scenario)):
    data = scenario.data.traffic_data
    if not data:
        raise HTTPException(status_code=404, detail="No traffic data in scenario")
    return {"Traffic Data": data}


@app.get("/get_mr_data")
def get_mr_data(scenario: Scenario = Depends(resolve_scenario)):
    data = scenario.data.mr_data
    if not data:
        raise HTTPException(status_code=404, detail="No traffic data in scenario")
    return {"MR Data": data}


@app.get("/throughput-logs")
def get_throughput_logs(scenario: Scenario = Depends(resolve_scenario)):
    df = read_user_plane_df(scenario)
    return {
        "Logs": df[
            ["Timestamp", "5G KPI PCell Layer2 MAC DL Throughput [Mbps]"]
        ].to_csv(index=False, sep="|")
    }


@app.get("/cell-info")
def get_cell_info(
    pci: int = Query(..., description="Physical Cell ID"),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[df["PCI"] == int(pci)]
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(status_code=404, detail=f"No cell found for PCI {pci}")

    result["notes"] = scenario.data.notes
    return result


@app.get("/gnodeb-location")
def get_gnodeb_location(
    pci: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[df["PCI"] == int(pci), ["Longitude", "Latitude"]]
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(status_code=404, detail=f"No location found for PCI {pci}")
    return result


@app.get("/user-location")
def get_user_location(
    time: str = Query(..., description="Timestamp, e.g. '2024-08-25 19:30:57.500'"),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["Longitude", "Latitude"])
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No user location found for time {time}"
        )
    return result


@app.get("/judge_mainlobe")
def judge_mainlobe_or_not(
    time: str = Query(..., description="Timestamp, e.g. '2024-08-25 19:30:57.500'"),
    pci: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[df["PCI"] == int(pci), ["Longitude", "Latitude"]]
    bs_location = df_first_or_none(info)
    info2 = df.loc[df["PCI"] == int(pci), ["Mechanical Azimuth"]]
    bs_azimuth = df_first_or_none(info2)

    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["Longitude", "Latitude"])
    user_location = df_first_or_none(info)

    if not bs_location or not user_location:
        raise HTTPException(status_code=404, detail=f"No location found for PCI {pci}")

    horizontal_angle = calculate_angle_between_user_and_cell(
        user_location["Longitude"],
        user_location["Latitude"],
        float(bs_location["Longitude"]),
        float(bs_location["Latitude"]),
        float(bs_azimuth["Mechanical Azimuth"]),
    )

    df = read_config_df(scenario)
    info2 = df.loc[df["PCI"] == int(pci), ["Mechanical Downtilt"]]
    bs_tilt = df_first_or_none(info2)
    info3 = df.loc[df["PCI"] == int(pci), ["Height"]]
    bs_height = df_first_or_none(info3)

    dist_km = haversine_distance(
        user_location["Longitude"],
        user_location["Latitude"],
        float(bs_location["Longitude"]),
        float(bs_location["Latitude"]),
    )

    dist_m = dist_km * 1000

    height_diff = 0 - bs_height["Height"]

    if dist_m == 0:
        tilt_angle = math.copysign(90, height_diff)
    else:
        tilt_angle = math.degrees(math.atan2(height_diff, dist_m))

    final_tilt = tilt_angle - bs_tilt["Mechanical Downtilt"]

    return {
        "Outside_Mainlobe_Flag": (abs(horizontal_angle) > 50) or (abs(final_tilt) > 6)
    }


@app.get("/optimize_antenna_gain")
def optimize_antenna_gain(
    time: str = Query(..., description="Timestamp, e.g. '2024-08-25 19:30:57.500'"),
    pci: int = Query(...),
    adjust_horizontal_angle: float = Query(...),
    adjust_tilt_angle: float = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[df["PCI"] == int(pci), ["Longitude", "Latitude"]]
    bs_location = df_first_or_none(info)
    info2 = df.loc[df["PCI"] == int(pci), ["Mechanical Azimuth"]]
    bs_azimuth = df_first_or_none(info2)

    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["Longitude", "Latitude"])
    user_location = df_first_or_none(info)

    if not bs_location or not user_location:
        raise HTTPException(status_code=404, detail=f"No location found for PCI {pci}")

    horizontal_angle = calculate_angle_between_user_and_cell(
        user_location["Longitude"],
        user_location["Latitude"],
        float(bs_location["Longitude"]),
        float(bs_location["Latitude"]),
        float(bs_azimuth["Mechanical Azimuth"]),
    )

    df = read_config_df(scenario)
    info2 = df.loc[df["PCI"] == int(pci), ["Mechanical Downtilt"]]
    bs_tilt = df_first_or_none(info2)
    info3 = df.loc[df["PCI"] == int(pci), ["Height"]]
    bs_height = df_first_or_none(info3)

    dist_km = haversine_distance(
        user_location["Longitude"],
        user_location["Latitude"],
        float(bs_location["Longitude"]),
        float(bs_location["Latitude"]),
    )

    dist_m = dist_km * 1000

    height_diff = 0 - bs_height["Height"]

    if dist_m == 0:
        tilt_angle = math.copysign(90, height_diff)
    else:
        tilt_angle = math.degrees(math.atan2(height_diff, dist_m))

    final_tilt = tilt_angle - bs_tilt["Mechanical Downtilt"]

    phi = np.linspace(0, 360, 361)  # azimuth 0~360 deg
    theta = np.linspace(0, 180, 181)  # elevation 0~180 deg
    Phi, Theta = np.meshgrid(phi, theta)
    phi_rad = np.radians(Phi)
    theta_rad = np.radians(Theta)
    G_lin = gain_pattern(phi_rad, theta_rad)
    G_lin = G_lin / np.max(G_lin)
    G_dB = 10 * np.log10(G_lin + 1e-12)

    serving_horizontal_location = 180 - abs(round(horizontal_angle))
    serving_tilt_location = 90 - abs(round(final_tilt))
    original_serving_gain = G_dB[serving_tilt_location, serving_horizontal_location]
    after_serving_gain = G_dB[
        serving_tilt_location + int(adjust_tilt_angle),
        serving_horizontal_location + int(adjust_horizontal_angle),
    ]

    adjust_gain = after_serving_gain - original_serving_gain

    return {"adjust_gain": adjust_gain}


@app.get("/calculate_tilt_angle")
def calculate_tilt_angle(
    time: str = Query(..., description="Timestamp, e.g. '2024-08-25 19:30:57.500'"),
    pci: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[df["PCI"] == int(pci), ["Longitude", "Latitude"]]
    bs_location = df_first_or_none(info)
    info2 = df.loc[df["PCI"] == int(pci), ["Mechanical Downtilt"]]
    bs_tilt = df_first_or_none(info2)
    info3 = df.loc[df["PCI"] == int(pci), ["Height"]]
    bs_height = df_first_or_none(info3)

    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["Longitude", "Latitude"])
    user_location = df_first_or_none(info)

    if not bs_location or not user_location:
        raise HTTPException(status_code=404, detail=f"No location found for PCI {pci}")

    dist_km = haversine_distance(
        user_location["Longitude"],
        user_location["Latitude"],
        float(bs_location["Longitude"]),
        float(bs_location["Latitude"]),
    )

    dist_m = dist_km * 1000

    height_diff = 0 - bs_height["Height"]

    if dist_m == 0:
        tilt_angle = math.copysign(90, height_diff)
    else:
        tilt_angle = math.degrees(math.atan2(height_diff, dist_m))

    final_tilt = tilt_angle - bs_tilt["Mechanical Downtilt"]

    return {
        "The tilt angle between the user and the cell is ": "{:.2f}".format(final_tilt)
    }


@app.get("/calculate_horizontal_angle")
def calculate_horizontal_angle(
    time: str = Query(..., description="Timestamp, e.g. '2024-08-25 19:30:57.500'"),
    pci: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[df["PCI"] == int(pci), ["Longitude", "Latitude"]]
    bs_location = df_first_or_none(info)
    info2 = df.loc[df["PCI"] == int(pci), ["Mechanical Azimuth"]]
    bs_azimuth = df_first_or_none(info2)

    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["Longitude", "Latitude"])
    user_location = df_first_or_none(info)

    if not bs_location or not user_location:
        raise HTTPException(status_code=404, detail=f"No location found for PCI {pci}")

    angle = calculate_angle_between_user_and_cell(
        user_location["Longitude"],
        user_location["Latitude"],
        float(bs_location["Longitude"]),
        float(bs_location["Latitude"]),
        float(bs_azimuth["Mechanical Azimuth"]),
    )

    return {
        "The horizontal angle between the user and the cell is ": "{:.2f}".format(angle)
    }


@app.get("/calculate_pathloss")
def calculate_pathloss(
    time: str = Query(..., description="Timestamp, e.g. '2024-08-25 19:30:57.500'"),
    pci: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info2 = df.loc[df["PCI"] == int(pci), ["Transmission Power"]]
    bs_power = df_first_or_none(info2)

    df = read_user_plane_df(scenario)
    info = get_fields_at_time(
        df, time, fields=["5G KPI PCell RF Serving SS-RSRP [dBm]"]
    )
    user_power = df_first_or_none(info)

    if not bs_power or not user_power:
        raise HTTPException(
            status_code=404, detail=f"No information found for PCI {pci}"
        )

    return {
        "The pathloss between the user and the cell is ": "{:.1f}".format(
            bs_power["Transmission Power"]
            - user_power["5G KPI PCell RF Serving SS-RSRP [dBm]"]
        )
    }


@app.get("/calculate_overlap_ratio")
def calculate_overlap_ratio(
    pci_serving: int = Query(...),
    pci_neighbor: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_config_df(scenario)
    info = df.loc[
        df["PCI"] == int(pci_serving), ["Longitude", "Latitude", "Mechanical Azimuth"]
    ]
    serving_information = df_first_or_none(info)

    df = read_config_df(scenario)
    info = df.loc[
        df["PCI"] == int(pci_neighbor), ["Longitude", "Latitude", "Mechanical Azimuth"]
    ]
    neighbor_information = df_first_or_none(info)

    if not serving_information or not neighbor_information:
        raise HTTPException(
            status_code=404,
            detail=f"No information found for PCI {pci_serving} or {pci_neighbor}",
        )

    overlap_ratio = calculate_overlap_coverage(
        serving_information["Longitude"],
        serving_information["Latitude"],
        serving_information["Mechanical Azimuth"],
        neighbor_information["Longitude"],
        neighbor_information["Latitude"],
        neighbor_information["Mechanical Azimuth"],
    )

    return {
        f"The overlap coverage ratio of the cell {pci_serving} and the cell {pci_neighbor} is ": "{:.2f}".format(
            overlap_ratio
        )
    }


@app.get("/user-speed")
def get_user_speed(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["GPS Speed (km/h)"])
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(status_code=404, detail=f"No speed found for time {time}")

    try:
        return {"GPS Speed (km/h)": float(result["GPS Speed (km/h)"])}
    except:
        return {"GPS Speed (km/h)": "Unknown"}


@app.get("/serving-cell-pci")
def get_serving_cell_pci(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["5G KPI PCell RF Serving PCI"])
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No serving cell PCI found for time {time}"
        )
    return {"PCI": int(result["5G KPI PCell RF Serving PCI"])}


@app.get("/serving-cell-rsrp")
def get_serving_cell_rsrp(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    info = get_fields_at_time(
        df, time, fields=["5G KPI PCell RF Serving SS-RSRP [dBm]"]
    )
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to retrieve the serving cell RSRP at {time}",
        )
    return {"SS-RSRP (dBm)": float(result["5G KPI PCell RF Serving SS-RSRP [dBm]"])}


@app.get("/serving-cell-sinr")
def get_serving_cell_sinr(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    info = get_fields_at_time(df, time, fields=["5G KPI PCell RF Serving SS-SINR [dB]"])
    sinr_dict = df_first_or_none(info)
    if not sinr_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to retrieve the serving cell SINR at {time}",
        )
    return {"SS-SINR (dB)": float(sinr_dict["5G KPI PCell RF Serving SS-SINR [dB]"])}


@app.get("/rbs-allocated-to-user")
def get_rbs_allocated_to_user(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    info = get_fields_at_time(
        df, time, fields=["5G KPI PCell Layer1 DL RB Num (Including 0)"]
    )
    result = df_first_or_none(info)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to retrieve the number of RBs allocated at {time}",
        )
    return {"RBs": float(result["5G KPI PCell Layer1 DL RB Num (Including 0)"])}


@app.get("/signaling-plane-event-log")
def get_signaling_plane_event_log(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_signaling_plane_df(scenario)
    info = get_fields_before_time(
        df, time, fields=["Timestamp", "Event Name", "Event Content"]
    )
    result = df_all_or_none(info)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to retrieve the signaling plane data at {time}",
        )
    return result


@app.get("/neighboring-cells-pci")
def get_neighboring_cells_pci(
    time: str = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    fields = [
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 1 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 2 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 3 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 4 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 5 PCI",
    ]
    info = get_fields_at_time(df, time, fields=fields)
    pci_dict = df_first_or_none(info)
    if not pci_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to retrieve the neighboring cells at {time}",
        )

    return {"PCIs": [int(r) for r in pci_dict.values() if r != "-"]}


@app.get("/neighboring-cell-rsrp")
def get_neighboring_cell_rsrp(
    time: str = Query(...),
    pci: int = Query(...),
    scenario: Scenario = Depends(resolve_scenario),
):
    df = read_user_plane_df(scenario)
    fields = [
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 1 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 2 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 3 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 4 PCI",
        "Measurement PCell Neighbor Cell Top Set(Cell Level) Top 5 PCI",
    ]

    info = get_fields_at_time(df, time, fields=fields)
    pci_dict = df_first_or_none(info)
    if not pci_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to retrieve the neighboring cells at {time}",
        )

    for key, cell_pci in pci_dict.items():
        if str(cell_pci) == str(pci):
            label = key.replace("PCI", "Filtered Tx BRSRP [dBm]")
            cell_rsrp = df_first_or_none(get_fields_at_time(df, time, fields=[label]))
            if not cell_rsrp:
                raise HTTPException(
                    status_code=404, detail=f"RSRP not found for PCI {pci} at {time}"
                )
            return {"Filtered Tx BRSRP [dBm]": float(cell_rsrp[label])}

    raise HTTPException(
        status_code=404,
        detail=f"Cell with PCI {pci} was not found in the neighboring cells at {time}",
    )


@app.get("/all-cells-pci")
def get_all_cells_pci(scenario: Scenario = Depends(resolve_scenario)):
    df = read_config_df(scenario)
    return {"PCIs": [int(x) for x in df["PCI"].dropna().astype(int).tolist()]}


@app.get("/beam-scenario-info")
def get_beam_scenario_info(
    name: str = Query(
        ..., description="Beam scenario name, e.g., 'DEFAULT' or 'SCENARIO_9'"
    ),
):
    return {"name": name, "vertical_beamwidth_deg": beam_scenario_to_v_bw(name)}


@app.get("/tools")
def get_available_tools():
    """
    Tool descriptors for tool-using agents.
    Note: scenario selection is done via the X-Scenario-Id header, not a parameter.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_throughput_logs",
                "description": "Get the timestamped user throughput logs during the drive-test. With the throughtput logs, we can identify the poor-quality point, and use the corresponding timestamp to gather more information for analysis by using tools.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_cell_info",
                "description": "Get full cell configuration given its PCI. The configuration contains cell information including the location, Azimuth, Mech Tilt, Elec Tilt, Ant Height, Duplex Mode, PCI, Band, DL ARFCN, Bandwidth, TX/RX Mode, Transmission Power, InterFreqHoEventType, CovInterFreqA2RsrpThld(dBm), InterFreqA2Hyst(0.5dB), CovInterFreqA5RsrpThld1(dBm), CovInterFreqA5RsrpThld2(dBm), IntraFreqHoA3Offset(0.5dB), IntraFreqHoA3Hyst(0.5dB), IntraFreqHoA3TimeToTrig, Neighbor(gNodeB_ID_ARFCN_PCI), PdcchOccupiedSymbolNum",
                "parameters": {
                    "type": "object",
                    "properties": {"pci": {"type": "integer"}},
                    "required": ["pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_gnodeb_location",
                "description": "Get gNodeB (cell) location (longitude, latitude) by PCI.",
                "parameters": {
                    "type": "object",
                    "properties": {"pci": {"type": "integer"}},
                    "required": ["pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_location",
                "description": "Get UE location (longitude, latitude) at a given timestamp, e.g. '2024-08-25 19:30:57.500'.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_serving_cell_pci",
                "description": "Get serving cell PCI at a given timestamp, e.g. '2024-08-25 19:30:57.500'.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_serving_cell_rsrp",
                "description": "Get serving cell SS-RSRP at a given timestamp, e.g. '2024-08-25 19:30:57.500'.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_serving_cell_sinr",
                "description": "Get serving cell SS-SINR at a given timestamp, e.g. '2024-08-25 19:30:57.500'.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_rbs_allocated_to_user",
                "description": "Get the number of RBs allocated to user by the gNobeB at a given timestamp.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_signaling_plane_event_log",
                "description": "Get the signaling plane event log until a given timestamp, e.g. '2024-08-25 19:30:57.500'.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_neighboring_cells_pci",
                "description": "Get the neighboring cells PCI of the serving cell at a given timestamp, e.g. '2024-08-25 19:30:57.500'.",
                "parameters": {
                    "type": "object",
                    "properties": {"time": {"type": "string"}},
                    "required": ["time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_neighboring_cell_rsrp",
                "description": "Get the beam-level RSRP of a neighboring cell at a given timestamp.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "pci": {"type": "integer"},
                    },
                    "required": ["time", "pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_all_cells_pci",
                "description": "List the PCIs of all cells in the network.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_kpi_data",
                "description": "Get the  data with cell-level KPI, including the information of PRB utilization, PRB Interference, Throughput, CCE utilization and CCE Allocation Success Rate",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_mr_data",
                "description": "Get the normal Measurement Report (MR) data surrounding poor-quality users",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "judge_mainlobe_or_not",
                "description": "Judge the user is in the cell's mainlobe or not. True means outside the mainlobe, False means in the mainlobe.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "pci": {"type": "integer"},
                    },
                    "required": ["time", "pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_horizontal_angle",
                "description": "Calculate the horizontal angle between the user and the cell.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "pci": {"type": "integer"},
                    },
                    "required": ["time", "pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_tilt_angle",
                "description": "Calculate the tilt angle between the user and the cell.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "pci": {"type": "integer"},
                    },
                    "required": ["time", "pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_pathloss",
                "description": "Calculate the pathloss between the user and the cell.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "pci": {"type": "integer"},
                    },
                    "required": ["time", "pci"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_overlap_ratio",
                "description": "Calculate the overlap coverage ratio of the serving cell and the neighbor cell.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pci_serving": {"type": "integer"},
                        "pci_neighbor": {"type": "integer"},
                    },
                    "required": ["pci_serving", "pci_neighbor"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "optimize_antenna_gain",
                "description": "Simulate the RSRP gain if adjust the azimuth angle and tilt angel of the antenna.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string"},
                        "pci": {"type": "integer"},
                        "adjust_horizontal_angle": {"type": "number"},
                        "adjust_tilt_angle": {"type": "number"},
                    },
                    "required": [
                        "time",
                        "pci",
                        "adjust_horizontal_angle",
                        "adjust_tilt_angle",
                    ],
                },
            },
        },
    ]


# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------

# Run with: uvicorn server:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=True)
