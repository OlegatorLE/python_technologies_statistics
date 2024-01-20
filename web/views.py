from itertools import cycle
from math import pi
from typing import Dict, Any, List

import pandas as pd
from bokeh.embed import components
from bokeh.models import (
    ColumnDataSource, FactorRange, HoverTool, CustomJS, TapTool, PanTool
)
from bokeh.palettes import Spectral6, Spectral11
from bokeh.plotting import figure
from bokeh.transform import factor_cmap, cumsum
from django.db.models import When, Value, Case, CharField, Count, QuerySet
from django.http import HttpRequest
from django.shortcuts import render

from .models import Job


def get_query_parameters(request: HttpRequest) -> int:
    min_vacancies_str: str = request.GET.get("min_vacancies", "3")
    try:
        min_vacancies: int = int(min_vacancies_str)
    except ValueError:
        min_vacancies = 3
    return min_vacancies


def setup_initial_queryset() -> QuerySet:
    jobs_qs: QuerySet = Job.objects.all()
    jobs_qs = jobs_qs.prefetch_related("technologies")
    jobs_qs = jobs_qs.annotate(experience_level=Case(
        When(experience=1, then=Value("Junior")),
        When(experience__in=[2, 3], then=Value("Middle")),
        When(experience__gte=5, then=Value("Senior")),
        default=Value('Other'),
        output_field=CharField(),
    ))
    return jobs_qs


def aggregate_technology_data() -> list[Dict[str, Any]]:
    tech_data: list[Dict[str, Any]] = (
        Job.objects.annotate(experience_level=Case(
            When(experience__in=[0, 1], then=Value("Junior")),
            When(experience__in=[2, 3], then=Value("Middle")),
            When(experience__gte=5, then=Value("Senior")),
            default=Value("Other"),
            output_field=CharField(),
        )
        )
        .values("technologies__name", "experience_level")
        .annotate(count=Count("technologies"))
        .order_by("experience_level", "technologies__name"))
    return tech_data


def aggregate_experience_data(jobs_qs: QuerySet) -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame(
        list(jobs_qs.values(
            "date", "company", "english", "experience", "url"
        ))
    )

    experience_counts: pd.DataFrame = df["experience"].value_counts().reset_index()
    experience_counts.columns = ["experience_level", "count"]
    experience_counts["angle"] = experience_counts['count'] / experience_counts[
        "count"].sum() * 2 * pi
    experience_counts["color"] = Spectral6[:len(experience_counts)]
    experience_counts["legend"] = experience_counts.apply(
        lambda x: f"{x['experience_level']} років - {x['count']} вакансій",
        axis=1
    )
    return experience_counts


def aggregate_english_level_data(jobs_qs: QuerySet) -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame(
        list(jobs_qs.values(
            "date", "company", "english", "experience", "url"
        ))
    )

    english_level_counts: pd.DataFrame = df[
        "english"].value_counts().reset_index()
    english_level_counts.columns = ["english_level", "count"]
    return english_level_counts


def aggregate_company_data(
        jobs_qs: QuerySet,
        min_vacancies: int
) -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame(
        list(jobs_qs.values(
            "date", "company", "english", "experience", "url", "title",
        ))
    )

    company_vacancies_counts: pd.Series = df["company"].value_counts()
    companies_with_multiple_applications: pd.Index = company_vacancies_counts[
        company_vacancies_counts >= min_vacancies].index

    filtered_df: pd.DataFrame = df[
        df["company"].isin(companies_with_multiple_applications)].copy()
    filtered_df.loc[:, "date_str"] = filtered_df["date"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else ""
    )
    filtered_df.sort_values("date", inplace=True)

    company_codes, unique_companies = pd.factorize(filtered_df["company"])
    filtered_df["company_codes"] = company_codes.astype(str)

    grouped: pd.DataFrame = filtered_df.groupby(['company', 'date_str'])[
        'url'].agg(
        lambda x: ','.join(x)
    ).reset_index()
    filtered_df = filtered_df.merge(
        grouped,
        on=['company', 'date_str'],
        how='left',
        suffixes=('', '_all')
    )

    return filtered_df


def create_technology_plot(
        tech_data: List[Dict[str, Any]], level: str
) -> figure:
    level_data: List[Dict[str, Any]] = list(
        filter(lambda x: x["experience_level"] == level, tech_data)
    )
    if not level_data:
        return None  # Return None if no data for this level

    technologies: List[str] = [
        tech["technologies__name"] for tech in level_data
        if tech["technologies__name"] is not None
    ]
    counts: List[int] = [
        tech["count"] for tech in level_data
        if tech["technologies__name"] is not None
    ]
    source = ColumnDataSource(
        data=dict(technologies=technologies, counts=counts)
    )

    color_palette = cycle(Spectral11)
    number_of_technologies: int = len(counts)
    colors: List[str] = [
        next(color_palette) for _ in range(number_of_technologies)
    ]

    p: figure = figure(
        x_range=technologies,
        height=800, width=1000,
        title=f"{level} Level Technologies",
        toolbar_location=None,
        tools="",
        tooltips=[("Count", "@counts")]
    )
    p.vbar(
        x="technologies",
        top="counts",
        width=0.9,
        source=source,
        line_color="white",
        fill_color=factor_cmap(
            "technologies", palette=colors, factors=technologies
        )
    )

    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_orientation = 1.2
    return p


def create_experience_plot(experience_df: pd.DataFrame) -> figure:
    source_experience = ColumnDataSource(experience_df)

    p: figure = figure(
        title="Розподіл вакансій за вимогами до досвіду роботи",
        toolbar_location=None,
        tools="",
        width=1000,
        tooltips=[("Count", "@count")]
    )

    p.wedge(
        x=0,
        y=1,
        radius=0.4,
        start_angle=cumsum("angle", include_zero=True),
        end_angle=cumsum("angle"),
        line_color="white",
        fill_color="color",
        legend_field="legend",
        source=source_experience
    )

    p.axis.visible = False
    p.grid.grid_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "vertical"
    return p


def create_english_level_plot(english_level_df: pd.DataFrame) -> figure:
    source_english = ColumnDataSource(english_level_df)
    p: figure = figure(
        x_range=english_level_df["english_level"],
        title="English level",
        toolbar_location=None,
        tooltips=[("Count", "@count")],
        tools="",
        width=1000,
        height=800
    )

    p.vbar(
        x="english_level",
        top="count",
        width=0.9,
        source=source_english,
        line_color="white",
        fill_color=factor_cmap(
            "english_level",
            palette=Spectral6,
            factors=english_level_df["english_level"]
        )
    )

    return p


def create_company_plot(company_df: pd.DataFrame) -> figure:
    unique_companies = company_df["company"].unique()
    min_spacing = 20
    plot_width = len(unique_companies) * min_spacing

    x_factors: List[str] = company_df["company"].unique().tolist()
    y_factors: List[str] = company_df["date_str"].unique().tolist()

    source = ColumnDataSource(company_df)
    p: figure = figure(
        x_range=FactorRange(*x_factors),
        y_range=FactorRange(*y_factors),
        width=plot_width,
        height=800,
        tools="xpan,xwheel_zoom",
    )

    p.add_tools(PanTool(dimensions="width"))

    p.xaxis.major_label_orientation = 1.2
    r = p.circle(x="company", y="date_str", size=10, source=source)

    hover = HoverTool()
    hover.tooltips = """
        <div>
            <h3>@company</h3>
            <div><strong>Title: </strong>@title</div>
            <div><strong>Date: </strong>@date_str</div>
            <div><strong>URL: </strong><a href="@url" target="_blank">Link to Job</a></div>
        </div>
    """
    p.add_tools(hover)

    tap_cb = CustomJS(code='''
        var urls = cb_data.source.data['url_all'][cb_data.source.inspected.indices[0]];
        var urlList = urls.split(',');
        for (var i = 0; i < urlList.length; i++) {
            window.open(urlList[i], '_blank');
        }
    ''')
    tapt = TapTool(renderers=[r], callback=tap_cb, behavior='inspect')
    p.add_tools(tapt)

    return p


def prepare_response(request) -> Dict[str, Any]:
    min_vacancies: int = get_query_parameters(request)
    jobs_qs = setup_initial_queryset()

    tech_data = aggregate_technology_data()
    experience_df = aggregate_experience_data(jobs_qs)
    english_level_df = aggregate_english_level_data(jobs_qs)
    company_df = aggregate_company_data(jobs_qs, min_vacancies)

    script_list: Dict[str, str] = {}
    div_list: Dict[str, str] = {}

    experience_levels = ["Junior", "Middle", "Senior"]
    for level in experience_levels:
        tech_plot = create_technology_plot(tech_data, level)
        if tech_plot is not None:
            script, div = components(tech_plot)
            script_list[level] = script
            div_list[level] = div
        else:
            script_list[level] = ""
            div_list[
                level] = "<p>No data available for this experience level.</p>"

    experience_plot = create_experience_plot(experience_df)
    script3, div3 = components(experience_plot)

    english_level_plot = create_english_level_plot(english_level_df)
    script2, div2 = components(english_level_plot)

    company_plot = create_company_plot(company_df)
    script, div = components(company_plot)

    context = {
        "script": script, "div": div,
        "script2": script2, "div2": div2,
        "script3": script3, "div3": div3,
        "script_junior": script_list.get("Junior", ""),
        "div_junior": div_list.get("Junior", ""),
        "script_middle": script_list.get("Middle", ""),
        "div_middle": div_list.get("Middle", ""),
        "script_senior": script_list.get("Senior", ""),
        "div_senior": div_list.get("Senior", ""),
    }

    return render(request, "index.html", context)


def index(request: HttpRequest):
    return prepare_response(request)
