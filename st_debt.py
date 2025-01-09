import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# Function Definitions
def calculate_remaining_balance(principal, annual_rate, months_elapsed, total_term):
    if annual_rate == 0:
        return principal * (1 - months_elapsed / total_term)
    monthly_payment, periodic_rate = calculate_monthly_payment(principal, annual_rate, total_term)
    remaining_balance = principal * (1 + periodic_rate) ** months_elapsed - \
                        (monthly_payment / periodic_rate) * ((1 + periodic_rate) ** months_elapsed - 1)
    return remaining_balance

def calculate_monthly_payment(principal, annual_rate, months):
    if annual_rate == 0:
        return principal / months, 0
    effective_rate = (1 + (annual_rate / 2)) ** 2 - 1
    periodic_rate = (1 + effective_rate) ** (1 / 12) - 1
    monthly_payment = principal * (periodic_rate / (1 - (1 + periodic_rate) ** -months))
    return monthly_payment, periodic_rate

def calculate_total_interest(principal, annual_rate, months):
    if months == 0:
        return 0
    monthly_payment, _ = calculate_monthly_payment(principal, annual_rate, months)
    total_payment = monthly_payment * months
    return total_payment - principal

def calculate_revolving_payment(balance, annual_rate):
    min_payment_percent = 3
    fixed_min_payment = 10
    percentage_payment = balance * (min_payment_percent / 100)
    return max(percentage_payment, fixed_min_payment)

def calculate_revolving_borrowing_cost_daily(balance, annual_rate, monthly_payment):
    total_interest = 0
    remaining_balance = balance
    daily_rate = annual_rate / 365
    days_in_month = 30

    while remaining_balance > 0:
        monthly_interest = 0
        for day in range(days_in_month):
            daily_interest = remaining_balance * daily_rate
            monthly_interest += daily_interest
            remaining_balance += daily_interest
            if monthly_payment >= remaining_balance:
                total_interest += monthly_interest
                remaining_balance = 0
                break
        if remaining_balance == 0:
            break
        total_interest += monthly_interest
        payment = min(monthly_payment, remaining_balance)
        remaining_balance -= payment
        if remaining_balance < 0:
            remaining_balance = 0
    return round(total_interest, 2)

def calculate_weighted_average_interest(debts, mortgage_balance, mortgage_rate):
    total_balance = mortgage_balance
    weighted_sum = mortgage_balance * mortgage_rate
    for debt in debts:
        balance = debt['balance']
        rate = debt['rate']
        total_balance += balance
        weighted_sum += balance * rate
    if total_balance == 0:
        return 0.0
    return round(weighted_sum / total_balance * 100, 2)

def generate_repayment_timeline(balance, annual_rate, monthly_payment, max_months=360):
    remaining_balance = balance
    monthly_rate = annual_rate / 12
    timeline = []
    for month in range(1, max_months + 1):
        if remaining_balance <= 0:
            break
        interest = remaining_balance * monthly_rate
        remaining_balance += interest - monthly_payment
        if remaining_balance < 0:
            remaining_balance = 0
        timeline.append((month, remaining_balance))
    return timeline

# Streamlit App
st.title("Debt Consolidation Model")

# Input Debt Details
st.header("Debt Details")
debts = []
num_debts = st.number_input("Number of Debts", min_value=1, max_value=10, value=1)
for i in range(num_debts):
    st.subheader(f"Debt {i + 1}")
    name = st.text_input(f"Name of Debt {i + 1}", value=f"Debt {i + 1}")
    loan_type = st.selectbox(f"Type of Debt {i + 1}", ["Fixed", "Revolving"], key=f"type_{i}")
    balance = st.number_input(f"Balance for {name}", min_value=0.0, step=100.0)
    rate = st.number_input(f"Annual Interest Rate (%) for {name}", min_value=0.0, step=0.1) / 100

    if loan_type == "Fixed":
        term_months = st.number_input(f"Loan Term (Months) for {name}", min_value=1, step=1)
        start_date = st.date_input(f"Start Date for {name}")
        today = datetime.today()
        start_date_datetime = datetime.combine(start_date, datetime.min.time())
        months_elapsed = max(0, (today.year - start_date_datetime.year) * 12 + today.month - start_date_datetime.month)
        remaining_term = max(0, term_months - months_elapsed)
        remaining_balance = calculate_remaining_balance(balance, rate, months_elapsed, term_months)
        monthly_payment, periodic_rate = calculate_monthly_payment(balance, rate, term_months)
        remaining_interest = calculate_total_interest(remaining_balance, rate, remaining_term)

        st.write(f"Monthly Payment for {name}: ${monthly_payment:,.2f}")
        st.write(f"Remaining Balance for {name}: ${remaining_balance:,.2f}")
        st.write(f"Remaining Interest to be Paid for {name}: ${remaining_interest:,.2f}")

        debts.append({
            "name": name,
            "type": loan_type,
            "balance": balance,
            "rate": rate,
            "remaining_term": remaining_term,
            "monthly_payment": monthly_payment,
            "remaining_interest": remaining_interest,
            "remaining_balance": remaining_balance,
        })

    elif loan_type == "Revolving":
        monthly_payment = calculate_revolving_payment(balance, rate)
        use_custom_payment = st.checkbox(f"Use Custom Payment for {name}")
        if use_custom_payment:
            custom_payment = st.number_input(f"Custom Monthly Payment for {name}", min_value=monthly_payment, step=10.0)
            monthly_payment = custom_payment
        total_interest = calculate_revolving_borrowing_cost_daily(balance, rate, monthly_payment)

        # Estimate remaining term based on payments
        remaining_term = int(balance / monthly_payment) if monthly_payment > 0 else 0

        st.write(f"Calculated Monthly Payment for {name}: ${monthly_payment:,.2f}")
        st.write(f"Total Interest Paid for {name}: ${total_interest:,.2f}")
        st.write(f"Estimated Remaining Term for {name}: {remaining_term} months")

        debts.append({
            "name": name,
            "type": loan_type,
            "balance": balance,
            "rate": rate,
            "monthly_payment": monthly_payment,
            "total_interest": total_interest,
            "remaining_balance": balance,
            "remaining_term": remaining_term,
        })


# Mortgage Details
st.header("Mortgage Details")
mortgage_balance = st.number_input("Current Mortgage Balance", min_value=0.0, step=1000.0)
mortgage_rate = st.number_input("Current Mortgage Rate (%)", min_value=0.0, step=0.1) / 100
mortgage_amortization = st.number_input("Mortgage Amortization (Months)", min_value=12, step=12)

if mortgage_balance > 0 and mortgage_amortization > 0:
    start_date = st.date_input("Mortgage Start Date")
    today = datetime.today()
    start_date_datetime = datetime.combine(start_date, datetime.min.time())
    months_elapsed = max(0, (today.year - start_date_datetime.year) * 12 + today.month - start_date_datetime.month)
    remaining_term = max(0, mortgage_amortization - months_elapsed)
    remaining_balance = calculate_remaining_balance(mortgage_balance, mortgage_rate, months_elapsed, mortgage_amortization)
    mortgage_payment, periodic_rate = calculate_monthly_payment(mortgage_balance, mortgage_rate, mortgage_amortization)
    remaining_mortgage_interest = calculate_total_interest(remaining_balance, mortgage_rate, remaining_term)

    st.write(f"Calculated Monthly Payment for Current Mortgage: ${mortgage_payment:,.2f}")
    st.write(f"Remaining Balance for Current Mortgage: ${remaining_balance:,.2f}")
    st.write(f"Remaining Interest on Current Mortgage: ${remaining_mortgage_interest:,.2f}")

# Consolidation Parameters
st.header("Consolidation Parameters")
new_rate = st.number_input("New Mortgage Rate (%)", min_value=0.0, step=0.1) / 100
new_amortization = st.number_input("New Amortization Length (Months)", min_value=12, step=12)
fees = st.number_input("Refinancing Fees", min_value=0.0, step=100.0)
selected_debts = st.multiselect("Select Debts to Consolidate", [debt["name"] for debt in debts])

# Weighted Average Interest Rate
if debts:
    pre_consolidation_wair = calculate_weighted_average_interest(debts, mortgage_balance, mortgage_rate)
    st.write(f"Pre-Consolidation Weighted Average Interest Rate: {pre_consolidation_wair:.2f}%")

# Consolidation Logic
if selected_debts and new_amortization > 0:
    new_balance = remaining_balance + sum(debt.get('remaining_balance', debt['balance']) for debt in debts if debt['name'] in selected_debts) + fees
    consolidated_monthly_payment, _ = calculate_monthly_payment(new_balance, new_rate, new_amortization)
    consolidated_total_interest = calculate_total_interest(new_balance, new_rate, new_amortization)

    st.subheader("Scenario Comparison")
    comparison_data = {
        "Metric": [
            "Total Interest to be Paid",
            "Monthly Payment",
            "Time to Pay Off Debts (Months)",
            "Net Savings from Consolidation"
        ],
        "Current Scenario": [
            remaining_mortgage_interest + sum(debt.get('total_interest', 0) for debt in debts),
            mortgage_payment + sum(debt['monthly_payment'] for debt in debts),
            max(mortgage_amortization, max(debt.get('remaining_term', 0) for debt in debts)),
            "N/A"
        ],
        "Consolidated Scenario": [
            consolidated_total_interest,
            consolidated_monthly_payment,
            new_amortization,
            (remaining_mortgage_interest + sum(debt.get('total_interest', 0) for debt in debts)) - consolidated_total_interest
        ]
    }
    comparison_df = pd.DataFrame(comparison_data)

    # Format numbers to 2 decimal places
    comparison_df["Current Scenario"] = comparison_df["Current Scenario"].apply(
        lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x
    )
    comparison_df["Consolidated Scenario"] = comparison_df["Consolidated Scenario"].apply(
        lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x
    )

    # Display the formatted dataframe
    st.write(comparison_df)

    # Timeline Visualization
    repayment_data = []

    # Add individual debts
    for debt in debts:
        name = debt['name']
        remaining_payments = len(generate_repayment_timeline(
            balance=debt.get('remaining_balance', debt['balance']),
            annual_rate=debt['rate'],
            monthly_payment=debt['monthly_payment']
        ))
        repayment_data.append({"name": name, "start": 0, "end": remaining_payments})

    # Add original mortgage
    original_mortgage_payments = len(generate_repayment_timeline(
        balance=remaining_balance,
        annual_rate=mortgage_rate,
        monthly_payment=mortgage_payment
    ))
    repayment_data.append({"name": "Original Mortgage", "start": 0, "end": original_mortgage_payments})

    # Add consolidated debt
    consolidated_payments = len(generate_repayment_timeline(
        balance=new_balance,
        annual_rate=new_rate,
        monthly_payment=consolidated_monthly_payment,
        max_months=new_amortization
    ))
    repayment_data.append({"name": "Consolidated Debt", "start": 0, "end": consolidated_payments})

    # Create the horizontal bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, item in enumerate(repayment_data):
        ax.barh(i, item["end"] - item["start"], left=item["start"], height=0.5, label=item["name"])

    # Formatting the chart
    ax.set_yticks(range(len(repayment_data)))
    ax.set_yticklabels([item["name"] for item in repayment_data])
    ax.set_xlabel("Months")
    ax.set_title("Repayment Timeline")
    ax.invert_yaxis()  # Reverse the y-axis for better readability
    ax.legend()

    # Display the chart
    st.pyplot(fig)



