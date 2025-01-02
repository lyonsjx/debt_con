import streamlit as st
from datetime import datetime

def calculate_remaining_balance(principal, annual_rate, months_elapsed, total_term):
    """Calculates the remaining balance of a fixed loan."""
    if annual_rate == 0:  # Handle zero-interest case
        return principal * (1 - months_elapsed / total_term)
    monthly_payment, periodic_rate = calculate_monthly_payment(principal, annual_rate, total_term)
    remaining_balance = principal * (1 + periodic_rate) ** months_elapsed - \
                        (monthly_payment / periodic_rate) * ((1 + periodic_rate) ** months_elapsed - 1)
    return remaining_balance

def calculate_monthly_payment(principal, annual_rate, months):
    """Calculates the monthly payment for a fixed loan."""
    if annual_rate == 0:  # Handle zero-interest case
        return principal / months, 0
    # Calculate effective and periodic rates
    effective_rate = (1 + (annual_rate / 2)) ** 2 - 1
    periodic_rate = (1 + effective_rate) ** (1 / 12) - 1
    # Calculate monthly payment
    monthly_payment = principal * (periodic_rate / (1 - (1 + periodic_rate) ** -months))
    return monthly_payment, periodic_rate

def calculate_total_interest(principal, annual_rate, months):
    """Calculates the total interest paid over the loan term."""
    if months == 0:
        return 0
    monthly_payment, _ = calculate_monthly_payment(principal, annual_rate, months)
    total_payment = monthly_payment * months
    return total_payment - principal

def calculate_revolving_payment(balance, annual_rate, min_payment_percent, fixed_min_payment):
    """Calculates the monthly payment for a revolving loan."""
    monthly_rate = annual_rate / 12
    interest_cost = balance * monthly_rate
    percentage_payment = balance * (min_payment_percent / 100)
    return max(percentage_payment, fixed_min_payment) + interest_cost

# Streamlit app
st.title("Debt Consolidation Model with Start Dates")

# Input debt details
st.header("Debt Details")
debts = []
num_debts = st.number_input("Number of Debts", min_value=1, max_value=10, value=2)
for i in range(num_debts):
    st.subheader(f"Debt {i + 1}")
    name = st.text_input(f"Name of Debt {i + 1}", value=f"Debt {i + 1}")
    loan_type = st.selectbox(f"Type of Debt {i + 1}", ["Fixed", "Revolving"], key=f"type_{i}")
    balance = st.number_input(f"Balance for {name}", min_value=0.0, step=100.0)
    rate = st.number_input(f"Annual Interest Rate (%) for {name}", min_value=0.0, step=0.1) / 100

    if loan_type == "Fixed":
        term_months = st.number_input(f"Loan Term (Months) for {name}", min_value=1, step=1)
        start_date = st.date_input(f"Start Date for {name}")
        
        # Calculate elapsed and remaining months
        today = datetime.today()
        start_date_datetime = datetime.combine(start_date, datetime.min.time())
        months_elapsed = max(0, (today.year - start_date_datetime.year) * 12 + today.month - start_date_datetime.month)
        remaining_term = max(0, term_months - months_elapsed)
        
        # Calculate remaining balance
        remaining_balance = calculate_remaining_balance(balance, rate, months_elapsed, term_months)
        
        # Calculate payments and interest
        monthly_payment, periodic_rate = calculate_monthly_payment(balance, rate, term_months)
        remaining_interest = calculate_total_interest(remaining_balance, rate, remaining_term)
        
        st.write(f"Monthly Payment for {name}: ${monthly_payment:,.2f}")
        st.write(f"Periodic Rate for {name}: {periodic_rate * 100:.4f}%")
        st.write(f"Remaining Balance for {name}: ${remaining_balance:,.2f}")
        st.write(f"Remaining Interest to be Paid for {name}: ${remaining_interest:,.2f}")
        st.write(f"Remaining Term for {name}: {remaining_term} months")
        
        debts.append({
            "name": name,
            "type": loan_type,
            "balance": balance,
            "rate": rate,
            "remaining_term": remaining_term,
            "monthly_payment": monthly_payment,
            "remaining_interest": remaining_interest,
            "remaining_balance": remaining_balance,
            "periodic_rate": periodic_rate
        })

    elif loan_type == "Revolving":
        min_payment_percent = st.number_input(f"Minimum Payment (% of Balance) for {name}", min_value=0.0, step=0.1)
        fixed_min_payment = st.number_input(f"Fixed Minimum Payment for {name}", min_value=0.0, step=10.0)
        monthly_payment = calculate_revolving_payment(balance, rate, min_payment_percent, fixed_min_payment)
        st.write(f"Calculated Monthly Payment for {name}: ${monthly_payment:,.2f}")
        debts.append({
            "name": name,
            "type": loan_type,
            "balance": balance,
            "rate": rate,
            "monthly_payment": monthly_payment
        })

# Input mortgage details
st.header("Mortgage Details")
mortgage_balance = st.number_input("Current Mortgage Balance", min_value=0.0, step=1000.0)
mortgage_rate = st.number_input("Current Mortgage Rate (%)", min_value=0.0, step=0.1) / 100
mortgage_amortization = st.number_input("Mortgage Amortization (Months)", min_value=12, step=12)

# Calculate and display original mortgage payment and remaining interest
if mortgage_balance > 0 and mortgage_amortization > 0:
    # Calculate remaining balance for backdated mortgage
    start_date = st.date_input("Mortgage Start Date")
    today = datetime.today()
    start_date_datetime = datetime.combine(start_date, datetime.min.time())
    months_elapsed = max(0, (today.year - start_date_datetime.year) * 12 + today.month - start_date_datetime.month)
    remaining_term = max(0, mortgage_amortization - months_elapsed)
    remaining_balance = calculate_remaining_balance(mortgage_balance, mortgage_rate, months_elapsed, mortgage_amortization)
    
    mortgage_payment, periodic_rate = calculate_monthly_payment(mortgage_balance, mortgage_rate, mortgage_amortization)
    remaining_mortgage_interest = calculate_total_interest(remaining_balance, mortgage_rate, remaining_term)
    
    st.write(f"Calculated Monthly Payment for Current Mortgage: ${mortgage_payment:,.2f}")
    st.write(f"Periodic Rate for Current Mortgage: {periodic_rate * 100:.4f}%")
    st.write(f"Remaining Balance for Current Mortgage: ${remaining_balance:,.2f}")
    st.write(f"Remaining Interest on Current Mortgage: ${remaining_mortgage_interest:,.2f}")

# Consolidation parameters
st.header("Consolidation Parameters")
new_rate = st.number_input("New Mortgage Rate (%)", min_value=0.0, step=0.1) / 100
new_amortization = st.number_input("New Amortization Length (Months)", min_value=12, step=12)
fees = st.number_input("Refinancing Fees", min_value=0.0, step=100.0)
selected_debts = st.multiselect("Select Debts to Consolidate", [debt["name"] for debt in debts])

# Calculate consolidated mortgage payment
if selected_debts and new_amortization > 0:
    new_balance = remaining_balance + sum(debt['remaining_balance'] for debt in debts if debt['name'] in selected_debts) + fees
    consolidated_monthly_payment, _ = calculate_monthly_payment(new_balance, new_rate, new_amortization)
    consolidated_total_interest = calculate_total_interest(new_balance, new_rate, new_amortization)
    st.write(f"Calculated Monthly Payment for Consolidated Mortgage: ${consolidated_monthly_payment:,.2f}")
    st.write(f"Total Interest Paid Over Consolidated Loan: ${consolidated_total_interest:,.2f}")

# Compute scenarios
if st.button("Compare Scenarios"):
    # Current scenario
    total_remaining_interest = sum(debt['remaining_interest'] for debt in debts if 'remaining_interest' in debt)
    total_current_interest = total_remaining_interest + remaining_mortgage_interest
    total_debt_payment = sum(debt['monthly_payment'] for debt in debts)
    current_total_payment = total_debt_payment + mortgage_payment

    # Display results
    st.subheader("Comparison Results")
    st.write("### Current Scenario")
    st.write(f"Remaining Total Interest to be Paid: ${total_current_interest:,.2f}")
    st.write(f"Total Monthly Payment: ${current_total_payment:,.2f}")

    st.write("### Consolidated Scenario")
    st.write(f"Total Interest Paid Over Consolidated Loan: ${consolidated_total_interest:,.2f}")
    st.write(f"Total Monthly Payment: ${consolidated_monthly_payment:,.2f}")

    # Comparison
    if consolidated_total_interest < total_current_interest:
        st.success("Consolidating saves you money!")
    else:
        st.warning("Consolidating may cost more in interest over time.")
