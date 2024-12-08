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

    df = pd.read_csv(os.getenv('HABITS_PATH'))
    df
    return (df,)


@app.cell
def __(df, pd):
    ### Fix some columns

    # Map mood from Apple Health
    mood_map = {
        'Very pleasant': '3',
        'Pleasant': '2',
        'Slightly pleasant': '1',
        'Neutral': '0',
        'Slightly unpleasant': '-1',
        'Unpleasant': '-2',
        'Very unpleasant': '-3',
    }

    # Rewrite some columns
    df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y').dt.date
    df['Quantity'] = df['Quantity'].map(mood_map).combine_first(df['Quantity'])
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
    # Get unique values of the 'name' column
    habits = sorted(df_daily["name"].unique(), reverse=True)
    dropdown = mo.ui.dropdown(habits)
    dropdown
    return dropdown, habits


@app.cell
def __(df_daily, dropdown, mo):
    df_daily_avg = mo.sql(
        f"""
        -- Calc moving avg

        select
            date,
            name,
            quantity,
            avg(quantity) over (
                partition by name
                order by date
                rows between 41 preceding and current row
            ) as moving_avg,
            avg(quantity) over (
                partition by name
            ) as overall_avg,
        from df_daily
        where name = '{dropdown.value}'
        order by date desc
        """
    )
    return (df_daily_avg,)


@app.cell
def __(alt, df_daily_avg, dropdown, mo):
    ### Visualise in Altair

    # Convert to Pandas and extract only last 28d
    _df_daily_avg = df_daily_avg.to_pandas()
    _df_daily_6w = _df_daily_avg.iloc[:42]

    # Moving Average Line Chart
    moving_avg_chart = alt.Chart(_df_daily_avg).mark_line(color="green").encode(
        x="date:T",
        y=alt.Y(
            "moving_avg:Q",
            scale=(
                alt.Scale(domain=[0, 1])  # Fixed domain for specific metrics
                if dropdown.value.split()[0] != "Track"
                else alt.Scale(domain=[_df_daily_avg["moving_avg"].min()*0.9, _df_daily_avg["moving_avg"].max()*1.1])
            )
        )
    ).properties(
        title=f"Moving 6w Avg of {dropdown.value} | Avg: {_df_daily_avg['quantity'].mean():.2f}",
        width=400,
        height=400
    )

    # Add dots to easily locate data points
    dots = alt.Chart(_df_daily_avg).mark_point(filled=True, size=20, color="green").encode(
            x="date:T",
            y="moving_avg:Q",
            tooltip=["date:T", "moving_avg:Q"]  # Tooltip for points
    )

    # Mean line for Overall Average
    mean_line = alt.Chart(_df_daily_avg).mark_rule(color="red", strokeDash=[5, 5]).encode(
        y="overall_avg:Q"
    )

    # Daily Quantity Bar Chart (Last 28 Days)
    bar_chart = alt.Chart(_df_daily_6w).mark_bar(color="skyblue").encode(
        x="date:T",
        y=alt.Y("quantity:Q", 
            scale=alt.Scale(domain=[0, 1]) 
            if dropdown.value.split()[0] != "Track" 
            else alt.Scale()
        ),
        tooltip=["date:T", "quantity:Q"]
    ).properties(
        title=f"Last 6w of {dropdown.value} | Avg: {_df_daily_6w['quantity'].mean():.2f}",
        width=400,
        height=400
    )

    # Display the chart
    chart_l = mo.ui.altair_chart(moving_avg_chart + dots + mean_line)
    chart_r = mo.ui.altair_chart(bar_chart)
    return bar_chart, chart_l, chart_r, dots, mean_line, moving_avg_chart


@app.cell
def __(chart_l, chart_r, mo):
    # In a new cell, display the chart
    mo.hstack([chart_l, chart_r])
    return


if __name__ == "__main__":
    app.run()
