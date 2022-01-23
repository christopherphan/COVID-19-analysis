#! /usr/bin/env python3

"""
process.py
Makes plots and CSV files based on the *New York Times*' COVID-19 data

Important disclaimer: the author of this program is **not** an epidemologist.
"""

__author__ = "Christopher Phan <cphan@chrisphan.com>"
__copyright__ = "Copyright \u00a9 2022 Christopher Phan"
__license__ = "MIT"
__date__ = "2022-01-21"
__maintainer__ = "Christopher Phan"
__email__ = "cphan@chrisphan.com"

import json
import sys

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

# This file is released under the following license:
#
# Copyright 2022 Christopher Phan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def roundup_next(x):
    """Given x >= 0, return next multiple of 10**floor(log_10(x))
    e.g. roundup_next(15) = 20
    """
    str_x = str(int(np.ceil(x)))  # Convert to string of ceiling
    if x < 0:
        raise ValueError("input {} is negative".format(x))
    first_digit = int(str_x[0])
    new_first_digit = first_digit + 1
    val = int(str(new_first_digit) + "0" * (len(str_x) - 1))
    return val


if __name__ == "__main__":

    # The file config.json contains the locations of data, etc.

    try:
        with open("config.json", "rt") as infile:
            try:
                config_data = json.load(infile)
            except json.JSONDecodeError:
                sys.exit("The file config.json is not valid JSON.")
    except FileNotFoundError:
        sys.exit("config.json not found.")

    # Import *NYT* COVID-19 data

    ## The folder ../covid-19-data/ is a clone of the repository at
    ## https://github.com/nytimes/covid-19-data

    data = pd.read_csv(
        f"{config_data['NYTDataDirectory']}/us-states.csv", parse_dates=[0]
    )

    last_date = data["date"].max()

    source_txt = """Sources: New York Times COVID-19 tracking project
    https://github.com/nytimes/covid-19-data
    Last updated: """

    source_txt += last_date.strftime("%Y-%m-%d")

    # Plot #1: Number of confirmed cases and deaths in the U.S. over time

    data_by_date = data.groupby("date").sum()[["cases", "deaths"]]

    fig1 = plt.figure(1, figsize=(12, 8))
    ax1 = fig1.add_subplot(111)
    plt.yscale("log")
    fmt = matplotlib.ticker.FuncFormatter(lambda y, f: "{:,.0f}".format(y))
    ax1.yaxis.set_major_formatter(fmt)
    plt.ylim(1, roundup_next(max(data_by_date["cases"])))
    plt.grid(True, which="both")
    plt.title("U.S. COVID-19 confirmed cases and deaths (log scale)")
    plt.xlabel("Date")
    plt.plot(data_by_date["cases"], "b", label="Confirmed cases")
    plt.plot(data_by_date["deaths"], "r", label="Deaths")
    plt.legend()
    fig1.autofmt_xdate()
    plt.figtext(
        0.025,
        -0.25,
        source_txt,
        transform=ax1.transAxes,
        bbox={"facecolor": "white", "alpha": 0.8},
    )
    fig1.savefig("plots/nyt_cases_and_deaths.png")
    fig1.savefig("plots/nyt_cases_and_deaths.pdf")

    data_by_date.to_csv("csv/nyt_total_us_cases_and_deaths.csv")

    # Import US Census data and merge

    col_names = ["state", "population", "blank"]
    state_pop_data = pd.read_csv(config_data["CensusData"], names=col_names)

    data2 = pd.merge(
        data[data["date"] == last_date],
        state_pop_data[["state", "population"]],
        on="state",
    )

    # Plot #2: Scatterplot showing the number of confirmed cases and deaths
    # (per capita) in each state

    data2["Cases_per_capita"] = data2["cases"] / data2["population"]
    data2["Deaths_per_capita"] = data2["deaths"] / data2["population"]

    source_txt2 = (
        "Sources: - "
        + source_txt[9:]
        + """
    - 2020 US Census"""
    )

    fig2 = plt.figure(2, figsize=(12, 8))
    ax2 = fig2.add_subplot(111)
    denominator = 10000
    denominator_string = "per {:,.0f}".format(denominator)
    plt.grid(True, which="both")
    plt.title("U.S. COVID-19 cases and deaths {} by state".format(denominator_string))
    plt.xlabel("Cases {}".format(denominator_string))
    plt.ylabel("Deaths {}".format(denominator_string))
    plt.xlim(0, 1.1 * max(denominator * data2["Cases_per_capita"]))
    plt.ylim(0, 1.1 * max(denominator * data2["Deaths_per_capita"]))
    plt.text(
        0.6,
        0.85,
        source_txt2,
        transform=ax2.transAxes,
        bbox={"facecolor": "white", "alpha": 0.8},
    )
    plt.plot(
        denominator * data2["Cases_per_capita"],
        denominator * data2["Deaths_per_capita"],
        "k.",
    )
    fig2.savefig("plots/nyt_by_state.png")
    fig2.savefig("plots/nyt_by_state.pdf")

    ## Create CSV files from NYT data

    data.pivot(index="date", columns="state", values="cases").fillna(0).astype(
        int
    ).to_csv("csv/nyt_cases.csv")

    data.pivot(index="date", columns="state", values="deaths").fillna(0).astype(
        int
    ).to_csv("csv/nyt_deaths.csv")

    data.pivot(index="state", columns="date", values="cases").fillna(0).astype(
        int
    ).to_csv("csv/nyt_cases_transpose.csv")

    data.pivot(index="state", columns="date", values="deaths").fillna(0).astype(
        int
    ).to_csv("csv/nyt_deaths_transpose.csv")

    ## State plots and CSV files

    state_list = sorted(list(set(data["state"])))

    state_readme_text = """# State plots

    The *New York Times* has been compiling COVID-19 data from various state
    health departments. They have published the data on GitHub, at:
    <https://github.com/nytimes/covid-19-data>

    Below are plots of this data for each U.S. state and
    territory in their dataset.

    ## Important disclaimers:

    * I am **not** an epidemologist.

    * "Number of cases" is the number of **confirmed** cases. The *Times* gives
    the following description:
    > Confirmed cases are patients who test positive for the coronavirus. We
    > consider a case confirmed when it is reported by a federal, state,
    > territorial or local government agency.

    """

    for state in state_list:
        cur_data = data[data["state"] == state]
        if max(cur_data["cases"]) > 0:
            newfig = plt.figure(figsize=(12, 8))
            ax = newfig.add_subplot(111)
            # Only use log scale when number of cases > 50
            if max(cur_data["cases"]) > 50:
                plt.yscale("log")
                ax.yaxis.set_major_formatter(fmt)
                plt.ylim(1, roundup_next(max(cur_data["cases"])))
                log_text = " (log scale)"
            else:
                log_text = ""
            plt.grid(True, which="both")
            plt.title("{} COVID-19 confirmed cases and deaths".format(state) + log_text)
            plt.xlabel("Date")
            plt.plot(cur_data["date"], cur_data["cases"], "b", label="Confirmed cases")
            plt.plot(cur_data["date"], cur_data["deaths"], "r", label="Deaths")
            plt.legend()
            newfig.autofmt_xdate()
            plt.figtext(
                0.025,
                -0.25,
                source_txt,
                transform=ax.transAxes,
                bbox={"facecolor": "white", "alpha": 0.8},
            )
            state_underscore = state.replace(" ", "_")
            newfig.savefig("plots/nyt_{}.png".format(state_underscore))
            newfig.savefig("plots/nyt_{}.pdf".format(state_underscore))
            cur_data[["date", "cases", "deaths"]].to_csv(
                "csv/nyt_{}.csv".format(state_underscore), index=False
            )
            plt.close()
            state_readme_text += "## {}\n\n".format(state)
            state_readme_text += "![](plots/nyt_{}.png)\n\n".format(state_underscore)

    with open("states.md", "wt") as state_readme_file:
        state_readme_file.write(state_readme_text)
