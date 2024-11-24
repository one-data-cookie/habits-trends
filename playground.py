import marimo

__generated_with = "0.9.23"
app = marimo.App(width="medium")


@app.cell
def __():
    import pandas as pd

    df = pd.read_csv('AwesomeHabits.csv')
    df
    return df, pd


@app.cell
def __():
    import marimo as mo
    return (mo,)


@app.cell
def __(df, mo):
    _df = mo.sql(
        f"""
        select * 
        from df
        limit 10
        """
    )
    return


if __name__ == "__main__":
    app.run()
