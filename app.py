# app.py
import streamlit as st
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import auth  # Import the authentication module

# Load the trained model and scaler
with open("scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

with open("anomaly_detection_model.pkl", "rb") as f:
    model = pickle.load(f)

# Thresholds for visualization
CPU_THRESHOLD = 80.0
RAM_THRESHOLD = 75.0
LATENCY_THRESHOLD = 200.0

# Streamlit page configuration
st.set_page_config(page_title="Anomaly Detection", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for styling alerts
st.markdown(
    """
    <style>
    .high-risk {background-color: #ff4d4f; color: white; padding: 10px; border-radius: 8px;}
    .moderate-risk {background-color: #ffa940; color: white; padding: 10px; border-radius: 8px;}
    .low-risk {background-color: #ffd666; color: black; padding: 10px; border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

def evaluate_data(data):
    """Evaluate the input data for anomalies."""
    # Create interaction features
    data["CPU_RAM_Interaction"] = data["CPU_Usage(%)"] * data["Memory_Usage(%)"]
    data["Latency_per_CPU"] = data["Latency(ms)"] / (data["CPU_Usage(%)"] + 1)

    # Select relevant columns and scale
    input_data = data[["CPU_Usage(%)", "Memory_Usage(%)", "Latency(ms)", "CPU_RAM_Interaction", "Latency_per_CPU"]]
    input_scaled = scaler.transform(input_data)

    # Predict anomaly scores and status
    anomaly_scores = model.decision_function(input_scaled)
    data["Anomaly_Score"] = anomaly_scores
    data["Anomaly_Status"] = (anomaly_scores < 0).astype(int)

    # Classify risk levels based on anomaly score
    data["Risk_Level"] = data["Anomaly_Score"].apply(lambda x: "High" if x < -0.5 else 
                                                      "Moderate" if -0.5 <= x < 0 else "Low")

    return data

def plot_usage_vs_threshold(data):
    """Plot bar graphs comparing actual values with thresholds."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    # CPU Usage Graph
    axes[0].bar(data.index, data["CPU_Usage(%)"], color="blue", alpha=0.6, label="CPU Usage")
    axes[0].axhline(CPU_THRESHOLD, color="red", linestyle="--", label="CPU Threshold")
    axes[0].set_title("CPU Usage vs Threshold")
    axes[0].set_xlabel("Index")
    axes[0].set_ylabel("CPU Usage (%)")
    axes[0].legend()
    axes[0].grid(True)

    # RAM Usage Graph
    axes[1].bar(data.index, data["Memory_Usage(%)"], color="green", alpha=0.6, label="RAM Usage")
    axes[1].axhline(RAM_THRESHOLD, color="red", linestyle="--", label="RAM Threshold")
    axes[1].set_title("RAM Usage vs Threshold")
    axes[1].set_xlabel("Index")
    axes[1].set_ylabel("Memory Usage (%)")
    axes[1].legend()
    axes[1].grid(True)

    # Latency Graph
    axes[2].bar(data.index, data["Latency(ms)"], color="orange", alpha=0.6, label="Latency")
    axes[2].axhline(LATENCY_THRESHOLD, color="red", linestyle="--", label="Latency Threshold")
    axes[2].set_title("Latency vs Threshold")
    axes[2].set_xlabel("Index")
    axes[2].set_ylabel("Latency (ms)")
    axes[2].legend()
    axes[2].grid(True)

    st.pyplot(fig)

def plot_pie_chart(data):
    """Plot a pie chart for CPU usage, RAM usage, and latency."""
    cpu_usage = data["CPU_Usage(%)"].mean()
    memory_usage = data["Memory_Usage(%)"].mean()
    latency = data["Latency(ms)"].mean()

    labels = ['CPU Usage', 'Memory Usage', 'Latency']
    sizes = [cpu_usage, memory_usage, latency]
    colors = ['lightblue', 'lightgreen', 'lightcoral']

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, shadow=True)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig1)

def show_alert(risk_level, ip_address=None, suggestion=None):
    """Display an alert based on the highest risk level detected."""
    if risk_level == "High":
        st.markdown('<div class="high-risk">⚠️ High-Risk Anomaly Detected!</div>', unsafe_allow_html=True)
    elif risk_level == "Moderate":
        st.markdown('<div class="moderate-risk">⚠️ Moderate-Risk Anomaly Detected!</div>', unsafe_allow_html=True)
    elif risk_level == "Low":
        st.markdown('<div class="low-risk">⚠️ Low-Risk Anomaly Detected!</div>', unsafe_allow_html=True)

    if ip_address:
        st.write(f"📡 IP Address of Anomaly: {ip_address}")

    if suggestion:
        st.success(f"✅ Mitigation Suggestion: {suggestion}")

def main():
    st.title("🚀 Cloud Infrastructure Anomaly Detection")
    st.sidebar.button("Logout", on_click=auth.logout)

    st.sidebar.header("Choose Input Method")
    input_method = st.sidebar.radio("Select input type:", ["CSV Upload", "Manual Entry"])

    if input_method == "CSV Upload":
        st.subheader("Upload your CSV File")
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

        if uploaded_file is not None:
            try:
                data = pd.read_csv(uploaded_file)
                # Filter rows where Alert_Triggered is 1
                data = data[data["Alert_Triggered"] == 1]
                st.write("Filtered Data with Anomalies:")
                st.dataframe(data)

                if st.button("Evaluate"):
                    result = evaluate_data(data)
                    anomalies = result[result["Anomaly_Status"] == 1]

                    if not anomalies.empty:
                        # Get the highest-risk anomaly to display an alert
                        highest_risk_anomaly = anomalies.iloc[anomalies["Risk_Level"].apply(
                            lambda x: {"High": 3, "Moderate": 2, "Low": 1}[x]
                        ).idxmax()]
                        show_alert(highest_risk_anomaly["Risk_Level"], highest_risk_anomaly["IP_Address"], 
                                   highest_risk_anomaly.get("Mitigation_Suggestion"))

                        st.write("Anomaly Detection Results:")
                        st.dataframe(anomalies)
                    else:
                        st.success("✅ No Anomalies Detected.")

                    # Download button for results
                    csv_result = result.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_result,
                        file_name="anomaly_detection_results.csv",
                        mime="text/csv",
                    )

                    st.subheader("Usage vs Threshold Comparison")
                    plot_usage_vs_threshold(result)
                    st.subheader("Pie Chart of Average Usage")
                    plot_pie_chart(result)

            except Exception as e:
                st.error(f"Error processing the file: {str(e)}")

    else:
        st.subheader("Enter Values Manually")

        cpu_usage = st.number_input("CPU Usage (%)", min_value=0.0, value=50.0)
        memory_usage = st.number_input("Memory Usage (%)", min_value=0.0, value=30.0)
        latency = st.number_input("Latency (ms)", min_value=0.0, value=100.0)
        ip_address = st.text_input("IP Address", value="192.168.1.1")
        timestamp = st.text_input("Timestamp", value="2024-10-19 12:00:00")

        if st.button("Evaluate"):
            input_data = pd.DataFrame(
                [[cpu_usage, memory_usage, latency, ip_address]],
                columns=["CPU_Usage(%)", "Memory_Usage(%)", "Latency(ms)", "IP_Address"],
            )
            result = evaluate_data(input_data)

            if result["Anomaly_Status"][0] == 1:
                show_alert(result["Risk_Level"][0], ip_address, "Consider optimizing your resource allocation.")
            else:
                st.success("✅ No Anomaly Detected.")

            st.write("Anomaly Score:", result["Anomaly_Score"][0])

            st.subheader("Usage vs Threshold Comparison")
            plot_usage_vs_threshold(result)
            st.subheader("Pie Chart of Input Data")
            plot_pie_chart(result)

# Streamlit App Entry Point
if not auth.is_authenticated():
    choice = st.sidebar.selectbox("Select Option", ["Login", "Sign Up"])
    if choice == "Login":
        if auth.login_screen():
            main()
    else:
        auth.signup_screen()
else:
    main()
