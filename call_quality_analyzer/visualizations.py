import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set_style("whitegrid")


def plot_score_distributions(df: pd.DataFrame,
                             group_col="organization_branch_name",
                             score_col="score",
                             title="Распределение оценок по филиалам",
                             bins=10, col_wrap=2, height=4, aspect=1.2,
                             fontsize_title=16, fontsize_labels=12):
    """
    FacetGrid гистограмм по колонке group_col. Возвращает matplotlib.figure.
    """
    if df is None or df.empty:
        return plt.figure()

    g = sns.FacetGrid(df, col=group_col, col_wrap=col_wrap, height=height, aspect=aspect)
    g.map(sns.histplot, score_col, bins=bins, stat="probability", kde=True)

    # добавляем mean/median lines
    for branch_name, ax in g.axes_dict.items():
        subset = df.loc[df[group_col] == branch_name, score_col].dropna()
        if subset.empty:
            continue
        mean_val = subset.mean()
        median_val = subset.median()
        ax.axvline(mean_val, color="red", linestyle="--", linewidth=2, label=f"Mean={mean_val:.2f}")
        ax.axvline(median_val, color="green", linestyle="-.", linewidth=2, label=f"Median={median_val:.2f}")
        ax.legend(fontsize=8)

    g.set_titles(col_template="{col_name}", size=fontsize_labels)
    g.fig.subplots_adjust(top=0.92, hspace=0.3)
    g.fig.suptitle(title, fontsize=fontsize_title)
    return g.fig


def plot_avg_bar(df_avg: pd.DataFrame, x="organization_branch_name", y="avg_score",
                 title="Средняя оценка филиалов", figsize=(10, 6)):
    if df_avg is None or df_avg.empty:
        return plt.figure()
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(data=df_avg, x=x, y=y, ax=ax)
    # подписи значений
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=9)
    ax.set_title(title)
    ax.set_xlabel("Филиал")
    ax.set_ylabel("Средняя оценка")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def plot_weekly_trends(df_weekly: pd.DataFrame, title="Недельная динамика средней оценки по филиалам"):
    if df_weekly is None or df_weekly.empty:
        return plt.figure()
    # melt
    melted = df_weekly.melt(id_vars="organization_branch_name", var_name="week", value_name="average_score")
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.lineplot(data=melted, x="week", y="average_score", hue="organization_branch_name", marker="o", ax=ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8)
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    ax.set_xlabel("Неделя")
    ax.set_ylabel("Средняя оценка")
    ax.set_title(title)
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.15)
    return fig


def plot_weekly_grid(df_weekly: pd.DataFrame, group_col="organization_branch_name",
                     col_wrap=2, height=3.5, aspect=1.5, title="Графики недельной динамики по филиалам"):
    if df_weekly is None or df_weekly.empty:
        return plt.figure()
    melted = df_weekly.melt(id_vars="organization_branch_name", var_name="week", value_name="average_score")
    g = sns.FacetGrid(melted, col=group_col, col_wrap=col_wrap, height=height, aspect=aspect)
    g.map_dataframe(sns.lineplot, x="week", y="average_score", marker="o")
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Неделя", "Средняя оценка")
    g.fig.subplots_adjust(top=0.92, hspace=0.3)
    g.fig.suptitle(title, fontsize=14)
    return g.fig


def plot_heatmap(df_heat: pd.DataFrame, title="Тепловая карта по критериям (средние)"):
    if df_heat is None or df_heat.empty:
        return plt.figure()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(df_heat, annot=True, fmt=".2f", cmap="coolwarm", center=df_heat.stack().mean(), ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Критерий")
    ax.set_ylabel("Филиал")
    plt.tight_layout()
    return fig