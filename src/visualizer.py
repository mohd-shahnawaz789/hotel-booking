"""
Module: visualizer.py
Description: Generates high-resolution visualizations and executive dashboards.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns


def generate_executive_dashboard(df, room_type_summary, channel_summary, monthly_summary, channel_lead_pivot, save_path=None):
    """
    Renders and exports a 6-panel executive business dashboard.
    """
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    
    fig, axes = plt.subplots(3, 2, figsize=(18, 16))
    plt.subplots_adjust(hspace=0.35, wspace=0.25)

    # 1. Monthly Revenue & Occupancy Trend
    ax1 = axes[0, 0]
    color_rev = "#1f77b4"
    color_nights = "#2ca02c"
    months_abbr = [m[:3] for m in monthly_summary["Arrival_Month_Name"]]

    ax1.bar(months_abbr, monthly_summary["Realized_Revenue"] / 1e5, color=color_rev, alpha=0.7, label="Revenue (Lakh INR)")
    ax1.set_ylabel("Realized Revenue (Lakh INR)", color=color_rev, fontsize=11, fontweight="bold")
    ax1.set_title("1. Monthly Realized Revenue & Room Nights Trend", fontsize=12, fontweight="bold")
    ax1.tick_params(axis="x", rotation=30)

    ax1_twin = ax1.twinx()
    ax1_twin.plot(months_abbr, monthly_summary["Realized_Nights"], color=color_nights, marker="o", linewidth=2.5, label="Nights")
    ax1_twin.set_ylabel("Realized Room Nights", color=color_nights, fontsize=11, fontweight="bold")
    ax1_twin.grid(False)

    # 2. Cancellation Rate by Booking Channel
    ax2 = axes[0, 1]
    sns.barplot(data=channel_summary, x="Booking_Channel", y="Cancellation_Rate_Pct", ax=ax2, hue="Booking_Channel", palette="Reds_d", legend=False)
    ax2.set_title("2. Cancellation Rate by Booking Channel (%)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Cancellation Rate (%)", fontsize=11)
    ax2.set_xlabel("Booking Channel", fontsize=11)
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")

    # 3. Revenue Share by Room Type
    ax3 = axes[1, 0]
    room_colors = ["#4e79a7", "#f28e2b", "#e15759"]
    ax3.pie(room_type_summary["Realized_Revenue"], labels=room_type_summary["Room_Type"],
            autopct="%1.1f%%", startangle=140, colors=room_colors, explode=(0.02, 0.02, 0.04),
            textprops={"fontsize": 11, "fontweight": "bold"})
    ax3.set_title("3. Realized Revenue Share by Room Type", fontsize=12, fontweight="bold")

    # 4. Cancellation Rate Heatmap: Channel vs. Lead-Time Band
    ax4 = axes[1, 1]
    sns.heatmap(channel_lead_pivot, annot=True, fmt=".1f", cmap="YlOrRd", 
                cbar_kws={"label": "Cancellation Rate (%)"}, ax=ax4)
    ax4.set_title("4. Cancellation Rate Heatmap: Channel vs. Lead-Time Band", fontsize=12, fontweight="bold")
    ax4.set_ylabel("Booking Channel", fontsize=11)
    ax4.set_xlabel("Lead-Time Band", fontsize=11)

    # 5. Stay Duration Distribution: Leisure vs. Business
    ax5 = axes[2, 0]
    sns.boxplot(data=df, x="Traveler_Type", y="Nights", hue="Traveler_Type", palette="Set2", ax=ax5, showmeans=True, legend=False,
                meanprops={"marker": "D", "markerfacecolor": "red", "markeredgecolor": "black", "markersize": "7"})
    ax5.set_title("5. Stay Duration Distribution (Red Diamond = Mean)", fontsize=12, fontweight="bold")
    ax5.set_ylabel("Nights Stayed", fontsize=11)
    ax5.set_xlabel("Traveler Segment", fontsize=11)

    # 6. Check-in Arrivals by Weekday (Front-Desk Staffing)
    ax6 = axes[2, 1]
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_counts = df["Arrival_Weekday"].value_counts().reindex(weekday_order)
    sns.barplot(x=weekday_counts.index, y=weekday_counts.values, hue=weekday_counts.index, ax=ax6, palette="Blues_d", legend=False)
    ax6.set_title("6. Front-Desk Workload: Total Arrivals by Day of Week", fontsize=12, fontweight="bold")
    ax6.set_ylabel("Arrival Bookings", fontsize=11)
    ax6.set_xlabel("Day of Arrival", fontsize=11)
    ax6.tick_params(axis="x", rotation=30)
    for p in ax6.patches:
        ax6.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")

    plt.tight_layout()
    
    # Resolve target save path to outputs folder
    if save_path is None:
        proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        out_dir = os.path.join(proj_root, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        save_path = os.path.join(out_dir, "hotel_booking_analysis_dashboard.png")
        
    plt.savefig(save_path, dpi=300)
    print(f"\n[VISUALIZER] Executive dashboard successfully saved to: {os.path.abspath(save_path)}")
    plt.close()
    return save_path
