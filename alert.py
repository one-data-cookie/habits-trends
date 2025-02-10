import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def __():
    ### Import what's needed

    import matplotlib.pyplot as plt
    import marimo as mo
    import numpy as np
    import os
    import pandas as pd
    import plotly.graph_objects as go
    import polars as pl
    import smtplib

    from collections import Counter
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    from matplotlib.colors import Normalize, LinearSegmentedColormap
    from plotly.subplots import make_subplots
    from wordcloud import WordCloud

    load_dotenv()
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")
    HABITS_PATH = os.getenv("HABITS_PATH")
    START_TS = datetime.now()

    # Also print the time
    print(f"Started the script by importing at {START_TS}!")
    return (
        Counter,
        LinearSegmentedColormap,
        MIMEImage,
        MIMEMultipart,
        MIMEText,
        Normalize,
        OUTPUT_FOLDER,
        HABITS_PATH,
        START_TS,
        WordCloud,
        datetime,
        go,
        load_dotenv,
        make_subplots,
        mo,
        np,
        os,
        pd,
        pl,
        plt,
        smtplib,
        timedelta,
    )


@app.cell
def __(HABITS_PATH, START_TS, datetime, os, pd, timedelta):
    ### Load data

    # Get the file modification time
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(HABITS_PATH))

    # Calculate the start of the current week (Monday at midnight)
    start_of_week = START_TS - timedelta(days=START_TS.weekday())  # Get Monday
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)  # Set to midnight

    # Check if the file has been modified this week
    if file_mod_time < start_of_week:
        raise RuntimeError("The file has not been updated this week. Update the file and try again.")

    # Load data
    df = pd.read_csv(HABITS_PATH)
    df
    return df, file_mod_time, start_of_week


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
def __(df_clean, mo):
    df_moods = mo.sql(
        f"""
        -- Transform mood labels

        select
            Date as date,
            "Mood Labels" as mood_labels,
            "Mood Associations" as mood_assocs
        from df_clean
        where Name = 'Track mood'
        """
    )
    return (df_moods,)


@app.cell
def __(Counter, OUTPUT_FOLDER, WordCloud, df_filter_lw, df_moods, os, plt):
    ### Create mood wordlouds

    # Filter the df
    df_moods_lw = df_filter_lw(df_moods)

    # Create word cloud configurations
    _configs = [
        {
            "data_column": "mood_labels",
            "title": "Mood Labels",
            "colormap": "viridis",
            "subplot_pos": 1,
        },
        {
            "data_column": "mood_assocs",
            "title": "Mood Associations",
            "colormap": "cividis",
            "subplot_pos": 2,
        },
    ]

    # Display both word clouds
    plt.figure(figsize=(16, 12))

    for _config in _configs:
        # Split and count words
        words = df_moods_lw[_config["data_column"]].fillna("").str.split(", ").explode().tolist()
        word_counts = Counter(words)

        # Create word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            colormap=_config["colormap"],
            contour_width=1,
            contour_color="black",
            prefer_horizontal=1.0,
            scale=10,
            margin=10,
        ).generate_from_frequencies(word_counts)

        # Plot
        plt.subplot(1, 2, _config["subplot_pos"])
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")

    # Save images to OUTPUT_FOLDER
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    _filepath = os.path.join(OUTPUT_FOLDER, "wordclouds.png")
    plt.savefig(_filepath, dpi=300, bbox_inches="tight")
    print(f"Wordclouds saved to: {_filepath}!")
    return df_moods_lw, word_counts, wordcloud, words


@app.cell
def __(OUTPUT_FOLDER, df_weekly, go, make_subplots, os, pl):
    ### Build a tiles
    habits = sorted(df_weekly["name"].unique(), reverse=True)

    for _habit in habits:
        # Prep data
        df_filtered = df_weekly.filter(pl.col("name") == _habit)
        trend = df_filtered["quantity_avg"].to_list()[-8:]
        time = df_filtered["week"].to_list()[-8:]

        # Create a 2x1 grid with different subplot types
        fig = make_subplots(
            rows=2,
            cols=1,
            specs=[[{"type": "indicator"}], [{"type": "xy"}]],
            row_heights=[0.5, 0.5],
            vertical_spacing=0.1,
        )

        # Create a configuration dictionary and assign
        _opts = {
            "Track": {"format": ".1f", "delta_relative": True, "y_range": None},
            "Default": {
                "format": ".0%",
                "delta_relative": False,
                "y_range": [-0.1, 1.1],
            },
        }
        _configs = _opts.get(_habit.split()[0], _opts["Default"])

        # Add the big number with delta in the top cell
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=trend[-1],
                number={"valueformat": _configs["format"]},
                delta={
                    "reference": trend[-2],
                    "relative": _configs["delta_relative"],
                    "valueformat": ".0%",
                    "increasing": {"color": "red"}
                                  if _habit.startswith("No") or _habit.endswith("screen")
                                  else None,
                    "decreasing": {"color": "green"}
                                  if _habit.startswith("No") or _habit.endswith("screen")
                                  else None,
                },
            ),
            row=1,
            col=1,
        )

        # Add the average line in the bottom cell first
        avg_value = sum(trend) / len(trend)
        fig.add_trace(
            go.Scatter(
                x=time,
                y=[avg_value] * len(time),  # Repeat avg for each x
                mode="lines",
                name="Average",
                line=dict(color="red", dash="dash"),
            ),
            row=2,
            col=1,
        )

        # Add the line chart in the bottom cell
        fig.add_trace(
            go.Scatter(
                x=time,
                y=trend,
                mode="lines+markers",
                name="Trendline",
                line=dict(color="blue"),
                marker=dict(size=8),
            ),
            row=2,
            col=1,
        )

        # Update layout
        fig.update_layout(
            title={
                "text": f"<u>{_habit}</u>",
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": {"size": 40},
            },
            height=500,
            width=500,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(200,200,200,0.5)",
                tickformat="%m-%d",
                tickmode="array",
                tickvals=[date for date in time if date.weekday() == 0],
            ),
            yaxis=dict(
                zeroline=True,
                zerolinecolor="rgba(200,200,200,0.5)",
                showgrid=True,
                automargin=True,
                gridcolor="rgba(200,200,200,0.5)",
                range=_configs["y_range"],
                tickformat=_configs["format"],
            ),
        )

        # Save images to OUTPUT_FOLDER
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        _filepath = os.path.join(OUTPUT_FOLDER, f"{_habit}.png")
        fig.write_image(_filepath)
        print(f"Habit tile saved to: {_filepath}!")
    return avg_value, df_filtered, fig, habits, time, trend


@app.cell
def __(START_TS, datetime, pl, timedelta):
    ### Create function for returning just last week

    def df_filter_lw(df):
        # Prep dates
        lw_end = datetime.combine(START_TS - timedelta(days=START_TS.weekday() + 1), datetime.max.time())
        lw_start = datetime.combine(lw_end - timedelta(days=6), datetime.min.time())

        # Filter and transform the DataFrame
        df_lw = df.filter((pl.col("date") >= lw_start) & (pl.col("date") <= lw_end))
        df_lw = df_lw.to_pandas()
        return df_lw

    return (df_filter_lw,)


@app.cell
def __(
    LinearSegmentedColormap,
    Normalize,
    OUTPUT_FOLDER,
    df_daily,
    df_filter_lw,
    np,
    os,
    plt,
):
    ### Create heatmap

    # Filter the df
    df_daily_lw = df_filter_lw(df_daily)

    # Pivot the data to create a matrix of `quantity` values with `day` as columns and `name` as rows
    heatmap_data = df_daily_lw.pivot_table(
        index="name", columns="day", values="quantity", aggfunc="mean"
    ).fillna(0)

    # Sort days in week order
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    heatmap_data = heatmap_data.reindex(columns=day_order)

    # Sort metrics in decreasing alphabetical order
    heatmap_data = heatmap_data.sort_index(ascending=False)

    # Prep the data
    metrics = heatmap_data.index.tolist()
    days = heatmap_data.columns.tolist()
    data_matrix = heatmap_data.to_numpy()

    # Adjust the transparency (alpha) of the colormap
    base_cmap = plt.colormaps.get_cmap("RdYlGn")
    colors = base_cmap(np.linspace(0, 1, 256))  # Extract original colours
    colors[:, -1] = 0.5  # Set alpha transparency to 50%
    cmap = LinearSegmentedColormap.from_list("PastelRdYlGn", colors)

    # Create the heatmap
    _fig, _ax = plt.subplots(figsize=(12, 8))

    # Normalize the data relative to each row
    for i, row in enumerate(data_matrix):
        # Only normalize for "track" metrics
        vmin, vmax = (
            (np.min(row), np.max(row))
            if metrics[i].split()[0] == "Track"
            else (0, 1)
        )
        norm = Normalize(vmin=vmin, vmax=vmax)

        for j, value in enumerate(row):
            # Invert colour for some metrics
            value_adj = (
                vmax + vmin - value
                if metrics[i].startswith("No") or metrics[i].endswith("screen")
                else value
            )
            color = cmap(norm(value_adj)) if vmax > 0 else (1, 1, 1, 0.5)
            _ax.add_patch(plt.Rectangle((j, i), 1, 1, color=color))
            _ax.text(
                j + 0.5,
                i + 0.5,
                f"{value:.1f}",
                ha="center",
                va="center",
                color="black",
            )

    # Configure axis labels and ticks
    _ax.set_xticks(np.arange(len(days)) + 0.5)
    _ax.set_yticks(np.arange(len(metrics)) + 0.5)
    _ax.set_xticklabels(days)
    _ax.set_yticklabels(metrics)
    _ax.set_xlim(0, len(days))
    _ax.set_ylim(0, len(metrics))
    _ax.invert_yaxis()

    # Add grid lines
    _ax.set_xticks(np.arange(len(days)), minor=True)
    _ax.set_yticks(np.arange(len(metrics)), minor=True)
    _ax.grid(which="minor", color="black", linestyle="-", linewidth=0.5)
    _ax.tick_params(which="minor", size=0)

    # Save images to OUTPUT_FOLDER
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    _filepath = os.path.join(OUTPUT_FOLDER, "heatmap.png")
    plt.savefig(_filepath, dpi=300, bbox_inches="tight")
    print(f"Heatmap saved to: {_filepath}!")
    return (
        base_cmap,
        cmap,
        color,
        colors,
        data_matrix,
        day_order,
        days,
        df_daily_lw,
        heatmap_data,
        i,
        j,
        metrics,
        norm,
        row,
        value,
        value_adj,
        vmax,
        vmin,
    )


@app.cell
def __(OUTPUT_FOLDER, habits, os):
    ### Stitch content together into html

    # Base HTML content
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
          font-family: "Helvetica", sans-serif;
          font-size: 14px;
        }
        h1 {
          text-align: center;
          font-family: "Helvetica", sans-serif;
          font-size: 24px;
        }
        h2 {
          text-align: center;
          font-family: "Helvetica", sans-serif;
          font-size: 20px;
        }
      </style>
    </head>
    <body>
    """

    # Add wordclouds section
    html_content += f"""
      <h2>Mood Wordclouds</h2>
      <div style="text-align: center;">
        <img src="wordclouds.png" alt="Wordclouds" style="max-width: 800px; padding: 5px;">
      </div>
      <br>
    """

    # Add tiles section
    html_content += """
      <h2>Habit Tiles</h2>
      <table style="width: auto; max-width: 800px; margin: auto; border-collapse: collapse; text-align: center;">
        <tr>
    """

    # Add each habit's tile to the HTML
    for index, _habit in enumerate(habits):
        html_content += f"""
          <td>
            <img src="{_habit}.png" alt="{_habit}" style="max-width: 200px; border: 1px solid #ddd; border-radius: 1px;">
          </td>
        """
        # Close the row every 4 items
        if (index + 1) % 4 == 0:
            html_content += "</tr><tr>"

    # Close the last row and table
    html_content += """
        </tr>
      </table>
      <br>
    """

    # Add heatmap section
    html_content += f"""
      <h2>Habit Heatmap</h2>
      <div style="text-align: center;">
        <img src="heatmap.png" alt="Heatmap" style="max-width: 800px; padding: 5px;">
      </div>
    """

    # Close the HTML
    html_content += """
    </body>
    </html>
    """

    # Save the HTML file in the output folder
    html_file = os.path.join(OUTPUT_FOLDER, "dashboard.html")
    with open(html_file, "w") as file:
        file.write(html_content)

    print(f"HTML file saved to: {html_file}")
    return file, html_content, html_file, index


@app.cell
def __(
    MIMEImage,
    MIMEMultipart,
    MIMEText,
    OUTPUT_FOLDER,
    habits,
    html_content,
    os,
    smtplib,
):
    ### Send the email

    # Email details
    email = os.getenv("EMAIL")
    subject = "How was last week?"

    # Create the email
    message = MIMEMultipart("alternative")
    message["From"] = email
    message["To"] = email
    message["Subject"] = subject

    # Attach the HTML content
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    # Attach images used in the HTML
    image_files = [
        f"{OUTPUT_FOLDER}/wordclouds.png",
        f"{OUTPUT_FOLDER}/heatmap.png",
    ] + [f"{OUTPUT_FOLDER}/{habit}.png" for habit in habits]  # Add habit tiles

    # Set up "cid"
    for _idx, image_path in enumerate(image_files):
        with open(image_path, "rb") as img:
            img_part = MIMEImage(img.read())
            img_part.add_header("Content-ID", f"<image{_idx+1}>")  # Match the "cid" in HTML
            img_part.add_header("Content-Disposition", "inline")  # Explicitly set as inline
            message.attach(img_part)

    # Ensure HTML content references the correct "cid"
    html_content_cid = html_content
    html_content_cid = html_content.replace(f"wordclouds.png", "cid:image1")
    html_content_cid = html_content_cid.replace(f"heatmap.png", "cid:image2")
    for _idx, habit in enumerate(habits):
        html_content_cid = html_content_cid.replace(
            f"{habit}.png", f"cid:image{_idx+3}"
        )

    # Update the HTML part with the modified content
    html_part.set_payload(html_content_cid)

    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, os.getenv("PASSWORD"))
            server.sendmail(email, email, message.as_string())
        print("Email with dashboard sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

    # Clean up all files in OUTPUT_FOLDER after the attempt to send
    if os.path.exists(OUTPUT_FOLDER):
        for _filename in os.listdir(OUTPUT_FOLDER):
            _filepath = os.path.join(OUTPUT_FOLDER, _filename)
            if os.path.isfile(_filepath):
                os.remove(_filepath)
        print(f"Deleted all files from {OUTPUT_FOLDER}!")
    else:
        print(f"Folder not found: {OUTPUT_FOLDER}")
    return (
        email,
        habit,
        html_content_cid,
        html_part,
        image_files,
        image_path,
        img,
        img_part,
        message,
        server,
        subject,
    )


if __name__ == "__main__":
    app.run()
