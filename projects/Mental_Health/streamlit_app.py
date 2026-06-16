from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_DIR = Path("processed")
RAW_DATA_PATH = Path("Teen_Mental_Health_Dataset.csv")
CATEGORY_ORDER = ["Low", "Medium", "High"]
AGE_ORDER = ["Early Teen", "Middle Teen", "Late Teen"]
PLATFORM_ORDER = ["Instagram", "TikTok", "Both"]
GENDER_ORDER = ["Male", "Female"]
CHART_DECIMAL_FORMAT = ".5f"


st.set_page_config(
    page_title="Teen Mental Health Analytics",
    page_icon="",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    fact = pd.read_csv(DATA_DIR / "Fact_TeenMentalHealth.csv")
    dim_age = pd.read_csv(DATA_DIR / "Dim_Age.csv")
    dim_gender = pd.read_csv(DATA_DIR / "Dim_Gender.csv")
    dim_platform = pd.read_csv(DATA_DIR / "Dim_Platform.csv")
    dim_social = pd.read_csv(DATA_DIR / "Dim_SocialInteraction.csv")

    data = (
        fact.merge(dim_age, on="AgeKey", how="left")
        .merge(dim_gender, on="GenderKey", how="left")
        .merge(dim_platform, on="PlatformKey", how="left")
        .merge(dim_social, on="SocialInteractionKey", how="left")
    )

    data["Stress Category"] = pd.cut(
        data["StressLevel"],
        bins=[-float("inf"), 3, 6, float("inf")],
        labels=CATEGORY_ORDER,
    ).astype(str)
    data["Anxiety Category"] = pd.cut(
        data["AnxietyLevel"],
        bins=[-float("inf"), 3, 6, float("inf")],
        labels=CATEGORY_ORDER,
    ).astype(str)
    data["Addiction Category"] = pd.cut(
        data["AddictionLevel"],
        bins=[-float("inf"), 3, 6, float("inf")],
        labels=CATEGORY_ORDER,
    ).astype(str)
    data["Social Media Usage Category"] = pd.cut(
        data["DailySocialMediaHours"],
        bins=[-float("inf"), 2.999, 5.999, float("inf")],
        labels=CATEGORY_ORDER,
    ).astype(str)
    data["Depression Status"] = data["DepressionLabel"].map(
        {0: "Not Depressed", 1: "Depressed"}
    )

    return data


def ordered_options(series: pd.Series, preferred_order: list[str]) -> list[str]:
    present = set(series.dropna().unique())
    ordered = [value for value in preferred_order if value in present]
    remaining = sorted(present - set(ordered))
    return ordered + remaining


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    age_group = st.sidebar.multiselect(
        "Age Group",
        ordered_options(data["AgeGroup"], AGE_ORDER),
        default=ordered_options(data["AgeGroup"], AGE_ORDER),
    )
    gender = st.sidebar.multiselect(
        "Gender",
        ordered_options(data["Gender"], GENDER_ORDER),
        default=ordered_options(data["Gender"], GENDER_ORDER),
    )
    platform = st.sidebar.multiselect(
        "Platform Usage",
        ordered_options(data["PlatformUsage"], PLATFORM_ORDER),
        default=ordered_options(data["PlatformUsage"], PLATFORM_ORDER),
    )
    interaction = st.sidebar.multiselect(
        "Social Interaction Level",
        ordered_options(data["SocialInteractionLevel"], CATEGORY_ORDER),
        default=ordered_options(data["SocialInteractionLevel"], CATEGORY_ORDER),
    )
    usage = st.sidebar.multiselect(
        "Social Media Usage Category",
        ordered_options(data["Social Media Usage Category"], CATEGORY_ORDER),
        default=ordered_options(data["Social Media Usage Category"], CATEGORY_ORDER),
    )
    stress = st.sidebar.multiselect(
        "Stress Category",
        ordered_options(data["Stress Category"], CATEGORY_ORDER),
        default=ordered_options(data["Stress Category"], CATEGORY_ORDER),
    )
    anxiety = st.sidebar.multiselect(
        "Anxiety Category",
        ordered_options(data["Anxiety Category"], CATEGORY_ORDER),
        default=ordered_options(data["Anxiety Category"], CATEGORY_ORDER),
    )

    return data[
        data["AgeGroup"].isin(age_group)
        & data["Gender"].isin(gender)
        & data["PlatformUsage"].isin(platform)
        & data["SocialInteractionLevel"].isin(interaction)
        & data["Social Media Usage Category"].isin(usage)
        & data["Stress Category"].isin(stress)
        & data["Anxiety Category"].isin(anxiety)
    ].copy()


def metrics(data: pd.DataFrame) -> dict[str, float]:
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
        "High Social Media Users": int((data["DailySocialMediaHours"] >= 6).sum()),
        "High Social Media User Rate": (data["DailySocialMediaHours"] >= 6).mean()
        if total
        else 0,
        "High Stress Rate": (data["StressLevel"] >= 7).mean() if total else 0,
    }


def show_kpis(data: pd.DataFrame, names: list[str]) -> None:
    values = metrics(data)
    columns = st.columns(len(names))
    for column, name in zip(columns, names):
        value = values[name]
        if "Rate" in name:
            display = f"{value:.1%}"
        elif name.startswith("Average"):
            display = f"{value:.2f}"
        else:
            display = f"{value:,}"
        column.metric(name, display)


def group_summary(
    data: pd.DataFrame, group_cols: list[str], sort_orders: dict[str, list[str]] | None = None
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


def fmt_percent(value: float) -> str:
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1%}"


def fmt_decimal(value: float) -> str:
    if pd.isna(value):
        return "0.00"
    return f"{value:.2f}"


def top_group(summary: pd.DataFrame, metric: str, label_cols: list[str]) -> tuple[str, float]:
    if summary.empty or metric not in summary:
        return "N/A", 0

    valid = summary.dropna(subset=[metric])
    if valid.empty:
        return "N/A", 0

    row = valid.sort_values(metric, ascending=False).iloc[0]
    label = " / ".join(str(row[column]) for column in label_cols)
    return label, float(row[metric])


def category_metric(summary: pd.DataFrame, column: str, value: str, metric: str) -> float:
    if summary.empty or column not in summary or metric not in summary:
        return 0

    matched = summary[summary[column].astype(str) == value]
    if matched.empty:
        return 0

    return float(matched.iloc[0][metric])


def category_count(data: pd.DataFrame, column: str, value: str) -> int:
    if column not in data:
        return 0
    return int((data[column].astype(str) == value).sum())


def bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str | None,
    title: str,
    barmode: str = "group",
):
    custom_data = [x]
    if color:
        custom_data.append(color)

    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        barmode=barmode,
        text_auto=CHART_DECIMAL_FORMAT,
        custom_data=custom_data,
        category_orders={
            "AgeGroup": AGE_ORDER,
            "Gender": GENDER_ORDER,
            "PlatformUsage": PLATFORM_ORDER,
            "Stress Category": CATEGORY_ORDER,
            "Anxiety Category": CATEGORY_ORDER,
            "Social Media Usage Category": CATEGORY_ORDER,
            "SocialInteractionLevel": CATEGORY_ORDER,
            "Depression Status": ["Not Depressed", "Depressed"],
        },
    )
    fig.update_layout(legend_title_text=color, yaxis_title=y, xaxis_title=x)
    fig.update_traces(
        texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}",
        hovertemplate=(
            f"{x}: %{{x}}<br>"
            f"{y}: %{{y:{CHART_DECIMAL_FORMAT}}}<extra></extra>"
        ),
    )
    return fig


def selection_state(key: str) -> dict:
    state = st.session_state.get(key)
    if not state:
        return {}
    if isinstance(state, dict):
        return state.get("selection", {}) or {}
    return getattr(state, "selection", {}) or {}


def selected_plotly_values(key: str, field: str, custom_fields: list[str]) -> set:
    selection = selection_state(key)
    values = set()

    for point in selection.get("points", []):
        custom_data = point.get("customdata")
        if custom_data is None:
            continue
        if not isinstance(custom_data, (list, tuple)):
            custom_data = [custom_data]
        if field in custom_fields:
            index = custom_fields.index(field)
            if index < len(custom_data):
                values.add(custom_data[index])

    return values


def selected_dataframe_values(key: str, data: pd.DataFrame, field: str) -> set:
    selection = selection_state(key)
    selected_rows = selection.get("rows", [])
    if not selected_rows or field not in data.columns:
        return set()

    valid_rows = [row for row in selected_rows if row < len(data)]
    return set(data.iloc[valid_rows][field].dropna())


def apply_page_filters(data: pd.DataFrame, filters: dict[str, set]) -> pd.DataFrame:
    page_data = data.copy()
    active_filters = {column: values for column, values in filters.items() if values}

    for column, values in active_filters.items():
        if column in page_data.columns:
            page_data = page_data[page_data[column].isin(values)]

    if active_filters:
        filter_text = ", ".join(
            f"{column}: {', '.join(map(str, sorted(values)))}"
            for column, values in active_filters.items()
        )
        st.info(f"Cross-filter active from selected visual values: {filter_text}")

    return page_data


def overview_page(data: pd.DataFrame) -> None:
    st.header("Dashboard 1: Teen Mental Health Overview")

    page_filters = {
        "Gender": selected_plotly_values(
            "overview_depression_rate_by_gender", "Gender", ["Gender"]
        )
        | selected_plotly_values(
            "overview_depression_rate_by_age_group_gender",
            "Gender",
            ["AgeGroup", "Gender"],
        ),
        "AgeGroup": selected_plotly_values(
            "overview_total_respondents_by_age_group", "AgeGroup", ["AgeGroup"]
        )
        | selected_plotly_values(
            "overview_depression_rate_by_age_group_gender",
            "AgeGroup",
            ["AgeGroup", "Gender"],
        ),
    }
    data = apply_page_filters(data, page_filters)

    show_kpis(
        data,
        [
            "Total Respondents",
            "Depressed Respondents",
            "Average Stress Level",
            "Average Anxiety Level",
            "Average Addiction Level",
        ],
    )

    left, right = st.columns(2)
    by_gender = group_summary(data, ["Gender"], {"Gender": GENDER_ORDER})
    by_age = group_summary(data, ["AgeGroup"], {"AgeGroup": AGE_ORDER})
    by_age_gender = group_summary(data, ["AgeGroup", "Gender"], {"AgeGroup": AGE_ORDER})

    left.plotly_chart(
        bar(by_gender, "Gender", "DepressionRate", None, "Depression Rate by Gender"),
        use_container_width=True,
        key="overview_depression_rate_by_gender",
        on_select="rerun",
        selection_mode="points",
    )
    right.plotly_chart(
        bar(by_age, "AgeGroup", "TotalRespondents", None, "Total Respondents by Age Group"),
        use_container_width=True,
        key="overview_total_respondents_by_age_group",
        on_select="rerun",
        selection_mode="points",
    )
    st.plotly_chart(
        bar(
            by_age_gender,
            "AgeGroup",
            "DepressionRate",
            "Gender",
            "Depression Rate by Age Group and Gender",
        ),
        use_container_width=True,
        key="overview_depression_rate_by_age_group_gender",
        on_select="rerun",
        selection_mode="points",
    )

    st.subheader("Key Insights and Findings")
    overview_metrics = metrics(data)
    largest_age_group, largest_age_count = top_group(
        by_age, "TotalRespondents", ["AgeGroup"]
    )
    highest_age_group, highest_age_rate = top_group(by_age, "DepressionRate", ["AgeGroup"])
    highest_gender, highest_gender_rate = top_group(by_gender, "DepressionRate", ["Gender"])
    female_rate = category_metric(by_gender, "Gender", "Female", "DepressionRate")
    male_rate = category_metric(by_gender, "Gender", "Male", "DepressionRate")
    st.markdown(
        f"""
        - The selected data contains **{overview_metrics["Total Respondents"]:,} respondents** and **{overview_metrics["Depressed Respondents"]:,} depressed respondents**, giving an overall depression rate of **{fmt_percent(overview_metrics["Depression Rate"])}**.
        - The average mental health indicator levels are **{fmt_decimal(overview_metrics["Average Stress Level"])} stress**, **{fmt_decimal(overview_metrics["Average Anxiety Level"])} anxiety**, and **{fmt_decimal(overview_metrics["Average Addiction Level"])} addiction**.
        - The largest age group is **{largest_age_group}** with **{largest_age_count:,.0f} respondents**.
        - The highest depression rate by age group is **{highest_age_group}** at **{fmt_percent(highest_age_rate)}**.
        - By gender, the highest depression rate is **{highest_gender}** at **{fmt_percent(highest_gender_rate)}**. Female rate is **{fmt_percent(female_rate)}** and male rate is **{fmt_percent(male_rate)}** for the current selection.
        """
    )


def social_media_page(data: pd.DataFrame) -> None:
    st.header("Dashboard 2: Social Media Impact")

    usage_platform_for_selection = group_summary(
        data,
        ["Social Media Usage Category", "PlatformUsage"],
        {"Social Media Usage Category": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER},
    )
    page_filters = {
        "Social Media Usage Category": selected_plotly_values(
            "social_total_respondents_by_usage_gender",
            "Social Media Usage Category",
            ["Social Media Usage Category", "Gender"],
        )
        | selected_plotly_values(
            "social_depression_rate_by_usage_platform",
            "Social Media Usage Category",
            ["Social Media Usage Category", "PlatformUsage"],
        )
        | selected_dataframe_values(
            "social_usage_platform_detail",
            usage_platform_for_selection,
            "Social Media Usage Category",
        ),
        "Gender": selected_plotly_values(
            "social_total_respondents_by_usage_gender",
            "Gender",
            ["Social Media Usage Category", "Gender"],
        ),
        "PlatformUsage": selected_plotly_values(
            "social_depression_rate_by_usage_platform",
            "PlatformUsage",
            ["Social Media Usage Category", "PlatformUsage"],
        )
        | selected_plotly_values(
            "social_avg_hours_and_depression_by_platform",
            "PlatformUsage",
            ["PlatformUsage"],
        )
        | selected_dataframe_values(
            "social_usage_platform_detail",
            usage_platform_for_selection,
            "PlatformUsage",
        ),
    }
    data = apply_page_filters(data, page_filters)

    show_kpis(
        data,
        ["High Social Media Users", "High Social Media User Rate", "High Stress Rate"],
    )

    left, right = st.columns(2)
    by_usage_gender = group_summary(
        data,
        ["Social Media Usage Category", "Gender"],
        {"Social Media Usage Category": CATEGORY_ORDER},
    )
    by_usage_platform = group_summary(
        data,
        ["Social Media Usage Category", "PlatformUsage"],
        {"Social Media Usage Category": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER},
    )

    left.plotly_chart(
        bar(
            by_usage_gender,
            "Social Media Usage Category",
            "TotalRespondents",
            "Gender",
            "Total Respondents by Social Media Usage and Gender",
        ),
        use_container_width=True,
        key="social_total_respondents_by_usage_gender",
        on_select="rerun",
        selection_mode="points",
    )
    right.plotly_chart(
        bar(
            by_usage_platform,
            "Social Media Usage Category",
            "DepressionRate",
            "PlatformUsage",
            "Depression Rate by Usage Category and Platform",
        ),
        use_container_width=True,
        key="social_depression_rate_by_usage_platform",
        on_select="rerun",
        selection_mode="points",
    )

    by_platform = group_summary(data, ["PlatformUsage"], {"PlatformUsage": PLATFORM_ORDER})
    combo = px.bar(
        by_platform,
        x="PlatformUsage",
        y="AverageSocialMediaHours",
        title="Average Social Media Hours and Depression Rate by Platform",
        text_auto=CHART_DECIMAL_FORMAT,
        custom_data=["PlatformUsage"],
        category_orders={"PlatformUsage": PLATFORM_ORDER},
    )
    combo.add_scatter(
        x=by_platform["PlatformUsage"],
        y=by_platform["DepressionRate"],
        name="Depression Rate",
        mode="lines+markers",
        yaxis="y2",
        customdata=by_platform[["PlatformUsage"]],
    )
    combo.update_layout(
        yaxis_title="Average Social Media Hours",
        yaxis2={"title": "Depression Rate", "overlaying": "y", "side": "right"},
        legend_title_text="Measure",
    )
    combo.update_traces(
        texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}",
        hovertemplate=(
            "PlatformUsage: %{x}<br>"
            f"Value: %{{y:{CHART_DECIMAL_FORMAT}}}<extra></extra>"
        ),
    )

    st.plotly_chart(
        combo,
        use_container_width=True,
        key="social_avg_hours_and_depression_by_platform",
        on_select="rerun",
        selection_mode="points",
    )

    st.subheader("Usage Category by Platform Detail")
    st.dataframe(
        by_usage_platform[
            [
                "Social Media Usage Category",
                "PlatformUsage",
                "TotalRespondents",
                "DepressionRate",
                "AverageSocialMediaHours",
                "AverageStressLevel",
                "AverageAnxietyLevel",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        key="social_usage_platform_detail",
        on_select="rerun",
        selection_mode="multi-row",
    )

    st.subheader("Key Insights and Findings")
    social_metrics = metrics(data)
    by_usage = group_summary(
        data,
        ["Social Media Usage Category"],
        {"Social Media Usage Category": CATEGORY_ORDER},
    )
    high_usage_count = category_count(data, "Social Media Usage Category", "High")
    medium_usage_count = category_count(data, "Social Media Usage Category", "Medium")
    low_usage_count = category_count(data, "Social Media Usage Category", "Low")
    high_usage_rate = category_metric(
        by_usage, "Social Media Usage Category", "High", "DepressionRate"
    )
    medium_usage_rate = category_metric(
        by_usage, "Social Media Usage Category", "Medium", "DepressionRate"
    )
    low_usage_rate = category_metric(
        by_usage, "Social Media Usage Category", "Low", "DepressionRate"
    )
    top_usage_platform, top_usage_platform_rate = top_group(
        by_usage_platform, "DepressionRate", ["Social Media Usage Category", "PlatformUsage"]
    )
    top_platform, top_platform_rate = top_group(
        by_platform, "DepressionRate", ["PlatformUsage"]
    )
    st.markdown(
        f"""
        - The selected data contains **{high_usage_count:,} high social media users**, equal to **{fmt_percent(social_metrics["High Social Media User Rate"])}** of respondents in the current selection.
        - Depression rate increases by usage category: **Low = {fmt_percent(low_usage_rate)}**, **Medium = {fmt_percent(medium_usage_rate)}**, and **High = {fmt_percent(high_usage_rate)}**.
        - Respondent distribution by usage level is **Low = {low_usage_count:,}**, **Medium = {medium_usage_count:,}**, and **High = {high_usage_count:,}**.
        - The highest usage-platform depression rate is **{top_usage_platform}** at **{fmt_percent(top_usage_platform_rate)}**.
        - By platform overall, **{top_platform}** has the highest depression rate at **{fmt_percent(top_platform_rate)}**, while the average daily social media usage across the selected data is **{fmt_decimal(social_metrics["Average Social Media Hours"])} hours**.
        """
    )


def stress_anxiety_page(data: pd.DataFrame) -> None:
    st.header("Dashboard 3: Stress and Anxiety Risk Analysis")

    matrix_for_selection = group_summary(
        data,
        ["Stress Category", "Anxiety Category"],
        {"Stress Category": CATEGORY_ORDER, "Anxiety Category": CATEGORY_ORDER},
    )
    page_filters = {
        "Stress Category": selected_dataframe_values(
            "stress_anxiety_matrix", matrix_for_selection, "Stress Category"
        )
        | selected_plotly_values(
            "stress_depression_rate_by_stress_gender",
            "Stress Category",
            ["Stress Category", "Gender"],
        )
        | selected_plotly_values(
            "stress_depression_distribution_by_stress",
            "Stress Category",
            ["Stress Category", "Depression Status"],
        ),
        "Anxiety Category": selected_dataframe_values(
            "stress_anxiety_matrix", matrix_for_selection, "Anxiety Category"
        )
        | selected_plotly_values(
            "stress_depression_rate_by_anxiety_gender",
            "Anxiety Category",
            ["Anxiety Category", "Gender"],
        ),
        "Gender": selected_plotly_values(
            "stress_depression_rate_by_stress_gender",
            "Gender",
            ["Stress Category", "Gender"],
        )
        | selected_plotly_values(
            "stress_depression_rate_by_anxiety_gender",
            "Gender",
            ["Anxiety Category", "Gender"],
        ),
        "Depression Status": selected_plotly_values(
            "stress_depression_distribution_by_stress",
            "Depression Status",
            ["Stress Category", "Depression Status"],
        ),
    }
    data = apply_page_filters(data, page_filters)

    matrix = group_summary(
        data,
        ["Stress Category", "Anxiety Category"],
        {"Stress Category": CATEGORY_ORDER, "Anxiety Category": CATEGORY_ORDER},
    )
    st.subheader("Stress and Anxiety Matrix")
    st.dataframe(
        matrix[
            [
                "Stress Category",
                "Anxiety Category",
                "TotalRespondents",
                "DepressionRate",
                "AverageSleepHours",
                "AverageSocialMediaHours",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        key="stress_anxiety_matrix",
        on_select="rerun",
        selection_mode="multi-row",
    )

    left, middle, right = st.columns(3)
    by_stress_gender = group_summary(
        data, ["Stress Category", "Gender"], {"Stress Category": CATEGORY_ORDER}
    )
    by_anxiety_gender = group_summary(
        data, ["Anxiety Category", "Gender"], {"Anxiety Category": CATEGORY_ORDER}
    )

    left.plotly_chart(
        bar(
            by_stress_gender,
            "Stress Category",
            "DepressionRate",
            "Gender",
            "Depression Rate by Stress Category and Gender",
        ),
        use_container_width=True,
        key="stress_depression_rate_by_stress_gender",
        on_select="rerun",
        selection_mode="points",
    )
    middle.plotly_chart(
        bar(
            by_anxiety_gender,
            "Anxiety Category",
            "DepressionRate",
            "Gender",
            "Depression Rate by Anxiety Category and Gender",
        ),
        use_container_width=True,
        key="stress_depression_rate_by_anxiety_gender",
        on_select="rerun",
        selection_mode="points",
    )

    indicators = pd.DataFrame(
        {
            "Indicator": ["Average Addiction Level", "Average Anxiety Level", "Average Stress Level"],
            "Value": [
                data["AddictionLevel"].mean() if len(data) else 0,
                data["AnxietyLevel"].mean() if len(data) else 0,
                data["StressLevel"].mean() if len(data) else 0,
            ],
        }
    )
    right.plotly_chart(
        px.bar(
            indicators,
            x="Indicator",
            y="Value",
            title="Average Mental Health Indicator Levels",
            text_auto=CHART_DECIMAL_FORMAT,
        ).update_traces(
            texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}",
            hovertemplate=(
                "Indicator: %{x}<br>"
                f"Value: %{{y:{CHART_DECIMAL_FORMAT}}}<extra></extra>"
            ),
        ),
        use_container_width=True,
        key="stress_average_indicator_levels",
        on_select="rerun",
        selection_mode="points",
    )

    depression_distribution = (
        data.groupby(["Stress Category", "Depression Status"], observed=True)
        .size()
        .reset_index(name="Respondents")
    )
    st.plotly_chart(
        bar(
            depression_distribution,
            "Stress Category",
            "Respondents",
            "Depression Status",
            "Depression Distribution by Stress Category",
            barmode="stack",
        ),
        use_container_width=True,
        key="stress_depression_distribution_by_stress",
        on_select="rerun",
        selection_mode="points",
    )

    st.subheader("Key Insights and Findings")
    stress_metrics = metrics(data)
    by_stress = group_summary(
        data, ["Stress Category"], {"Stress Category": CATEGORY_ORDER}
    )
    by_anxiety = group_summary(
        data, ["Anxiety Category"], {"Anxiety Category": CATEGORY_ORDER}
    )
    high_stress_count = category_count(data, "Stress Category", "High")
    high_anxiety_count = category_count(data, "Anxiety Category", "High")
    high_stress_rate = category_metric(by_stress, "Stress Category", "High", "DepressionRate")
    high_anxiety_rate = category_metric(
        by_anxiety, "Anxiety Category", "High", "DepressionRate"
    )
    low_stress_rate = category_metric(by_stress, "Stress Category", "Low", "DepressionRate")
    medium_stress_rate = category_metric(
        by_stress, "Stress Category", "Medium", "DepressionRate"
    )
    top_stress_anxiety, top_stress_anxiety_rate = top_group(
        matrix, "DepressionRate", ["Stress Category", "Anxiety Category"]
    )
    depressed_high_stress = int(
        data.loc[data["Stress Category"] == "High", "DepressionLabel"].sum()
    )
    depressed_high_anxiety = int(
        data.loc[data["Anxiety Category"] == "High", "DepressionLabel"].sum()
    )
    st.markdown(
        f"""
        - The selected data has **{high_stress_count:,} high-stress respondents** and **{high_anxiety_count:,} high-anxiety respondents**.
        - High-stress respondents contain **{depressed_high_stress:,} depressed cases** with a depression rate of **{fmt_percent(high_stress_rate)}**.
        - High-anxiety respondents contain **{depressed_high_anxiety:,} depressed cases** with a depression rate of **{fmt_percent(high_anxiety_rate)}**.
        - Stress category comparison shows **Low = {fmt_percent(low_stress_rate)}**, **Medium = {fmt_percent(medium_stress_rate)}**, and **High = {fmt_percent(high_stress_rate)}** depression rate.
        - The highest stress-anxiety combination is **{top_stress_anxiety}** with a depression rate of **{fmt_percent(top_stress_anxiety_rate)}**. Average sleep is **{fmt_decimal(stress_metrics["Average Sleep Hours"])} hours** and average social media use is **{fmt_decimal(stress_metrics["Average Social Media Hours"])} hours** for the current selection.
        """
    )


def demographics_page(data: pd.DataFrame) -> None:
    st.header("Dashboard 4: Demographics and Lifestyle Factors")

    age_gender_for_selection = group_summary(
        data, ["AgeGroup", "Gender"], {"AgeGroup": AGE_ORDER, "Gender": GENDER_ORDER}
    )
    page_filters = {
        "AgeGroup": selected_plotly_values(
            "demographics_depression_rate_by_age_gender",
            "AgeGroup",
            ["AgeGroup", "Gender"],
        )
        | selected_dataframe_values(
            "demographics_age_gender_matrix", age_gender_for_selection, "AgeGroup"
        ),
        "Gender": selected_plotly_values(
            "demographics_depression_rate_by_age_gender",
            "Gender",
            ["AgeGroup", "Gender"],
        )
        | selected_plotly_values(
            "demographics_average_indicators_by_gender",
            "Gender",
            ["Gender", "Indicator"],
        )
        | selected_dataframe_values(
            "demographics_age_gender_matrix", age_gender_for_selection, "Gender"
        ),
        "SocialInteractionLevel": selected_plotly_values(
            "demographics_depression_rate_by_interaction_platform",
            "SocialInteractionLevel",
            ["SocialInteractionLevel", "PlatformUsage"],
        ),
        "PlatformUsage": selected_plotly_values(
            "demographics_depression_rate_by_interaction_platform",
            "PlatformUsage",
            ["SocialInteractionLevel", "PlatformUsage"],
        ),
    }
    data = apply_page_filters(data, page_filters)

    show_kpis(
        data,
        [
            "Total Respondents",
            "Depressed Respondents",
            "Average Stress Level",
            "Average Anxiety Level",
            "Average Addiction Level",
        ],
    )

    left, middle, right = st.columns(3)
    by_age_gender = group_summary(
        data, ["AgeGroup", "Gender"], {"AgeGroup": AGE_ORDER, "Gender": GENDER_ORDER}
    )
    by_interaction_platform = group_summary(
        data,
        ["SocialInteractionLevel", "PlatformUsage"],
        {"SocialInteractionLevel": CATEGORY_ORDER, "PlatformUsage": PLATFORM_ORDER},
    )

    left.plotly_chart(
        bar(
            by_age_gender,
            "AgeGroup",
            "DepressionRate",
            "Gender",
            "Depression Rate by Age Group and Gender",
        ),
        use_container_width=True,
        key="demographics_depression_rate_by_age_gender",
        on_select="rerun",
        selection_mode="points",
    )
    middle.plotly_chart(
        bar(
            by_interaction_platform,
            "SocialInteractionLevel",
            "DepressionRate",
            "PlatformUsage",
            "Depression Rate by Social Interaction and Platform",
        ),
        use_container_width=True,
        key="demographics_depression_rate_by_interaction_platform",
        on_select="rerun",
        selection_mode="points",
    )

    by_gender = group_summary(data, ["Gender"], {"Gender": GENDER_ORDER})
    long_gender = by_gender.melt(
        id_vars="Gender",
        value_vars=["AverageAnxietyLevel", "AverageStressLevel", "AverageAddictionLevel"],
        var_name="Indicator",
        value_name="Value",
    )
    right.plotly_chart(
        px.bar(
            long_gender,
            x="Gender",
            y="Value",
            color="Indicator",
            barmode="group",
            title="Average Anxiety, Stress and Addiction by Gender",
            text_auto=CHART_DECIMAL_FORMAT,
            custom_data=["Gender", "Indicator"],
            category_orders={"Gender": GENDER_ORDER},
        ).update_traces(
            texttemplate=f"%{{y:{CHART_DECIMAL_FORMAT}}}",
            hovertemplate=(
                "Gender: %{x}<br>"
                "Indicator: %{customdata[1]}<br>"
                f"Value: %{{y:{CHART_DECIMAL_FORMAT}}}<extra></extra>"
            ),
        ),
        use_container_width=True,
        key="demographics_average_indicators_by_gender",
        on_select="rerun",
        selection_mode="points",
    )

    st.subheader("Age Group and Gender Matrix")
    st.dataframe(
        by_age_gender[
            [
                "AgeGroup",
                "Gender",
                "TotalRespondents",
                "DepressionRate",
                "AverageSocialMediaHours",
                "AverageSleepHours",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        key="demographics_age_gender_matrix",
        on_select="rerun",
        selection_mode="multi-row",
    )

    st.subheader("Key Insights and Findings")
    demographic_metrics = metrics(data)
    top_age_gender, top_age_gender_rate = top_group(
        by_age_gender, "DepressionRate", ["AgeGroup", "Gender"]
    )
    largest_age_gender, largest_age_gender_count = top_group(
        by_age_gender, "TotalRespondents", ["AgeGroup", "Gender"]
    )
    top_interaction_platform, top_interaction_platform_rate = top_group(
        by_interaction_platform,
        "DepressionRate",
        ["SocialInteractionLevel", "PlatformUsage"],
    )
    top_gender_anxiety, top_gender_anxiety_value = top_group(
        by_gender, "AverageAnxietyLevel", ["Gender"]
    )
    top_gender_stress, top_gender_stress_value = top_group(
        by_gender, "AverageStressLevel", ["Gender"]
    )
    top_gender_addiction, top_gender_addiction_value = top_group(
        by_gender, "AverageAddictionLevel", ["Gender"]
    )
    st.markdown(
        f"""
        - The selected demographic/lifestyle view contains **{demographic_metrics["Total Respondents"]:,} respondents** and **{demographic_metrics["Depressed Respondents"]:,} depressed respondents**.
        - The highest age-gender depression rate is **{top_age_gender}** at **{fmt_percent(top_age_gender_rate)}**.
        - The largest age-gender group is **{largest_age_gender}** with **{largest_age_gender_count:,.0f} respondents**.
        - The highest social interaction/platform depression rate is **{top_interaction_platform}** at **{fmt_percent(top_interaction_platform_rate)}**.
        - By gender, the highest average anxiety is **{top_gender_anxiety} ({fmt_decimal(top_gender_anxiety_value)})**, highest average stress is **{top_gender_stress} ({fmt_decimal(top_gender_stress_value)})**, and highest average addiction is **{top_gender_addiction} ({fmt_decimal(top_gender_addiction_value)})**.
        """
    )


def show_project_context() -> None:
    with st.expander("Project Objective, Business Problem, and Data Transformations", expanded=True):
        st.subheader("Project Objective & Business Problem")
        st.markdown(
            """
            This project analyzes teenage mental health patterns using social media usage,
            sleep, stress, anxiety, addiction level, academic performance, physical activity,
            gender, age group, platform usage, and social interaction level.

            The main business problem is to identify which behavioral and lifestyle factors
            are associated with higher depression risk among teenagers. The dashboard helps
            answer whether high social media usage, high stress, high anxiety, platform usage,
            age group, gender, or social interaction level are linked to different mental
            health outcomes.
            """
        )

        st.subheader("Data Sources & Transformations")
        st.markdown(
            """
            The original dataset comes from `Teen_Mental_Health_Dataset.csv`.
            The data was preprocessed using `teen_mental_health_preprocessing.ipynb`,
            and the cleaned Power BI/Python-ready tables were exported into `processed/`.

            Main transformation steps:

            - Loaded and validated the raw CSV with **1,200 rows** and **13 columns**.
            - Checked that all expected fields were present before processing.
            - Standardized text categories such as `Male/Female`, `Instagram/TikTok/Both`,
              and `Low/Medium/High` social interaction levels.
            - Converted numeric fields such as social media hours, sleep hours, stress level,
              anxiety level, addiction level, and depression label into numeric types.
            - Created age groups: `Early Teen`, `Middle Teen`, and `Late Teen`.
            - Built a star schema with one fact table and four dimension tables.
            - Created surrogate keys for age, gender, platform, and social interaction.
            - Validated unique dimension keys, matching foreign keys, and unique respondent IDs.
            - Exported five cleaned CSV tables into `processed/`.
            """
        )

        if RAW_DATA_PATH.exists():
            st.download_button(
                label="Download Original CSV Dataset",
                data=RAW_DATA_PATH.read_bytes(),
                file_name=RAW_DATA_PATH.name,
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.warning("Original CSV file is not available for download.")


def main() -> None:
    st.title("Teen Mental Health Analytics Dashboard")
    st.caption(
        "Interactive Python recreation of the Power BI report using processed star-schema CSV tables."
    )
    show_project_context()

    data = load_data()
    filtered = apply_filters(data)

    if filtered.empty:
        st.warning("No records match the selected filters.")
        return

    tabs = st.tabs(
        [
            "Overview",
            "Social Media Impact",
            "Stress and Anxiety",
            "Demographics and Lifestyle",
        ]
    )
    with tabs[0]:
        overview_page(filtered)
    with tabs[1]:
        social_media_page(filtered)
    with tabs[2]:
        stress_anxiety_page(filtered)
    with tabs[3]:
        demographics_page(filtered)


if __name__ == "__main__":
    main()
