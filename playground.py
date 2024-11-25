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
                Quantity::float as quantity
            from df
            where Name = 'Sleep'
        )

        select
            day,
            avg(quantity) over (
                order by day
                range between interval 30 day preceding and current row    
            )/60 as moving_avg_30d
        from prep
        order by day
        """
    )
    return (sql,)


@app.cell
def __(sql):
    import matplotlib.pyplot as plt

    plt.plot(sql['day'], sql['moving_avg_30d'])
    plt.xlabel('Day')
    plt.ylabel('30d Moving Avg (hours)')
    plt.title('Average Sleep')
    plt.gca()
    return (plt,)


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
