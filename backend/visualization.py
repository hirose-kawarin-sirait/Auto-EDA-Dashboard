import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as scipy_stats


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

DARK_BG   = '#1e2140'
PLOT_BG   = '#252847'
COLORS    = px.colors.qualitative.Plotly

def _layout(fig, title='', height=380):
    fig.update_layout(
        title=None,
        template='plotly_dark',
        paper_bgcolor=DARK_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=40, r=20, t=20, b=40),
        height=height,
        font=dict(color='#e0e0e0'),
        autosize=True,
        width=None,
    )
    return fig

def _json(fig):
    return fig.to_json(engine='json')

def _chart(title, fig, height=380, full_width=False):
    _layout(fig, title, height)
    return {'title': title, 'chart': _json(fig), 'full_width': full_width}


# ─────────────────────────────────────────────
#  SINGLE CHART  (route /visualize)
# ─────────────────────────────────────────────

def generate_single_chart(df, column, chart_type):
    if column not in df.columns:
        return {'error': f'Column {column} not found'}

    data = df[column].dropna()
    fig  = None

    if chart_type == 'histogram':
        fig = px.histogram(df, x=column, color_discrete_sequence=['#6c63ff'])

    elif chart_type == 'boxplot':
        fig = px.box(df, y=column, color_discrete_sequence=["#b463ff"])

    elif chart_type == 'density':
        kde_x = np.linspace(data.min(), data.max(), 200)
        kde   = scipy_stats.gaussian_kde(data)
        fig   = go.Figure(go.Scatter(x=kde_x, y=kde(kde_x),
                                     fill='tozeroy', line_color='#6c63ff'))

    elif chart_type == 'violin':
        fig = px.violin(df, y=column, box=True,
                        color_discrete_sequence=['#6c63ff'])

    elif chart_type == 'bar':
        counts = data.value_counts().head(20)
        fig = px.bar(x=counts.index.tolist(), y=counts.values.tolist(),
                     color_discrete_sequence=['#6c63ff'])

    elif chart_type == 'pie':
        counts = data.value_counts().head(10)
        fig = px.pie(names=counts.index.tolist(),
                     values=counts.values.tolist(),
                     color_discrete_sequence=COLORS)

    elif chart_type == 'scatter':
        fig = px.scatter(df, x=df.columns[0], y=column,
                         color_discrete_sequence=['#6c63ff'])

    elif chart_type == 'heatmap':
        num_df = df.select_dtypes(include=np.number)
        corr   = num_df.corr().round(2)
        fig    = px.imshow(corr, text_auto=True,
                           color_continuous_scale='RdBu', zmin=-1, zmax=1)

    else:
        return {'error': f'Chart type {chart_type} not supported'}

    _layout(fig)
    return {'chart': _json(fig)}


# ─────────────────────────────────────────────
#  UNIVARIATE
# ─────────────────────────────────────────────

def generate_univariate(df, column, var_type):
    if not column or column not in df.columns:
        return {'error': 'Kolom tidak valid'}

    charts = []
    data   = df[column].dropna()

    if var_type == 'numerical':
        # 1. Histogram
        # Buat histogram dengan warna gradient per bar
        counts, bins = np.histogram(df[column].dropna(), bins=30)
        bin_centers = (bins[:-1] + bins[1:]) / 2

        # Gradient ungu ke biru
        import plotly.colors as pc
        palette = pc.sample_colorscale('Purples', [i/len(counts) for i in range(len(counts))])

        fig = go.Figure(go.Bar(
            x=bin_centers,
            y=counts,
            marker=dict(
                color=palette,
                line=dict(width=0),
            ),
            width=(bins[1] - bins[0]) * 0.9,
        ))
        fig.update_xaxes(title=column)
        fig.update_yaxes(title='Count')
        charts.append(_chart(f'Histogram — {column}', fig))

        # 2. Boxplot
        fig = px.box(df, y=column, points='outliers',
             color_discrete_sequence=['#00c864'])
        fig.update_traces(marker_color='#ffd700',
                          line_color='#00c864',
                          fillcolor='rgba(0,200,100,0.3)')
        charts.append(_chart(f'Boxplot — {column}', fig))

        # 3. Density (KDE)
        kde_x = np.linspace(data.min(), data.max(), 300)
        kde   = scipy_stats.gaussian_kde(data)
        fig = go.Figure(go.Scatter(
            x=kde_x, y=kde(kde_x),
            fill='tozeroy',
            line=dict(color='#a855f7', width=2),
            fillcolor='rgba(108,99,255,0.2)',
            name='KDE',
        ))
        fig.update_xaxes(title=column)
        fig.update_yaxes(title='Density')
        charts.append(_chart(f'Density Plot — {column}', fig))

        # 4. QQ Plot
        (osm, osr), (slope, intercept, _) = scipy_stats.probplot(data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(osm), y=list(osr),
                         mode='markers', name='Data',
                         marker=dict(
                             color=list(osm),
                             colorscale='Purples',
                             size=5,
                             showscale=False,
                         )))
        ref_x = [min(osm), max(osm)]
        ref_y = [slope * v + intercept for v in ref_x]
        fig.add_trace(go.Scatter(x=ref_x, y=ref_y,
                                 mode='lines', name='Normal Line',
                                 line=dict(color='#ff6464', dash='dash')))
        fig.update_xaxes(title='Theoretical Quantiles')
        fig.update_yaxes(title='Sample Quantiles')
        charts.append(_chart(f'QQ Plot — {column}', fig))

        # 5. Violin
        fig = px.violin(df, y=column, box=True, points='all',
                        color_discrete_sequence=['#a855f7'])
        fig.update_traces(fillcolor='rgba(168,85,247,0.3)',
                         line_color='#6c63ff',
                         marker=dict(color="#00ffe5", size=3, opacity=0.5))
        charts.append(_chart(f'Violin Plot — {column}', fig))

    elif var_type == 'categorical':
        # Guard: tolak kalau terlalu banyak unique (kemungkinan date/ID)
        if data.nunique() > 50:
            return {'error': f'Kolom "{column}" memiliki {data.nunique()} unique values — terlalu banyak untuk analisis kategorikal. Pilih kolom dengan kategori lebih sedikit.'}

        counts = data.astype(str).value_counts()

        # 1. Bar Chart
        cat_labels = [str(x) for x in counts.index.tolist()]
        n = len(cat_labels)
        # Gradient ungu tua ke muda
        bar_colors = [f'hsl(260, {int(70 - i * 20 / max(n-1,1))}%, {int(35 + i * 30 / max(n-1,1))}%)' for i in range(n)]

        fig = px.bar(x=cat_labels, y=counts.values.tolist(),
                     color=cat_labels,
                     color_discrete_sequence=bar_colors)
        fig.update_xaxes(title=column, tickangle=-45, tickfont=dict(size=10))
        fig.update_yaxes(title='Count')
        fig.update_layout(showlegend=False, bargap=0.15, autosize=True)
        charts.append(_chart(f'Bar Chart — {column}', fig))

        # 2. Pie Chart
        top = counts.head(10)
        n = len(top)
        pie_colors = [f'hsl(140, {int(70 - i * 20 / max(n-1,1))}%, {int(25 + i * 35 / max(n-1,1))}%)' for i in range(n)]

        fig = px.pie(names=[str(x) for x in top.index.tolist()],
                     values=top.values.tolist(),
                     color_discrete_sequence=pie_colors,
                     hole=0.3)
        fig.update_layout(autosize=True)
        charts.append(_chart(f'Pie Chart — {column}', fig))

        # 3. Count Plot (horizontal bar)
        n = len(counts)
        palette = [f'hsl({int(260 + i * 80 / max(n-1,1))}, 70%, {int(55 + i * 20 / max(n-1,1))}%)' for i in range(n)]
        fig = go.Figure(go.Bar(
            y=[str(x) for x in counts.index.tolist()],
            x=counts.values.tolist(),
            orientation='h',
            text=counts.values.tolist(),
            textposition='outside',
            marker_color=palette,
        ))
        fig.update_xaxes(title='Count')
        fig.update_yaxes(title=column, autorange='reversed')
        fig.update_layout(showlegend=False, margin=dict(l=120, r=20, t=20, b=40))
        fig.update_layout(autosize=True)
        charts.append(_chart(f'Count Plot — {column}', fig))

        # 4. Pareto Chart
        pareto_labels = [str(x) for x in counts.index.tolist()]
        cum_pct = counts.cumsum() / counts.sum() * 100
        fig = go.Figure()
        fig.add_trace(go.Bar(x=pareto_labels,
                             y=counts.values.tolist(),
                             name='Count',
                             marker_color='#6c63ff'))
        fig.add_trace(go.Scatter(x=pareto_labels,
                                 y=cum_pct.values.tolist(),
                                 name='Cumulative %',
                                 yaxis='y2',
                                 line=dict(color='#ffd700', width=2),
                                 mode='lines+markers'))
        fig.update_layout(
            yaxis2=dict(title='Cumulative %', overlaying='y',
                        side='right', range=[0, 110], showgrid=False),
            showlegend=False
        )
        fig.update_xaxes(tickangle=-45, tickfont=dict(size=10))
        fig.update_layout(autosize=True, showlegend=False)
        charts.append(_chart(f'Pareto Chart — {column}', fig))
    else:
        return {'error': 'var_type harus numerical atau categorical'}

    return {'charts': charts}


# ─────────────────────────────────────────────
#  BIVARIATE
# ─────────────────────────────────────────────

def generate_bivariate(df, col1, col2):
    if not col1 or not col2:
        return {'error': 'Pilih 2 kolom'}
    if col1 not in df.columns or col2 not in df.columns:
        return {'error': 'Kolom tidak ditemukan'}

    charts = []

    # 1. Scatter Plot
    fig = px.scatter(df, x=col1, y=col2,
                     color_discrete_sequence=["#ffe563"],
                     opacity=0.7)
    charts.append(_chart(f'Scatter Plot — {col1} vs {col2}', fig))

    # 2. Correlation Heatmap (2 kolom)
    corr_val = round(float(df[[col1, col2]].corr().iloc[0, 1]), 4)
    fig = go.Figure(go.Heatmap(
        z=[[1, corr_val], [corr_val, 1]],
        x=[col1, col2], y=[col1, col2],
        colorscale='RdBu', zmin=-1, zmax=1,
        text=[[1, corr_val], [corr_val, 1]],
        texttemplate='%{text}',
    ))
    charts.append(_chart(f'Correlation Heatmap — {col1} & {col2}', fig))

    # 3. Regression Plot
    clean = df[[col1, col2]].dropna()
    x_vals = clean[col1].values
    y_vals = clean[col2].values
    m, b, r, p, se = scipy_stats.linregress(x_vals, y_vals)
    x_line = np.linspace(x_vals.min(), x_vals.max(), 200)
    y_line = m * x_line + b

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals.tolist(), y=y_vals.tolist(),
                             mode='markers', name='Data',
                             marker=dict(color="#7aff63", size=5, opacity=0.6)))
    fig.add_trace(go.Scatter(x=x_line.tolist(), y=y_line.tolist(),
                             mode='lines', name=f'y={m:.2f}x+{b:.2f}',
                             line=dict(color='#ff6464', width=2)))
    fig.update_xaxes(title=col1)
    fig.update_yaxes(title=col2)
    charts.append(_chart(f'Regression Plot — {col1} vs {col2}', fig, height=450))

    # 4. Bubble Chart (size = abs residual)
    residuals = np.abs(y_vals - (m * x_vals + b))
    fig = px.scatter(x=x_vals.tolist(), y=y_vals.tolist(),
                     size=residuals.tolist(),
                     color=residuals.tolist(),
                     color_continuous_scale='Viridis',
                     labels={'x': col1, 'y': col2},
                     size_max=30)
    charts.append(_chart(f'Bubble Chart — {col1} vs {col2}', fig))

    return {'charts': charts}


# ─────────────────────────────────────────────
#  MULTIVARIATE
# ─────────────────────────────────────────────

def generate_multivariate(df, columns, hue=None, bubble_size=None):
    if len(columns) < 2:
        return {'error': 'Pilih minimal 2 kolom'}

    missing = [c for c in columns if c not in df.columns]
    if missing:
        return {'error': f'Kolom tidak ditemukan: {missing}'}

    charts = []
    num_df = df[columns].dropna()

    # 1. Correlation Heatmap
    corr = num_df.corr().round(2)
    fig  = px.imshow(corr, text_auto=True,
                     color_continuous_scale='RdBu', zmin=-1, zmax=1)
    charts.append(_chart('Correlation Heatmap', fig, height=max(350, len(columns)*60)))

    # 2. Pair Plot (Plotly interaktif dengan diagonal histogram)
    color_col = hue if (hue and hue in df.columns) else None
    plot_df   = df[columns + ([hue] if color_col else [])].dropna()
    if len(plot_df) > 1000:
        plot_df = plot_df.sample(1000, random_state=42)

    n = len(columns)
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=n, cols=n,
                        shared_xaxes=False,
                        shared_yaxes=False,
                        horizontal_spacing=0.05,
                        vertical_spacing=0.05)

    # Kategori untuk warna
    SCATTER_COLORS = ['#ff6b6b', '#ffd93d', '#6bcb77', '#4d96ff', '#ff922b',
                      '#cc5de8', '#20c997', '#f06595', '#74c0fc', '#a9e34b']

    if color_col:
        categories = plot_df[color_col].unique().tolist()
        cat_colors = SCATTER_COLORS[:len(categories)]
    else:
        categories = [None]
        cat_colors = SCATTER_COLORS

    for i, col_y in enumerate(columns):
        for j, col_x in enumerate(columns):
            for k, (cat, color) in enumerate(zip(categories, cat_colors)):
                if color_col and cat is not None:
                    mask = plot_df[color_col] == cat
                    sub  = plot_df[mask]
                    name = str(cat)
                else:
                    sub  = plot_df
                    name = col_x

                show_legend = (i == 0 and j == 1 and color_col is not None)

                if i == j:
                     # Diagonal → histogram dengan warna gradient per bar
                     hist_vals, hist_bins = np.histogram(sub[col_x].dropna(), bins=20)
                     bin_centers = (hist_bins[:-1] + hist_bins[1:]) / 2
                     n_bins = len(hist_vals)
                     # Warna gradient dari ungu muda ke ungu terang per kolom
                     base_hue = (260 + i * 40) % 360
                     bar_colors = [f'hsl({base_hue}, {int(55 + k*25/max(n_bins-1,1))}%, {int(40 + k*30/max(n_bins-1,1))}%)' for k in range(n_bins)]
                     fig.add_trace(go.Bar(
                         x=bin_centers,
                         y=hist_vals,
                         name=name,
                         marker=dict(color=bar_colors, line=dict(width=0)),
                         width=(hist_bins[1] - hist_bins[0]) * 0.85,
                         opacity=0.85,
                         showlegend=show_legend,
                         legendgroup=name,
                     ), row=i+1, col=j+1)
                else:
                    # Off-diagonal → scatter
                    scatter_color = SCATTER_COLORS[(i * n + j) % len(SCATTER_COLORS)]
                    fig.add_trace(go.Scatter(
                        x=sub[col_x],
                        y=sub[col_y],
                        mode='markers',
                        name=name,
                        marker=dict(color=scatter_color, size=4, opacity=0.6),
                        showlegend=show_legend,
                        legendgroup=name,
                    ), row=i+1, col=j+1)

    # Tambah label sumbu hanya di tepi
    for i, col in enumerate(columns):
        fig.update_yaxes(title_text=col, row=i+1, col=1,
                         title_font=dict(size=10, color='#e0e0e0'),
                         tickfont=dict(size=8))
        fig.update_xaxes(title_text=col, row=n, col=i+1,
                         title_font=dict(size=10, color='#e0e0e0'),
                         tickfont=dict(size=8))

    charts.append(_chart('Pair Plot', fig, height=max(600, n * 180)))


    # 3. Bubble Chart
    if len(columns) >= 3:
        x_col, y_col, z_col = columns[0], columns[1], columns[2]
        size_col = bubble_size if (bubble_size and bubble_size in df.columns) else z_col
        plot_df2 = df[[x_col, y_col, z_col] +
                       ([hue] if color_col else []) +
                       ([size_col] if size_col != z_col else [])].dropna()
        # normalise size
        sz = plot_df2[size_col].abs()
        sz = ((sz - sz.min()) / (sz.max() - sz.min() + 1e-9) * 40 + 5).tolist()
        fig = px.scatter(plot_df2, x=x_col, y=y_col,
                         size=sz,
                         color=hue if color_col else z_col,
                         color_discrete_sequence=COLORS,
                         color_continuous_scale='Viridis',
                         opacity=0.7,
                         labels={'x': x_col, 'y': y_col})
        charts.append(_chart(f'Bubble Chart — {x_col} vs {y_col} (size: {size_col})', fig, height=500, full_width=True))
    return {'charts': charts}


# ─────────────────────────────────────────────
#  CAT vs NUM
# ─────────────────────────────────────────────

def generate_cat_vs_num(df, num_col, cat_col):
    if not num_col or not cat_col:
        return {'error': 'Pilih kolom numerik dan kategorikal'}
    if num_col not in df.columns or cat_col not in df.columns:
        return {'error': 'Kolom tidak ditemukan'}

    # Batasi data supaya tidak crash
    df = df[[num_col, cat_col]].dropna()
    if len(df) > 5000:
        df = df.sample(5000, random_state=42)

    charts  = []
    # Kalau kolom kategori bertipe datetime, konversi ke string pendek
    if pd.api.types.is_datetime64_any_dtype(df[cat_col]):
        df = df.copy()
        df[cat_col] = df[cat_col].dt.strftime('%Y-%m')

    df = df.copy()
    df[cat_col] = df[cat_col].astype(str)
    top_cats = df[cat_col].value_counts().head(10).index.tolist()
    filtered = df[df[cat_col].isin(top_cats)]

    # 1. Boxplot by Category
    n_cats = len(top_cats)
    brown_colors = [f'hsl(30, {int(70 - i * 20 / max(n_cats-1,1))}%, {int(20 + i * 40 / max(n_cats-1,1))}%)' for i in range(n_cats)]

    fig = px.box(filtered, x=cat_col, y=num_col,
                 color=cat_col,
                 color_discrete_sequence=brown_colors,
                 points='outliers')
    charts.append(_chart(f'Boxplot — {num_col} by {cat_col}', fig))

    # 2. Violin by Category
    n_cats = len(top_cats)
    purple_colors = [f'hsl(270, {int(70 - i * 15 / max(n_cats-1,1))}%, {int(20 + i * 40 / max(n_cats-1,1))}%)' for i in range(n_cats)]

    fig = px.violin(filtered, x=cat_col, y=num_col,
                color=cat_col,
                color_discrete_sequence=purple_colors,
                box=True, points=False)
    charts.append(_chart(f'Violin — {num_col} by {cat_col}', fig))
    
    # 3. Grouped Bar Chart (mean per category)
    means = filtered.groupby(cat_col)[num_col].mean().reindex(top_cats)
    n_means = len(means)
    yellow_colors = [f'hsl(45, {int(90 - i * 15 / max(n_means-1,1))}%, {int(25 + i * 40 / max(n_means-1,1))}%)' for i in range(n_means)]

    fig = go.Figure(go.Bar(
        x=means.index.tolist(),
        y=means.values.tolist(),
        marker_color=yellow_colors,
        text=[f'{v:.2f}' for v in means.values],
        textposition='inside',
        textfont=dict(color='white', size=11),
    ))
    fig.update_xaxes(title=cat_col)
    fig.update_yaxes(title=f'Mean {num_col}')
    charts.append(_chart(f'Grouped Bar — Mean {num_col} by {cat_col}', fig))

    # 4. Strip Plot
    n_cats = len(top_cats)
    green_colors = [f'hsl(140, {int(70 - i * 15 / max(n_cats-1,1))}%, {int(20 + i * 40 / max(n_cats-1,1))}%)' for i in range(n_cats)]

    fig = px.strip(filtered, x=cat_col, y=num_col,
                   color=cat_col,
                   color_discrete_sequence=green_colors,
                   stripmode='overlay')
    charts.append(_chart(f'Strip Plot — {num_col} by {cat_col}', fig))
    # Sembunyikan legend supaya chart tidak terpotong
    for c in charts:
        import json
        parsed = json.loads(c['chart'])
        parsed['layout']['showlegend'] = False
        parsed['layout']['margin'] = {'l': 50, 'r': 20, 't': 30, 'b': 80}
        c['chart'] = json.dumps(parsed)

    return {'charts': charts}

# ─────────────────────────────────────────────
#  CAT vs CAT
# ─────────────────────────────────────────────

def generate_cat_vs_cat(df, col1, col2):
    if not col1 or not col2:
        return {'error': 'Pilih 2 kolom kategorikal'}
    if col1 not in df.columns or col2 not in df.columns:
        return {'error': 'Kolom tidak ditemukan'}

    # Tolak kolom datetime yang nyasar ke categorical
    for col in [col1, col2]:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return {'error': f'Kolom "{col}" adalah datetime, bukan kategorikal. Pilih kolom teks/kategori.'}
        # Juga cek kalau isinya bisa di-parse sebagai tanggal (string date)
        if df[col].dtype == object:
            sample = df[col].dropna().head(10).astype(str)
            try:
                parsed = pd.to_datetime(sample, errors='coerce')
                if parsed.notna().sum() >= 8:
                    return {'error': f'Kolom "{col}" terdeteksi sebagai tanggal, bukan kategorikal.'}
            except:
                pass

    df = df[[col1, col2]].dropna()

    # Filter hanya top categories
    top1 = df[col1].value_counts().head(8).index.tolist()
    top2 = df[col2].value_counts().head(8).index.tolist()
    df = df[df[col1].isin(top1) & df[col2].isin(top2)]

    if len(df) == 0:
        return {'error': 'Data tidak cukup setelah filtering. Pastikan kolom berisi data kategorikal.'}

    charts = []

    # 1. Grouped Bar Chart
    ct = pd.crosstab(df[col1], df[col2])
    fig = go.Figure()
    for i, col in enumerate(ct.columns):
        fig.add_trace(go.Bar(name=str(col), x=ct.index.tolist(),
                             y=ct[col].tolist(), marker_color=COLORS[i % len(COLORS)]))
    fig.update_layout(barmode='group')
    fig.update_xaxes(title=col1)
    fig.update_yaxes(title='Count')
    charts.append(_chart(f'Grouped Bar — {col1} vs {col2}', fig))

    # 2. Stacked Bar Chart
    fig = go.Figure()
    for i, col in enumerate(ct.columns):
        fig.add_trace(go.Bar(name=str(col), x=ct.index.tolist(),
                             y=ct[col].tolist(), marker_color=COLORS[i % len(COLORS)]))
    fig.update_layout(barmode='stack')
    fig.update_xaxes(title=col1)
    fig.update_yaxes(title='Count')
    charts.append(_chart(f'Stacked Bar — {col1} vs {col2}', fig))

    # 3. Heatmap Crosstab
    fig = px.imshow(ct, text_auto=True, color_continuous_scale='Purples')
    fig.update_xaxes(title=col2)
    fig.update_yaxes(title=col1)
    charts.append(_chart(f'Crosstab Heatmap — {col1} vs {col2}', fig))

    # 4. Stacked Bar 100%
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for i, col in enumerate(ct_pct.columns):
        fig.add_trace(go.Bar(name=str(col), x=ct_pct.index.tolist(),
                             y=ct_pct[col].tolist(), marker_color=COLORS[i % len(COLORS)]))
    fig.update_layout(barmode='stack')
    fig.update_xaxes(title=col1)
    fig.update_yaxes(title='Percentage (%)', range=[0, 100])
    charts.append(_chart(f'Stacked Bar 100% — {col1} vs {col2}', fig))

    return {'charts': charts}

# ─────────────────────────────────────────────
#  NUM vs NUM
# ─────────────────────────────────────────────

def generate_num_vs_num(df, col1, col2):
    if not col1 or not col2:
        return {'error': 'Pilih 2 kolom numerik'}
    if col1 not in df.columns or col2 not in df.columns:
        return {'error': 'Kolom tidak ditemukan'}
    if col1 == col2:
        return {'error': 'Pilih kolom yang berbeda'}

    clean = df[[col1, col2]].dropna()
    if len(clean) > 5000:
        clean = clean.sample(5000, random_state=42)

    charts = []

    # 1. Scatter Plot
    fig = px.scatter(clean, x=col1, y=col2,
                     color_discrete_sequence=["#ff6363"], opacity=0.6)
    charts.append(_chart(f'Scatter Plot — {col1} vs {col2}', fig))

    # 2. Regression Plot
    x_vals = clean[col1].values
    y_vals = clean[col2].values
    m, b, r, p, se = scipy_stats.linregress(x_vals, y_vals)
    x_line = np.linspace(x_vals.min(), x_vals.max(), 200)
    y_line = m * x_line + b
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals.tolist(), y=y_vals.tolist(),
                             mode='markers', name='Data',
                             marker=dict(color="#70ff63", size=5, opacity=0.5)))
    fig.add_trace(go.Scatter(x=x_line.tolist(), y=y_line.tolist(),
                             mode='lines', name=f'r={r:.2f}',
                             line=dict(color='#ff6464', width=2)))
    fig.update_xaxes(title=col1)
    fig.update_yaxes(title=col2)
    charts.append(_chart(f'Regression Plot — {col1} vs {col2}', fig, height=450))

    # 3. Density Heatmap (2D KDE)
    fig = go.Figure(go.Histogram2dContour(
        x=clean[col1], y=clean[col2],
        colorscale='Purples', reversescale=False,
        contours=dict(showlabels=True),
        line=dict(width=0),
    ))
    fig.add_trace(go.Scatter(
        x=clean[col1], y=clean[col2],
        mode='markers',
        marker=dict(color="#ff6387", size=3, opacity=0.3),
        showlegend=False,
    ))
    fig.update_xaxes(title=col1)
    fig.update_yaxes(title=col2)
    charts.append(_chart(f'Density Heatmap — {col1} vs {col2}', fig))

    # 4. Residual Plot
    residuals = y_vals - (m * x_vals + b)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=(m * x_vals + b).tolist(), y=residuals.tolist(),
        mode='markers',
        marker=dict(color="#55f7f7", size=5, opacity=0.6),
        name='Residuals',
    ))
    fig.add_hline(y=0, line_color='#ff6464', line_dash='dash')
    fig.update_xaxes(title='Fitted Values')
    fig.update_yaxes(title='Residuals')
    charts.append(_chart(f'Residual Plot — {col1} vs {col2}', fig))

    return {'charts': charts}


# ─────────────────────────────────────────────
#  DEFAULT / PLACEHOLDER CHARTS
# ─────────────────────────────────────────────

def _placeholder_fig(title, subtitle='', icon='📊'):
    """Buat placeholder chart kosong yang menarik."""
    fig = go.Figure()
    fig.add_annotation(
        text=f'{icon}<br><b style="font-size:16px">{title}</b><br>'
             f'<span style="font-size:12px;color:#8b8fa8">{subtitle}</span>',
        xref='paper', yref='paper',
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color='#c4c6d8'),
        align='center',
    )
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=PLOT_BG,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig

def default_charts(section):
    """
    Kembalikan list placeholder chart sesuai section.
    Setiap item: {'title': str, 'chart': json_str}
    """
    charts = []

    if section == 'univariate':
        placeholders = [
            ('Histogram', 'Pilih kolom numerik untuk melihat distribusi', '📊'),
            ('Boxplot',   'Deteksi outlier dan rentang data', '📦'),
            ('Density Plot', 'Estimasi distribusi probabilitas', '〰️'),
            ('QQ Plot',   'Uji normalitas distribusi data', '📈'),
            ('Violin Plot', 'Distribusi + boxplot dalam satu chart', '🎻'),
        ]
        for title, sub, icon in placeholders:
            fig = _placeholder_fig(title, sub, icon)
            charts.append({'title': title, 'chart': _json(fig)})

    elif section == 'categorical':
        placeholders = [
            ('Bar Chart',   'Pilih kolom kategorikal untuk melihat frekuensi', '📊'),
            ('Pie Chart',   'Proporsi setiap kategori', '🥧'),
            ('Count Plot',  'Jumlah data per kategori (horizontal)', '📋'),
            ('Pareto Chart','80/20 rule — kategori dominan', '📉'),
        ]
        for title, sub, icon in placeholders:
            fig = _placeholder_fig(title, sub, icon)
            charts.append({'title': title, 'chart': _json(fig)})

    elif section == 'bivariate':
        placeholders = [
            ('Scatter Plot',       'Pilih 2 kolom numerik untuk melihat hubungan', '✦'),
            ('Correlation Heatmap','Kekuatan hubungan antar variabel', '🌡️'),
            ('Regression Plot',    'Garis regresi linear', '📐'),
            ('Bubble Chart',       'Scatter dengan dimensi ukuran tambahan', '🫧'),
        ]
        for title, sub, icon in placeholders:
            fig = _placeholder_fig(title, sub, icon)
            charts.append({'title': title, 'chart': _json(fig)})

    elif section == 'multivariate':
        placeholders = [
            ('Correlation Heatmap', 'Pilih kolom-kolom numerik lalu Generate', '🌡️'),
            ('Pair Plot',           'Scatter matrix semua pasangan variabel', '🔢'),
            ('Bubble Chart',        'Tiga dimensi dalam satu chart', '🫧'),
        ]
        for title, sub, icon in placeholders:
            fig = _placeholder_fig(title, sub, icon)
            charts.append({'title': title, 'chart': _json(fig)})

    elif section == 'catvsnum':
        placeholders = [
            ('Boxplot by Category',   'Pilih kolom kategorikal & numerik', '📦'),
            ('Violin by Category',    'Distribusi per kategori', '🎻'),
            ('Grouped Bar Chart',     'Rata-rata nilai per kategori', '📊'),
            ('Strip Plot',            'Sebaran titik data per kategori', '•••'),
        ]
        for title, sub, icon in placeholders:
            fig = _placeholder_fig(title, sub, icon)
            charts.append({'title': title, 'chart': _json(fig)})

    else:
        # fallback generic
        fig = _placeholder_fig('Visualisasi', 'Pilih tab dan kolom untuk memulai', '📊')
        charts.append({'title': 'Visualisasi', 'chart': _json(fig)})

    return charts