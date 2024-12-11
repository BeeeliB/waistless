import streamlit as st
import pandas as pd
import plotly.express as px  # Using Plotly for enhanced charting
from datetime import datetime

# Initialize session state keys
if "roommates" not in st.session_state: #check if roommates exists in session state
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]  #initialize with example roommates
if "expenses" not in st.session_state: #check if expenses exist in session state
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]} #initialize expenses (per roommate)
if "purchases" not in st.session_state: #check if purchases exist in session state
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]} #initialize purchases (per roommate)
if "consumed" not in st.session_state:#check if consumed goods exist in session state
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]} #initialize consumtion (per roommate)


# Overview page function
def overview_page():
    st.title("Flatmate Overview") #set page title

    # Chart 1: Total Expenses by Flatmate (Bar Chart)
    st.subheader("1. Total Expenses by Flatmate") #add subheader for chart
    expense_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"]) #convert expenses to dataframe
    if not expense_df.empty: #check if data available
        fig1 = px.bar(expense_df, x="Roommate", y="Total Expenses (CHF)", title="Total Expenses by Flatmate") #create bar chart
        st.plotly_chart(fig1) #display chart
    else:
        st.write("No expense data available.") #if no data -> display message


    # Chart 2: Monthly Purchases by Flatmate (Line Chart)
    st.subheader("2. Monthly Purchases by Flatmate") #add subheader for chart

    # Step 1: Collect purchase data
    purchases_data = [] #initialize empty list to store data of purchases
    for mate in st.session_state["roommates"]: #go over each roommate
        purchases_data.extend([ #extend data list with purchase details
            {
                "Roommate": mate,
                "Date": purchase.get("Date", "1900-01-01"),  #get date or use default
                "Total": purchase.get("Price", 0)           # get price or use 0
            }
            for purchase in st.session_state["purchases"][mate] #loop through roomatess purchases
        ])

    # Step 2: Create DataFrame
    purchases_df = pd.DataFrame(purchases_data) #convert purchase data into dataframe

    if not purchases_df.empty: #check if data available
        # Step 3: Convert Date to datetime
        purchases_df["Date"] = pd.to_datetime(purchases_df["Date"], errors="coerce")  # convert values in "date" to datetime ebjects 
    
        
        # Step 4: Filter for the current month and year
        current_month = datetime.now().month #get month
        current_year = datetime.now().year #get year
        purchases_df = purchases_df[ #filter dataframe for current month & year
            (purchases_df["Date"].dt.month == current_month) & 
            (purchases_df["Date"].dt.year == current_year)
        ]

        # Step 5: Group data by date date and roommate
        daily_purchases = purchases_df.groupby([purchases_df["Date"].dt.date, "Roommate"])["Total"].sum().unstack(fill_value=0)

        # Step 6: reshape for plotly (Convert to long format for Plotly)
        daily_purchases_long = daily_purchases.reset_index().melt(
            id_vars=["Date"], 
            var_name="Roommate", 
            value_name="Total Purchases (CHF)" #reshape dataframe for line chart
        )

        

        # Step 7: Plot
        if not daily_purchases_long.empty: #check if reshaped data available
            fig2 = px.line(
                daily_purchases_long,
                x="Date",
                y="Total Purchases (CHF)",
                color="Roommate",
                title=f"Daily Purchases by Flatmate - {datetime.now().strftime('%B %Y')}",
                markers=True,  #add markers -> better visibility
            )
            st.plotly_chart(fig2) #show line chart
        else:
            st.write("No data available for the current month.") #message if no data available
    else:
        st.write("No purchases data available.") #message if no purchase data




    # Chart 3: Total Consumption by Flatmate (Pie Chart)
    st.subheader("3. Total Consumption by Flatmate") #add a subheader for chart
    consumption_data = {mate: sum([item["Price"] for item in st.session_state["consumed"][mate]]) #calculate consumtion (per roommmate)
                        for mate in st.session_state["roommates"]}
    consumption_df = pd.DataFrame(list(consumption_data.items()), columns=["Roommate", "Total Consumption (CHF)"]) #convert to dataframe
    if not consumption_df.empty: #check if data available
        fig3 = px.pie(consumption_df, names="Roommate", values="Total Consumption (CHF)",
                      title="Total Consumption by Flatmate", hole=0.3,  #create pie chart
                      color_discrete_sequence=px.colors.qualitative.Pastel) #use pastel colors
        fig3.update_traces(textinfo='percent+label', hoverinfo='label+percent+value') #update chart labels
        st.plotly_chart(fig3) #show pie chart
    else:
        st.write("No consumption data available.") #message if no consumtion data

    # Chart 4: Inventory Summary (Stacked Bar Chart)
    st.subheader("4. Inventory Value by Roommate") #add subhead for chart
    inventory_data = [] #initialize empty list for inventory data
    for mate in st.session_state["roommates"]: #go trough each roommate
        for purchase in st.session_state["purchases"][mate]: #loop throiugh roommates purchases
            inventory_data.append({"Roommate": mate, "Product": purchase["Product"], "Price": purchase["Price"]}) #add product details
    inventory_df = pd.DataFrame(inventory_data) #convert inventory to dataframe
    if not inventory_df.empty: #check if data available
        inventory_summary = inventory_df.groupby(["Roommate", "Product"])["Price"].sum().unstack(fill_value=0) #groups databy roomate and product
        fig4 = px.bar(inventory_summary.reset_index(), 
                      x="Roommate", y=inventory_summary.columns, 
                      title="Inventory Value by Roommate", 
                      labels={"value": "Price (CHF)", "variable": "Product"}, 
                      barmode="stack") #create stacked bar chart
        st.plotly_chart(fig4) #show bar chart
    else:
        st.write("No inventory data available.") #message if there is no inventory

#call function to generate/display the page
overview_page()
