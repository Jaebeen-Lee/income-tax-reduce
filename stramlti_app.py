import streamlit as st
from dataclasses import dataclass

# ----------------------------
# 기본 설정
# ----------------------------
st.set_page_config(page_title="통합고용증대 세액공제 계산기", layout="centered")
st.title("📈 통합고용증대 세액공제 계산기 (예시)")

st.caption(
    "※ 학습/시연용 예시입니다. 실제 공제 단가·요건(기업규모, 지역, 유지의무, 한도 등)은 "
    "정책 공고를 확인해 반영하세요."
)

# ----------------------------
# 공제 단가 (예시값)
# ----------------------------
@dataclass
class CreditRates:
    base_per_head: int = 5_000_000        # 상시근로자 순증 1인당 기본공제 (예시)
    youth_bonus_per_head: int = 7_000_000 # 청년근로자 순증 1인당 추가공제 (예시)
    non_metro_bonus_per_head: int = 2_000_000  # 비수도권 가산 (예시)

def calc_employment_increase_credit(
    reg_2024: int,
    youth_2024: int,
    reg_2025: int,
    youth_2025: int,
    *,
    is_non_metro: bool,
    rates: CreditRates,
):
    # 방어코드
    for name, v in {
        "’24 상시근로자": reg_2024, "’24 청년근로자": youth_2024,
        "’25 상시근로자": reg_2025, "’25 청년근로자": youth_2025
    }.items():
        if v < 0:
            raise ValueError(f"{name}는 음수가 될 수 없습니다.")

    total_2024 = reg_2024 + youth_2024
    total_2025 = reg_2025 + youth_2025

    inc_total = max(0, total_2025 - total_2024)   # 총 상시근로자 순증
    inc_youth = max(0, youth_2025 - youth_2024)   # 청년근로자 순증
    inc_youth = min(inc_youth, inc_total)         # 청년 순증이 총 순증 초과하지 않도록 캡

    credit_base = inc_total * rates.base_per_head
    credit_youth = inc_youth * rates.youth_bonus_per_head
    credit_non_metro = inc_total * rates.non_metro_bonus_per_head if is_non_metro else 0

    total_credit = credit_base + credit_youth + credit_non_metro

    return {
        "총상시(’24)": total_2024,
        "총상시(’25)": total_2025,
        "총 순증": inc_total,
        "청년(’24)": youth_2024,
        "청년(’25)": youth_2025,
        "청년 순증": inc_youth,
        "기본공제": credit_base,
        "청년가산": credit_youth,
        "비수도권가산": credit_non_metro,
        "합계 공제액": total_credit,
    }

# ----------------------------
# 사이드바: 단가/지역 설정
# ----------------------------
st.sidebar.header("⚙️ 설정")
base_per_head = st.sidebar.number_input("상시 1인당 기본공제(원)", min_value=0, step=100_000, value=5_000_000)
youth_bonus = st.sidebar.number_input("청년 1인당 추가공제(원)", min_value=0, step=100_000, value=7_000_000)
non_metro_bonus = st.sidebar.number_input("비수도권 1인당 가산(원)", min_value=0, step=100_000, value=2_000_000)
is_non_metro = st.sidebar.toggle("비수도권 사업장", value=False)

rates = CreditRates(
    base_per_head=int(base_per_head),
    youth_bonus_per_head=int(youth_bonus),
    non_metro_bonus_per_head=int(non_metro_bonus),
)

# ----------------------------
# 본문 입력
# ----------------------------
st.subheader("👥 인원 입력")

c1, c2 = st.columns(2)
with c1:
    reg_2024 = st.number_input("’24년 상시근로자 수", min_value=0, step=1, value=18)
    reg_2025 = st.number_input("’25년 상시근로자 수", min_value=0, step=1, value=20)
with c2:
    youth_2024 = st.number_input("’24년 청년근로자 수", min_value=0, step=1, value=5)
    youth_2025 = st.number_input("’25년 청년근로자 수", min_value=0, step=1, value=7)

# ----------------------------
# 계산 버튼 & 결과
# ----------------------------
if st.button("🧮 공제액 계산하기"):
    try:
        result = calc_employment_increase_credit(
            reg_2024, youth_2024, reg_2025, youth_2025,
            is_non_metro=is_non_metro, rates=rates
        )

        # 표 형태로 보여주기
        st.success("계산이 완료되었습니다.")
        st.write("### 결과 요약")
        st.table(
            [{"항목": k, "값": (f"{v:,}원" if ("공제" in k or "합계" in k) else v)}
             for k, v in result.items()]
        )

        # 핵심만 강조
        st.metric("합계 공제액", f"{result['합계 공제액']:,} 원")

    except ValueError as e:
        st.error(str(e))

with st.expander("📘 계산 로직(요약)"):
    st.markdown("""
- **총 상시근로자 순증** = (’25 상시+청년) − (’24 상시+청년) → 0 미만이면 0 처리  
- **청년근로자 순증** = (’25 청년) − (’24 청년) → 0 미만이면 0 처리, 총 순증 초과 시 총 순증으로 캡  
- **공제액(예시)** = 기본공제(총 순증×단가) + 청년가산(청년 순증×단가) + (비수도권 가산 선택)  
> 실제 제도는 기업규모·지역·유지의무·상한 등이 있으니 별도 확인 후 단가/요건을 적용하세요.
    """)
