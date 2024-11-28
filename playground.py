import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md(
        r"""
        ### TODOs

        - Try altair
        - Choose between maplotlib and seaborn
        """
    )
    return


@app.cell
def __():
    import matplotlib.pyplot as plt
    import marimo as mo
    import pandas as pd
    import polars as pl
    import plotly.graph_objects as go
    import seaborn as sns

    from datetime import timedelta
    from plotly.subplots import make_subplots
    return go, make_subplots, mo, pd, pl, plt, sns, timedelta


@app.cell
def __(pd):
    df = pd.read_csv('AwesomeHabits.csv')
    df
    return (df,)


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
def __(pl, plt, sql):
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
    return filter_name, filtered_sql


@app.cell
def __(pl, plt, sql, timedelta):
    # Add a list to specify metrics that should have y-axis fixed from 0 to 1
    _fixed_zero_to_one_metrics = [
        "No meat", "No alcohol", "No screen",
        "Read some", "Take vitamins", "Exercise some", "Walk Falco"
    ]

    # Get unique values of the 'name' column
    _unique_names = sorted(sql["name"].unique())

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Calculate number of rows and columns for subplots
    _n = len(_unique_names)
    _cols = 2  # Two plots per name (line and bar)
    _rows = _n  # Each name gets one row

    # Create a figure with subplots
    plt.figure(figsize=(15, 5 * _rows))

    # Iterate over each unique name and plot both charts
    for _i, _name in enumerate(_unique_names):
        # Filter data for the current group
        _group = sql.filter(pl.col("name") == _name)
        _group_last_28_days = _sql_last_28_days.filter(pl.col("name") == _name)

        # Calculate means
        _group_mean = _group["quantity"].mean()
        _group_last_28_days_mean = _group_last_28_days["quantity"].mean()

        # Line Chart: Moving Average
        plt.subplot(_rows, _cols, _i * _cols + 1)
        plt.plot(
            _group["day"].to_list(), 
            _group["moving_avg"].to_list(), 
            label="Moving Avg", 
            color="blue"
        )
        plt.axhline(y=_group_mean, color="r", linestyle="--", label="Mean")
        plt.xlabel("Day")
        plt.ylabel("Moving Avg")
        plt.title(f"Moving 28d Avg of {_name}\nAvg: {_group_mean:.2f}")
        plt.xticks(rotation=90, fontsize=10)

        # Manually reorder legend for line chart
        _handles, _labels = plt.gca().get_legend_handles_labels()
        _order = [1, 0]
        plt.legend([_handles[_idx] for _idx in _order], [_labels[_idx] for _idx in _order])

        # Set y-axis limits to 0-1 if the metric is in the fixed list
        if _name in _fixed_zero_to_one_metrics:
            plt.ylim(0, 1)

        # Bar Chart: Daily Quantity
        plt.subplot(_rows, _cols, _i * _cols + 2)
        _x_ticks = _group_last_28_days["day"].to_list()
        _y_values = _group_last_28_days["quantity"].to_list()
        _bars = plt.bar(
            _x_ticks, 
            _y_values, 
            label="Quantity", 
            color="skyblue", 
            edgecolor="blue"
        )
        plt.axhline(
            y=_group_last_28_days_mean, 
            color="red", 
            linestyle="--", 
            label="Mean"
        )
        plt.xlabel("Day")
        plt.ylabel("Quantity")
        plt.title(f"Last 28d of {_name}\nAvg: {_group_last_28_days_mean:.2f}")
        plt.xticks(ticks=_x_ticks, rotation=90, fontsize=10)
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        # Set y-axis limits to 0-1 if the metric is in the fixed list
        if _name in _fixed_zero_to_one_metrics:
            plt.ylim(0, 1)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Show the plot
    plt.show()
    return


@app.cell
def __(pl, plt, sns, sql, timedelta):
    # Add a list to specify metrics that should have y-axis fixed from 0 to 1
    _fixed_zero_to_one_metrics = [
        "No meat", "No alcohol", "No screen",
        "Read some", "Take vitamins", "Exercise some", "Walk Falco"
    ]

    # Get unique values of the 'name' column
    _unique_names = sorted(sql["name"].unique())

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Create figure
    _fig, _axes = plt.subplots(
        nrows=len(_unique_names), 
        ncols=2, 
        figsize=(15, 5 * len(_unique_names))  # Increased vertical space
    )

    # Iterate over each unique name and plot both charts
    for _i, _name in enumerate(_unique_names):
        # Filter data for the current group
        _group = sql.filter(pl.col("name") == _name)
        _group_last_28_days = _sql_last_28_days.filter(pl.col("name") == _name)

        # Calculate means
        _group_mean = _group["quantity"].mean()
        _group_last_28_days_mean = _group_last_28_days["quantity"].mean()

        # Line Chart: Moving Average
        _line = sns.lineplot(
            x="day", 
            y="moving_avg", 
            data=_group.to_pandas(), 
            ax=_axes[_i, 0], 
            color='blue',
            label='Moving Avg'
        )
        _axes[_i, 0].axhline(y=_group_mean, color='r', linestyle='--', label='Mean')
        _axes[_i, 0].set_title(f"Moving 28d Avg of {_name}")
        _axes[_i, 0].set_xlabel("Day")
        _axes[_i, 0].set_ylabel("Moving Avg")
        _axes[_i, 0].tick_params(axis='x', rotation=90)
        _axes[_i, 0].set_title(f"Moving 28d Avg of {_name}\nAvg: {_group_mean:.2f}")

        # Manually reorder legend for line chart
        handles, labels = _axes[_i, 0].get_legend_handles_labels()
        _axes[_i, 0].legend([handles[1], handles[0]], [labels[1], labels[0]])

        # Bar Chart: Daily Quantity (Last 28 days)
        _bar = sns.barplot(
            x="day", 
            y="quantity", 
            data=_group_last_28_days.to_pandas(), 
            ax=_axes[_i, 1], 
            color='skyblue', 
            edgecolor='blue',
            label='Quantity'
        )
        _axes[_i, 1].axhline(y=_group_last_28_days_mean, color='r', linestyle='--', label='Mean')
        _axes[_i, 1].set_title(f"Last 28d of {_name}\nAvg: {_group_last_28_days_mean:.2f}")
        _axes[_i, 1].set_xlabel("Day")
        _axes[_i, 1].set_ylabel("Quantity")
        _axes[_i, 1].tick_params(axis='x', rotation=90)
        _axes[_i, 1].legend() # keep the original order

        # Set y-axis limits to 0-1 if the metric is in the fixed list
        if _name in _fixed_zero_to_one_metrics:
            _axes[_i, 0].set_ylim(0, 1)
            _axes[_i, 1].set_ylim(0, 1)

    # Adjust layout
    plt.tight_layout()

    # Show the plot
    plt.show()
    return handles, labels


@app.cell
def __(go, make_subplots, pl, sql, timedelta):
    # Add a list to specify metrics that should have y-axis fixed from 0 to 1
    _fixed_zero_to_one_metrics = [
        "No meat", "No alcohol", "No screen",
        "Read some", "Take vitamins", "Exercise some", "Walk Falco"
    ]

    # Get unique values of the 'name' column
    _unique_names = sorted(sql["name"].unique())

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Create subplots
    _fig = make_subplots(
        rows=len(_unique_names), 
        cols=2, 
        subplot_titles=[
            item for _name in _unique_names 
            for item in [f"Moving 28d Avg of {_name}", f"Last 28d of {_name}"]
        ],
        vertical_spacing=0.05,  # Reduced vertical spacing
        horizontal_spacing=0.05
    )

    # Iterate over each unique name and plot both charts
    for _i, _name in enumerate(_unique_names, 1):
        # Filter data for the current group
        _group = sql.filter(pl.col("name") == _name)
        _group_last_28_days = _sql_last_28_days.filter(pl.col("name") == _name)

        # Calculate means
        _group_mean = _group["quantity"].mean()
        _group_last_28_days_mean = _group_last_28_days["quantity"].mean()

        # Line Chart: Moving Average
        _fig.add_trace(
            go.Scatter(
                x=_group["day"].to_list(), 
                y=_group["moving_avg"].to_list(), 
                mode='lines', 
                name='Moving Avg',
                line=dict(color='blue')
            ),
            row=_i, col=1
        )

        # Mean line for Moving Average
        _fig.add_trace(
            go.Scatter(
                x=[_group["day"].min(), _group["day"].max()],
                y=[_group_mean, _group_mean],
                mode='lines',
                name='Mean',
                line=dict(color='red', dash='dash')
            ),
            row=_i, col=1
        )

        # Bar Chart: Daily Quantity (Last 28 days)
        _fig.add_trace(
            go.Bar(
                x=_group_last_28_days["day"].to_list(), 
                y=_group_last_28_days["quantity"].to_list(), 
                name='Quantity',
                marker_color='skyblue',
                marker_line_color='blue'
            ),
            row=_i, col=2
        )

        # Mean line for Daily Quantity
        _fig.add_trace(
            go.Scatter(
                x=[_group_last_28_days["day"].min(), _group_last_28_days["day"].max()],
                y=[_group_last_28_days_mean, _group_last_28_days_mean],
                mode='lines',
                name='Mean',
                line=dict(color='red', dash='dash')
            ),
            row=_i, col=2
        )

        # Set y-axis limits to 0-1 if the metric is in the fixed list
        if _name in _fixed_zero_to_one_metrics:
            _fig.update_yaxes(range=[0, 1], row=_i, col=1)
            _fig.update_yaxes(range=[0, 1], row=_i, col=2)

    # Update layout
    _fig.update_layout(
        height=300 * len(_unique_names),  # Reduced height per subplot
        width=1200,
        title_text='Metric Analysis',
        showlegend=False
    )

    # Rotate x-axis labels
    _fig.update_xaxes(tickangle=90)

    # Show the plot
    _fig.show()
    return


if __name__ == "__main__":
    app.run()
