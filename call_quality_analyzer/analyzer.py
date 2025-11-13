import pandas as pd
import streamlit as st
from scipy.stats import wilcoxon

from data_preparation import prepare_data
from visualizations import (
    plot_score_distributions,
    plot_avg_bar,
    plot_weekly_trends,
    plot_weekly_grid,
    plot_heatmap,
)


class CallQualityAnalyzer:
    """
    Класс-обёртка, возвращает все сводные таблицы и фигуры, 
    аналогичные исходному ноутбуку (для всех типов и отдельно по REGULAR / AUDIO_BADGE).
    """
    # Минимальный набор обязательных столбцов
    REQUIRED_BASE = ["call_id", "call_type", "branch_name", "organization_name", "score"]

    def __init__(self, df: pd.DataFrame):
        """
        Инициализация: сначала сохраняем raw, подготавливаем данные,
        затем вычисляем df_call/df_badge, call_badge_count и доступные блоки.
        """
        # сохраняем "сырые" данные (на случай потребности)
        self.raw = df.copy()

        # подготавливаем (создаёт organization_branch_name, фильтрует score==0, парсит created_at)
        self.df = prepare_data(self.raw)

        # разделение по типам (безопасно — если нет колонки, получаем пустой DF)
        if "call_type" in self.df.columns:
            self.df_call = self.df[self.df["call_type"] == "REGULAR"].copy()
            self.df_badge = self.df[self.df["call_type"] == "AUDIO_BADGE"].copy()
        else:
            self.df_call = pd.DataFrame()
            self.df_badge = pd.DataFrame()

        # вычисляем таблицу с count по call_id (нужно для блока с вкладом критериев)
        self.call_badge_count = self._compute_call_badge_count()

        # когда self.df существует, можно корректно определить доступные блоки
        self.available_blocks = self._detect_available_blocks()

    def _detect_available_blocks(self):
        """
        Проверяет наличие необходимых столбцов.
        Блоки 1-2 требуют базовый набор,
        блок 3 — базовый + created_at,
        блок 4 — базовый + criteria_name.
        """
        cols = set(self.df.columns) if hasattr(self, "df") and self.df is not None else set()

        base_ok = all(c in cols for c in self.REQUIRED_BASE)
        date_ok = "created_at" in cols
        criteria_ok = "criteria_name" in cols

        return {
            "Распределение оценок/звонков, средние оценки": base_ok,
            "Динамика оценок": base_ok and date_ok,
            "Анализ критериев оценок": base_ok and criteria_ok,
                }
 
      
    # вспомогательное: call/badge counts (по уникальным call_id)
    def _compute_call_badge_count(self, grouper="organization_branch_name"):
        if self.df.empty or grouper not in self.df.columns:
            return pd.DataFrame()
        df_call = self.df[self.df["call_type"] == "REGULAR"]
        df_badge = self.df[self.df["call_type"] == "AUDIO_BADGE"]

        df_all = self.df.pivot_table(index=grouper, values="call_id", aggfunc="nunique").reset_index()
        df_all.columns = [grouper, "count_all_type_call"]

        df_call_count = df_call.pivot_table(index=grouper, values="call_id", aggfunc="nunique").reset_index()
        df_call_count.columns = [grouper, "count_call"]

        df_badge_count = df_badge.pivot_table(index=grouper, values="call_id", aggfunc="nunique").reset_index()
        df_badge_count.columns = [grouper, "count_audio_badge"]

        merged = df_all.merge(df_call_count, on=grouper, how="outer").merge(df_badge_count, on=grouper, how="outer")
        merged = merged.fillna(0)
        for c in ["count_call", "count_audio_badge"]:
            if c in merged.columns:
                merged[c] = merged[c].astype("int64")
        return merged.sort_values(by="count_all_type_call", ascending=False).reset_index(drop=True)
        
 
    # 1. Распределение оценок по филиалам (количества по оценкам -> counts)
    # возвращаем counts таблицу: count_all_score, count_call_score, count_audio_badge_score

    def get_all_score_by_branch(self, grouper="organization_branch_name"):
        if self.df.empty or grouper not in self.df.columns:
            return pd.DataFrame()
        # value_counts на всей выборке и для подвыборок
        df_all = self.df[grouper].value_counts().reset_index()
        df_all.columns = [grouper, "count_all_score"]

        df_call = self.df_call[grouper].value_counts().reset_index() if not self.df_call.empty else pd.DataFrame(columns=[grouper, "count_call_score"])
        if not df_call.empty:
            df_call.columns = [grouper, "count_call_score"]

        df_badge = self.df_badge[grouper].value_counts().reset_index() if not self.df_badge.empty else pd.DataFrame(columns=[grouper, "count_audio_badge_score"])
        if not df_badge.empty:
            df_badge.columns = [grouper, "count_audio_badge_score"]

        merged = df_all.merge(df_call, on=grouper, how="outer").merge(df_badge, on=grouper, how="outer").fillna(0)
        merged[["count_call_score", "count_audio_badge_score"]] = merged[["count_call_score", "count_audio_badge_score"]].astype("int64")
        merged = merged.sort_values(by="count_all_score", ascending=False).reset_index(drop=True)
        return merged

    # call counts (unique call_id) - аналог get_call_count
    def get_call_count(self, grouper="organization_branch_name"):
        return self._compute_call_badge_count(grouper=grouper)

    # plot distributions (возвращают фигуру)
    # три варианта: по всей выборке, только звонки, только бейджи
    
    def plot_distributions_all(self):
        return plot_score_distributions(self.df, title="Распределение оценок: все типы")

    def plot_distributions_call(self):
        return plot_score_distributions(self.df_call, title="Распределение оценок: звонки (REGULAR)")

    def plot_distributions_badge(self):
        return plot_score_distributions(self.df_badge, title="Распределение оценок: аудиобейджи (AUDIO_BADGE)")

    # 2. Средние оценки по филиалам (all / call / badge)
    
    def get_avg_score_by_branch(self):
        if self.df.empty:
            return pd.DataFrame()
        avg = self.df.pivot_table(index="organization_branch_name", values="score", aggfunc="mean").round(1).reset_index().rename(columns={"score": "avg_score"})
        return avg.sort_values(by="avg_score", ascending=False).reset_index(drop=True)

    def get_avg_score_by_branch_call(self):
        if self.df_call.empty:
            return pd.DataFrame()
        avg = self.df_call.pivot_table(index="organization_branch_name", values="score", aggfunc="mean").round(1).reset_index().rename(columns={"score": "avg_score"})
        return avg.sort_values(by="avg_score", ascending=False).reset_index(drop=True)

    def get_avg_score_by_branch_badge(self):
        if self.df_badge.empty:
            return pd.DataFrame()
        avg = self.df_badge.pivot_table(index="organization_branch_name", values="score", aggfunc="mean").round(1).reset_index().rename(columns={"score": "avg_score"})
        return avg.sort_values(by="avg_score", ascending=False).reset_index(drop=True)

    def plot_avg_score(self):
        return plot_avg_bar(self.get_avg_score_by_branch(), title="Средняя оценка филиалов (все типы)")

    def plot_avg_score_call(self):
        return plot_avg_bar(self.get_avg_score_by_branch_call(), title="Средняя оценка филиалов — звонки")

    def plot_avg_score_badge(self):
        return plot_avg_bar(self.get_avg_score_by_branch_badge(), title="Средняя оценка филиалов — аудиобейджи")

    def get_full_avg_score_by_branch(self, grouper="organization_branch_name"):
        """
        Объединённая сводная по звонкам и бейджам (по аналогии с ноутбуком).
        Возвращаем таблицу со столбцами avg_score_call, avg_score_badge.
        """
        avg_call = self.get_avg_score_by_branch_call().rename(columns={"avg_score": "avg_score_call"})
        avg_badge = self.get_avg_score_by_branch_badge().rename(columns={"avg_score": "avg_score_badge"})
        # outer merge по поля (если пустые — вернём то, что есть)
        merged = pd.merge(avg_call, avg_badge, on=grouper, how="outer")
        # если нужно — можно добавить avg_all из get_avg_score_by_branch
        avg_all = self.get_avg_score_by_branch().rename(columns={"avg_score": "avg_score_all"})
        merged = avg_all.merge(merged, on=grouper, how="outer")
        # сортировка по полю avg_score_all (если есть)
        if "avg_score_all" in merged.columns:
            merged = merged.sort_values(by="avg_score_all", ascending=False).reset_index(drop=True)
        return merged

    # 3. Недельная динамика
    
    def add_week_from_start(self, df_in, date_col="created_at"):
        df = df_in.copy()
        if date_col not in df.columns:
            return df
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.floor("D")
        start_date = df[date_col].min()
        if pd.isna(start_date):
            return df
        start_week_date = start_date - pd.to_timedelta(start_date.weekday(), unit="D")
        df["week_from_start"] = ((df[date_col] - start_week_date).dt.days // 7) + 1
        return df

    def get_avg_score_by_week(self, df_in=None):
        """
        Возвращает сводную таблицу: строки — филиалы, колонки — week_1, week_2, ...
        По умолчанию берёт полный df, можно передать df_call или df_badge.
        """
        if df_in is None:
            df_in = self.df
        if df_in.empty or "created_at" not in df_in.columns:
            return pd.DataFrame()
        df2 = self.add_week_from_start(df_in, date_col="created_at")
        pivot = df2.pivot_table(index="organization_branch_name", columns="week_from_start", values="score",     aggfunc="mean").round(1).dropna(how="all").sort_values(by=1, ascending=False)
        if pivot.empty:
            return pd.DataFrame()
        # reset & rename columns to week_1, week_2...
        pivot = pivot.reset_index()
        new_cols = ["organization_branch_name"] + [f"week_{int(c)}" for c in pivot.columns[1:]]
        pivot.columns = new_cols
        return pivot

    def plot_weekly_all(self):
        return plot_weekly_trends(self.get_avg_score_by_week(self.df), title="Недельная динамика — все типы")

    def plot_weekly_call(self):
        return plot_weekly_trends(self.get_avg_score_by_week(self.df_call), title="Недельная динамика — звонки (REGULAR)")

    def plot_weekly_badge(self):
        return plot_weekly_trends(self.get_avg_score_by_week(self.df_badge), title="Недельная динамика — аудиобейджи (AUDIO_BADGE)")

    def plot_weekly_grid_all(self):
        return plot_weekly_grid(self.get_avg_score_by_week(self.df), group_col="organization_branch_name", title="Графики недельной динамики — все типы")

    def plot_weekly_grid_call(self):
        return plot_weekly_grid(self.get_avg_score_by_week(self.df_call), group_col="organization_branch_name", title="Графики недельной динамики — звонки")

    def plot_weekly_grid_badge(self):
        return plot_weekly_grid(self.get_avg_score_by_week(self.df_badge), group_col="organization_branch_name", title="Графики недельной динамики — аудиобейджи")

    # 4. По критериям: pivot и impact
    
    def get_avg_score_criteria(self, df_in=None):
        if df_in is None:
            df_in = self.df
        if df_in.empty or "criteria_name" not in df_in.columns:
            return pd.DataFrame()
        pivot = df_in.pivot_table(index="organization_branch_name", columns="criteria_name", values="score", aggfunc="mean").round(1).reset_index()
        pivot.columns.name = None
        return pivot

    def get_criteria_impact(self, df_in=None, avg_score_criteria=None, avg_score_by_branch=None, count_col="count_all_type_call"):
        """
        Возвращает скорректированный вклад критериев (criteria_corr_impact),
        как в исходном ноутбуке.
        Если некоторые аргументы не переданы, они будут рассчитаны из self.
        """
        if df_in is None:
            df_in = self.df
        if avg_score_criteria is None:
            avg_score_criteria = self.get_avg_score_criteria(df_in)
        if avg_score_criteria.empty:
            return pd.DataFrame()
        if avg_score_by_branch is None:
            avg_score_by_branch = self.get_avg_score_by_branch()

        # соединяем
        merged = avg_score_criteria.merge(avg_score_by_branch, on="organization_branch_name").set_index("organization_branch_name")
        # impact = avg_by_crit / avg_overall
        criteria_impact = merged.div(merged["avg_score"], axis=0).drop(columns="avg_score").round(2)

        # counts by criteria
        score_count = df_in.pivot_table(index="organization_branch_name", columns="criteria_name", values="score", aggfunc="count").reset_index()
        # merge call_badge_count to get denominator
        counts_merge = score_count.merge(self.call_badge_count[["organization_branch_name", count_col]], on="organization_branch_name", how="left").set_index("organization_branch_name")
        criteria_share = counts_merge.div(counts_merge[count_col], axis=0).fillna(0).drop(columns=count_col)

        criteria_corr_impact = (1 + criteria_share * (criteria_impact - 1)).fillna(0).round(2)
        return criteria_corr_impact

    def plot_criteria_heatmap(self, df_heat=None):
        if df_heat is None:
            df_heat = self.get_criteria_impact()
        if df_heat is None or df_heat.empty:
            return plt.figure()
        return plot_heatmap(df_heat, title="Относительный вклад критериев в общую оценку филиала")
    
    # вспомогательные функции для статистических тестов
    def _count_scores_per_branch(self, df_calls, criteria_list):
        """
        Возвращает словарь branch -> {criterion: count}
        """
        counts = (
            df_calls[df_calls["criteria_name"].isin(criteria_list)]
            .groupby(["organization_branch_name", "criteria_name"])["score"]
            .count()
            .unstack(fill_value=0)
            .to_dict(orient="index")
                )
        return counts

    def _branch_has_enough_scores(self, counts_dict, branch, criteria_list, min_n=10):
        """Проверяет, что у филиала есть >= min_n оценок по каждому из критериев."""
        if branch not in counts_dict:
            return False
        for crit in criteria_list:
            if counts_dict[branch].get(crit, 0) < min_n:
                return False
        return True

    # ТЕСТ 1: Проф. этика > Активное слушание
    def test_professional_vs_active_listening(self, min_pairs=10, alpha=0.05):
        df_calls = self.df.copy()
        criteria_main = "Профессиональная этика"
        criteria_cmp = "Активное слушание"

        results = []
        counts = self._count_scores_per_branch(df_calls, [criteria_main, criteria_cmp])

        for branch in sorted(df_calls["organization_branch_name"].dropna().unique()):
            if not self._branch_has_enough_scores(counts, branch, [criteria_main, criteria_cmp], min_pairs):
                continue

            sub = df_calls[df_calls["organization_branch_name"] == branch]
            calls = sub.pivot(index="call_id", columns="criteria_name", values="score")
            if not {criteria_main, criteria_cmp}.issubset(calls.columns):
                continue
            
            common_idx = calls.dropna(subset=[criteria_main, criteria_cmp]).index
            if len(common_idx) < min_pairs:
                continue

            x = calls.loc[common_idx, criteria_main]
            y = calls.loc[common_idx, criteria_cmp]
            # Тест Вилкоксона
            stat, p = wilcoxon(x, y, alternative="greater")
            conclusion = (
                    "Средняя оценка по критерию 'Профессиональная этика' статистически значимо выше"
                    if p < alpha else
                    "Средние оценки по критериям не имеют различий"
                            )
            results.append({
                "Филиал": branch,
                "n_pairs": len(common_idx),
                "p-value": round(p, 5),
                "Вывод": conclusion
                            })
        return pd.DataFrame(results)


    # ТЕСТ 2: Вклад Проф. этика > Вклад Работа с возражениями
    def test_impact_ethics_vs_objections(self, min_pairs=10, alpha=0.05):
        df_calls = self.df.copy()
        c1 = "Профессиональная этика"
        c2 = "Работа с возражениями"

        results = []
        counts = self._count_scores_per_branch(df_calls, [c1, c2])

        for branch in sorted(df_calls["organization_branch_name"].dropna().unique()):
            if not self._branch_has_enough_scores(counts, branch, [c1, c2], min_pairs):
                continue

            sub = df_calls[df_calls["organization_branch_name"] == branch]
            calls_with_both = sub.groupby("call_id")["criteria_name"].apply(lambda x: {c1, c2} <= set(x))
            calls_with_both = calls_with_both[calls_with_both].index
            if len(calls_with_both) < min_pairs:
                continue

            sub_valid = sub[sub["call_id"].isin(calls_with_both)]
            mean_branch = sub_valid["score"].mean()

            diff1 = (sub_valid[sub_valid["criteria_name"] == c1]["score"] - mean_branch).abs()
            diff2 = (sub_valid[sub_valid["criteria_name"] == c2]["score"] - mean_branch).abs()

            stat, p = wilcoxon(diff1, diff2, alternative="greater")
            conclusion = (
                "Вклад критерия 'Профессиональная этика' статистически значимо выше"
                if p < alpha else
                "Средние оценки по критериям не имеют различий"
                         )
            results.append({
                "Филиал": branch,
                "n_pairs": len(calls_with_both),
                "p-value": round(p, 5),
                "Вывод": conclusion
                           })
        return pd.DataFrame(results)

    # ТЕСТ 3: Презентация продукта ≠ Работа с возражениями
    def test_presentation_vs_objections(self, min_pairs=10, alpha=0.05):
        df_calls = self.df.copy()
        c1 = "Качество презентации продукта"
        c2 = "Работа с возражениями"

        results = []
        counts = self._count_scores_per_branch(df_calls, [c1, c2])

        for branch in sorted(df_calls["organization_branch_name"].dropna().unique()):
            if not self._branch_has_enough_scores(counts, branch, [c1, c2], min_pairs):
                continue

            sub = df_calls[df_calls["organization_branch_name"] == branch]
            calls = sub.pivot(index="call_id", columns="criteria_name", values="score")
            
            if not {c1, c2}.issubset(calls.columns):
                continue
            
            common_idx = calls.dropna(subset=[c1, c2]).index
            if len(common_idx) < min_pairs:
                continue

            x = calls.loc[common_idx, c1]
            y = calls.loc[common_idx, c2]
            stat, p = wilcoxon(x, y, alternative="two-sided")
            conclusion = (
                "Различия статистически значимы"
                if p < alpha else
                "Средние оценки по критериям не имеют различий"
            )
            results.append({
                "Филиал": branch,
                "n_pairs": len(common_idx),
                "p-value": round(p, 5),
                "Вывод": conclusion
            })
        return pd.DataFrame(results)