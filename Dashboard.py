# streamlit run Multi_touch_U.py
import streamlit as st
import plotly_express as px
import pandas as pd
import warnings
import numpy as np
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

st.set_page_config(
    page_title="Production Analysis",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

#-------------------------------------------------------------------------------------------
# Filtering the data for dashboard
#-------------------------------------------------------------------------------------------
Columns = ['Index','Encounter #','DOS','Total Balance','Bucket','Activity Date','Action Code','Associate','Supervisor',
            'Billed Amount','Index_val','Prod_Year','Prod_Month','Total_Touch','Enc','Next_Activity',
            'Date_Diff','Adj Amt','Liq_Category','Pay Amt','Encounter','Balance_worked',
            'Resolved_Encounter','Resolved','Fully_Adjusted','Disposition_Code_Category','Activity_Year',
            'Activity_Month','Prac_Type','Inventory_type','Tasked_Status']
@st.cache_data

def load_data():
    df = pd.read_csv(r"data_model_production.csv", 
                     usecols=Columns, low_memory=False)
    df['Tasked_Status'].fillna("Not Taked", inplace=True)
    df['Total_Bucket']=df['Total_Touch'].apply(lambda x: "0-3" if x<=3 else '4-5' if x<=5 else '5+') 
    return df
raw = load_data()
def Prod_count(df):
    dataP = df.groupby(by=['Activity_Month','Activity_Year','Inventory_type'])['Index_val'].nunique().reset_index()
    dataP.rename(columns={'Index_val':'Production_count'},inplace = True)
    dataP.sort_values(by =['Activity_Year','Activity_Month'], ascending=True, inplace=True )
    dataP["Year_Month"] = dataP.Activity_Year.astype(str)+"-"+dataP.Activity_Month.astype(str)
    return dataP
def Prod_bal(df):
    dataB = df.groupby(by=['Activity_Month','Activity_Year','Inventory_type'])['Balance_worked'].sum().reset_index()
    dataB.sort_values(by =['Activity_Year','Activity_Month'], ascending=True, inplace=True )
    dataB["Year_Month"] = dataB.Activity_Year.astype(str)+"-"+dataB.Activity_Month.astype(str)
    return dataB
def Resolution(df):
    dataR = pd.pivot_table(df,
                        index =['Activity_Year','Activity_Month','Prac_Type','Inventory_type','Tasked_Status'],
                        values = ['Encounter','Balance_worked','Pay Amt','Adj Amt'],
                        aggfunc = {'Encounter':'count','Balance_worked':'sum','Pay Amt':'sum','Adj Amt':'sum'}).reset_index()
    dataR['Activity_Year']=dataR['Activity_Year'].astype(str)
    return(dataR)
def AR_res(df):
    Overall_LN = df.groupby(by=['Activity_Year','Activity_Month','Prac_Type'])[['Adj Amt','Balance_worked','Pay Amt']].sum().reset_index()
    Overall_LN["Resolution%"] = (((Overall_LN['Pay Amt']+Overall_LN['Adj Amt'])/Overall_LN['Balance_worked'])*100).round(1)
    Overall_R = df.groupby(by=['Activity_Year','Activity_Month'])[['Adj Amt','Balance_worked','Pay Amt']].sum().reset_index()
    Overall_R["Resolution%"] = (((Overall_R['Pay Amt']+Overall_R['Adj Amt'])/Overall_R['Balance_worked'])*100).round(1)
    df1 = pd.concat([Overall_R,Overall_LN], axis = 0)
    df1['Prac_Type'].fillna("Overall", inplace = True)
    return df1
def Res_Adj(df):
    Resolved = df[(df['Resolved']=='Y')& (df['Fully_Adjusted'].notna())]
    Res_Adj_L = Resolved.groupby(by=['Activity_Year','Activity_Month','Prac_Type'])['Adj Amt'].sum().reset_index()
    Res_Adj_O = Resolved.groupby(by=['Activity_Year','Activity_Month'])['Adj Amt'].sum().reset_index()
    df1 = pd.concat([Res_Adj_O,Res_Adj_L], axis = 0)
    df1['Prac_Type'].fillna("Overall", inplace = True)
    df1['Activity_Year']=df1['Activity_Year'].astype(str)
    df1['u'] =  df1['Activity_Year']+df1['Activity_Month'].astype(str)+df1['Prac_Type']

    Res_Bal_L = df.groupby(by=['Activity_Month','Activity_Year','Prac_Type'])['Balance_worked'].sum().reset_index()
    Res_Bal_O = df.groupby(by=['Activity_Month','Activity_Year'])['Balance_worked'].sum().reset_index()
    df2 = pd.concat([Res_Bal_O,Res_Bal_L], axis = 0)
    df2['Prac_Type'].fillna("Overall", inplace = True)
    df2['Activity_Year']=df2['Activity_Year'].astype(str)
    df2['u'] =  df2['Activity_Year']+df2['Activity_Month'].astype(str)+df2['Prac_Type']
    
    dfA=df1.merge(df2[['u','Balance_worked']], how="left", on='u')
    dfA["Work Bal to Adj Ratio"] = ((dfA['Adj Amt']/dfA['Balance_worked'])*100).round(2)
    dfA.drop(columns = 'u', inplace = True)
    dfA = dfA.reindex(['Activity_Year','Activity_Month','Prac_Type','Balance_worked','Adj Amt','Work Bal to Adj Ratio'], axis=1)
    return dfA
#-------------------------------------------------------------------------------------------
# Creating the side Bar for data filteration and summary
#-------------------------------------------------------------------------------------------
with st.sidebar:
    st.title(" :bar_chart: Production Analysis")
    st.text ("Please select the year and month \nyou want to view the analysis")
    year = st.multiselect(label="Year",options=raw.Activity_Year.unique())
    month = st.multiselect(label="Month",options=raw.Activity_Month.unique())
    if st.button("Clear Cache"):
        st.cache_data.clear()  # For caching data
        st.cache_resource.clear()  # For caching resources
        
if not year and month:
    st.warning("Please enter the Year to choose month of the Year")
else:
    filtered_df = raw.copy()

    # Filter the dataframe based on selections
    if year:
        filtered_df = filtered_df[filtered_df.Activity_Year.isin(year)]
    if month:
        filtered_df = filtered_df[filtered_df.Activity_Month.isin(month)]
    if year and month:
        filtered_df = filtered_df[filtered_df.Activity_Year.isin(year) & filtered_df.Activity_Month.isin(month)]
#-------------------------------------------------------------------------------------------
# Plotting and placing the charts and graphs on the Dashboard
#-------------------------------------------------------------------------------------------
col1,col2 = st.columns(2)

###################---Production by count---###################
with col1:
    data_P = Prod_count(filtered_df) 
    fig1 = px.bar(
        data_frame=data_P, 
        x="Year_Month", y='Production_count',
        title = "Production count by Year-Month",
        labels={'Year_Month':'Year-Month','Production_count':'Production count'},
        color='Inventory_type'
    )
    fig1.update_layout(margin=dict(l=20, r=20, t=90, b=10))
    st.plotly_chart(fig1, use_container_width = True)

###################---Production by Worked Balance---###################
with col2:
    data_B = Prod_bal(filtered_df)
    fig2 = px.bar(
        data_frame=data_B, x="Year_Month", y='Balance_worked',
        title = "Production count by Year-Month",
        labels={'Year_Month':'Year-Month','Balance_worked':'$ Worked'},
        color='Inventory_type'
    )
    fig2.update_layout(margin=dict(l=20, r=20, t=90, b=10))
    st.plotly_chart(fig2, use_container_width = True)

###################---TREE Map---###################
st.markdown("---")
data_M =filtered_df.groupby(by = ['Prac_Type','Inventory_type','Disposition_Code_Category','Action Code'])['Index_val'].nunique().reset_index()
fig3 = px.treemap(data_M,
                  title = "Production distribution by Practice - Disposition - Action", 
                  path=[px.Constant('Production'),'Prac_Type','Inventory_type','Disposition_Code_Category','Action Code'], 
                  values='Index_val',
                  color='Index_val',
                  labels = {'Index_val':'Production Count'}, template = "plotly_white")
fig3.update_layout(margin=dict(l=20, r=20, t=20, b=10))
st.plotly_chart(fig3,use_container_width = True)
st.markdown("---")

###################---creating function to return values for filter pivot---###################
def P_cat(): return 'Prac_Type' if st.session_state.P else None
def I_cat(): return 'Inventory_type' if st.session_state.I else None
def T_cat(): return 'Tasked_Status' if st.session_state.T else None

###################---Displaying the Table Data---###################
col1,col2,col3 = st.columns((3))
with col1:
    st.checkbox(label="Prac_Type",value =False, on_change = P_cat ,key="P")
with col2:
    st.checkbox(label ="Inventory_type", value =False, on_change = I_cat ,key="I")
with col3:
    st.checkbox(label ="Tasked_Status",value =False, on_change = T_cat ,key="T")
# Gather selected categories
selected_categories = [func() for func in [P_cat, I_cat, T_cat]]
# Filter out None values
selected_categories = [cat for cat in selected_categories if cat is not None]
# Check if any categories are selected
data_R = Resolution(filtered_df)
if selected_categories:
    Pvt = pd.pivot_table(
        data_R,
        index=selected_categories,
        values=['Balance_worked', 'Pay Amt', 'Adj Amt'],
        aggfunc='sum'
    )
    new_order = ['Balance_worked', 'Pay Amt', 'Adj Amt']
    Pvt = Pvt[new_order]
else:
    Pvt = pd.pivot_table(
        data_R,
        index='Activity_Year',
        values=['Balance_worked', 'Pay Amt', 'Adj Amt'],
        aggfunc='sum'
    )
    new_order = ['Balance_worked', 'Pay Amt', 'Adj Amt']
    Pvt = Pvt[new_order]
# Calculate Resolution
Pvt["Resolution %"] = (((Pvt['Pay Amt'] + Pvt['Adj Amt']) / Pvt['Balance_worked'].replace(0,1))*100).round(1)
# Display the pivot table
st.dataframe(Pvt)

# comparing the AR relolution
Overall_RLN = AR_res(filtered_df)
fig4 = px.line(Overall_RLN,
               title="Resolution Trends - Volume of worked AR resolved",
               x='Activity_Month',
               y='Resolution%',
               line_shape="spline", 
               color='Activity_Year',
               facet_col='Prac_Type',
               labels = {'Activity_Month':'Production Month'}, template = "ggplot2")
fig4.update_layout(margin=dict(l=20, r=20, t=50, b=10),
                   paper_bgcolor="plum",)
st.plotly_chart(fig4, use_container_width=True)

# Account fully adjusted volume

Adj_Overall = Res_Adj(filtered_df)
fig5_adj = px.bar(Adj_Overall, x='Activity_Month', 
                  title="No payment claim volume - This is the volume of claim which is resolved due to 100% adjustment",
                  y='Adj Amt',
                  facet_col='Prac_Type',
                  labels = {'Activity_Month':'Production Month'},
                  template = "plotly", barmode="group",
                  color = "Activity_Year")
fig5_adj.update_layout(margin=dict(l=20, r=20, t=50, b=10),paper_bgcolor="olive",)
st.plotly_chart(fig5_adj, use_container_width=True)
with st.expander("Claim with no payment (Adjustment to Work Balance Ratio)"):
        styled_df = Adj_Overall.style.apply(
            lambda x: ['background: gradient' if col == 'Work Bal to Adj Ratio' else '' for col in x.index],axis=1
            ).background_gradient(subset=['Work Bal to Adj Ratio'], cmap='Blues')
        st.write(styled_df)
        csv = Adj_Overall.to_csv(index = False).encode('utf-8')
        st.download_button("Download Data", data = csv, file_name = "Adj_to_Bill_Ratio.csv", mime = "text/csv",
                            help = 'Click here to download the data as a CSV file')

st.markdown("---")
# Supervisior analysis
sup = filtered_df.pivot_table(index = ['Prac_Type','Supervisor','Total_Touch'], 
                               values='Index_val', aggfunc= {'Index_val':'nunique'}).reset_index()
fig_sup = px.box(sup,title ="Average touch distribution by supervisor" , x='Total_Touch',y='Supervisor', color='Prac_Type', template='ggplot2')
fig_sup.update_layout(margin=dict(l=20, r=20, t=40, b=10),paper_bgcolor="turquoise")
st.plotly_chart(fig_sup, use_container_width=True)

# Associate analysis
Asc = filtered_df.pivot_table(index = ['Prac_Type','Associate','Total_Touch'], 
                               values='Index_val', aggfunc= {'Index_val':'nunique'}).reset_index()
# Asc = Asc.groupby(['Prac_Type', 'Associate']).agg(
#     Total_Touch=('Total_Touch', 'median'),
#     Index_val=('Index_val', 'sum')
# ).query('Total_Touch > 5').reset_index()
Asc = Asc[Asc['Total_Touch']>10]
fig_Asc = px.box(Asc,title ="Touch distribution by Associate on claim with gtr 10 touch" , y='Total_Touch',x='Associate', color='Prac_Type', template='ggplot2')
fig_Asc.update_layout(margin=dict(l=20, r=20, t=40, b=10),paper_bgcolor="turquoise")
st.plotly_chart(fig_Asc, use_container_width=True)
