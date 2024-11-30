import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium", layout_file="layouts/app.grid.json")


@app.cell
def __():
    import os
    import pandas as pd

    from dotenv import load_dotenv
    return load_dotenv, os, pd


@app.cell
def __(load_dotenv, os, pd):
    load_dotenv()
    file_path = os.getenv('HABITS_PATH')
    pd.read_csv(file_path)
    return (file_path,)


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
