import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium", layout_file="layouts/app.grid.json")


@app.cell
def __():
    ### Import what's needed

    import altair as alt
    import os
    import pandas as pd
    import marimo as mo

    from datetime import timedelta
    from dotenv import load_dotenv

    load_dotenv()
    return alt, load_dotenv, mo, os, pd, timedelta


@app.cell
def __(os, pd):
    ### Load data

    df = pd.read_csv(os.getenv("HABITS_PATH"))
    df
    return (df,)


@app.cell
def __(df, pd):
    ### Fix some columns

    # Map mood from Apple Health
    mood_map = {
        "Very pleasant": "3",
        "Pleasant": "2",
        "Slightly pleasant": "1",
        "Neutral": "0",
        "Slightly unpleasant": "-1",
        "Unpleasant": "-2",
        "Very unpleasant": "-3",
    }

    # Rewrite some columns
    df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y").dt.date
    df["Quantity"] = df["Quantity"].map(mood_map).combine_first(df["Quantity"])
    df_clean = df
    df_clean
    return df_clean, mood_map


@app.cell
def __(df_clean, mo):
    df_daily = mo.sql(
        f"""
        -- Clean up df_clean even more

        select
            Date as date,
            strftime(Date, '%a') as day,
            Name as name,
            case 
                when Name in ('Track sleep', 'Track screen')
                then Quantity::float / 60

                when Name = 'Track steps'
                then Quantity::float / 1000

                else Quantity::float
            end as quantity
        from df_clean
        where
            Name not in ('Mark habits', 'Export habits')
            and Date < date_trunc('week', current_date)
        """
    )
    return (df_daily,)


@app.cell
def __(df_daily, mo):
    # Create habits dropdown
    habits = sorted(df_daily["name"].unique(), reverse=True)

    dd_habits = mo.ui.dropdown(habits, value=habits[0])
    dd_habits
    return dd_habits, habits


@app.cell
def __(mo):
    # Create weeks dropdown
    weeks = ["1", "2", "4", "6", "8"]

    dd_weeks = mo.ui.dropdown(weeks, value="4")
    dd_weeks
    return dd_weeks, weeks


@app.cell
def __(dd_habits, dd_weeks, df_daily, mo):
    df_daily_avg = mo.sql(
        f"""
        -- Calc moving avg

        select
            date,
            day,
            name,
            round(quantity, 2) as quantity,
            round(avg(quantity) over (
                partition by name
                order by date
                rows between '{dd_weeks.value}'::int * 7 - 1 preceding and current row
            ), 2) as moving_avg
        from df_daily
        where name = '{dd_habits.value}'
        order by date desc
        """
    )
    return (df_daily_avg,)


@app.cell
def __(alt, dd_habits, dd_weeks, df_daily_avg, mo):
    ### Visualise in Altair

    # Prep a bit
    _df_daily_avg = df_daily_avg.to_pandas()
    _days_cut = int(dd_weeks.value) * 7

    _df_daily_cut = _df_daily_avg.iloc[:_days_cut]

    # Moving Average Line Chart
    moving_chart = (
        alt.Chart(_df_daily_avg)
        .mark_line(color="#067764")
        .encode(
            x="date:T",
            y=alt.Y(
                "moving_avg:Q",
                scale=(
                    alt.Scale(domain=[0, 1])  # Fixed domain for specific metrics
                    if dd_habits.value.split()[0] != "Track"
                    else alt.Scale(
                        domain=[
                            _df_daily_avg["moving_avg"].min() * 0.9,
                            _df_daily_avg["moving_avg"].max() * 1.1,
                        ]
                    )
                ),
            ),
            tooltip=["day", "date:T", alt.Tooltip("moving_avg:Q", format=".2f")],
        )
        .properties(
            title=f"Moving {dd_weeks.value}w Avg of {dd_habits.value} | Avg: {_df_daily_avg['quantity'].mean():.2f}",
            width=400,
            height=400,
        )
    )

    # Add dots to easily locate data points
    moving_dots = (
        alt.Chart(_df_daily_avg)
        .mark_point(filled=True, size=25, color="#067764")
        .encode(x="date:T", y="moving_avg:Q")
    )

    # Mean line for Overall Average
    _df_daily_avg_mean = _df_daily_avg["quantity"].mean()
    moving_mean = (
        alt.Chart(_df_daily_avg)
        .mark_rule(color="red", strokeDash=[5, 5])
        .encode(y=alt.datum(_df_daily_avg_mean))
    )

    # Daily Quantity Bar Chart (Last 28 Days)
    daily_chart = (
        alt.Chart(_df_daily_cut)
        .mark_bar(color="#067764")
        .encode(
            x="date:T",
            y=alt.Y(
                "quantity:Q",
                scale=alt.Scale(domain=[0, 1])
                      if dd_habits.value.split()[0] != "Track"
                      else alt.Scale(),
            ),
            tooltip=["day", "date:T", alt.Tooltip("quantity:Q", format=".2f")],
        )
        .properties(
            title=f"Last {dd_weeks.value}w of {dd_habits.value} | Avg: {_df_daily_cut['quantity'].mean():.2f}",
            width=400,
            height=400,
        )
    )

    # Mean line for Overall Average
    _df_daily_cut_mean = _df_daily_cut["quantity"].mean()
    daily_mean = (
        alt.Chart(_df_daily_cut)
        .mark_rule(color="red", strokeDash=[5, 5])
        .encode(y=alt.datum(_df_daily_cut_mean))
    )

    # Display the chart
    chart_l = mo.ui.altair_chart(moving_chart + moving_dots + moving_mean).interactive(False)
    chart_r = mo.ui.altair_chart(daily_chart + daily_mean).interactive(False)
    return (
        chart_l,
        chart_r,
        daily_chart,
        daily_mean,
        moving_chart,
        moving_dots,
        moving_mean,
    )


@app.cell
def __(dd_habits, dd_weeks, mo):
    mo.md(f"""# <u>**Stats for {dd_habits.value} | {dd_weeks.value} weeks**</u>""")
    return


@app.cell
def __(chart_l, chart_r, mo):
    # In a new cell, display the chart
    mo.hstack([chart_l, chart_r])
    return


if __name__ == "__main__":
    app.run()
