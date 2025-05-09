import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title='Prognoser på svensk ekonomi', page_icon=':bar_chart:')

@st.cache_data
def load_forecast_from_blocked_excel():
        
    df  = pd.read_excel("Prognoser.xlsx", sheet_name="Data", header=[0,1], index_col=0).T
    #Swap index and columns
    df = df.reset_index()
    df = df.loc[:, ~df.columns.get_level_values(0).isna()]
    df = df.rename(columns={"Mydighet & Datum": "Myndighet_prognosdatum", "År ": "År"})

    return df

def my_plotter(df, target_variable:str='Hushållens konsumtion'):
    y_min = df[target_variable].min()
    y_max = df[target_variable].max()
    margin = (y_max - y_min) * 0.05 if y_max > y_min else 1
    domain = [y_min - margin, y_max + margin]
        
    chart = alt.Chart(df.loc[:,['Myndighet_prognosdatum','År',target_variable]]).mark_line().encode(
        y=alt.Y(f'{target_variable}:Q',scale=alt.Scale(domain=domain, nice=False)),
        x=alt.X('År:O'),
        color=alt.Color('Myndighet_prognosdatum')
    )
    # legend in bottom 2 rows
    chart = chart.configure_legend(
        orient='bottom',
        title=None,
        labelLimit=100,
        columns=6
    ).properties(
    width=900,
    height=600,
    title=f"{vald_indikator} från olika prognosmakare"
    ).interactive()

    return chart


# Läs in data
df = load_forecast_from_blocked_excel()

# Huvudrubrik
st.title(":bar_chart: Prognoser på svensk ekonomi")
st.markdown("Jämför ekonomiska prognoser från olika svenska myndigheter och propositioner.")

# Välj indikator
# Strip column names
df.columns = df.columns.str.strip()
df.columns = df.columns.str.replace(r"%", "procentuell", regex=False).str.replace(r".", "_", regex=False)
indikatorer = sorted(df.columns.unique())
remove_cols = ["Myndighet_prognosdatum", "År"] # Lägg till fler kolumner att ta bort här om vi vill!
indikatorer = [col for col in indikatorer if col not in remove_cols]
vald_indikator = st.selectbox("Välj indikator att visa", indikatorer)

# Filtrera på indikator
df_filtered = df.loc[:,["Myndighet_prognosdatum","År"] + [vald_indikator]]

# Drop rows with NaN values
df_filtered = df_filtered.dropna(subset=[vald_indikator])

# Välj myndigheter
myndigheter = sorted(df_filtered["Myndighet_prognosdatum"].unique())
valda_myndigheter = st.multiselect("Välj prognosmakare", myndigheter, default=myndigheter)

df_filtered = df_filtered[df_filtered["Myndighet_prognosdatum"].isin(valda_myndigheter)]

# Årsintervall
år_min, år_max = int(df_filtered["År"].min()), int(df_filtered["År"].max())
från_år, till_år = st.slider("Välj årintervall", år_min, år_max, (år_min, år_max))

df_filtered = df_filtered[(df_filtered["År"] >= från_år) & (df_filtered["År"] <= till_år)]

# Interaktiv Altair-graf
st.subheader(f"{vald_indikator} ({från_år}–{till_år})")

# Y-axeljustering
#y_min = st.number_input("Y-axel: minimum", value=float(df_filtered["Värde"].min()), step=0.1)
#y_max = st.number_input("Y-axel: maximum", value=float(df_filtered["Värde"].max()), step=0.1)

chart_df = df_filtered.copy()
chart = my_plotter(chart_df, target_variable=vald_indikator)

st.altair_chart(chart, use_container_width=True)

# Nyckeltalsjämförelse
st.subheader(f"Nyckeltalsjämförelse ({från_år}–{till_år})")
cols = st.columns(len(valda_myndigheter))

# Visa i två rader om fler än 5 myndigheter
max_per_row = 5
num_cols = min(len(valda_myndigheter), max_per_row)
num_rows = (len(valda_myndigheter) + max_per_row - 1) // max_per_row

for row in range(num_rows):
    start_idx = row * max_per_row
    end_idx = min(start_idx + max_per_row, len(valda_myndigheter))
    cols = st.columns(end_idx - start_idx)
    for i, myndighet in enumerate(valda_myndigheter[start_idx:end_idx]):
        df_start = df_filtered[(df_filtered["År"] == från_år) & (df_filtered["Myndighet_prognosdatum"] == myndighet)]
        df_end = df_filtered[(df_filtered["År"] == till_år) & (df_filtered["Myndighet_prognosdatum"] == myndighet)]

        if not df_start.empty and not df_end.empty:
            start = df_start[vald_indikator].values[0]
            end = df_end[vald_indikator].values[0]
            delta = end - start
            delta_pct = (delta / start * 100) if start != 0 else 0
            with cols[i]:
                st.metric(label=myndighet, value=f"{end:.2f}", delta=f"{delta_pct:.2f}%")
