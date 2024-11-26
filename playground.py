import marimo

__generated_with = "0.9.23"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    return (mo,)


@app.cell
def __():
    import pandas as pd

    df = pd.read_csv('AwesomeHabits.csv')
    df
    return df, pd


@app.cell
def __(df, mo):
    sql = mo.sql(
        f"""
        with
        prep as (
            select
                strptime(Date, '%d %b %Y')::date AS day,
                Name as name,
                case 
                    when Name in ('Sleep time', 'Screen time') 
                    then Quantity::float / 60 
                    else Quantity::float 
                end as quantity
            from df
            where Name not in ('Daily mood', 'Mark habits')
        )

        select
            day,
            name,
            quantity,
            avg(quantity) over (
                partition by name
                order by day
                range between interval 28 day preceding and current row    
            ) as moving_avg
        from prep
        order by day
        """
    )
    return (sql,)


@app.cell
def __(sql):
    import matplotlib.pyplot as plt
    import polars as pl

    filter_name = 'Take vitamins'

    filtered_sql = sql.filter(pl.col('name') == filter_name).to_pandas()
    plt.plot(filtered_sql['day'], filtered_sql['moving_avg'])
    plt.axhline(y=filtered_sql['quantity'].mean(), color='r', linestyle='--')
    plt.xlabel('Day')
    plt.ylabel('Moving Avg')
    plt.title(f'My stats for {filter_name}')

    # Rotate X-axis labels
    plt.xticks(rotation=90)

    plt.gca()
    plt.show()
    return filter_name, filtered_sql, pl, plt


@app.cell
def __(pl, plt, sql):
    from datetime import timedelta

    # Get unique values of the 'name' column
    unique_names = sorted(sql["name"].unique())

    # Filter for the last 28 days
    sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Calculate number of rows and columns for subplots
    n = len(unique_names)
    cols = 2  # Two plots per name (line and bar)
    rows = n  # Each name gets one row

    # Create a figure with subplots
    plt.figure(figsize=(15, 5 * rows))

    # Iterate over each unique name and plot both charts
    for i, name in enumerate(unique_names):
        # Filter data for the current group
        group = sql.filter(pl.col("name") == name)
        group_last_28_days = sql_last_28_days.filter(pl.col("name") == name)

        # Calculate means
        group_mean = group["quantity"].mean()
        group_last_28_days_mean = group_last_28_days["quantity"].mean()

        # Line Chart: Moving Average
        plt.subplot(rows, cols, i * cols + 1)
        plt.plot(
            group["day"].to_list(),
            group["moving_avg"].to_list(),
            label="Moving Avg",
            color="blue",
        )
        plt.axhline(y=group_mean, color="r", linestyle="--", label="Mean")
        plt.xlabel("Day")
        plt.ylabel("Moving Avg")
        plt.title(f"Moving 28d Avg of {name}\nAvg: {group_mean:.2f}")
        plt.xticks(rotation=90)
        plt.legend()

        # Bar Chart: Daily Quantity
        plt.subplot(rows, cols, i * cols + 2)
        plt.bar(
            group_last_28_days["day"].to_list(),
            group_last_28_days["quantity"].to_list(),
            label="Quantity",
            color="skyblue",
            edgecolor="blue",
        )
        plt.axhline(
            y=group_last_28_days_mean,
            color="red",
            linestyle="--",
            label="Mean",
        )
        plt.xlabel("Day")
        plt.ylabel("Quantity")
        plt.title(f"Last 28d of {name}\nAvg: {group_last_28_days_mean:.2f}")
        plt.xticks(rotation=90, fontsize=8)
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Show the plot
    plt.show()
    return (
        cols,
        group,
        group_last_28_days,
        group_last_28_days_mean,
        group_mean,
        i,
        n,
        name,
        rows,
        sql_last_28_days,
        timedelta,
        unique_names,
    )


if __name__ == "__main__":
    app.run()
