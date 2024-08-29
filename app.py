import streamlit as st

#-- PAGE SETUP -- 
moagem_page = st.Page(
    page="views/moagem.py",
    title="Moagem",
    icon=":material/factory:",
    default=True
)

acucar_page = st.Page(

    page="views/acucar.py",
    title="Açúcar",
    icon=":material/ac_unit:",
)

etanol_page = st.Page(

    page="views/etanol.py",
    title="Etanol",
    icon=":material/water_drop:",
)


#-- NAVIGATION SETUP --
pg = st.navigation(pages=[moagem_page,acucar_page,etanol_page])

#--ON ALL PAGES--
st.logo("assets\ARALCO.png")
#st.sidebar.text("Em desenvolvimento")

#-- RUN NAVIGATION --
pg.run()