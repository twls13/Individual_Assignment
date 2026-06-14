import streamlit as st
import pandas as pd

def main():
    st.set_page_config(page_title="완벽 통합 정산기", page_icon="💰", layout="centered")
    
    st.title("💰 완벽 통합 정산기")
    
    mode = st.radio(
        "원하는 계산 방식을 선택하세요:", 
        ["1/N 정산 (통합)", "술값 따로 정산 (항목별)"], 
        horizontal=True
    )
    st.divider()

    if mode == "1/N 정산 (통합)":
        run_n_bbang()
    else:
        run_alcohol_settlement()

def run_n_bbang():
    st.subheader("🤝 흩어진 결제내역 완벽 N빵 정산기")
    st.markdown("각자 결제한 총액을 1/N으로 나누어 깔끔하게 정산합니다.")
    
    st.info("💡 결제 금액 1, 2: 음식값과 배달비를 따로 적거나, 1차/2차 비용을 따로 적으세요. 하나만 적고 나머지는 0으로 둬도 됩니다.")
    
    if 'df_nbbang' not in st.session_state:
        st.session_state.df_nbbang = pd.DataFrame({
            "이름": ["친구A", "친구B", "친구C", ""], 
            "결제 금액 1 (음식 등)": [20000, 15000, 14000, 0], 
            "결제 금액 2 (배달 등)": [1500, 3000, 2000, 0]
        })

    edited_df = st.data_editor(st.session_state.df_nbbang, num_rows="dynamic", use_container_width=True)

    if st.button("1/N 정산하기", type="primary"):
        df = edited_df[edited_df["이름"].str.strip() != ""].copy()
        df.fillna(0, inplace=True)
        
        df["총액"] = df["결제 금액 1 (음식 등)"] + df["결제 금액 2 (배달 등)"]
        total = df["총액"].sum()
        num_people = len(df)
        
        if num_people == 0 or total == 0:
            st.error("입력된 데이터가 없습니다.")
            return
            
        avg = total / num_people
        df["정산 잔액"] = df["총액"] - avg

        col1, col2 = st.columns(2)
        col1.metric("총 결제 금액", f"{int(total):,}원")
        col2.metric("1인당 내야 할 금액 (1/N)", f"{int(avg):,}원")

        st.subheader("💸 최종 송금 안내")
        receivers = sorted(df[df["정산 잔액"] > 0].to_dict('records'), key=lambda x: x["정산 잔액"], reverse=True)
        senders = sorted(df[df["정산 잔액"] < 0].to_dict('records'), key=lambda x: x["정산 잔액"])
        
        i, j = 0, 0
        transactions = []
        while i < len(senders) and j < len(receivers):
            amt = min(abs(senders[i]["정산 잔액"]), receivers[j]["정산 잔액"])
            amt = int(round(amt, 0))
            if amt > 0:
                transactions.append(f"👉 {senders[i]['이름']} 님이 {receivers[j]['이름']} 님에게 {amt:,}원 송금")
            senders[i]["정산 잔액"] += amt
            receivers[j]["정산 잔액"] -= amt
            if abs(senders[i]["정산 잔액"]) < 1: i += 1
            if receivers[j]["정산 잔액"] < 1: j += 1
            
        if transactions:
            for t in transactions: st.markdown(t)
        else:
            st.success("모든 정산이 완벽히 맞아떨어져 송금할 금액이 없습니다!")

def run_alcohol_settlement():
    st.subheader("🍻 술값 따로 정산기")
    st.markdown("전체 결제액에서 술값만 따로 빼서, 마신 사람들에게만 분배합니다.")
    
    names = st.text_input("참여자 이름을 쉼표(,)로 구분해서 입력하세요", "김철수,이영희,박민수,최수진")
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    
    st.markdown("#### 1. 술값 정보")
    st.info("💡 영수증에 찍힌 '술값'만 합산해서 적고, 술을 마신 사람을 선택하세요.")
    
    c1, c2 = st.columns([1, 2])
    with c1: 
        alcohol_price = st.number_input("술값 총액 (원)", value=0, step=1000)
    with c2: 
        default_drinkers = name_list[:2] if len(name_list) >= 2 else name_list
        drinkers = st.multiselect("누가 술을 마셨나요?", name_list, default=default_drinkers)
    
    st.markdown("#### 2. 각자 카드로 긁은 총액")
    st.info("💡 본인 카드로 최종 결제한 총액을 입력하세요. 결제하지 않은 사람은 0으로 둡니다.")
    
    paid_dict = {}
    cols = st.columns(min(len(name_list), 4))
    for i, name in enumerate(name_list):
        with cols[i % len(cols)]:
            paid_dict[name] = st.number_input(f"{name}", value=0, step=1000, key=f"paid_{name}")
            
    if st.button("계산하기", type="primary"):
        total_paid = sum(paid_dict.values())
        if total_paid == 0:
            st.error("입력된 총 결제 금액이 없습니다.")
            return
            
        common_total = total_paid - alcohol_price
        
        if common_total < 0:
            st.error("결제한 총액보다 술값이 더 큽니다! 금액을 확인해주세요.")
            return
            
        burden = {name: 0.0 for name in name_list}
        
        common_share = common_total / len(name_list) if len(name_list) > 0 else 0
        for name in name_list:
            burden[name] += common_share
            
        alcohol_share = alcohol_price / len(drinkers) if len(drinkers) > 0 else 0
        if alcohol_price > 0 and drinkers:
            for p in drinkers:
                if p in burden:
                    burden[p] += alcohol_share
                    
        st.subheader("📊 개인별 상세 정산 내역")
        detail_data = []
        for name in name_list:
            my_alcohol = alcohol_share if name in drinkers else 0
            detail_data.append({
                "이름": name,
                "내가 결제한 돈": paid_dict[name],
                "내야 할 밥값": int(common_share),
                "내야 할 술값": int(my_alcohol),
                "최종 내야 할 돈": int(burden[name])
            })
        st.dataframe(pd.DataFrame(detail_data), use_container_width=True)
                    
        bal = {name: paid_dict[name] - burden[name] for name in name_list}
        rec = sorted([{"이름": k, "잔액": v} for k, v in bal.items() if v > 0], key=lambda x: x["잔액"], reverse=True)
        sen = sorted([{"이름": k, "잔액": v} for k, v in bal.items() if v < 0], key=lambda x: x["잔액"])
        
        st.subheader("💸 상세 송금 안내")
        st.caption(f"전체 결제액 {total_paid:,}원 = 공통 음식값 {int(common_total):,}원 + 술값 {int(alcohol_price):,}원")
        
        i, j = 0, 0
        transactions = []
        while i < len(sen) and j < len(rec):
            amt = min(abs(sen[i]["잔액"]), rec[j]["잔액"])
            amt = int(round(amt, 0))
            if amt > 0:
                transactions.append(f"👉 {sen[i]['이름']} 님이 {rec[j]['이름']} 님에게 {amt:,}원 송금")
            sen[i]["잔액"] += amt
            rec[j]["잔액"] -= amt
            if abs(sen[i]["잔액"]) < 1: i += 1
            if rec[j]["잔액"] < 1: j += 1
            
        if transactions:
            for t in transactions: st.markdown(t)
        else:
            st.success("모든 정산이 완벽히 맞아떨어져 송금할 금액이 없습니다!")

if __name__ == "__main__":
    main()
