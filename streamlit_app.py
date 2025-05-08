import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title='Prognoser på svensk ekonomi', page_icon=':bar_chart:')

@st.cache_data
def load_forecast_from_blocked_excel():
    df_full = pd.read_excel("Prognoser.xlsx", sheet_name="Data", header=None)

    cols_per_block = 5
    num_blocks = (df_full.shape[1] - 1) // cols_per_block
    all_blocks = []

    for block in range(num_blocks):
        start_col = 1 + block * cols_per_block
        end_col = start_col + cols_per_block

        myndighet = str(df_full.iloc[0, start_col]).strip()
        årtal = df_full.iloc[1, start_col:end_col].astype(str).tolist()

        indikatorer = df_full.iloc[2:, 0].reset_index(drop=True)
        värden = df_full.iloc[2:, start_col:end_col].reset_index(drop=True)
        värden.columns = årtal

        df_block = pd.melt(
            pd.concat([indikatorer, värden], axis=1, ignore_index=True),
            id_vars=0,
            var_name="År",
            value_name="Värde"
        )
        df_block.columns = ["Indikator", "År", "Värde"]
        df_block["Myndighet"] = myndighet
        df_block["År"] = pd.to_numeric(df_block["År"], errors='coerce')
        df_block = df_block.dropna(subset=["År", "Värde", "Indikator"])

        all_blocks.append(df_block)

    return pd.concat(all_blocks, ignore_index=True)

# Läs in data
df = load_forecast_from_blocked_excel()

# Huvudrubrik
st.title(":bar_chart: Prognoser på svensk ekonomi")
st.markdown("Jämför ekonomiska prognoser från olika svenska myndigheter och propositioner.")

# Välj indikator
indikatorer = sorted(df["Indikator"].unique())
vald_indikator = st.selectbox("Välj indikator att visa", indikatorer)

# Filtrera på indikator
df_filtered = df[df["Indikator"] == vald_indikator]

# Välj myndigheter
myndigheter = sorted(df_filtered["Myndighet"].unique())
valda_myndigheter = st.multiselect("Välj prognosmakare", myndigheter, default=myndigheter)

df_filtered = df_filtered[df_filtered["Myndighet"].isin(valda_myndigheter)]

# Årsintervall
år_min, år_max = int(df_filtered["År"].min()), int(df_filtered["År"].max())
från_år, till_år = st.slider("Välj årintervall", år_min, år_max, (år_min, år_max))

df_filtered = df_filtered[(df_filtered["År"] >= från_år) & (df_filtered["År"] <= till_år)]

# Interaktiv Altair-graf
st.subheader(f"{vald_indikator} ({från_år}–{till_år})")

# Y-axeljustering
y_min = st.number_input("Y-axel: minimum", value=float(df_filtered["Värde"].min()), step=0.1)
y_max = st.number_input("Y-axel: maximum", value=float(df_filtered["Värde"].max()), step=0.1)

chart_df = df_filtered.copy()
chart_df["År"] = chart_df["År"].astype(str)  # för att visas som etiketter

chart = alt.Chart(chart_df).mark_line(point=True).encode(
    x=alt.X("År:O", title="År"),
    y=alt.Y("Värde:Q", title=vald_indikator, scale=alt.Scale(domain=[y_min, y_max])),
    color="Myndighet:N",
    tooltip=["Myndighet", "År", "Värde"]
).properties(
    width=700,
    height=400,
    title=f"{vald_indikator} från olika prognosmakare"
).interactive()

st.altair_chart(chart, use_container_width=True)

# Nyckeltalsjämförelse
st.subheader(f"Utveckling mellan {från_år} och {till_år}")
cols = st.columns(len(valda_myndigheter))

for i, myndighet in enumerate(valda_myndigheter):
    df_start = df_filtered[(df_filtered["År"] == från_år) & (df_filtered["Myndighet"] == myndighet)]
    df_end = df_filtered[(df_filtered["År"] == till_år) & (df_filtered["Myndighet"] == myndighet)]

    if not df_start.empty and not df_end.empty:
        start = df_start["Värde"].values[0]
        end = df_end["Värde"].values[0]
        delta = end - start
        delta_pct = (delta / start * 100) if start != 0 else 0
        with cols[i]:
            st.metric(label=myndighet, value=f"{end:.2f}", delta=f"{delta_pct:.1f}%")

