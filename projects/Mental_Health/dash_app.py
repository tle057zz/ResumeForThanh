from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
from dash import dash_table

# ---------- Constants and data paths ----------
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_CANDIDATES = [
    BASE_DIR / "Teen_Mental_Health_Dataset.csv",
    BASE_DIR.parent / "Final_Project" / "Teen_Mental_Health_Dataset.csv",
]
CHART_DECIMAL_FORMAT = ".5f"

AGE_ORDER = ["Early Teen", "Middle Teen", "Late Teen"]
PLATFORM_ORDER = ["Instagram", "TikTok", "Both"]
GENDER_ORDER = ["Male", "Female"]
CATEGORY_ORDER = ["Low", "Medium", "High"]


# ---------- Data loading and utilities ----------
REQUIRED_DATA_FILES = [
    "Fact_TeenMentalHealth.csv",
    "Dim_Age.csv",
    "Dim_Gender.csv",
    "Dim_Platform.csv",
    "Dim_SocialInteraction.csv",
]


def resolve_data_dir() -> Path:
    """Find a directory that contains all required processed CSV files."""
    candidates = [
        BASE_DIR / "processed",
        BASE_DIR.parent / "Final_Project" / "processed",
        Path.cwd() / "projects" / "Mental_Health" / "processed",
        Path.cwd() / "projects" / "Final_Project" / "processed",
    ]
    for cand in candidates:
        if all((cand / f).exists() for f in REQUIRED_DATA_FILES):
            return cand
    # If none matched, return the first existing candidate (partial) or BASE_DIR to trigger a helpful error later
    for cand in candidates:
        if cand.exists():
            return cand
    return BASE_DIR


def load_data(data_dir: Path) -> pd.DataFrame:
    fact = pd.read_csv(data_dir / "Fact_TeenMentalHealth.csv")
    dim_age = pd.read_csv(data_dir / "Dim_Age.csv")
    dim_gender = pd.read_csv(data_dir / "Dim_Gender.csv")
    dim_platform = pd.read_csv(data_dir / "Dim_Platform.csv")
    dim_social = pd.read_csv(data_dir / "Dim_SocialInteraction.csv")

    data = (
        fact.merge(dim_age, on="AgeKey", how="left")
        .merge(dim_gender, on="GenderKey", how="left")
        .merge(dim_platform, on="PlatformKey", how="left")
        .merge(dim_social, on="SocialInteractionKey", how="left")
    )

    data["Stress Category"] = pd.cut(
        data["StressLevel"], bins=[-float("inf"), 3, 6, float("inf")], labels=CATEGORY_ORDER
    ).astype(str)
    data["Anxiety Category"] = pd.cut(
        data["AnxietyLevel"], bins=[-float("inf"), 3, 6, float("inf")], labels=CATEGORY_ORDER
    ).astype(str)
    data["Addiction Category"] = pd.cut(
        data["AddictionLevel"], bins=[-float("inf"), 3, 6, float("inf")], labels=CATEGORY_ORDER
    ).astype(str)
    data["Social Media Usage Category"] = pd.cut(
        data["DailySocialMediaHours"], bins=[-float("inf"), 2.999, 5.999, float("inf")], labels=CATEGORY_ORDER
    ).astype(str)
    data["Depression Status"] = data["DepressionLabel"].map({0: "Not Depressed", 1: "Depressed"})
    return data


def ordered(series: pd.Series, order: List[str]) -> List[str]:
    present = [v for v in order if v in set(series.dropna().unique())]
    rest = sorted(set(series.dropna().unique()) - set(present))
    return present + rest


def group_summary(
    data: pd.DataFrame, group_cols: List[str], sort_orders: Dict[str, List[str]] | None = None
) -> pd.DataFrame:
    summary = (
        data.groupby(group_cols, observed=True)
        .agg(
            TotalRespondents=("RespondentID", "count"),
            DepressedRespondents=("DepressionLabel", "sum"),
            DepressionRate=("DepressionLabel", "mean"),
            AverageSocialMediaHours=("DailySocialMediaHours", "mean"),
            AverageSleepHours=("SleepHours", "mean"),
            AverageStressLevel=("StressLevel", "mean"),
            AverageAnxietyLevel=("AnxietyLevel", "mean"),
            AverageAddictionLevel=("AddictionLevel", "mean"),
        )
        .reset_index()
    )
    if sort_orders:
        for column, order in sort_orders.items():
            if column in summary:
                summary[column] = pd.Categorical(summary[column], categories=order, ordered=True)
        summary = summary.sort_values(list(sort_orders))
    return summary


def metrics(data: pd.DataFrame) -> Dict[str, float]:
    total = len(data)
    depressed = int(data["DepressionLabel"].sum()) if total else 0
    return {
        "Total Respondents": total,
        "Depressed Respondents": depressed,
        "Depression Rate": data["DepressionLabel"].mean() if total else 0,
        "Average Social Media Hours": data["DailySocialMediaHours"].mean() if total else 0,
        "Average Sleep Hours": data["SleepHours"].mean() if total else 0,
        "Average Stress Level": data["StressLevel"].mean() if total else 0,
        "Average Anxiety Level": data["AnxietyLevel"].mean() if total else 0,
        "Average Addiction Level": data["AddictionLevel"].mean() if total else 0,
    }

def top_group(summary: pd.DataFrame, metric: str, label_cols: List[str]) -> Tuple[str, float]:
    if summary.empty or metric not in summary:
        return "N/A", 0.0
    valid = summary.dropna(subset=[metric])
    if valid.empty:
        return "N/A", 0.0
    row = valid.sort_values(metric, ascending=False).iloc[0]
    label = " / ".join(str(row[c]) for c in label_cols)
    return label, float(row[metric])

def category_metric(summary: pd.DataFrame, column: str, value: str, metric: str) -> float:
    if summary.empty or column not in summary or metric not in summary:
        return 0.0
    matched = summary[summary[column].astype(str) == value]
    if matched.empty:
        return 0.0
    return float(matched.iloc[0][metric])

def category_count(data: pd.DataFrame, column: str, value: str) -> int:
    if column not in data:
        return 0
    return int((data[column].astype(str) == value).sum())


def kpi(value: Any, label: str) -> html.Div:
    return html.Div(
        className="kpi",
        children=[html.Div(className="kpi-value", children=f"{value}"), html.Div(className="kpi-label", children=label)],
        style={
            "padding": "12px 16px",
            "border": "1px solid rgba(0,0,0,.08)",
            "borderRadius": "10px",
            "background": "rgba(255,255,255,.7)",
        },
    )


def fmt_percent(value: float) -> str:
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1%}"


def fmt_decimal(value: float) -> str:
    if pd.isna(value):
        return "0.00"
    return f"{value:.2f}"


def bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str | None,
    title: str,
    barmode: str = "group",
    category_orders: Dict[str, List[str]] | None = None,
    custom_fields: List[str] | None = None,
):
    """Robust bar chart helper that tolerates empty/missing columns."""
    if data is None or len(data) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(title=title, xaxis_title=x, yaxis_title=y)
        return empty_fig

    df = data.copy()
    # Ensure required columns exist
    required_cols = [x, y] + ([color] if color else [])
    for col in required_cols:
        if col and col not in df.columns:
            df[col] = pd.Series(dtype="object")

    # Sanitize custom_data fields to those present
    if custom_fields:
        custom_data_fields = [c for c in custom_fields if c in df.columns]
        if not custom_data_fields:
            custom_data_fields = [x] + ([color] if color and color in df.columns else [])
    else:
        custom_data_fields = [x] + ([color] if color and color in df.columns else [])

    try:
        fig = px.bar(
            df,
            x=x,
            y=y,
            color=color if color in df.columns else None,
            title=title,
            barmode=barmode,
            text_auto=CHART_DECIMAL_FORMAT,
            custom_data=custom_data_fields,
            category_orders=category_orders or {},
        )
    except Exception:
        # Fallback to a simple figure if Plotly rejects inputs
        fig = go.Figure()
        if x in df.columns and y in df.columns:
            fig.add_bar(x=df[x], y=df[y], name=title)
        fig.update_layout(title=title, xaxis_title=x, yaxis_title=y)
    fig.update_layout(legend_title_text=color if color in df.columns else None, yaxis_title=y, xaxis_title=x)
    fig.update_traces(texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}")
    return fig


def extract_selected_values(selected_data: Dict[str, Any] | None, custom_field_index: int) -> Set[str]:
    values: Set[str] = set()
    if not selected_data:
        return values
    for point in selected_data.get("points", []):
        custom = point.get("customdata")
        if custom is None:
            continue
        if isinstance(custom, (list, tuple)) and len(custom) > custom_field_index:
            values.add(str(custom[custom_field_index]))
        elif custom_field_index == 0:
            values.add(str(custom))
    return values


# ---------- Dash app registration ----------
def register_dash(server) -> None:
    app = Dash(
        __name__,
        server=server,
        url_base_pathname="/mental-health/",
        suppress_callback_exceptions=True,
        title="Teen Mental Health Analytics",
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    )

    data_dir = resolve_data_dir()
    try:
        df = load_data(data_dir)
    except Exception as e:
        # Show a helpful inline error page instead of crashing Flask
        err = html.Div(
            style={"padding": "16px"},
            children=[
                html.H3("Mental Health dashboard data not found"),
                html.P(
                    f"Expected processed CSVs in: {data_dir}. "
                    f"Required files: {', '.join(REQUIRED_DATA_FILES)}."
                ),
                html.Pre(str(e)),
            ],
        )
        app.layout = err
        return

    # Shared filters
    controls = html.Div(
        style={"padding": "12px", "background": "rgba(0,0,0,0.02)", "borderRadius": "10px"},
        children=[
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
                    "gap": "12px",
                },
                children=[
                    html.Div(
                        children=[
                            html.Label("Age Group"),
                            dcc.Dropdown(
                                id="f_age_group",
                                options=[{"label": v, "value": v} for v in ordered(df["AgeGroup"], AGE_ORDER)],
                                value=ordered(df["AgeGroup"], AGE_ORDER),
                                multi=True,
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Gender"),
                            dcc.Dropdown(
                                id="f_gender",
                                options=[{"label": v, "value": v} for v in ordered(df["Gender"], GENDER_ORDER)],
                                value=ordered(df["Gender"], GENDER_ORDER),
                                multi=True,
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Platform Usage"),
                            dcc.Dropdown(
                                id="f_platform",
                                options=[{"label": v, "value": v} for v in ordered(df["PlatformUsage"], PLATFORM_ORDER)],
                                value=ordered(df["PlatformUsage"], PLATFORM_ORDER),
                                multi=True,
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Social Interaction Level"),
                            dcc.Dropdown(
                                id="f_interaction",
                                options=[{"label": v, "value": v} for v in ordered(df["SocialInteractionLevel"], CATEGORY_ORDER)],
                                value=ordered(df["SocialInteractionLevel"], CATEGORY_ORDER),
                                multi=True,
                            ),
                        ]
                    ),
                ],
            ),
        ],
    )

    tabs = dcc.Tabs(
        id="tabs",
        value="tab-overview",
        children=[
            dcc.Tab(label="Overview", value="tab-overview", children=[
                html.Div(
                    id="ov-kpis",
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                    children=[
                        dcc.Graph(id="ov-by-gender", config={"responsive": True}, style={"minHeight": "320px"}),
                        dcc.Graph(id="ov-total-by-age", config={"responsive": True}, style={"minHeight": "320px"}),
                    ],
                ),
                dcc.Graph(id="ov-by-age-gender", config={"responsive": True}, style={"marginTop": "12px", "minHeight": "360px"}),
                html.Div(id="ov-insights", style={"marginTop": "8px"}),
            ]),
            dcc.Tab(label="Social Media Impact", value="tab-social", children=[
                html.Div(
                    id="sm-kpis",
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                    children=[
                        dcc.Graph(id="sm-by-usage-gender", config={"responsive": True}, style={"minHeight": "320px"}),
                        dcc.Graph(id="sm-by-usage-platform", config={"responsive": True}, style={"minHeight": "320px"}),
                    ],
                ),
                dcc.Graph(id="sm-combo-platform", config={"responsive": True}, style={"marginTop": "12px", "minHeight": "360px"}),
                html.H4("Usage Category by Platform Detail"),
                dash_table.DataTable(
                    id="sm-usage-platform-table",
                    columns=[
                        {"name": "Social Media Usage Category", "id": "Social Media Usage Category"},
                        {"name": "PlatformUsage", "id": "PlatformUsage"},
                        {"name": "TotalRespondents", "id": "TotalRespondents"},
                        {"name": "DepressionRate", "id": "DepressionRate", "type": "numeric", "format": {"specifier": ".3f"}},
                        {"name": "AverageSocialMediaHours", "id": "AverageSocialMediaHours", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "AverageStressLevel", "id": "AverageStressLevel", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "AverageAnxietyLevel", "id": "AverageAnxietyLevel", "type": "numeric", "format": {"specifier": ".2f"}},
                    ],
                    data=[],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left"},
                    row_selectable="multi",
                    selected_rows=[],
                ),
                html.Div(id="sm-insights", style={"marginTop": "8px"}),
            ]),
            dcc.Tab(label="Stress and Anxiety", value="tab-stress", children=[
                html.H4("Stress and Anxiety Matrix"),
                dash_table.DataTable(
                    id="sa-matrix",
                    columns=[
                        {"name": "Stress Category", "id": "Stress Category"},
                        {"name": "Anxiety Category", "id": "Anxiety Category"},
                        {"name": "TotalRespondents", "id": "TotalRespondents"},
                        {"name": "DepressionRate", "id": "DepressionRate", "type": "numeric", "format": {"specifier": ".3f"}},
                        {"name": "AverageSleepHours", "id": "AverageSleepHours", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "AverageSocialMediaHours", "id": "AverageSocialMediaHours", "type": "numeric", "format": {"specifier": ".2f"}},
                    ],
                    data=[],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left"},
                    row_selectable="multi",
                    selected_rows=[],
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                    children=[
                        dcc.Graph(id="sa-by-stress-gender", config={"responsive": True}, style={"minHeight": "320px"}),
                        dcc.Graph(id="sa-by-anxiety-gender", config={"responsive": True}, style={"minHeight": "320px"}),
                        dcc.Graph(id="sa-indicators", config={"responsive": True}, style={"minHeight": "320px"}),
                    ],
                ),
                dcc.Graph(id="sa-distribution", config={"responsive": True}, style={"marginTop": "12px", "minHeight": "360px"}),
                html.Div(id="sa-insights", style={"marginTop": "8px"}),
            ]),
            dcc.Tab(label="Demographics and Lifestyle", value="tab-demographics", children=[
                html.Div(
                    id="dem-kpis",
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                        "gap": "12px",
                        "marginTop": "12px",
                    },
                    children=[
                        dcc.Graph(id="dem-by-age-gender", config={"responsive": True}, style={"minHeight": "320px"}),
                        dcc.Graph(id="dem-by-interaction-platform", config={"responsive": True}, style={"minHeight": "320px"}),
                        dcc.Graph(id="dem-avg-indicators-by-gender", config={"responsive": True}, style={"minHeight": "320px"}),
                    ],
                ),
                html.H4("Age Group and Gender Matrix"),
                dash_table.DataTable(
                    id="dem-age-gender-table",
                    columns=[
                        {"name": "AgeGroup", "id": "AgeGroup"},
                        {"name": "Gender", "id": "Gender"},
                        {"name": "TotalRespondents", "id": "TotalRespondents"},
                        {"name": "DepressionRate", "id": "DepressionRate", "type": "numeric", "format": {"specifier": ".3f"}},
                        {"name": "AverageSocialMediaHours", "id": "AverageSocialMediaHours", "type": "numeric", "format": {"specifier": ".2f"}},
                        {"name": "AverageSleepHours", "id": "AverageSleepHours", "type": "numeric", "format": {"specifier": ".2f"}},
                    ],
                    data=[],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left"},
                    row_selectable="multi",
                    selected_rows=[],
                ),
                html.Div(id="dem-insights", style={"marginTop": "8px"}),
            ]),
        ],
    )

    app.layout = html.Div(
        style={"padding": "16px"},
        children=[
            html.H2("Teen Mental Health Analytics"),
            # Project context (from original Streamlit)
            html.Div(
                style={
                    "padding": "12px",
                    "marginBottom": "12px",
                    "background": "rgba(0,0,0,0.02)",
                    "border": "1px solid rgba(0,0,0,0.06)",
                    "borderRadius": "10px",
                },
                children=[
                    html.H4("Project Objective, Business Problem, and Data Transformations"),
                    dcc.Markdown(
                        (
                            "### Project Objective & Business Problem\n"
                            "This project analyzes teenage mental health patterns using social media usage, sleep, stress, anxiety, "
                            "addiction level, academic performance, physical activity, gender, age group, platform usage, and social interaction level. "
                            "The main business problem is to identify which behavioral and lifestyle factors are associated with higher depression risk among teenagers. "
                            "The dashboard helps answer whether high social media usage, high stress, high anxiety, platform usage, age group, gender, or social "
                            "interaction level are linked to different mental health outcomes.\n\n"
                            "### Data Sources & Transformations\n"
                            "The original dataset comes from `Teen_Mental_Health_Dataset.csv`. The data was preprocessed using "
                            "`teen_mental_health_preprocessing.ipynb`, and the cleaned Power BI/Python‑ready tables were exported into `processed/`.\n\n"
                            "- Loaded and validated the raw CSV with 1,200 rows and 13 columns.\n"
                            "- Checked that all expected fields were present before processing.\n"
                            "- Standardized text categories such as Male/Female, Instagram/TikTok/Both, and Low/Medium/High social interaction levels.\n"
                            "- Converted numeric fields such as social media hours, sleep hours, stress level, anxiety level, addiction level, and depression label.\n"
                            "- Created age groups: Early Teen, Middle Teen, and Late Teen.\n"
                            "- Built a star schema with one fact table and four dimension tables.\n"
                            "- Created surrogate keys for age, gender, platform, and social interaction.\n"
                            "- Validated unique dimension keys, matching foreign keys, and unique respondent IDs.\n"
                            "- Exported five cleaned CSV tables into `processed/`."
                        ),
                        style={"whiteSpace": "pre-wrap"},
                    ),
                    html.Div(
                        children=[
                            html.A(
                                "Download Original CSV Dataset",
                                href="/mental-health/download",
                                target="_blank",
                                rel="noopener",
                                className="btn btn-primary",
                                style={
                                    "display": "inline-block",
                                    "padding": "8px 12px",
                                    "borderRadius": "8px",
                                    "border": "1px solid rgba(0,0,0,0.1)",
                                    "background": "#0d6efd",
                                    "color": "white",
                                    "textDecoration": "none",
                                },
                            ),
                            html.Span(
                                "" if any(p.exists() for p in RAW_DATA_CANDIDATES) else "  (Original CSV not found in project directories.)",
                                style={"marginLeft": "8px", "color": "#6b7280"},
                            ),
                        ]
                    ),
                ],
            ),
            controls,
            tabs,
        ],
    )

    # ---------- Helpers for filtered data ----------
    def apply_filters(
        data: pd.DataFrame,
        age_group: List[str],
        gender: List[str],
        platform: List[str],
        interaction: List[str],
    ) -> pd.DataFrame:
        return data[
            data["AgeGroup"].isin(age_group)
            & data["Gender"].isin(gender)
            & data["PlatformUsage"].isin(platform)
            & data["SocialInteractionLevel"].isin(interaction)
        ].copy()

    # ---------- Overview callbacks ----------
    @app.callback(
        Output("ov-kpis", "children"),
        Output("ov-by-gender", "figure"),
        Output("ov-total-by-age", "figure"),
        Output("ov-by-age-gender", "figure"),
        Output("ov-insights", "children"),
        Input("tabs", "value"),
        Input("f_age_group", "value"),
        Input("f_gender", "value"),
        Input("f_platform", "value"),
        Input("f_interaction", "value"),
        Input("ov-by-gender", "selectedData"),
        Input("ov-total-by-age", "selectedData"),
        Input("ov-by-age-gender", "selectedData"),
    )
    def ov_update(_tab_value, age_group, gender, platform, interaction, sel_gender, sel_age, sel_age_gender):
        local = apply_filters(df, age_group, gender, platform, interaction)

        # Cross-filter: selections from charts
        sel_genders = extract_selected_values(sel_gender, 0)
        sel_ages = extract_selected_values(sel_age, 0)
        sel_ages2 = extract_selected_values(sel_age_gender, 0)
        sel_genders2 = extract_selected_values(sel_age_gender, 1)
        if sel_genders:
            local = local[local["Gender"].astype(str).isin(sel_genders)]
        if sel_ages or sel_ages2:
            chosen_ages = sel_ages or sel_ages2
            local = local[local["AgeGroup"].astype(str).isin(chosen_ages)]
        if sel_genders2:
            local = local[local["Gender"].astype(str).isin(sel_genders2)]

        m = metrics(local)
        kpis = [
            kpi(f"{m['Total Respondents']:,}", "Total Respondents"),
            kpi(f"{m['Depressed Respondents']:,}", "Depressed Respondents"),
            kpi(fmt_decimal(m["Average Stress Level"]), "Average Stress"),
            kpi(fmt_decimal(m["Average Anxiety Level"]), "Average Anxiety"),
            kpi(fmt_decimal(m["Average Addiction Level"]), "Average Addiction"),
        ]

        by_gender = group_summary(local, ["Gender"], {"Gender": GENDER_ORDER})
        by_age = group_summary(local, ["AgeGroup"], {"AgeGroup": AGE_ORDER})
        by_age_gender = group_summary(local, ["AgeGroup", "Gender"], {"AgeGroup": AGE_ORDER})

        fig_gender = bar(
            by_gender, "Gender", "DepressionRate", None, "Depression Rate by Gender",
            category_orders={"Gender": GENDER_ORDER}, custom_fields=["Gender"]
        )
        fig_age = bar(
            by_age, "AgeGroup", "TotalRespondents", None, "Total Respondents by Age Group",
            category_orders={"AgeGroup": AGE_ORDER}, custom_fields=["AgeGroup"]
        )
        fig_age_gender = bar(
            by_age_gender, "AgeGroup", "DepressionRate", "Gender",
            "Depression Rate by Age Group and Gender",
            category_orders={"AgeGroup": AGE_ORDER, "Gender": GENDER_ORDER},
            custom_fields=["AgeGroup", "Gender"]
        )
        fig_gender.update_layout(yaxis_tickformat=".1%")
        fig_age_gender.update_layout(yaxis_tickformat=".1%")
        # Insights (match Streamlit)
        by_gender_rates = group_summary(local, ["Gender"], {"Gender": GENDER_ORDER})
        female_rate = category_metric(by_gender_rates, "Gender", "Female", "DepressionRate")
        male_rate = category_metric(by_gender_rates, "Gender", "Male", "DepressionRate")
        largest_age_group, largest_age_count = top_group(by_age, "TotalRespondents", ["AgeGroup"])
        highest_age_group, highest_age_rate = top_group(by_age, "DepressionRate", ["AgeGroup"])
        highest_gender, highest_gender_rate = top_group(by_gender, "DepressionRate", ["Gender"])
        ov_text = (
            f"The selected data contains {m['Total Respondents']:,} respondents and "
            f"{m['Depressed Respondents']:,} depressed respondents (overall {fmt_percent(m['Depression Rate'])}).\n\n"
            f"The average mental‑health indicators are Stress {fmt_decimal(m['Average Stress Level'])}, "
            f"Anxiety {fmt_decimal(m['Average Anxiety Level'])}, and Addiction {fmt_decimal(m['Average Addiction Level'])}.\n\n"
            f"The largest age group is {largest_age_group} with {largest_age_count:,.0f} respondents. "
            f"The highest depression rate by age group is {highest_age_group} at {fmt_percent(highest_age_rate)}. "
            f"By gender, the highest rate is {highest_gender} at {fmt_percent(highest_gender_rate)} "
            f"(Female {fmt_percent(female_rate)}, Male {fmt_percent(male_rate)})."
        )
        ov_insights = dcc.Markdown(ov_text, style={"whiteSpace": "pre-wrap"})
        return kpis, fig_gender, fig_age, fig_age_gender, ov_insights

    # ---------- Social Media Impact callbacks ----------
    @app.callback(
        Output("sm-kpis", "children"),
        Output("sm-by-usage-gender", "figure"),
        Output("sm-by-usage-platform", "figure"),
        Output("sm-combo-platform", "figure"),
        Output("sm-usage-platform-table", "data"),
        Output("sm-usage-platform-table", "selected_rows"),
        Output("sm-insights", "children"),
        Input("tabs", "value"),
        Input("f_age_group", "value"),
        Input("f_gender", "value"),
        Input("f_platform", "value"),
        Input("f_interaction", "value"),
        Input("sm-by-usage-gender", "selectedData"),
        Input("sm-by-usage-platform", "selectedData"),
        Input("sm-usage-platform-table", "selected_rows"),
        State("sm-usage-platform-table", "data"),
    )
    def sm_update(_tab_value, age_group, gender, platform, interaction, sel_usage_gender, sel_usage_platform, selected_rows, table_data):
        base_local = apply_filters(df, age_group, gender, platform, interaction)

        # Compute table data from base (not affected by table selection) to avoid sticky indices
        by_usage_platform_all = group_summary(
            base_local, ["Social Media Usage Category", "PlatformUsage"],
            {"Social Media Usage Category": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER}
        )

        # Cross-filter using chart/table selections
        sel_usage = extract_selected_values(sel_usage_gender, 0) | extract_selected_values(sel_usage_platform, 0)
        sel_gender = extract_selected_values(sel_usage_gender, 1)
        sel_platform = extract_selected_values(sel_usage_platform, 1)
        local = base_local.copy()
        if sel_usage:
            local = local[local["Social Media Usage Category"].astype(str).isin(sel_usage)]
        if sel_gender:
            local = local[local["Gender"].astype(str).isin(sel_gender)]
        if sel_platform:
            local = local[local["PlatformUsage"].astype(str).isin(sel_platform)]
        # Table row selections (use current table_data snapshot)
        if table_data and selected_rows:
            selected_keys = {
                (row["Social Media Usage Category"], row["PlatformUsage"])
                for i, row in enumerate(table_data) if i in selected_rows
            }
            if selected_keys:
                local = local[
                    local.apply(
                        lambda r: (str(r["Social Media Usage Category"]), str(r["PlatformUsage"])) in selected_keys,
                        axis=1,
                    )
                ]

        m = metrics(local)
        kpis = [
            kpi(f"{int((local['DailySocialMediaHours'] >= 6).sum()):,}", "High SM Users"),
            kpi(fmt_percent((local["DailySocialMediaHours"] >= 6).mean() if len(local) else 0), "High SM User Rate"),
            kpi(fmt_percent((local["StressLevel"] >= 7).mean() if len(local) else 0), "High Stress Rate"),
        ]

        # Recompute summaries for charts only
        by_usage_gender = group_summary(
            local, ["Social Media Usage Category", "Gender"], {"Social Media Usage Category": CATEGORY_ORDER}
        )
        by_usage_platform_charts = group_summary(
            local, ["Social Media Usage Category", "PlatformUsage"],
            {"Social Media Usage Category": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER}
        )
        by_platform = group_summary(local, ["PlatformUsage"], {"PlatformUsage": PLATFORM_ORDER})

        fig_usage_gender = bar(
            by_usage_gender,
            "Social Media Usage Category",
            "TotalRespondents",
            "Gender",
            "Total Respondents by Social Media Usage and Gender",
            category_orders={"Social Media Usage Category": CATEGORY_ORDER, "Gender": GENDER_ORDER},
            custom_fields=["Social Media Usage Category", "Gender"],
        )
        fig_usage_platform = bar(
            by_usage_platform_charts,
            "Social Media Usage Category",
            "DepressionRate",
            "PlatformUsage",
            "Depression Rate by Usage Category and Platform",
            category_orders={"Social Media Usage Category": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER},
            custom_fields=["Social Media Usage Category", "PlatformUsage"],
        )
        fig_usage_platform.update_layout(yaxis_tickformat=".1%")

        # Combo chart: bars for Avg Hours, line for Depression Rate by Platform
        combo = go.Figure()
        combo.add_bar(
            x=by_platform["PlatformUsage"],
            y=by_platform["AverageSocialMediaHours"],
            name="Average Social Media Hours",
            text=[f"{v:{CHART_DECIMAL_FORMAT}}" for v in by_platform["AverageSocialMediaHours"]],
            textposition="auto",
        )
        combo.add_scatter(
            x=by_platform["PlatformUsage"],
            y=by_platform["DepressionRate"],
            name="Depression Rate",
            mode="lines+markers",
            yaxis="y2",
        )
        combo.update_layout(
            title="Average Social Media Hours and Depression Rate by Platform",
            yaxis_title="Average Social Media Hours",
            yaxis2=dict(title="Depression Rate", overlaying="y", side="right", tickformat=".1%"),
            xaxis_title="PlatformUsage",
        )

        # Table data comes from base (stable indices)
        table = by_usage_platform_all[
            [
                "Social Media Usage Category",
                "PlatformUsage",
                "TotalRespondents",
                "DepressionRate",
                "AverageSocialMediaHours",
                "AverageStressLevel",
                "AverageAnxietyLevel",
            ]
        ].to_dict("records")

        # Rebuild selected_rows to match current table by key (prevents stuck selections)
        new_selected_rows = []
        if table_data and selected_rows:
            selected_keys = {(row["Social Media Usage Category"], row["PlatformUsage"]) for i, row in enumerate(table_data) if i in selected_rows}
            for i, row in enumerate(table):
                if (row["Social Media Usage Category"], row["PlatformUsage"]) in selected_keys:
                    new_selected_rows.append(i)

        # Insights (match Streamlit)
        by_usage = group_summary(local, ["Social Media Usage Category"], {"Social Media Usage Category": CATEGORY_ORDER})
        high_usage_count = category_count(local, "Social Media Usage Category", "High")
        medium_usage_count = category_count(local, "Social Media Usage Category", "Medium")
        low_usage_count = category_count(local, "Social Media Usage Category", "Low")
        high_usage_rate = category_metric(by_usage, "Social Media Usage Category", "High", "DepressionRate")
        medium_usage_rate = category_metric(by_usage, "Social Media Usage Category", "Medium", "DepressionRate")
        low_usage_rate = category_metric(by_usage, "Social Media Usage Category", "Low", "DepressionRate")
        top_usage_platform, top_usage_platform_rate = top_group(
            by_usage_platform_charts, "DepressionRate", ["Social Media Usage Category", "PlatformUsage"]
        )
        top_platform, top_platform_rate = top_group(by_platform, "DepressionRate", ["PlatformUsage"])
        sm_text = (
            f"There are {high_usage_count:,} high social‑media users in the current selection "
            f"({fmt_percent((local['DailySocialMediaHours']>=6).mean() if len(local) else 0)} of respondents).\n\n"
            f"Depression rate by usage level: Low {fmt_percent(low_usage_rate)}, "
            f"Medium {fmt_percent(medium_usage_rate)}, High {fmt_percent(high_usage_rate)}. "
            f"Respondent distribution is Low {low_usage_count:,}, Medium {medium_usage_count:,}, High {high_usage_count:,}.\n\n"
            f"The highest usage/platform depression rate is {top_usage_platform} at {fmt_percent(top_usage_platform_rate)}. "
            f"Overall, {top_platform} shows the highest depression rate at {fmt_percent(top_platform_rate)}, "
            f"and the average daily social‑media time is {fmt_decimal(m['Average Social Media Hours'])} hours."
        )
        sm_insights = dcc.Markdown(sm_text, style={"whiteSpace": "pre-wrap"})

        return kpis, fig_usage_gender, fig_usage_platform, combo, table, new_selected_rows, sm_insights

    # ---------- Stress & Anxiety callbacks ----------
    @app.callback(
        Output("sa-matrix", "data"),
        Output("sa-matrix", "selected_rows"),
        Output("sa-by-stress-gender", "figure"),
        Output("sa-by-anxiety-gender", "figure"),
        Output("sa-indicators", "figure"),
        Output("sa-distribution", "figure"),
        Output("sa-insights", "children"),
        Input("tabs", "value"),
        Input("f_age_group", "value"),
        Input("f_gender", "value"),
        Input("f_platform", "value"),
        Input("f_interaction", "value"),
        Input("sa-matrix", "selected_rows"),
        State("sa-matrix", "data"),
    )
    def sa_update(_tab_value, age_group, gender, platform, interaction, selected_rows, matrix_data):
        local = apply_filters(df, age_group, gender, platform, interaction)

        matrix = group_summary(
            local, ["Stress Category", "Anxiety Category"],
            {"Stress Category": CATEGORY_ORDER, "Anxiety Category": CATEGORY_ORDER}
        )

        # Table selection filters
        if matrix_data and selected_rows:
            selected_pairs = {(matrix_data[i]["Stress Category"], matrix_data[i]["Anxiety Category"]) for i in selected_rows}
            matrix_filtered = matrix[
                matrix.apply(
                    lambda r: (str(r["Stress Category"]), str(r["Anxiety Category"])) in selected_pairs,
                    axis=1,
                )
            ]
            if not matrix_filtered.empty:
                local = local.merge(
                    matrix_filtered[["Stress Category", "Anxiety Category"]].drop_duplicates(), how="inner"
                )

        by_stress_gender = group_summary(local, ["Stress Category", "Gender"], {"Stress Category": CATEGORY_ORDER})
        by_anxiety_gender = group_summary(local, ["Anxiety Category", "Gender"], {"Anxiety Category": CATEGORY_ORDER})

        fig_stress_gender = bar(
            by_stress_gender, "Stress Category", "DepressionRate", "Gender",
            "Depression Rate by Stress Category and Gender",
            category_orders={"Stress Category": CATEGORY_ORDER, "Gender": GENDER_ORDER},
        )
        fig_stress_gender.update_layout(yaxis_tickformat=".1%")
        fig_anxiety_gender = bar(
            by_anxiety_gender, "Anxiety Category", "DepressionRate", "Gender",
            "Depression Rate by Anxiety Category and Gender",
            category_orders={"Anxiety Category": CATEGORY_ORDER, "Gender": GENDER_ORDER},
        )
        fig_anxiety_gender.update_layout(yaxis_tickformat=".1%")

        indicators = pd.DataFrame(
            {
                "Indicator": ["Average Addiction Level", "Average Anxiety Level", "Average Stress Level"],
                "Value": [
                    local["AddictionLevel"].mean() if len(local) else 0,
                    local["AnxietyLevel"].mean() if len(local) else 0,
                    local["StressLevel"].mean() if len(local) else 0,
                ],
            }
        )
        fig_indicators = px.bar(indicators, x="Indicator", y="Value", title="Average Mental Health Indicator Levels", text_auto=CHART_DECIMAL_FORMAT)
        fig_indicators.update_traces(texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}")

        depression_distribution = (
            local.groupby(["Stress Category", "Depression Status"], observed=True)
            .size()
            .reset_index(name="Respondents")
        )
        fig_dist = bar(
            depression_distribution,
            "Stress Category",
            "Respondents",
            "Depression Status",
            "Depression Distribution by Stress Category",
            barmode="stack",
            category_orders={"Stress Category": CATEGORY_ORDER, "Depression Status": ["Not Depressed", "Depressed"]},
        )

        # Insights
        m = metrics(local)
        by_stress = group_summary(local, ["Stress Category"], {"Stress Category": CATEGORY_ORDER})
        by_anxiety = group_summary(local, ["Anxiety Category"], {"Anxiety Category": CATEGORY_ORDER})

        def get_rate(df_in: pd.DataFrame, col: str, val: str) -> float:
            row = df_in[df_in[col].astype(str) == val]
            return float(row["DepressionRate"].iloc[0]) if not row.empty else 0.0

        sa_text = (
            f"The selection contains {int((local['StressLevel'] >= 7).sum()):,} high‑stress respondents. "
            f"The depression rate among high‑stress respondents is {fmt_percent(get_rate(by_stress, 'Stress Category', 'High'))}, "
            f"and among high‑anxiety respondents it is {fmt_percent(get_rate(by_anxiety, 'Anxiety Category', 'High'))}.\n\n"
            f"Average sleep is {fmt_decimal(m['Average Sleep Hours'])} hours, and average social‑media use is "
            f"{fmt_decimal(m['Average Social Media Hours'])} hours."
        )
        insights = dcc.Markdown(sa_text, style={"whiteSpace": "pre-wrap"})

        # Rebuild selected_rows indices to match current matrix (prevents sticky selections)
        new_selected_rows = []
        if matrix_data and selected_rows:
            selected_pairs = {(matrix_data[i]["Stress Category"], matrix_data[i]["Anxiety Category"]) for i in selected_rows}
            current_records = matrix.to_dict("records")
            for i, row in enumerate(current_records):
                if (row["Stress Category"], row["Anxiety Category"]) in selected_pairs:
                    new_selected_rows.append(i)

        return matrix.to_dict("records"), new_selected_rows, fig_stress_gender, fig_anxiety_gender, fig_indicators, fig_dist, insights

    # ---------- Demographics callbacks ----------
    @app.callback(
        Output("dem-kpis", "children"),
        Output("dem-by-age-gender", "figure"),
        Output("dem-by-interaction-platform", "figure"),
        Output("dem-avg-indicators-by-gender", "figure"),
        Output("dem-age-gender-table", "data"),
        Output("dem-age-gender-table", "selected_rows"),
        Output("dem-insights", "children"),
        Input("tabs", "value"),
        Input("f_age_group", "value"),
        Input("f_gender", "value"),
        Input("f_platform", "value"),
        Input("f_interaction", "value"),
        Input("dem-by-age-gender", "selectedData"),
        Input("dem-by-interaction-platform", "selectedData"),
        Input("dem-avg-indicators-by-gender", "selectedData"),
        Input("dem-age-gender-table", "selected_rows"),
        State("dem-age-gender-table", "data"),
    )
    def dem_update(_tab_value, age_group, gender, platform, interaction, sel_age_gender_chart, sel_inter_platform_chart, sel_avg_by_gender_chart, selected_rows, table_data):
        base_local = apply_filters(df, age_group, gender, platform, interaction)

        # Build stable table from base (unaffected by previous table selection) to avoid index drift
        by_age_gender_all = group_summary(
            base_local, ["AgeGroup", "Gender"], {"AgeGroup": AGE_ORDER, "Gender": GENDER_ORDER}
        )

        # Apply table selection as a filter to local view for charts/KPIs
        local = base_local.copy()
        if table_data and selected_rows:
            selected_pairs = {(table_data[i]["AgeGroup"], table_data[i]["Gender"]) for i in selected_rows}
            if selected_pairs:
                local = local[
                    local.apply(lambda r: (str(r["AgeGroup"]), str(r["Gender"])) in selected_pairs, axis=1)
                ]

        # Cross-filter using chart selections
        # dem-by-age-gender provides AgeGroup and Gender
        sel_age_from_chart = extract_selected_values(sel_age_gender_chart, 0)
        sel_gender_from_chart = extract_selected_values(sel_age_gender_chart, 1)
        if sel_age_from_chart:
            local = local[local["AgeGroup"].astype(str).isin(sel_age_from_chart)]
        if sel_gender_from_chart:
            local = local[local["Gender"].astype(str).isin(sel_gender_from_chart)]

        # dem-by-interaction-platform provides SocialInteractionLevel and PlatformUsage
        sel_interaction_from_chart = extract_selected_values(sel_inter_platform_chart, 0)
        sel_platform_from_chart = extract_selected_values(sel_inter_platform_chart, 1)
        if sel_interaction_from_chart:
            local = local[local["SocialInteractionLevel"].astype(str).isin(sel_interaction_from_chart)]
        if sel_platform_from_chart:
            local = local[local["PlatformUsage"].astype(str).isin(sel_platform_from_chart)]

        # dem-avg-indicators-by-gender provides Gender (and Indicator)
        sel_gender_from_avg = extract_selected_values(sel_avg_by_gender_chart, 0)
        if sel_gender_from_avg:
            local = local[local["Gender"].astype(str).isin(sel_gender_from_avg)]

        m = metrics(local)
        kpis = [
            kpi(f"{m['Total Respondents']:,}", "Total Respondents"),
            kpi(f"{m['Depressed Respondents']:,}", "Depressed Respondents"),
            kpi(fmt_decimal(m["Average Stress Level"]), "Average Stress"),
            kpi(fmt_decimal(m["Average Anxiety Level"]), "Average Anxiety"),
            kpi(fmt_decimal(m["Average Addiction Level"]), "Average Addiction"),
        ]

        by_age_gender = group_summary(local, ["AgeGroup", "Gender"], {"AgeGroup": AGE_ORDER, "Gender": GENDER_ORDER})
        by_interaction_platform = group_summary(
            local, ["SocialInteractionLevel", "PlatformUsage"],
            {"SocialInteractionLevel": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER}
        )
        by_gender = group_summary(local, ["Gender"], {"Gender": GENDER_ORDER})
        long_gender = by_gender.melt(
            id_vars="Gender",
            value_vars=["AverageAnxietyLevel", "AverageStressLevel", "AverageAddictionLevel"],
            var_name="Indicator",
            value_name="Value",
        )

        fig_age_gender = bar(
            by_age_gender, "AgeGroup", "DepressionRate", "Gender",
            "Depression Rate by Age Group and Gender",
            category_orders={"AgeGroup": AGE_ORDER, "Gender": GENDER_ORDER},
            custom_fields=["AgeGroup", "Gender"]
        )
        fig_age_gender.update_layout(yaxis_tickformat=".1%")
        fig_interaction_platform = bar(
            by_interaction_platform, "SocialInteractionLevel", "DepressionRate", "PlatformUsage",
            "Depression Rate by Social Interaction and Platform",
            category_orders={"SocialInteractionLevel": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER},
            custom_fields=["SocialInteractionLevel", "PlatformUsage"]
        )
        fig_interaction_platform.update_layout(yaxis_tickformat=".1%")

        fig_avg_by_gender = px.bar(
            long_gender,
            x="Gender",
            y="Value",
            color="Indicator",
            barmode="group",
            title="Average Anxiety, Stress and Addiction by Gender",
            text_auto=CHART_DECIMAL_FORMAT,
            category_orders={"Gender": GENDER_ORDER},
            custom_data=["Gender", "Indicator"],
        )
        fig_avg_by_gender.update_traces(texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}")

        # Table data comes from stable base summary
        table = by_age_gender_all[
            [
                "AgeGroup",
                "Gender",
                "TotalRespondents",
                "DepressionRate",
                "AverageSocialMediaHours",
                "AverageSleepHours",
            ]
        ].to_dict("records")

        # Rebuild selected_rows to match current stable table by key
        new_selected_rows = []
        if table_data and selected_rows:
            selected_pairs = {(table_data[i]["AgeGroup"], table_data[i]["Gender"]) for i in selected_rows}
            for i, row in enumerate(table):
                if (row["AgeGroup"], row["Gender"]) in selected_pairs:
                    new_selected_rows.append(i)

        # Detailed insights (match Streamlit)
        top_age_gender, top_age_gender_rate = top_group(by_age_gender, "DepressionRate", ["AgeGroup", "Gender"])
        largest_age_gender, largest_age_gender_count = top_group(by_age_gender, "TotalRespondents", ["AgeGroup", "Gender"])
        top_interaction_platform, top_interaction_platform_rate = top_group(
            by_interaction_platform, "DepressionRate", ["SocialInteractionLevel", "PlatformUsage"]
        )
        top_gender_anxiety, top_gender_anxiety_value = top_group(by_gender, "AverageAnxietyLevel", ["Gender"])
        top_gender_stress, top_gender_stress_value = top_group(by_gender, "AverageStressLevel", ["Gender"])
        top_gender_addiction, top_gender_addiction_value = top_group(by_gender, "AverageAddictionLevel", ["Gender"])
        dem_text = (
            f"This view contains {m['Total Respondents']:,} respondents with {m['Depressed Respondents']:,} depressed respondents. "
            f"The highest age–gender depression rate is {top_age_gender} at {fmt_percent(top_age_gender_rate)}, while the "
            f"largest age–gender group is {largest_age_gender} with {largest_age_gender_count:,.0f} respondents.\n\n"
            f"The highest social‑interaction/platform depression rate is {top_interaction_platform} at "
            f"{fmt_percent(top_interaction_platform_rate)}. By gender, the highest averages are: "
            f"anxiety {top_gender_anxiety} ({fmt_decimal(top_gender_anxiety_value)}), "
            f"stress {top_gender_stress} ({fmt_decimal(top_gender_stress_value)}), and "
            f"addiction {top_gender_addiction} ({fmt_decimal(top_gender_addiction_value)})."
        )
        insights = dcc.Markdown(dem_text, style={"whiteSpace": "pre-wrap"})

        return kpis, fig_age_gender, fig_interaction_platform, fig_avg_by_gender, table, new_selected_rows, insights

