import streamlit as st
import pandas as pd

def main():
    st.set_page_config(page_title="완벽 N빵 정산기", page_icon="🤝")
    st.title("🤝 흩어진 결제내역 완벽 N빵 정산기")
    st.markdown("여러 명이 각자 결제해서 복잡해진 돈 계산, **1/N로 깔끔하게 맞춰서 누가 누구에게 얼마를 보내면 되는지** 알려드립니다.")

    st.subheader("1. 결제 내역 입력")
    st.info("💡 **결제 금액 1, 2**: 음식값과 배달비를 따로 적거나, 1차/2차 비용을 따로 적으세요. 하나만 적고 나머지는 0으로 둬도 됩니다.")
    
    # 예시 데이터 (질문자님이 말씀하신 상황 세팅)
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame({
            "이름": ["친구A", "친구B", "친구C", ""], 
            "결제 금액 1 (음식 등)": [20000, 15000, 14000, 0],
            "결제 금액 2 (배달 등)": [1500, 3000, 2000, 0]
        })

    # 표 UI 제공
    edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

    if st.button("1/N 정산하기", type="primary"):
        # 빈칸 및 데이터 전처리
        valid_df = edited_df[edited_df["이름"].str.strip() != ""].copy()
        valid_df.fillna(0, inplace=True)
        
        # 개인별 총 결제 금액 합산
        valid_df["개인별 총 결제액"] = valid_df["결제 금액 1 (음식 등)"] + valid_df["결제 금액 2 (배달 등)"]
        
        total_spent = valid_df["개인별 총 결제액"].sum()
        num_people = len(valid_df)

        if num_people == 0 or total_spent == 0:
            st.error("입력된 결제 데이터가 없습니다.")
            return

        # 1인당 평균 부담액 계산 (1/N)
        target_amount = total_spent / num_people
        
        # 정산액: 본인이 낸 돈 - 1/N 금액
        # 플러스(+)면 돈을 더 낸 사람 (받아야 함), 마이너스(-)면 돈을 덜 낸 사람 (보내야 함)
        valid_df["정산 잔액"] = valid_df["개인별 총 결제액"] - target_amount

        st.success("✅ 정산이 완료되었습니다!")
        col1, col2 = st.columns(2)
        col1.metric("총 결제 금액", f"{int(total_spent):,}원")
        col2.metric("1인당 내야 할 금액 (1/N)", f"{int(target_amount):,}원")

        # --- 송금 최적화 매칭 알고리즘 ---
        st.subheader("💸 최종 송금 안내")
        
        # 받을 사람(+)과 보낼 사람(-) 리스트 분리
        receivers = valid_df[valid_df["정산 잔액"] > 0].to_dict('records')
        senders = valid_df[valid_df["정산 잔액"] < 0].to_dict('records')

        # 금액 단위가 큰 사람부터 우선 매칭하여 송금 횟수 줄이기
        receivers.sort(key=lambda x: x["정산 잔액"], reverse=True)
        senders.sort(key=lambda x: x["정산 잔액"])

        transactions = []
        i, j = 0, 0

        while i < len(senders) and j < len(receivers):
            sender = senders[i]
            receiver = receivers[j]

            # 보낼 금액과 받을 금액 중 더 작은 쪽을 교환
            amount = min(abs(sender["정산 잔액"]), receiver["정산 잔액"])
            
            # 1원 단위 절사 (깔끔한 표시를 위해)
            amount = int(round(amount, 0))
            
            if amount > 0:
                transactions.append(f"👉 **{sender['이름']}** 님이 **{receiver['이름']}** 님에게 **{amount:,}원**을 송금하세요.")

            # 잔액 차감
            sender["정산 잔액"] += amount
            receiver["정산 잔액"] -= amount

            # 소수점 오차 방지를 위해 1보다 작아지면 다음 사람으로 넘어감
            if abs(sender["정산 잔액"]) < 1:
                i += 1
            if receiver["정산 잔액"] < 1:
                j += 1

        # 결과 출력
        if transactions:
            for t in transactions:
                st.markdown(t)
        else:
            st.info("모든 사람이 정확히 똑같은 금액을 결제하여 송금할 필요가 없습니다!")

        # --- 상세 내역 표 및 다운로드 ---
        st.subheader("📊 상세 정산 내역")
        # 보여주기용 표 포맷팅
        display_df = valid_df[["이름", "개인별 총 결제액"]].copy()
        display_df["1인당 부담액"] = int(target_amount)
        display_df["초과/부족 금액"] = valid_df["정산 잔액"].astype(int)
        
        st.dataframe(display_df, use_container_width=True)

        st.subheader("다운로드")
        csv_data = display_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 정산 내역 CSV 다운로드",
            data=csv_data,
            file_name="n_bbang_receipt.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()