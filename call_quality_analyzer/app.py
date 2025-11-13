import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from analyzer import CallQualityAnalyzer

st.set_page_config(page_title="Call Quality Analyzer", layout="wide")
st.title("📞 Анализ качества звонков по филиалам")

uploaded_file = st.file_uploader("Загрузите файл в формате CSV или Excel", type=["csv", "xlsx"])

if not uploaded_file:
    st.info("⬆️ Загрузите файл для анализа.")
    st.stop()

# чтение файла
try:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Ошибка при чтении файла: {e}")
    st.stop()

st.success(f"Файл загружен — {len(df)} строк")
analyzer = CallQualityAnalyzer(df)

st.markdown("### Доступные столбцы")
st.dataframe(pd.DataFrame({"columns": df.columns}))

st.markdown("---")
st.header("📍 Обнаруженные доступные блоки анализа")

available_blocks = analyzer.available_blocks
for block, available in available_blocks.items():
    emoji = "✅" if available else "❌"
    st.write(f"{emoji} {block.replace('_', ' ').title()}")

st.markdown("---")

# ------------------ Блок 1: распределение оценок и звонков ------------------
if available_blocks["Распределение оценок/звонков, средние оценки"]:
    st.header("1️⃣ Распределение оценок и звонков/аудиобейджей по филиалам")

    st.subheader("Количество оценок (всего / звонки / аудиобейджи) по филиалам")
    all_score = analyzer.get_all_score_by_branch()
    st.dataframe(all_score)

    st.subheader("Количество уникальных call_id (всего / звонки / аудиобейджи) по филиалам")
    call_count = analyzer.get_call_count()
    st.dataframe(call_count)

    with st.expander("График распределений — все типы коммуникации"):
        fig = analyzer.plot_distributions_all()
        st.pyplot(fig)

    with st.expander("График распределений — звонки (REGULAR)"):
        fig = analyzer.plot_distributions_call()
        st.pyplot(fig)

    with st.expander("График распределений — аудиобейджи (AUDIO_BADGE)"):
        fig = analyzer.plot_distributions_badge()
        st.pyplot(fig)
else:
    st.warning("Для блока распределения оценок и звонков требуются столбцы: 'call_id', 'call_type', 'branch_name', 'organization_name', 'score'")

st.markdown("---")

# ------------------ Блок 2: средние оценки ------------------
if available_blocks["Распределение оценок/звонков, средние оценки"]:
    st.header("2️⃣ Средние оценки за звонки и аудиобейджи по филиалам")

    st.subheader("Средняя оценка — все типы коммуникации")
    avg_all = analyzer.get_avg_score_by_branch()
    st.dataframe(avg_all)
    fig = analyzer.plot_avg_score()
    st.pyplot(fig)

    st.subheader("Средняя оценка — звонки (REGULAR)")
    avg_call = analyzer.get_avg_score_by_branch_call()
    st.dataframe(avg_call)
    fig = analyzer.plot_avg_score_call()
    st.pyplot(fig)

    st.subheader("Средняя оценка — аудиобейджи (AUDIO_BADGE)")
    avg_badge = analyzer.get_avg_score_by_branch_badge()
    st.dataframe(avg_badge)
    fig = analyzer.plot_avg_score_badge()
    st.pyplot(fig)

    st.subheader("Объединённая сводная таблица средних оценок (call / badge / all)")
    full_avg = analyzer.get_full_avg_score_by_branch()
    st.dataframe(full_avg)
else:
    st.info("Средние оценки недоступны: отсутствуют базовые столбцы 'call_id', 'call_type', 'branch_name', 'organization_name', 'score'")

st.markdown("---")

# ------------------ Блок 3: недельная динамика ------------------
if available_blocks["Динамика оценок"]:
    st.header("3️⃣ Недельная динамика средних оценок")

    st.subheader("Сводная таблица и графики — все типы коммуникации")
    weekly_all = analyzer.get_avg_score_by_week(analyzer.df)
    st.dataframe(weekly_all)
    fig = analyzer.plot_weekly_all()
    st.pyplot(fig)

    st.subheader("Сводная таблица и графики — звонки")
    weekly_call = analyzer.get_avg_score_by_week(analyzer.df_call)
    st.dataframe(weekly_call)
    fig = analyzer.plot_weekly_call()
    st.pyplot(fig)

    st.subheader("Сводная таблица и графики — аудиобейджи")
    weekly_badge = analyzer.get_avg_score_by_week(analyzer.df_badge)
    st.dataframe(weekly_badge)
    fig = analyzer.plot_weekly_badge()
    st.pyplot(fig)

    with st.expander("Сетка графиков динамики по филиалам — все типы коммуникации"):
        fig = analyzer.plot_weekly_grid_all()
        st.pyplot(fig)
    with st.expander("Сетка графиков динамики по филиалам — звонки"):
        fig = analyzer.plot_weekly_grid_call()
        st.pyplot(fig)
    with st.expander("Сетка графиков динамики по филиалам — аудиобейджи"):
        fig = analyzer.plot_weekly_grid_badge()
        st.pyplot(fig)
else:
    st.info(" Динамика по неделям недоступна, не хватает столбца 'created_at' и/ или базовых столбцов")

st.markdown("---")

# ------------------ Блок 4: сравнение по критериям ------------------
if available_blocks["Анализ критериев оценок"]:
    st.header("4️⃣ Сравнение оценок филиалов в разрезе по критериям")

    st.subheader("Средняя оценка филиалов по критериям — звонки (REGULAR)")
    avg_call_criteria = analyzer.get_avg_score_criteria(analyzer.df_call)
    st.dataframe(avg_call_criteria)

    st.subheader("Относительный вклад критериев — звонки")
    criteria_impact_call = analyzer.get_criteria_impact(analyzer.df_call, avg_score_criteria=avg_call_criteria, avg_score_by_branch=analyzer.get_avg_score_by_branch_call(), count_col="count_call")
    st.dataframe(criteria_impact_call)
    fig = analyzer.plot_criteria_heatmap(criteria_impact_call)
    st.pyplot(fig)

    with st.expander("📊 Статистические тесты по критериям оценки звонков", expanded=False):
        min_pairs = st.slider("Минимум оценок по каждому критерию", 10, 30, 10)
        alpha = st.number_input("Уровень значимости α", 0.01, 0.1, 0.05, step=0.01)

        if st.button("▶ Запустить статистические тесты"):
            with st.spinner("Выполняется анализ..."):
                st.subheader("Тест 1: 'Профессиональная этика' > 'Активное слушание'")
                st.markdown("""
                            **Гипотеза**: Для каждого филиала средняя оценка по критерию *"Профессиональная этика"* выше средней оценки по критерию *"Активное слушание"*
                            
                            **Статистические гипотезы**:

                              - H0: среднее по критерию "Профессиональная этика" <= среднее по критерию "Активное слушание"
                                
                              - H1: среднее по критерию "Профессиональная этика" > среднее по критерию "Активное слушание"
                            """)
                df1 = analyzer.test_professional_vs_active_listening(min_pairs=min_pairs, alpha=alpha)
                st.dataframe(df1)
                st.download_button("⬇ Скачать результаты (Тест 1)", df1.to_csv(index=False), "test1_results.csv")

                st.subheader("Тест 2: Вклад 'Профессиональная этика' > Вклад 'Работа с возражениями'")
                st.markdown("""
                            **Гипотеза**: Для каждого каждого филиала вклад по критерию *"Профессиональная этика"* выше вклада по критерию *"Работа с возражениями"* в общую среднюю оценку по филиалу
                            
                            **Статистические гипотезы**:

                              - H0: средний вклад критерия "Профессиональная этика" <= средний вклад критерия "Работа с возражениями"
                            
                              - H1: средний вклад критерия "Профессиональная этика" > средний вклад критерия "Работа с возражениями"
                            """)
                df2 = analyzer.test_impact_ethics_vs_objections(min_pairs=min_pairs, alpha=alpha)
                st.dataframe(df2)
                st.download_button("⬇ Скачать результаты (Тест 2)", df2.to_csv(index=False), "test2_results.csv")

                st.subheader("Тест 3: Презентация продукта ≠ Работа с возражениями")
                st.markdown("""
                            **Гипотеза**: Для каждого каждого филиала средняя оценка по критерию *"Качество презентации продукта"* не отличается от средней оценки по критерию *"Работа с возражениями"*
                            
                            **Статистические гипотезы**:

                              - H0: среднее по критерию "Качество презентации продукта" = среднее по критерию "Работа с возражениями"
                            
                              - H1: среднее по критерию "Качество презентации продукта" ≠ среднее по критерию "Работа с возражениями"
                            """)
                df3 = analyzer.test_presentation_vs_objections(min_pairs=min_pairs, alpha=alpha)
                st.dataframe(df3)
                st.download_button("⬇ Скачать результаты (Тест 3)", df3.to_csv(index=False), "test3_results.csv")

    st.subheader("Средняя оценка филиалов по критериям — аудиобейджи (AUDIO_BADGE)")
    avg_badge_criteria = analyzer.get_avg_score_criteria(analyzer.df_badge)
    st.dataframe(avg_badge_criteria)

    st.subheader("Относительный вклад критериев — аудиобейджи")
    criteria_impact_badge = analyzer.get_criteria_impact(analyzer.df_badge, avg_score_criteria=avg_badge_criteria, avg_score_by_branch=analyzer.get_avg_score_by_branch_badge(), count_col="count_audio_badge")
    st.dataframe(criteria_impact_badge)
    fig = analyzer.plot_criteria_heatmap(criteria_impact_badge)
    st.pyplot(fig)
else:
    st.info("Сравнение по критериям недоступно, не хватает столбца 'criteria_name' и/ или базовых столбцов")

st.markdown("---")
st.success("Аналитика готова")