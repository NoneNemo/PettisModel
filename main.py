import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Pettis Class-Warfare Model v6.9", layout="wide")

st.title("Trade Wars Are Class Wars: Geopolitical Simulator (v6.9)")
st.markdown("""
This master version models global macroeconomics as an institutional class conflict. 
Track the division of wealth between asset owners and workers, watch distinct debt categories accumulate over a 10-year loop, 
and test structural policy interventions like Tariffs vs. Capital Controls.
""")

# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 10-Year Simulation & Policy", 
    "⚖️ Inequality & Debt Deconstruction", 
    "🏦 Currency & The Exorbitant Burden",
    "📖 Advanced Theoretical Manual"
])

# =========================================================================
# GLOBAL PRESETS & RESET FUNCTION VIA SESSION STATE
# =========================================================================
default_presets = [
    {"gdp": 1000, "wage": 42, "repr": 8, "curr": 20, "safe": 75, "inv": 46, "mal": 48, "prod": 0.35},
    {"gdp": 800,  "wage": 52, "repr": 1, "curr": 12, "safe": 25, "inv": 22, "mal": 8, "prod": 0.35},
    {"gdp": 1600, "wage": 66, "repr": 0, "curr": 0, "safe": 35, "inv": 18, "mal": 5, "prod": 0.40}
]

def reset_all_sliders():
    """Directly mutates session state keys to restore baseline presets."""
    for idx, preset in enumerate(default_presets):
        st.session_state[f"d_gdp_{idx}"] = preset["gdp"]
        st.session_state[f"d_wage_{idx}"] = preset["wage"]
        st.session_state[f"d_repr_{idx}"] = preset["repr"]
        st.session_state[f"d_curr_{idx}"] = preset["curr"]
        st.session_state[f"d_safe_{idx}"] = preset["safe"]
        st.session_state[f"d_inv_{idx}"] = preset["inv"]
        st.session_state[f"d_mal_{idx}"] = preset["mal"]
        st.session_state[f"d_prod_{idx}"] = preset["prod"]
    
    st.session_state["c_alloc_treasuries"] = 40
    st.session_state["c_alloc_real_estate"] = 30
    st.session_state["c_alloc_equities"] = 30
    st.session_state["c_fx_elasticity"] = 20.0
    st.session_state["c_deindustrialization_beta"] = 1.5
    st.session_state["c_policy_year_5"] = "None"

# =========================================================================
# GLOBAL ENGINE FUNCTION
# =========================================================================
def run_10_year_simulation(inputs):
    """
    Simulates a 10-year macroeconomic cycle tracking class wealth, deconstructed debt,
    endogenous interest rates, and institutional policy feedbacks.
    """
    states = {
        c: {
            "GDP": inputs[c]["init_gdp"],
            "Debt": 0.0,
            "BaseWage": inputs[c]["base_wage"],
            "Repression": inputs[c]["repression"],
            "Currency": inputs[c]["currency_under"],
            "SafetyNet": inputs[c]["safety_net"],
            "NomInv": inputs[c]["nom_inv"],
            "Malinvestment": inputs[c]["malinvestment"],
            "ProdCoef": inputs[c]["prod_coef"],
            # Debt Categories
            "Debt_Household": 10.0, 
            "Debt_Corp_LGFV": 15.0,
            "Debt_Sovereign": 20.0,
            # Financial & Open Market metrics
            "Treasuries": 0.0,
            "RealEstate": 0.0,
            "Equities": 0.0,
            "AssetIndex": 100.0,
            "IndustrialBase": 100.0,
            "Wealth_Top10": 100.0,
            "Wealth_Bottom90": 100.0,
            "InterestRate": 0.04
        } for c in inputs
    }
    
    # Financial allocation parameters for Country C
    alloc_t = inputs["Country C"]["alloc_treasuries"]
    alloc_re = inputs["Country C"]["alloc_real_estate"]
    alloc_eq = inputs["Country C"]["alloc_equities"]
    total_alloc = alloc_t + alloc_re + alloc_eq
    
    alloc_rates = {"Treasuries": 0.33, "RealEstate": 0.33, "Equities": 0.34} if total_alloc == 0 else {
        "Treasuries": alloc_t / total_alloc,
        "RealEstate": alloc_re / total_alloc,
        "Equities": alloc_eq / total_alloc
    }
        
    gamma = inputs["Country C"]["fx_elasticity"]
    beta = inputs["Country C"]["deindustrialization_beta"]
    policy_action = inputs["Country C"]["policy_year_5"]
    
    history = []
    
    for year in range(11):
        # --- DYNAMIC COST OF CARRY (ENDOGENOUS INTEREST RATES) ---
        for c in states:
            total_debt = states[c]["Debt_Household"] + states[c]["Debt_Corp_LGFV"] + states[c]["Debt_Sovereign"]
            debt_to_gdp = (total_debt / states[c]["GDP"]) if states[c]["GDP"] > 0 else 0
            
            if c in ["Country A", "Country B"]:
                states[c]["InterestRate"] = min(0.12, 0.05 + (debt_to_gdp * 0.03))
            else:
                states[c]["InterestRate"] = min(0.14, 0.03 + (debt_to_gdp * 0.05))

        # --- STEP 1: COMPUTE STRUCTURAL DEMAND & AGGREGATES ---
        ca_desired = {}
        prod_i = {}
        waste_i = {}
        c_consumption = {}
        
        for c in states:
            total_debt = states[c]["Debt_Household"] + states[c]["Debt_Corp_LGFV"] + states[c]["Debt_Sovereign"]
            debt_to_gdp = (total_debt / states[c]["GDP"]) if states[c]["GDP"] > 0 else 0
            
            trans = (states[c]["Repression"] / 100 * 0.5) + (states[c]["Currency"] / 100 * 0.4)
            sh_hh = (states[c]["BaseWage"] / 100) - trans
            base_prop = 0.96 - (states[c]["SafetyNet"] / 100 * 0.4)
            
            if c == "Country C":
                ineq_ratio = states[c]["Wealth_Top10"] / states[c]["Wealth_Bottom90"] if states[c]["Wealth_Bottom90"] > 0 else 1
                base_prop = base_prop * max(0.4, 1.0 - (ineq_ratio - 1.0) * 0.04)
            
            c_consumption[c] = (states[c]["GDP"] * sh_hh) * base_prop
            s = states[c]["GDP"] - c_consumption[c]
            i = states[c]["GDP"] * (states[c]["NomInv"] / 100)
            
            current_mal_rate = states[c]["Malinvestment"] / 100
            if c in ["Country A", "Country B"] and debt_to_gdp > 1.0:
                current_mal_rate = min(0.95, current_mal_rate * (1.0 + (debt_to_gdp - 1.0) * 0.4))
            
            prod_i[c] = i * (1 - current_mal_rate)
            waste_i[c] = i * current_mal_rate
            ca_desired[c] = s - i

        # --- STEP 2: GLOBAL BALANCE SHEET CLEARING & SHOCKS ---
        ca_a_final = ca_desired["Country A"]
        ca_b_final = ca_desired["Country B"]
        ca_c_final = -(ca_a_final + ca_b_final)
        
        if year >= 5:
            if policy_action == "Tariffs on Country A":
                pass 
            elif policy_action == "Capital Controls":
                ca_c_final = max(-40.0, ca_c_final * 0.1)
                
                for merc in ["Country A", "Country B"]:
                    allocated_share = 0.6 if merc == "Country A" else 0.4
                    lost_export_demand = max(0.0, ca_desired[merc] - (abs(ca_c_final) * allocated_share))
                    states[merc]["GDP"] = max(100.0, states[merc]["GDP"] - lost_export_demand)
                
                ca_a_final = abs(ca_c_final) * 0.6
                ca_b_final = abs(ca_c_final) * 0.4
                
        debt_pressure_c = max(0.0, -ca_c_final)

        # --- STEP 3: FINANCIAL PLUMBING & ASSET SPECULATION ---
        flow_to_treasuries = debt_pressure_c * alloc_rates["Treasuries"]
        flow_to_real_estate = debt_pressure_c * alloc_rates["RealEstate"]
        flow_to_equities = debt_pressure_c * alloc_rates["Equities"]

        states["Country C"]["Treasuries"] += flow_to_treasuries
        states["Country C"]["RealEstate"] += flow_to_real_estate
        states["Country C"]["Equities"] += flow_to_equities

        inflow_ratio = debt_pressure_c / states["Country C"]["GDP"] if states["Country C"]["GDP"] > 0 else 0
        speculative_flows = flow_to_real_estate + flow_to_equities
        inflation_spike = (speculative_flows / states["Country C"]["GDP"]) * 100 if states["Country C"]["GDP"] > 0 else 0
        states["Country C"]["AssetIndex"] += inflation_spike
        
        fx_shock = inflow_ratio * gamma
        states["Country C"]["Currency"] += fx_shock
        
        industrial_decay = fx_shock * beta
        states["Country C"]["IndustrialBase"] = max(10.0, states["Country C"]["IndustrialBase"] - industrial_decay)
        states["Country C"]["BaseWage"] = max(10.0, states["Country C"]["BaseWage"] - (industrial_decay * 0.4))
        prod_i["Country C"] = prod_i["Country C"] * (states["Country C"]["IndustrialBase"] / 100)

        # --- STEP 4: CLASS-BASED WEALTH & REALISTIC DEBT NETWORKS ---
        for c in states:
            trans_local = (states[c]["Repression"] / 100 * 0.5) + (states[c]["Currency"] / 100 * 0.4)
            effective_labor_power = (states[c]["BaseWage"] / 100) - trans_local - (states[c]["SafetyNet"] / 100 * 0.1)
            states[c]["AmortizationPaydown"] = max(0.0, effective_labor_power * 0.08)

        for c in ["Country A", "Country B"]:
            paydown = states[c]["AmortizationPaydown"] * states[c]["GDP"] * 0.1
            debt_leverage_need = 0.20 * (states[c]["Malinvestment"] / 100)
            
            states[c]["Debt_Corp_LGFV"] = max(0.0, states[c]["Debt_Corp_LGFV"] + waste_i[c] + (states[c]["Debt_Corp_LGFV"] * states[c]["InterestRate"]) - paydown)
            states[c]["Debt_Sovereign"] = max(0.0, states[c]["Debt_Sovereign"] + (waste_i[c] * 0.15) + (states[c]["Debt_Sovereign"] * states[c]["InterestRate"]) - (paydown * 0.3))
            states[c]["Debt_Household"] = max(0.0, states[c]["Debt_Household"] + (prod_i[c] * debt_leverage_need) + (states[c]["Debt_Household"] * states[c]["InterestRate"]) - paydown)
        
        # Country C
        paydown_c = states["Country C"]["AmortizationPaydown"] * states["Country C"]["GDP"] * 0.1
        states["Country C"]["Debt_Household"] = max(0.0, states["Country C"]["Debt_Household"] + (flow_to_real_estate * 1.3) + (states["Country C"]["Debt_Household"] * states["Country C"]["InterestRate"]) - paydown_c)
        states["Country C"]["Debt_Sovereign"] = max(0.0, states["Country C"]["Debt_Sovereign"] + flow_to_treasuries + (states["Country C"]["Debt_Sovereign"] * states["Country C"]["InterestRate"]) - (paydown_c * 0.4))
        states["Country C"]["Debt_Corp_LGFV"] = max(0.0, states["Country C"]["Debt_Corp_LGFV"] + (flow_to_equities * 0.8) + (states["Country C"]["Debt_Corp_LGFV"] * states["Country C"]["InterestRate"]) - paydown_c)
        
        states["Country C"]["Wealth_Top10"] = 100.0 + (states["Country C"]["AssetIndex"] - 100.0) * 1.5
        states["Country C"]["Wealth_Bottom90"] = max(10.0, 100.0 + (states["Country C"]["BaseWage"] - inputs["Country C"]["base_wage"]) - (states["Country C"]["Debt_Household"] / states["Country C"]["GDP"] * 50))

        # Capture Records
        for c, final_ca, pi_val in [
            ("Country A", ca_a_final, prod_i["Country A"]),
            ("Country B", ca_b_final, prod_i["Country B"]),
            ("Country C", ca_c_final, prod_i["Country C"])
        ]:
            total_debt = states[c]["Debt_Household"] + states[c]["Debt_Corp_LGFV"] + states[c]["Debt_Sovereign"]
            debt_ratio = (total_debt / states[c]["GDP"]) * 100 if states[c]["GDP"] > 0 else 0
            
            history.append({
                "Year": year,
                "Country": c,
                "GDP": states[c]["GDP"],
                "Total Debt": total_debt,
                "Debt-to-GDP (%)": debt_ratio,
                "Household Debt": states[c]["Debt_Household"],
                "Corp/LGFV Debt": states[c]["Debt_Corp_LGFV"],
                "Sovereign Debt": states[c]["Debt_Sovereign"],
                "Interest Rate (%)": states[c]["InterestRate"] * 100,
                "Current Account": final_ca,
                "Productive Investment": pi_val,
                "Asset Inflation Index": states[c]["AssetIndex"],
                "Currency Valuation": states[c]["Currency"],
                "Industrial Base Index": states[c]["IndustrialBase"],
                "Top 10% Wealth": states[c]["Wealth_Top10"],
                "Bottom 90% Wealth": states[c]["Wealth_Bottom90"]
            })

        # --- STEP 5: DYNAMIC GDP TRANSITIONS ---
        if year < 10:
            for c in states:
                total_debt = states[c]["Debt_Household"] + states[c]["Debt_Corp_LGFV"] + states[c]["Debt_Sovereign"]
                current_debt_ratio = total_debt / states[c]["GDP"] if states[c]["GDP"] > 0 else 0
                debt_drag = max(0.1, 1.0 - (current_debt_ratio * 0.18))
                
                gdp_delta = prod_i[c] * states[c]["ProdCoef"] * debt_drag
                states[c]["GDP"] += gdp_delta
                    
    return pd.DataFrame(history)

# =========================================================================
# TAB 1: UI CONFIGURATION & SIMULATION
# =========================================================================
with tab1:
    st.header("Configure Structural Distortions & Policies")
    
    # NEW PIECE: The Global Master Reset Interlock
    st.button("🔄 Reset All Sliders to Default System Settings", on_click=reset_all_sliders)
    st.divider()

    inputs = {}
    cols = st.columns(3)
    
    names = ["Country A (Mercantilist/High Malinvestment eg. China)", "Country B (Mercantilist/Low Malinvestment eg. Germany)", "Country C (Open Capital / Sponge eg. US)"]
    short_names = ["Country A", "Country B", "Country C"]
    
    help_texts = {
        "gdp": "Initial size of the economy. High nominal values can be sustained early on purely via debt-expanded outlays.",
        "wage": "Base percentage of national income flowing to laborers. Lower shares suppress consumption and build structural trade surpluses.",
        "repr": "Financial Repression: Administratively suppressing bank deposit yields. Transfers wealth from householders to fund cheap industrial debt.",
        "curr": "Currency Undervaluation: Central bank currency suppression. Functions as an implicit tax on consumer imports and a direct subsidy for domestic exporters.",
        "safe": "Social Safety Net Deficit: Absence of state-backed welfare. Forces citizens to hoard precautionary savings, lowering spending velocity.",
        "inv": "The overall percentage of national GDP committed to fixed infrastructure, factory expansions, and real estate builds.",
        "mal": "Malinvestment Rate: Percentage of capital outlays directed to projects returning less than their financing cost. Generates short-term GDP but creates unpayable Local Government (LGFV) or Corporate debt.",
        "prod": "Capital Productivity Coefficient: Technological multiplier (e.g., AI integration) dictating how effectively productive investment fuels future real GDP."
    }
    
    for idx, col in enumerate(cols):
        with col:
            st.subheader(names[idx])
            c_key = short_names[idx]
            preset = default_presets[idx]
            
            init_gdp = st.number_input(f"Initial GDP ({c_key})", value=preset["gdp"], step=100, key=f"d_gdp_{idx}", help=help_texts["gdp"])
            base_wage = st.slider(f"Base Wage Share (% GDP)", 30, 80, preset["wage"], key=f"d_wage_{idx}", help=help_texts["wage"])
            repression = st.slider(f"Financial Repression (Rate Suppression)", 0, 10, preset["repr"], key=f"d_repr_{idx}", help=help_texts["repr"])
            currency_under = st.slider(f"Currency Undervaluation (%)", -10, 30, preset["curr"], key=f"d_curr_{idx}", help=help_texts["curr"])
            safety_net = st.slider(f"Social Safety Net Deficit (%)", 0, 100, preset["safe"], key=f"d_safe_{idx}", help=help_texts["safe"])
            nom_inv = st.slider(f"Nominal Investment Rate (% GDP)", 10, 60, preset["inv"], key=f"d_inv_{idx}", help=help_texts["inv"])
            malinvestment = st.slider(f"Malinvestment Rate (Waste %)", 0, 100, preset["mal"], key=f"d_mal_{idx}", help=help_texts["mal"])
            prod_coef = st.slider(f"Capital Productivity (Tech/AI Edge)", 0.10, 0.80, preset["prod"], step=0.05, key=f"d_prod_{idx}", help=help_texts["prod"])
            
            inputs[c_key] = {
                "init_gdp": init_gdp, "base_wage": base_wage, "repression": repression,
                "currency_under": currency_under, "safety_net": safety_net, "nom_inv": nom_inv,
                "malinvestment": malinvestment, "prod_coef": prod_coef,
                "alloc_treasuries": 0, "alloc_real_estate": 0, "alloc_equities": 0,
                "fx_elasticity": 20.0, "deindustrialization_beta": 1.5, "policy_year_5": "None"
            }

    st.divider()
    st.subheader("🏦 Financial Asset Flows & Currency Elasticity (Country C Only)")
    st.markdown("Determine how the surplus capital forced into Country C is distributed across its domestic financial asset classes.")
    
    help_fx = {
        "treasuries": "Surplus capital entering sovereign debt markets, artificially funding government fiscal deficits.",
        "real_estate": "Surplus capital entering property markets, driving real estate inflation and inducing household debt extractions.",
        "equities": "Surplus capital entering stock markets. Drives equity valuations up, incentivizing stock buybacks over real capital investments.",
        "gamma": "Currency Elasticity Coefficient: Measures how intensely incoming capital flows drive up Country C's exchange rate (DXY Index effect).",
        "beta": "Deindustrialization Beta: Measures how aggressively an overvalued currency hollows out domestic manufacturing profit margins, suppressing wages."
    }
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        inputs["Country C"]["alloc_treasuries"] = st.slider("Flow to Treasuries", 0, 100, 40, help=help_fx["treasuries"], key="c_alloc_treasuries")
    with f_col2:
        inputs["Country C"]["alloc_real_estate"] = st.slider("Flow to Real Estate", 0, 100, 30, help=help_fx["real_estate"], key="c_alloc_real_estate")
    with f_col3:
        inputs["Country C"]["alloc_equities"] = st.slider("Flow to Equities", 0, 100, 30, help=help_fx["equities"], key="c_alloc_equities")
    with f_col4:
        inputs["Country C"]["fx_elasticity"] = st.slider("Currency Flow Elasticity (Gamma)", 0.0, 50.0, 20.0, help=help_fx["gamma"], key="c_fx_elasticity")
        inputs["Country C"]["deindustrialization_beta"] = st.slider("Deindustrialization Drag (Beta)", 0.0, 5.0, 1.5, help=help_fx["beta"], key="c_deindustrialization_beta")

    st.divider()
    st.subheader("🛡️ Policy Intervention Dashboard (Activates in Year 5)")
    inputs["Country C"]["policy_year_5"] = st.radio(
        "Select Country C's Year 5 Strategic Choice:",
        ["None", "Tariffs on Country A", "Capital Controls"],
        horizontal=True,
        help="None allows imbalances to compound. Tariffs impose taxes on imports without altering capital flows. Capital Controls close the capital account to reject foreign savings gluts.",
        key="c_policy_year_5"
    )

    df_sim = run_10_year_simulation(inputs)
    
    st.divider()
    plot_col1, plot_col2 = st.columns(2)
    with plot_col1:
        fig_gdp = px.line(df_sim, x="Year", y="GDP", color="Country", markers=True, title="Real GDP Path Dynamics")
        st.plotly_chart(fig_gdp, width="stretch")
    with plot_col2:
        fig_debt = px.line(df_sim, x="Year", y="Debt-to-GDP (%)", color="Country", markers=True, title="Total Compounding Debt-to-GDP Ratio")
        st.plotly_chart(fig_debt, width="stretch")

# =========================================================================
# TAB 2: INEQUALITY & DEBT DECONSTRUCTION
# =========================================================================
with tab2:
    st.header("Deconstructing the Class War")
    st.markdown("Pettis asserts that global trade conflicts are internal distribution conflicts wrapped in national flags.")
    
    df_c = df_sim[df_sim["Country"] == "Country C"]
    df_a = df_sim[df_sim["Country"] == "Country A"]
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        df_a_debt = df_a.melt(id_vars=["Year"], value_vars=["Household Debt", "Corp/LGFV Debt", "Sovereign Debt"])
        fig_a_debt = px.area(df_a_debt, x="Year", y="value", color="variable", title="Country A Balance Sheet: State-Directed LGFV/Corporate Debt Build")
        st.plotly_chart(fig_a_debt, width="stretch")
    with col_d2:
        df_c_debt = df_c.melt(id_vars=["Year"], value_vars=["Household Debt", "Corp/LGFV Debt", "Sovereign Debt"])
        fig_c_debt = px.area(df_c_debt, x="Year", y="value", color="variable", title="Country C Balance Sheet: Forced Consumer & Sovereign Debt Build")
        st.plotly_chart(fig_c_debt, width="stretch")

    st.divider()
    st.subheader("Country C: The Internal Class Disconnect")
    
    df_ineq_melted = df_c.melt(id_vars=["Year"], value_vars=["Top 10% Wealth", "Bottom 90% Wealth"],
                               var_name="Social Class", value_name="Wealth Index Balance")
    fig_ineq = px.line(df_ineq_melted, x="Year", y="Wealth Index Balance", color="Social Class", markers=True, 
                       title="Wealth Divergence in the Absorbent Sponge Economy",
                       color_discrete_sequence=["green", "red"])
    st.plotly_chart(fig_ineq, width="stretch")

# =========================================================================
# TAB 3: CURRENCY & ASSET PLUMBING
# =========================================================================
with tab3:
    st.header("The Exorbitant Burden & Financial Asset Price Inflation")
    st.markdown("""
    **Educational Focus:** Pettis highlights the **Current Account Balance** ($S - I = CA$) as the core container for tracking global distortions. 
    Because capital account flows dominate the trading loop, mercantile economies with suppressed wages dump their domestic savings gluts abroad, forcing the reserve economy (Country C) into matching deficits.
    """)
    
    fig_ca = px.line(df_sim, x="Year", y="Current Account", color="Country", markers=True,
                     title="Global Current Account Balances (The Accounting Mirror)",
                     labels={"Current Account": "Current Account Balance (Absolute Value)"})
    fig_ca.add_hline(y=0.0, line_dash="dash", line_color="gray", annotation_text="Perfect Balanced Trade Baseline")
    st.plotly_chart(fig_ca, use_container_width=True)
    
    st.divider()
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        df_fx_melted = df_c.melt(id_vars=["Year"], value_vars=["Currency Valuation", "Industrial Base Index"],
                                 var_name="Transmission Metric", value_name="Index Scale")
        fig_fx = px.line(df_fx_melted, x="Year", y="Index Scale", color="Transmission Metric", markers=True,
                         title="Country C: The Endogenous Exchange Rate Weapon",
                         color_discrete_sequence=["green", "red"])
        st.plotly_chart(fig_fx, width="stretch")
    with c_col2:
        fig_rates = px.line(df_sim, x="Year", y="Interest Rate (%)", color="Country", markers=True,
                            title="Endogenous Yield Dynamics (The Cost of Carry)")
        st.plotly_chart(fig_rates, width="stretch")

# =========================================================================
# TAB 4: ADVANCED THEORETICAL MANUAL
# =========================================================================
with tab4:
    st.header("The Pettis Framework: Complete Operational Documentation")
    st.markdown("""
    This manual provides a detailed operational map of the model's inner mechanics. It serves as standalone 
    documentation designed to explain Michael Pettis's core worldview (*Trade Wars Are Class Wars*) to an individual completely 
    unfamiliar with his work.
    """)
    
    st.subheader("Core Axiom: Global Balance Sheet Identities")
    st.markdown("""
    The foundational building block of Pettis's thinking is that global trade and capital flows are strictly bound by **double-entry bookkeeping identities**, not by comparative advantages or consumer tastes. 
    National savings (S), domestic investment (I), and the trade account or Current Account (CA) are structurally locked:
    
    **S - I = CA**
    
    A country cannot 'choose' to have a trade surplus without running policies that artificially force its national savings to exceed its local investments. 
    Conversely, an open-market nation with deep financial structures (like the US) cannot 'choose' to balance its trade deficit if foreign mercantile powers are actively using its asset markets to deposit their excess national savings.
    """)

    st.divider()
    st.subheader("Comprehensive Variable Glossary & Interconnectedness")
    
    st.markdown(r"""
    ### 1. Institutional Vectors (The Root Causes)
    * **Base Wage Share:** The initial share of GDP distributed to laborers. Workers spend the majority of their income on everyday goods. If an economy suppresses this parameter, it caps domestic purchasing power, making it impossible for citizens to buy back what they manufacture.
    * **Financial Repression:** A policy where state-controlled banks fix interest rates below inflation. This behaves as an invisible structural tax extracting wealth from household savers and giving it as low-cost loans to state enterprises and exporters.
    * **Currency Undervaluation:** A central bank policy keeping the local currency artificially cheap. This works exactly like a universal tariff on all consumer imports (eroding real wages) and a direct cash handout to exporters.
    * **Social Safety Net Deficit:** A weak or non-existent welfare state. It suppresses the marginal propensity to consume because citizens are structurally forced to hoard **precautionary savings** out of their wages to cover emergencies (health, aging), removing liquidity from the real economy.
    
    ### 2. The Domestic Transmission Channel (Income to Savings)
    The model translates the institutional variables above into an **Effective Household Income Share** (Share_HH). 
    Repression and undervalued currencies are deducted from the base wage because they extract wealth from workers and transfer it to the corporate/state sector.
    
    Share_HH = Base Wage Share - (Financial Repression / 100 * 0.5) - (Currency Undervaluation / 100 * 0.4)
    
    Because the Social Safety Net Deficit lowers the propensity to consume, the final real **Consumption** (C) is artificially suppressed. By accounting identity, whatever is not consumed is saved (S):
    
    S = GDP - C

    ### 3. Investment, Malinvestment, and the Growth Illusion
    A country allocates its GDP to nominal investment (I). However, Pettis strictly separates this into productive capital and waste.
    
    I_Total = I_Productive + I_Waste
    
    * **Productive Investment (I_Productive):** Channeled into viable technology or vital updates. This serves as the engine for next year's growth, multiplied by the **Capital Productivity Coefficient** (alpha).
    * **Malinvestment (I_Waste):** Channeled into dead-weight, non-performing projects (e.g., building roads to nowhere). This generates nominal GDP in the current year (boosting superficial statistics), but permanently destroys wealth, leaving behind a legacy of non-performing loans.

    ### 4. Global Interdependence & Forced Absorption
    When mercantile economies suppress wages, they generate massive savings that they cannot absorb internally (S > I). They export this capital, running a **Current Account Surplus** (CA > 0).
    Because the global system is a closed loop, the sum of all trade balances must equal zero (sum CA = 0). Country C (with fully open capital markets) acts as the **Systemic Sponge**. The global system overrides its domestic preferences and forces it to absorb the shock, running a trade deficit:
    
    CA_Final, C = - (CA_Final, A + CA_Final, B)

    ### 5. The Endogenous Feedback Loops (The Overhauls)
    * **Pillar 1: The Wealth Inequality Trap:** Foreign capital floods into Country C's Equities and Real Estate. This drives up the **Asset Inflation Index**, causing the wealth of the **Top 10%** to skyrocket. Because the rich save most of their gains, this concentration of wealth further suppresses Country C's aggregate consumption propensity, driving an internal demand crisis.
    * **Pillar 2: Asymmetric Debt Deconstruction:** In Countries A and B, malinvestment debt builds up hidden in **Corporate/LGFV (Local Government Financing Vehicle) Debt**. In Country C, the forced drop in domestic savings ($S = I + CA$) squeezes the working class. To maintain their standard of living amid job losses, the **Bottom 90%** are forced to issue massive **Household Debt**.
    * **Pillar 3: Endogenous Cost of Carry:** Interest rates are dynamic. Mercantilist nations use administrative repression to keep rates near zero to keep their zombie LGFVs afloat, risking prolonged stagnation. Absorbent nations face organic rate spikes as total household leverage compiles, increasing default risk.
    * **Pillar 4: Currency & Deindustrialization (The Death Spiral):** Large capital inflows create massive demand for Country C's currency ($E_C$), causing it to appreciate automatically. This overvalued exchange rate makes domestic manufacturing non-competitive. The **Industrial Base Index** drops, factories close, and worker wages are forced down, completing the spiral.
    """)

    st.divider()
    st.subheader("Core Geopolitical Scenarios Argued by Pettis")
    st.markdown("""
    Use the simulation sliders in Tab 1 to run the six defining economic trajectories of the modern world:
    """)

    with st.expander("Scenario 1: The High-Investment Malinvestment Mirror (e.g., China)"):
        st.markdown("""
        * **Setup:** Give Country A a low `Base Wage Share` (under 45%), high `Financial Repression` (7-10%), and an extreme `Nominal Investment Rate` (45%+) with a `Malinvestment Rate` above 45%.
        * **The Mechanic:** In Years 0 to 4, Country A's GDP compounds spectacularly. This perfectly replicates the high-investment growth miracle. However, because half of that capital is nonproductive waste, its future capacity returns collapse.
        * **The Reckoning:** By Year 10, Country A's **Corp/LGFV Debt** line moves vertically. The massive debt burden triggers a harsh *Debt Drag*, grinding real growth down to a halt and leaving the nation trapped in structural stagnation.
        """)

    with st.expander("Scenario 2: Efficient Mercantilism & The Savings Glut (e.g., Germany)"):
        st.markdown("""
        * **Setup:** Give Country B a low `Base Wage Share` (under 50%), but keep `Financial Repression` and `Malinvestment` near 0%. Maintain a high `Currency Undervaluation` (representing how a shared Euro currency keeps Germany structurally undervalued relative to its industrial capability).
        * **The Mechanic:** Unlike Country A, Country B does not waste its capital on ghost cities; its investments are highly productive. However, because it structurally suppresses wages relative to productivity, its domestic population cannot afford to consume what its factories produce.
        * **The Reckoning:** Country B runs a permanent **Current Account Surplus**. It uses foreign consumers to subsidize its employment and exports its excess capital directly into the asset markets of Country C.
        """)

    with st.expander("Scenario 3: The Reserve Currency Trap & The Exorbitant Burden (e.g., USA)"):
        st.markdown("""
        * **Setup:** Keep Country C's internal variables perfectly balanced (High wage share, 0% repression). Maximize the structural distortions in Countries A and B.
        * **The Mechanic:** Because Country C has a fully open capital account and acts as the global reserve currency, the excess savings of A and B flood into its markets. This capital surge automatically bids up Country C's currency, triggering an aggressive appreciation shock.
        * **The Reckoning:** The overvalued currency acts as a massive tax on Country C's factories. The **Industrial Base Index** collapses, destroying middle-class manufacturing jobs. While Wall Street celebrates an exploding **Asset Inflation Index** (fueled by foreign cash entering stocks), the working-class **Bottom 90%** experience severe wealth erosion and are forced to pile on massive **Household Debt** just to survive.
        """)

    with st.expander("Scenario 4: The Trade Policy Showdown (Tariffs vs. Capital Controls)"):
        st.markdown("""
        * **Setup:** Run the simulation with standard mercantile distortions in A and B. In Year 5, toggle between the two policy options under Tab 1.
        * **Tariffs:** Select Tariffs. Notice that the graphs do not shift. Pettis argues that because tariffs do not alter the underlying income inequality (suppressed wages) in Country A, Country A's excess savings remain identical. The capital simply bypasses the tariff by rerouting through Country B (e.g., transshipments via Vietnam or Mexico). Country C's aggregate deficit and debt load remain completely unchanged.
        * **Capital Controls:** Select Capital Controls. By directly restricting the capital account, Country C refuses to act as the global dumping ground. It rejects the savings glut. Country C's household debt immediately flatlines, and its industrial base stabilizes. However, because the global system is a closed loop, Countries A and B are instantly hit with a massive **Capacity Utilization Demand Shock**. Their factory exports collapse, forcing severe domestic recessions that strip away their ability to mask overcapacity with fake growth.
        """)

    with st.expander("Scenario 5: Global Structural Rebalancing (The Root Cure)"):
        st.markdown("""
        * **Setup:** Go to the configuration sliders for **Country A** and **Country B** and manually rebalance their domestic income distributions: Increase `Base Wage Share` to a healthy 65%–70%, reduce `Financial Repression` to 0, eliminate `Currency Undervaluation` to 0%, and lower the `Social Safety Net Deficit` to 10%–20%.
        * **The Mechanic:** By shifting wealth back to their domestic households and reinforcing public welfare networks, Countries A and B resolve their systemic under-consumption crises from within. Their citizens can finally afford to purchase the output their factories produce.
        * **The Reckoning:** Because Countries A and B consume their own industrial output, their national savings drop to match their local investments (Savings = Investment). Their structural trade surpluses drop to zero (Current Account approaches 0). Because there is no longer a 'global savings glut' looking for a geopolitical hiding place, zero surplus capital floods into Country C. Country C's exchange rate stabilizes, its manufacturing ecosystem recovers, and its Debt-to-GDP ratio completely flattens out.
        """)

    with st.expander("Scenario 6: The Global Golden Equilibrium (Total Debt Eradication)"):
        st.markdown("""
        * **Setup:** Configure **Country A** and **Country B** into perfect, non-distortionary consumer economies: Set `Base Wage Share` = **75%**, drop `Financial Repression`, `Currency Undervaluation`, and `Social Safety Net Deficit` to **0%**, set `Malinvestment Rate` to **0%**, and carefully align `Nominal Investment Rate` to exactly **28%**. Finally, give all nations high technology baselines (`Capital Productivity` = **0.60**).
        * **The Mechanic:** 1. **Eliminating the 4% Leak:** Elevating the wage share to 75% under a zero welfare deficit means households spend 96% of their disposable earnings. This fixes Country A and B's aggregate domestic consumption at 72% of GDP ($75\\% \\times 96\\% = 72\\%$) and leaves their national savings at exactly 28% ($100\\% - 72\\% = 28\\%$). By turning the investment slider to exactly 28%, their internal savings perfectly clear with internal outlays ($S = I$). Their net trade surpluses drop to absolute zero.
            2. **Starving Foreign Capital Inflows:** Because Country A and B's current accounts are perfectly balanced, Country C receives exactly zero units of excess capital dumping (`debt_pressure_c = 0.0`). The foreign transmission channel into US Treasuries, Equities, and Real Estate completely vaporizes. 
        * **The Reckoning:** With zero external capital forcing credit expansions onto Country C, and zero malinvestment waste creating bad assets in Countries A and B, the system's structural debt engines are turned off. Backed by their strong domestic worker wages, all three nations activate their natural **Amortization and Paydown engines**, completely overtaking historical interest charges. On the chart, Country A and B's lines curve downward into permanent stability, while Country C's debt drops smoothly and **flatlines perfectly along the 0.0% axis**. Global equilibrium is fully restored.
        """)

    # =========================================================================
    # ADVANCED THEORETICAL ADDENDUMS
    # =========================================================================
    st.divider()
    st.subheader("🔀 Advanced Theoretical Addendums: The Mechanical Fault Lines")
    st.markdown("""
    This advanced appendix maps the complex institutional policy interactions, structural tax shields, 
    and systemic blowback configurations modeled in the latest general equilibrium parameters.
    """)

    with st.expander("Addendum A: The Micro-Macro Tariff Disconnect (Miran vs. Pettis)"):
        st.markdown("""
        * **The Micro Argument (Tax Incidence):** Conventional microeconomists argue that if a deficit nation imposes tariffs, foreign exporters bear the burden (~70%) by slitting their factory prices, eroding corporate margins, or accepting currency depreciation to retain market access.
        * **The Pettis Macro Critique:** This view mistakes tax incidence for structural erasure. If foreign states/corporations absorb a tariff by compressing profit margins or slashing local manufacturing input costs, *income inequality inside that foreign country gets worse*. 
        * **The Balance Sheet Trajectory:** Squeezing foreign workers further lowers their domestic consumption share, mechanically compounding their internal savings glut ($S > I$). If Country C's capital account remains open, those new savings *must* find a home. The capital flows simply reroute via transshipments (e.g., routing Country A's components through Country B to exploit trade loopholes). The aggregate current account deficit and matching debt expansion remain completely unchanged.
        """)

    with st.expander("Addendum B: OBBA Full Expensing and Tariff Counter-Productivity"):
        st.markdown("""
        * **The Structural Interaction:** Under the One Big Beautiful Bill (OBBA), corporations are permitted 100% first-year expensing (accelerated bonus depreciation) on capital acquisitions. 
        * **The Micro Tax Shield:** When an intermediate or capital industrial asset is imported under a heavy protective tariff, full expensing allows corporations to immediately write off the entire inflated cost against their current year tax liabilities. The tax code effectively functions as a massive structural subsidy, castrating the tariff's core penalty and incentivizing the continued import of foreign intermediate goods.
        * **The Macro Collapse of National Savings:** On a general equilibrium level, this interaction accelerates debt creation. Widespread first-year write-offs drop state tax revenues, exploding the fiscal deficit. In macro identities, a widening government deficit is a collapse in **Government Savings** ($S_{\text{gov}}$). Simultaneously, investment ($I$) ticks up. By structural identity ($S - I = CA$), dropping savings paired with climbing investment forces the national current account deficit to widen, forcing a massive surge in matching foreign capital absorption.
        """)

    with st.expander("Addendum C: The Illusion of Digital Escapes (Why Stablecoins Worsen the Trap)"):
        st.markdown("""
        * **The Misconception:** Proponents argue that fiat-backed stablecoins (e.g., USDT, USDC) build an independent, parallel financial layer that relieves structural pressure on the traditional banking system.
        * **The Double-Entry Accounting Reality:** Stablecoins do not bypass the reserve currency loop; they optimize its speed. To back their circulating digital liability, stablecoin networks are structurally bound to purchase ultra-liquid, short-term **U.S. Treasury Bills**.
        * **The Systemic Reinforcement:** Stablecoins act as a frictionless global siphon that converts distributed digital cash directly into a perpetual demand pipeline for U.S. sovereign debt. By making it easier for foreign wealth to escape into dollar-denominated safe assets, stablecoins actively reinforce the overvaluation of the dollar, suppress long-term domestic yields, and accelerate the hollowing out of the domestic manufacturing core.
        """)

    with st.expander("Addendum D: The Endgame of Sovereign Leverage (The Miran Doctrine)"):
        st.markdown("""
        * **The Core Premise:** Because global production capacity is deeply overbuilt due to underconsumption, **global consumer demand is the single scariest commodity in the world**. The deficit nation, as the ultimate provider of that demand, possesses massive systemic leverage over surplus nations.
        * **The Capital Flow Weaponization Blueprint:** The Miran Doctrine suggests using capital account weapons rather than product tariffs to force international rebalancing:
            1. **User Fees on Official Reserves:** Imposing direct withholding taxes or maintenance fees on foreign central bank holdings of U.S. Treasuries, making capital dumping highly expensive.
            2. **The Century Bond Restructuring:** Legally forcing foreign mercantile states to swap short-term liquid bonds into illiquid, 100-year near-zero interest structures as a condition for market access, completely neutralizing the threat of a sudden treasury sell-off.
        * **The Systemic Volatility Trade-Off:** Pettis completely agrees that the U.S. has the leverage to force this. However, the model tracks a severe economic paradox: forcefully shutting down capital inflows instantly cuts the foreign liquidity propping up Wall Street asset premiums. Forcing global rebalancing via capital controls creates a zero-sum political showdown—rescuing the physical economy of domestic industrial workers requires intentionally detonating the financialized wealth premiums of the stock market.
        """)