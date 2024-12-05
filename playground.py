import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def __():
    import altair as alt
    import matplotlib.pyplot as plt
    import marimo as mo
    import pandas as pd
    import polars as pl
    import plotly.graph_objects as go
    import plotly.io as pio
    import seaborn as sns

    from datetime import timedelta
    from plotly.subplots import make_subplots
    return alt, go, make_subplots, mo, pd, pio, pl, plt, sns, timedelta


@app.cell
def __(pd):
    df = pd.read_csv('AwesomeHabits.csv')
    df
    return (df,)


@app.cell
def __(df, mo):
    sql = mo.sql(
        f"""
        --- Data Prep

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
            where Name not in ('Track mood', 'Mark habits')
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
    ### Common Variables

    # Add a list to specify metrics that should have y-axis fixed from 0 to 1
    fixed_zero_to_one_metrics = [
        "No meat", "No alcohol", "No screen",
        "Some reading", "Some vitamins", "Some exercise", "Some Falco"
    ]

    # Get unique values of the 'name' column
    unique_names = sorted(sql["name"].unique())
    return fixed_zero_to_one_metrics, unique_names


@app.cell
def __(mo, unique_names):
    first_dropdown = mo.ui.dropdown(unique_names, value='Some exercise')
    first_dropdown
    return (first_dropdown,)


@app.cell
def __(first_dropdown, pl, plt, sql):
    ### One metric

    filter_name = first_dropdown.value

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
def __(fixed_zero_to_one_metrics, pl, plt, sql, timedelta, unique_names):
    ### Matplotlib

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Calculate number of rows and columns for subplots
    _n = len(unique_names)
    _cols = 2  # Two plots per name (line and bar)
    _rows = _n  # Each name gets one row

    # Create a figure with subplots
    plt.figure(figsize=(15, 5 * _rows))

    # Iterate over each unique name and plot both charts
    for _i, _name in enumerate(unique_names):
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
        if _name in fixed_zero_to_one_metrics:
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
        if _name in fixed_zero_to_one_metrics:
            plt.ylim(0, 1)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Show the plot
    plt.show()
    return


@app.cell
def __(
    fixed_zero_to_one_metrics,
    pl,
    plt,
    sns,
    sql,
    timedelta,
    unique_names,
):
    ### Seaborn

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Create figure
    _fig, _axes = plt.subplots(
        nrows=len(unique_names), 
        ncols=2, 
        figsize=(15, 5 * len(unique_names))  # Increased vertical space
    )

    # Iterate over each unique name and plot both charts
    for _i, _name in enumerate(unique_names):
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
        if _name in fixed_zero_to_one_metrics:
            _axes[_i, 0].set_ylim(0, 1)
            _axes[_i, 1].set_ylim(0, 1)

    # Adjust layout
    plt.tight_layout()

    # Show the plot
    plt.show()
    return handles, labels


@app.cell
def __(
    fixed_zero_to_one_metrics,
    go,
    make_subplots,
    pio,
    pl,
    sql,
    timedelta,
    unique_names,
):
    ### Plotly

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Create subplots
    _fig = make_subplots(
        rows=len(unique_names), 
        cols=2, 
        subplot_titles=[
            item for _name in unique_names 
            for item in [
                f"Moving 28d Avg of {_name} | Avg: {sql.filter(pl.col('name') == _name)['quantity'].mean():.2f}", 
                f"Last 28d of {_name} | Avg: {_sql_last_28_days.filter(pl.col('name') == _name)['quantity'].mean():.2f}"
            ]
        ],
        vertical_spacing=0.05,  # Reduced vertical spacing
        horizontal_spacing=0.05
    )

    # Iterate over each unique name and plot both charts
    for _i, _name in enumerate(unique_names, 1):
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
                marker_line_color='blue',
                customdata=_group_last_28_days["day"].dt.strftime('%d %b').to_list(),
                hovertemplate='Day: %{customdata}<br>Quantity: %{y:.2f}<extra></extra>',
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
        if _name in fixed_zero_to_one_metrics:
            _fig.update_yaxes(range=[0, 1], row=_i, col=1)
            _fig.update_yaxes(range=[0, 1], row=_i, col=2)

        # Increase y-axis ticks
        _fig.update_yaxes(nticks=10, row=_i, col=1)
        _fig.update_yaxes(nticks=10, row=_i, col=2)

        # Update x-axis for bar chart with date formatting and rotation
        _fig.update_xaxes(
            tickangle=-90,
            tickvals=_group_last_28_days["day"].to_list(),
            ticktext=_group_last_28_days["day"].dt.strftime('%m-%d').to_list(),
            row=_i, 
            col=2
        )

    # Update layout
    _fig.update_layout(
        height=300 * len(unique_names),
        width=1080,
        title_text='Metric Analysis',
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=10)
    )

    # Show the plot
    _fig.show()


    # Export to PNG
    #pio.write_image(_fig, "plot.png")

    # Export to JPEG
    pio.write_image(_fig, "plot.jpeg", format="jpeg")

    # Save the figure as an HTML file
    # pio.write_html(_fig, file="plot.html", auto_open=False)
    return


@app.cell
def __(mo, unique_names):
    dropdown = mo.ui.dropdown(unique_names, value='Some exercise')
    dropdown
    return (dropdown,)


@app.cell
def __(
    alt,
    dropdown,
    fixed_zero_to_one_metrics,
    mo,
    pd,
    pl,
    sql,
    timedelta,
):
    ### Altair

    # Filter for the last 28 days
    _sql_last_28_days = sql.filter(pl.col("day") >= (sql["day"].max() - timedelta(days=27)))

    # Filter data for the current group
    _group = sql.filter(pl.col("name") == dropdown.value)
    _group_last_28_days = _sql_last_28_days.filter(pl.col("name") == dropdown.value)

    # Convert to Pandas for Altair compatibility
    _group_df = _group.to_pandas()
    _group_last_28_days_df = _group_last_28_days.to_pandas()

    # Moving Average Line Chart
    moving_avg_chart = alt.Chart(_group_df).mark_line(color="blue").encode(
        x="day:T",
        y=alt.Y(
            "moving_avg:Q",
            scale=(
                alt.Scale(domain=[0, 1])  # Fixed domain for specific metrics
                if dropdown.value in fixed_zero_to_one_metrics
                else alt.Scale(domain=[_group_df["moving_avg"].min()*0.9, _group_df["moving_avg"].max()*1.1])
            )
        ),
        tooltip=["day:T", "moving_avg:Q"]
    ).properties(
        title=f"Moving 28d Avg of {dropdown.value} | Avg: {_group_df['quantity'].mean():.2f}",
        width=400,
        height=400
    )

    dots = alt.Chart(_group_df).mark_point(filled=True, size=20, color="blue").encode(
            x="day:T",
            y="moving_avg:Q",
            tooltip=["day:T", "moving_avg:Q"]  # Tooltip for points
    )

    # Mean line for Moving Average
    mean_line = alt.Chart(pd.DataFrame({"mean": [_group_df["quantity"].mean()]})).mark_rule(color="red", strokeDash=[5, 5]).encode(
        y="mean:Q"
    )

    # Daily Quantity Bar Chart (Last 28 Days)
    bar_chart = alt.Chart(_group_last_28_days_df).mark_bar(color="skyblue").encode(
        x="day:T",
        y=alt.Y("quantity:Q", scale=alt.Scale(domain=[0, 1]) if dropdown.value in fixed_zero_to_one_metrics else alt.Scale()),
        tooltip=["day:T", "quantity:Q"]
    ).properties(
        title=f"Last 28d of {dropdown.value} | Avg: {_group_last_28_days_df['quantity'].mean():.2f}",
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


@app.cell
def __():
    ### DotEnv

    from dotenv import load_dotenv
    import os

    load_dotenv()
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    return email, load_dotenv, os, password


@app.cell
def __(email, password):
    ### Emails

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage

    # Email details
    subject = "Email with Embedded Picture"
    body = """
    <html>
      <body>
        <h1>Hello!</h1>
        <a href="iterm://newtab?command=echo%20Hello%2C%20World%21">Run 'echo Hello, World!'</a>
        <a href="https://www.google.com">Google</a>
        <p>This email has an embedded picture:</p>
        <img src="cid:image1">
      </body>
    </html>
    """

    # Create the email
    message = MIMEMultipart("related")
    message["From"] = email
    message["To"] = email
    message["Subject"] = subject

    # Add the HTML body
    html_part = MIMEText(body, "html")
    message.attach(html_part)

    # Add the picture
    filename = "plot.jpeg"  # Replace with your image file
    with open(filename, "rb") as img:
        img_part = MIMEImage(img.read())
        img_part.add_header("Content-ID", "<image1>")  # Match the "cid" in the HTML
        message.attach(img_part)

    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, password)
            server.sendmail(email, email, message.as_string())
        print("Email with embedded picture sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    return (
        MIMEImage,
        MIMEMultipart,
        MIMEText,
        body,
        filename,
        html_part,
        img,
        img_part,
        message,
        server,
        smtplib,
        subject,
    )


@app.cell
def __(go, make_subplots):
    ### Tiles

    # Example data
    current_value = 1234
    previous_value = 1200
    trend = [1000, 1100, 1200, 1234]
    time = ['Week 1', 'Week 2', 'Week 3', 'Week 4']

    # Create a 2x1 grid with different subplot types
    fig = make_subplots(
        rows=2, cols=1,
        specs=[
            [{"type": "indicator"}],  # Big number
            [{"type": "xy"}]          # Chart
        ],
        row_heights=[0.5, 0.5],  # Adjust row heights
        vertical_spacing=0.1     # Space between rows
    )

    # Add the big number with delta in the top cell
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=current_value,
            delta={
                "reference": previous_value,
                "relative": True,
                "valueformat": ".1%"
            },
        ),
        row=1, col=1
    )

    # Add the trendline chart in the bottom cell
    fig.add_trace(
        go.Scatter(
            x=time,
            y=trend,
            mode='lines+markers',
            name='Trendline',
            line=dict(color='blue'),
            marker=dict(size=8)
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        title={
            'text': "<u>Metric 1</u>",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 40}
        },
        height=500,
        width=500,
        showlegend=False,
        xaxis2=dict(title="Time"),  # Bottom x-axis (second row)
        yaxis2=dict(title="Value"),  # Bottom y-axis (second row)
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.5)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.5)')
    )

    fig.show()
    fig.write_image("fig.png")
    return current_value, fig, previous_value, time, trend


@app.cell
def __(go):
    ### Tiles to HTML

    # Create individual figures
    fig1 = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
    fig2 = go.Figure(data=go.Bar(x=[1, 2, 3], y=[4, 5, 6]))
    fig3 = go.Figure(data=go.Pie(values=[10, 20, 30]))
    fig4 = go.Figure(data=go.Indicator(mode="number", value=1234))

    # Save each figure as a PNG image
    fig1.write_image("fig1.png")
    fig2.write_image("fig2.png")
    fig3.write_image("fig3.png")
    fig4.write_image("fig4.png")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        .grid-container {
          display: grid;
          grid-template-columns: 1fr 1fr; /* 2 columns */
          gap: 10px;
        }
        .grid-item img {
          width: 100%; /* Make images responsive */
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 5px;
        }
      </style>
    </head>
    <body>
      <div class="grid-container">
        <div class="grid-item"><img src="fig1.png" alt="Figure 1"></div>
        <div class="grid-item"><img src="fig2.png" alt="Figure 2"></div>
        <div class="grid-item"><img src="fig3.png" alt="Figure 3"></div>
        <div class="grid-item"><img src="fig4.png" alt="Figure 4"></div>
      </div>
    </body>
    </html>
    """

    # Save the HTML file
    with open("combined.html", "w") as file:
        file.write(html_content)
    return fig1, fig2, fig3, fig4, file, html_content


@app.cell
def __(plt):
    ### Wordcloud

    from wordcloud import WordCloud
    import random

    # Generate random words with random frequencies
    words = {f"Word{i}": random.randint(1, 6) for i in range(1, 10)}
    print(words)

    # Create the word cloud with padding to avoid overlap
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white', 
        colormap='viridis',
        contour_width=1,
        contour_color='black',
        prefer_horizontal=1.0,
        scale=10,
    ).generate_from_frequencies(words)

    # Display the word cloud
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  # Turn off the axis
    plt.title("Word Cloud", fontsize=20)
    plt.show()
    return WordCloud, random, wordcloud, words


@app.cell
def __(plt):
    ### Heatmap

    import numpy as np
    from matplotlib.colors import Normalize
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.cm as cm

    # Example data: values over 7 days for 4 metrics
    _data = np.array([
        [1, 0, 0, 1, 0, 1, 0],  
        [2000, 2500, 1000, 1700, 2500, 1000, 1800],
        [5, 10, 15, 5, 10, 15, 5],
        [300, 100, 200, 400, 500, 250, 350]
    ])

    # Metric labels
    _metrics = ["Metric 1", "Metric 2", "Metric 3", "Metric 4"]

    # Adjust the transparency (alpha) of the colormap
    _base_cmap = plt.colormaps.get_cmap('RdYlGn')
    _colors = _base_cmap(np.linspace(0, 1, 256))  # Extract original colours
    _colors[:, -1] = 0.5  # Set alpha transparency to 50%
    _cmap = LinearSegmentedColormap.from_list("PastelRdYlGn", _colors)

    # Create the heatmap
    _fig, _ax = plt.subplots(figsize=(10, 6))

    # Normalize each row independently
    for _i, row in enumerate(_data):
        _min, _max = np.min(row), np.max(row)
        _mean = np.mean(row)
        _norm = Normalize(vmin=_min, vmax=_max)
        for _j, value in enumerate(row):
            # Normalise value and get colour
            color = _cmap(_norm(value))
            _ax.add_patch(plt.Rectangle((_j, _i), 1, 1, color=color))
            _ax.text(_j + 0.5, _i + 0.5, f"{value:.1f}", ha="center", va="center", color="black")

    # Set axis labels and ticks
    _ax.set_xticks(np.arange(_data.shape[1]) + 0.5)
    _ax.set_yticks(np.arange(_data.shape[0]) + 0.5)
    _ax.set_xticklabels(['M', 'T', 'W', 'T', 'F', 'S', 'S'])
    _ax.set_yticklabels(_metrics)
    _ax.set_xlim(0, _data.shape[1])
    _ax.set_ylim(0, _data.shape[0])
    _ax.invert_yaxis()

    # Add grid lines
    _ax.set_xticks(np.arange(_data.shape[1]), minor=True)
    _ax.set_yticks(np.arange(_data.shape[0]), minor=True)
    _ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
    _ax.tick_params(which="minor", size=0)

    plt.show()
    return LinearSegmentedColormap, Normalize, cm, color, np, row, value


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
