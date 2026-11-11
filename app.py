import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import datetime

# 页面设置 (使用深色宽屏模式，装杯必备)
st.set_page_config(page_title="本量利(CVP)智能决策系统", layout="wide", initial_sidebar_state="expanded")
st.title("📊 本量利 (CVP) 智能决策与动态分析系统")
st.markdown("👉 **拖动左侧参数，实时联动保本点、利润测算与成本结构！** *(商业模拟版)*")

# ---------------- 左侧：参数输入区 ----------------
st.sidebar.header("⚙️ 核心参数调节")
price = st.sidebar.number_input("单价 (元)", min_value=1.0, max_value=1000.0, value=20.0, step=0.5)
vc = st.sidebar.number_input("单位变动成本 (元)", min_value=1.0, max_value=1000.0, value=12.0, step=0.5)
fc = st.sidebar.number_input("固定成本总额 (元)", min_value=0.0, max_value=1000000.0, value=20000.0, step=1000.0)

st.sidebar.divider()
st.sidebar.header("🎯 目标与预期测算")
current_sales = st.sidebar.number_input("当前预计销量 (件)", min_value=0, max_value=1000000, value=3000, step=100)
target_profit = st.sidebar.number_input("期望目标利润 (元)", value=10000.0, step=1000.0)

# ---------------- 核心计算逻辑 ----------------
cm = price - vc 
cm_ratio = (cm / price) * 100 if price > 0 else 0

if cm > 0:
    be_units = fc / cm
    be_sales = be_units * price
    target_units = (fc + target_profit) / cm
else:
    be_units = float('inf')
    be_sales = float('inf')
    target_units = float('inf')

current_profit = (price * current_sales) - (fc + vc * current_sales)
safe_margin_units = current_sales - be_units if cm > 0 else 0
safe_margin_ratio = (safe_margin_units / current_sales * 100) if current_sales > 0 else 0

# ---------------- 主界面：数据展示区 ----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("单位边际贡献", f"¥ {cm:.2f}")
col2.metric("边际贡献率", f"{cm_ratio:.1f} %")
col3.metric("保本点销量", f"{int(be_units)} 件" if cm > 0 else "无法保本")
col4.metric("保本点销售额", f"¥ {be_sales:,.2f}" if cm > 0 else "无法保本")

st.divider()

# 实时利润看板
st.subheader("💼 当前经营状况预测")
col5, col6, col7 = st.columns(3)
if current_profit > 0:
    col5.metric("当前预计利润", f"¥ {current_profit:,.2f}", delta="盈利", delta_color="normal")
else:
    col5.metric("当前预计利润", f"¥ {current_profit:,.2f}", delta="亏损", delta_color="inverse")

if safe_margin_units > 0:
    col6.metric("安全边际 (件)", f"{int(safe_margin_units)} 件", delta=f"{safe_margin_ratio:.1f}%", delta_color="normal")
else:
    col6.metric("安全边际 (件)", f"{int(safe_margin_units)} 件", delta="已跌破保本点", delta_color="inverse")

if cm > 0:
    col7.metric("目标利润所需销量", f"{int(target_units)} 件")
else:
    col7.metric("目标利润所需销量", "无法实现")

if cm <= 0:
    st.error("⚠️ 警告：单价小于或等于单位变动成本，卖得越多亏得越多，永远无法保本！")

st.divider()

# ---------------- 图表区 ----------------
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("📈 动态保本图 (CVP Chart)")
    max_units = max(be_units * 2 if cm > 0 else 1000, target_units * 1.2 if cm > 0 else 1000, current_sales * 1.2, 100)
    x_units = np.linspace(0, max_units, 100)
    revenue = x_units * price
    total_cost = fc + (x_units * vc)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_units, y=revenue, mode='lines', name='销售收入', line=dict(color='#00d2ff', width=3)))
    fig.add_trace(go.Scatter(x=x_units, y=total_cost, mode='lines', name='总成本', line=dict(color='#ff4b4b', width=3)))

    if cm > 0 and be_units <= max_units:
        fig.add_trace(go.Scatter(
            x=[be_units], y=[be_sales], mode='markers+text', name='保本点', 
            marker=dict(color='#00ff00', size=14, symbol='star'),
            text=[f"保本点: {int(be_units)}件"], textposition="top center"
        ))
    
    if current_sales <= max_units:
        fig.add_trace(go.Scatter(
            x=[current_sales], y=[price * current_sales], mode='markers+text', name='当前销量', 
            marker=dict(color='#ffa500', size=12, symbol='circle'),
            text=[f"当前销量"], textposition="bottom center"
        ))

    fig.update_layout(
        xaxis_title="销售量 (件)", yaxis_title="金额 (元)", hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=True, gridcolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#333'), template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("🍩 成本与利润结构")
    total_rev = price * current_sales
    total_vc = vc * current_sales
    
    if total_rev > 0:
        profit_part = max(current_profit, 0)
        vc_part = max(total_vc, 0)
        fc_part = max(fc, 0)
        
        if current_profit < 0:
             labels = ['固定成本', '变动成本', '亏损金额']
             values = [fc_part, vc_part, abs(current_profit)]
             colors = ['#ff7f0e', '#ff4b4b', '#7f7f7f']
        else:
             labels = ['固定成本', '变动成本', '净利润']
             values = [fc_part, vc_part, profit_part]
             colors = ['#ff7f0e', '#ff4b4b', '#00ff00']

        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=colors))])
        fig_pie.update_layout(margin=dict(t=30, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h"), template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("预计销量为0，无法生成结构图")

# ---------------- 底部功能：敏感度雷达图 & 下载 ----------------
st.divider()
bottom_col1, bottom_col2 = st.columns([3, 1])

with bottom_col1:
    st.subheader("🕸️ 利润敏感性雷达图")
    if cm > 0:
        # 计算各因素变动10%对利润的影响
        p_up = (price*1.1 * current_sales) - (fc + vc * current_sales)
        vc_down = (price * current_sales) - (fc + vc*0.9 * current_sales)
        fc_down = (price * current_sales) - (fc*0.9 + vc * current_sales)
        
        # 计算影响率
        base_profit = current_profit if current_profit != 0 else 1
        impact_p = abs(p_up - current_profit) / abs(base_profit) * 100
        impact_vc = abs(vc_down - current_profit) / abs(base_profit) * 100
        impact_fc = abs(fc_down - current_profit) / abs(base_profit) * 100
        
        categories = ['单价上升10%', '变动成本降10%', '固定成本降10%']
        values_radar = [impact_p, impact_vc, impact_fc]
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values_radar + [values_radar[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(0, 210, 255, 0.3)',
            line=dict(color='#00d2ff')
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(values_radar)*1.2])),
            showlegend=False, margin=dict(t=30, b=10, l=10, r=10), template="plotly_dark"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

with bottom_col2:
    st.subheader("📄 导出报告")
    st.write("生成当前参数下的智能分析报告。")
    # 生成报告文本
    report_df = pd.DataFrame({
    "指标项目": ["单价", "单位变动成本", "固定成本", "预计销量", "保本点销量", "当前预计利润", "安全边际率"],
    "数值": [f"¥ {price:.2f}", f"¥ {vc:.2f}", f"¥ {fc:,.2f}", f"{current_sales} 件", 
             f"{int(be_units) if cm > 0 else 0} 件", f"¥ {current_profit:,.2f}", f"{safe_margin_ratio:.1f}%"]
})

# 转成 CSV 格式（可以用 Excel 打开）
csv_data = report_df.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📊 下载 Excel 数据报告",
    data=csv_data,
    file_name=f"CVP分析报告_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)