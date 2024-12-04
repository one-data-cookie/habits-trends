import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def __():
    ### Import what's needed

    import marimo as mo
    import os
    import pandas as pd
    import plotly.graph_objects as go
    import polars as pl

    from plotly.subplots import make_subplots

    OUTPUT_FOLDER = "output"
    return OUTPUT_FOLDER, go, make_subplots, mo, os, pd, pl


@app.cell
def __(pd):
    ### Load data

    df = pd.read_csv('AwesomeHabits.csv')
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
    df
    return (mood_map,)


@app.cell
def __(df, mo):
    df_daily = mo.sql(
        f"""
        -- Clean up df

        select
            Date as date,
            strftime(Date, '%a') as day,
            Name as name,
            case 
                when Name in ('Track sleep', 'Track screen')
                then Quantity::float / 60
                else Quantity::float
            end as quantity
        from df
        where Name not in ('Mark habits')
        and Date < date '2024-12-02'
        """
    )
    return (df_daily,)


@app.cell
def __(df_daily, mo):
    df_weekly = mo.sql(
        f"""
        -- Transform df_daily to a weekly view

        select
            date_trunc('week', date) as week,
            name,
            round(avg(quantity), 2) as quantity_avg
        from df_daily
        group by 1, 2
        order by 1, 2
        """
    )
    return (df_weekly,)


@app.cell
def __(df_weekly):
    print(df_weekly)
    return


@app.cell
def __(OUTPUT_FOLDER, df_weekly, go, make_subplots, os, pl):
    ### Build a tiles
    habits = sorted(df_weekly["name"].unique(), reverse=True)

    for _habit in habits:
        # Prep data
        df_filtered = df_weekly.filter(pl.col('name') == _habit)
        trend = df_filtered['quantity_avg'].to_list()[-6:]
        time = df_filtered['week'].to_list()[-6:]
        
        # Create a 2x1 grid with different subplot types
        fig = make_subplots(
            rows=2, cols=1,
            specs=[
                [{"type": "indicator"}],
                [{"type": "xy"}]
            ],
            row_heights=[0.5, 0.5],
            vertical_spacing=0.1
        )

        # Create a configuration dictionary and assign
        opts = {
            "Track": {
                "format": ".1f",
                "delta_relative": True,
                "y_range": None
            },
            "Default": {
                "format": ".0%",
                "delta_relative": False,
                "y_range": [-0.1, 1.1]
            }
        }
        config = opts.get(_habit.split()[0], opts["Default"])

        # Add the big number with delta in the top cell
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=trend[-1],
                number={
                    "valueformat": config["format"]
                },
                delta={
                    "reference": trend[-2],
                    "relative": config["delta_relative"],
                    "valueformat": ".0%"
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
                'text': f"<u>{_habit}</u>",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 40}
            },
            height=500,
            width=500,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(200,200,200,0.5)',
                tickformat="%m-%d",
                tickmode="array",
                tickvals=[date for date in time if date.weekday() == 0]
            ),
            yaxis=dict(
                zeroline=True,
                zerolinecolor='rgba(200,200,200,0.5)',
                showgrid=True,
                automargin=True,
                gridcolor='rgba(200,200,200,0.5)',
                range=config["y_range"],
                tickformat=config["format"]
            )
        )

        # Save images to OUTPUT_FOLDER
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        _filepath = os.path.join(OUTPUT_FOLDER, f"{_habit}.png")
        fig.write_image(_filepath)
    return config, df_filtered, fig, habits, opts, time, trend


@app.cell
def __(OUTPUT_FOLDER, habits, os):
    ### Put tiles into HTML

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        .grid-container {
          display: grid;
          grid-template-columns: repeat(4, 1fr); /* 4 columns */
          gap: 10px;
        }
        .grid-item img {
          width: 100%;
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 5px;
        }
        .grid-item {
          text-align: center;
          font-family: Arial, sans-serif;
          font-size: 14px;
        }
      </style>
    </head>
    <body>
      <div class="grid-container">
    """

    # Add each habit's tile to the HTML
    for _habit in habits:
        html_content += f"""
        <div class="grid-item">
          <img src="{_habit}.png" alt="{_habit}">
        </div>
        """

    # Close the grid and HTML
    html_content += """
      </div>
    </body>
    </html>
    """

    # Save the HTML file to OUTPUT_FOLDER
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    html_file = os.path.join(OUTPUT_FOLDER, "dashboard.html")
    with open(html_file, "w") as file:
        file.write(html_content)
    return file, html_content, html_file


@app.cell
def __():
    # Delete png files from OUTPUT_FOLDER
    # for _habit in habits:
    #     _filepath = os.path.join(OUTPUT_FOLDER, f"{_habit}.png")
    #     if os.path.exists(_filepath):
    #         os.remove(_filepath)
    #         print(f"Deleted: {_filepath}")
    #     else:
    #         print(f"File not found: {_filepath}")
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
