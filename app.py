from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from backend.visualization import (
    generate_single_chart,
    generate_univariate,
    generate_bivariate,
    generate_multivariate,
    generate_cat_vs_num,
    generate_cat_vs_cat,
    generate_num_vs_num,
    default_charts,
)
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import os
import io
import warnings
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import plotly.graph_objects as go



warnings.filterwarnings('ignore')

CLEANED_FOLDER = 'cleaned_data'
os.makedirs(CLEANED_FOLDER, exist_ok=True)

df_global = None
df_original = None
current_filename = None
is_cleaned = False

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = "autoeda_secret"

UPLOAD_FOLDER = 'data/uploaded'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()


def load_dataframe(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(filepath)
    elif ext == '.xlsx':
        df = pd.read_excel(filepath)
    elif ext == '.txt':
        try:
            df = pd.read_csv(filepath, sep='|')
            if df.shape[1] <= 1:
                df = pd.read_csv(filepath, sep='\t')
            if df.shape[1] <= 1:
                df = pd.read_csv(filepath, sep=',')
        except:
            df = pd.read_csv(filepath, sep=',')

    for col in df.columns:
        try:
            cleaned = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            converted = pd.to_numeric(cleaned, errors='coerce')
            if converted.notna().sum() / len(df) > 0.8:
                df[col] = converted
        except:
            pass

    return df


# ===== AUTH =====

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # cek username
        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )
        if cursor.fetchone():
            conn.close()
            return render_template(
                'register.html',
                error='Username sudah digunakan'
            )

        # cek password
        cursor.execute(
            "SELECT * FROM users WHERE password=?",
            (password,)
        )
        if cursor.fetchone():
            conn.close()
            return render_template(
                'register.html',
                error='Password sudah digunakan'
            )

        # simpan data
        cursor.execute(
            "INSERT INTO users(username,email,password) VALUES (?,?,?)",
            (username, email, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect('/dashboard')
        return render_template('login.html', error='Username atau Password salah')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']
        new_password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            cursor.execute(
                "UPDATE users SET password=? WHERE email=?",
                (new_password, email)
            )

            conn.commit()
            conn.close()

            return redirect('/login')

        conn.close()

        return render_template(
            'forgot_password.html',
            error='Email tidak ditemukan'
        )

    return render_template('forgot_password.html')

@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users WHERE username=?", (session['user'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('settings.html', username=user[0], email=user[1])

@app.route('/settings/update-account', methods=['POST'])
def settings_update_account():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip()
    new_bio = data.get('bio', '').strip()
    if not new_username or not new_email:
        return jsonify({'error': 'Username dan email tidak boleh kosong'}), 400
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username=?, email=? WHERE username=?",
                   (new_username, new_email, session['user']))
    conn.commit()
    conn.close()
    session['user'] = new_username
    return jsonify({'success': True})

@app.route('/settings/update-password', methods=['POST'])
def settings_update_password():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')
    confirm_pw = data.get('confirm_password', '')
    if new_pw != confirm_pw:
        return jsonify({'error': 'Password baru tidak cocok'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'Password minimal 8 karakter'}), 400
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (session['user'], current_pw))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Password saat ini salah'}), 400
    cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pw, session['user']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/settings/delete-account', methods=['POST'])
def settings_delete_account():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username=?", (session['user'],))
    conn.commit()
    conn.close()
    session.clear()
    return jsonify({'success': True})

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/')
def index():
    return render_template('team.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', username=session.get('user', 'User'))

@app.route('/cleaning/status', methods=['GET'])
def cleaning_status():
    global is_cleaned
    return jsonify({'is_cleaned': is_cleaned})

# ===== UPLOAD =====

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'})

    global df_global, df_original, current_filename

    file = request.files['file']
    current_filename = file.filename
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        df_global = load_dataframe(filepath)
        df_original = df_global.copy()

        file_size_kb = round(os.path.getsize(filepath) / 1024, 2)

        auto_types = []
        for col in df_global.columns:
            dtype = str(df_global[col].dtype)
            if pd.api.types.is_numeric_dtype(df_global[col]):
                detected = "Numerical"
            elif pd.api.types.is_datetime64_any_dtype(df_global[col]):
                detected = "Datetime"
            elif df_global[col].nunique() < 20:
                detected = "Categorical"
            else:
                detected = "Text"
            auto_types.append({"column": col, "dtype": dtype, "detected": detected})

        # Deteksi datetime
        datetime_cols = df_global.select_dtypes(include='datetime').columns.tolist()
        for col in df_global.columns:
           if any(kw in col.lower() for kw in ['date','time','tanggal','tgl']):
                try:
                    df_global[col] = pd.to_datetime(df_global[col])
                    if col not in datetime_cols:
                        datetime_cols.append(col)
                except:
                    pass

        # Categorical bersih (tanpa datetime)
        categorical_cols = [
            col for col in df_global.select_dtypes(include='object').columns.tolist()
            if col not in datetime_cols
        ]
        # ===== Hitung Outlier Dataset =====
        total_outliers = 0
        total_numeric_values = 0

        numeric_cols = df_global.select_dtypes(include=np.number).columns

        for col in numeric_cols:
            data = df_global[col].dropna()

            if len(data) < 4:
                continue

            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1

            outliers = data[
                (data < Q1 - 1.5 * IQR) |
                (data > Q3 + 1.5 * IQR)
            ]

            total_outliers += len(outliers)
            total_numeric_values += len(data)

        outlier_percent = (
            round(total_outliers / total_numeric_values * 100, 2)
            if total_numeric_values > 0 else 0
        )

        info = {
            'filename': file.filename,
            'file_size': str(file_size_kb) + ' KB',
            'rows': int(df_global.shape[0]),
            'columns': int(df_global.shape[1]),
            'columns_list': df_global.columns.tolist(),
            'dtypes': df_global.dtypes.astype(str).to_dict(),
            'preview': df_global.head(5).fillna('NaN').to_dict(orient='records'),
            'full_data': df_global.fillna('NaN').to_dict(orient='records'),
            'auto_types': auto_types,
            'numeric_cols': df_global.select_dtypes(include=np.number).columns.tolist(),
            'categorical_cols': categorical_cols,
            'datetime_cols': datetime_cols,
            'missing_total': int(df_global.isnull().sum().sum()),
            'missing_percent': round(df_global.isnull().sum().sum() / df_global.size * 100, 2),
            'duplicate_count': int(df_global.duplicated().sum()),
            'duplicate_percent': round(df_global.duplicated().sum() / len(df_global) * 100, 2) if len(df_global) > 0 else 0,
            'outlier_count': int(total_outliers),
            'outlier_percent': outlier_percent
        }

        for col in df_global.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    df_global[col] = pd.to_datetime(df_global[col])
                    if col not in info['datetime_cols']:
                        info['datetime_cols'].append(col)
                except:
                    pass

        return jsonify({'status': 'success', 'info': info})
    return jsonify({'status': 'error', 'message': 'No file uploaded'})


# ===== STATS =====

@app.route('/stats/numerical', methods=['GET'])
def numerical_stats():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    numeric_cols = df_global.select_dtypes(include=np.number).columns
    result = {}

    for col in numeric_cols:
        data = df_global[col].dropna()
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        outliers = data[(data < Q1 - 1.5 * IQR) | (data > Q3 + 1.5 * IQR)]

        try:
            normality = stats.shapiro(data[:500])
            is_normal = 'Normal' if normality.pvalue > 0.05 else 'Not Normal'
        except:
            is_normal = 'N/A'

        result[col] = {
            'mean': round(float(data.mean()), 2),
            'median': round(float(data.median()), 2),
            'min': round(float(data.min()), 2),
            'max': round(float(data.max()), 2),
            'std': round(float(data.std()), 2),
            'variance': round(float(data.var()), 2),
            'mode': round(float(data.mode()[0]), 2) if len(data.mode()) > 0 else None,
            'skewness': round(float(data.skew()), 2),
            'kurtosis': round(float(data.kurtosis()), 2),
            'missing_count': int(df_global[col].isnull().sum()),
            'missing_percent': round(df_global[col].isnull().sum() / len(df_global) * 100, 2),
            'normality': is_normal,
            'outliers': int(len(outliers))
        }

    return jsonify(result)


@app.route('/stats/categorical', methods=['GET'])
def categorical_stats():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    dt_cols = df_global.select_dtypes(include='datetime').columns.tolist()
    for col in df_global.select_dtypes(include='object').columns:
        try:
            df_global[col] = pd.to_datetime(df_global[col])
            if col not in dt_cols:
                dt_cols.append(col)
        except Exception:
            pass
    cat_cols = [c for c in df_global.select_dtypes(include='object').columns if c not in dt_cols]
    result = {}

    for col in cat_cols:
        data = df_global[col].dropna()
        mode_val = data.mode()[0] if len(data.mode()) > 0 else None
        mode_freq = int(data.value_counts()[mode_val]) if mode_val else 0

        result[col] = {
            'unique': int(data.nunique()),
            'mode': str(mode_val),
            'mode_freq': mode_freq,
            'mode_percent': round(mode_freq / len(data) * 100, 2) if len(data) > 0 else 0,
            'missing_count': int(df_global[col].isnull().sum()),
            'missing_percent': round(df_global[col].isnull().sum() / len(df_global) * 100, 2)
        }

    return jsonify(result)


# ===== INSIGHTS =====

@app.route('/insights', methods=['GET'])
def insights():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    result = []
    numeric_cols = df_global.select_dtypes(include=np.number).columns

    result.append(
        f"Dataset terdiri dari {df_global.shape[0]} baris dan {df_global.shape[1]} kolom, dengan {len(numeric_cols)} variabel numerik."
    )

    if len(numeric_cols) > 0:
        highest_mean_col = df_global[numeric_cols].mean().idxmax()
        result.append(
            f"Variabel {highest_mean_col} memiliki rata-rata tertinggi sebesar {round(df_global[highest_mean_col].mean(), 2)}, menunjukkan nilai yang relatif lebih besar dibanding variabel numerik lainnya."
        )

        missing = df_global.isnull().sum()
        if missing.max() > 0:
            most_missing = missing.idxmax()
            result.append(
                f"Kolom {most_missing} memiliki missing value terbanyak yaitu {missing.max()} data sehingga perlu perhatian pada proses pembersihan data."
            )

        outlier_counts = {}
        for col in numeric_cols:
            data = df_global[col].dropna()
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            outlier_counts[col] = len(data[(data < Q1 - 1.5 * IQR) | (data > Q3 + 1.5 * IQR)])

        most_outliers = max(outlier_counts, key=outlier_counts.get)
        result.append(
            f"Variabel {most_outliers} memiliki jumlah outlier tertinggi yaitu {outlier_counts[most_outliers]} data yang dapat memengaruhi hasil analisis statistik."
        )

        highest_std = df_global[numeric_cols].std().idxmax()
        result.append(
            f"Variabel {highest_std} memiliki standar deviasi terbesar sebesar {round(df_global[highest_std].std(), 2)}, yang menunjukkan penyebaran data paling tinggi."
        )

        if len(numeric_cols) >= 2:
            corr = df_global[numeric_cols].corr()
            corr_unstacked = corr.abs().unstack()
            corr_unstacked = corr_unstacked[corr_unstacked < 1].dropna()
            if len(corr_unstacked) > 0:
                strongest = corr_unstacked.idxmax()
                result.append(
                    f"Variabel {strongest[0]} dan {strongest[1]} memiliki korelasi sangat kuat dengan nilai r = {round(corr_unstacked.max(), 2)}."
                )

    return jsonify(result)


# ===== VISUALIZE =====

@app.route('/visualize', methods=['POST'])
def visualize():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    data = request.json
    column = data.get('column')
    chart_type = data.get('type')

    try:
        result = generate_single_chart(df_global, column, chart_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

# ===== AUTOMATED VISUALIZATION ANALYTICS =====

@app.route('/visualize/univariate', methods=['POST'])
def visualize_univariate():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    data = request.json
    col = data.get('column')
    v_type = data.get('var_type')

    try:
        result = generate_univariate(df_global, col, v_type)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)})


@app.route('/visualize/bivariate', methods=['POST'])
def visualize_bivariate():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    data = request.json
    col1 = data.get('col1')
    col2 = data.get('col2')

    try:
        result = generate_bivariate(df_global, col1, col2)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/visualize/multivariate', methods=['POST'])
def visualize_multivariate():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    data = request.json
    cols = data.get('columns', [])
    hue = data.get('hue')
    bubble_size = data.get('bubble_size')

    try:
        result = generate_multivariate(df_global, cols, hue, bubble_size)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/visualize/cat-vs-num', methods=['POST'])
def visualize_cat_vs_num():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    data = request.json
    num_col = data.get('num_col')
    cat_col = data.get('cat_col')

    try:
        result = generate_cat_vs_num(df_global, num_col, cat_col)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)})
    

@app.route('/visualize/cat-vs-cat', methods=['POST'])
def visualize_cat_vs_cat():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})
    data = request.json
    try:
        result = generate_cat_vs_cat(df_global, data.get('col1'), data.get('col2'))
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/visualize/num-vs-num', methods=['POST'])
def visualize_num_vs_num():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})
    data = request.json
    try:
        result = generate_num_vs_num(df_global, data.get('col1'), data.get('col2'))
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)})
    

@app.route('/visualize/default', methods=['POST'])
def visualize_default():
    """
    Mengembalikan placeholder chart untuk ditampilkan
    sebelum user memilih kolom & menekan Generate.
    """
    data = request.json
    section = data.get('section', 'numerical')

    try:
        charts = default_charts(section)
        return jsonify({'charts': charts})
    except Exception as e:
        return jsonify({'error': str(e)})


# ===== DATA CLEANING =====

@app.route('/clean', methods=['POST'])
def clean_data():
    global df_global, is_cleaned
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    data = request.json
    method = data.get('method')

    before_missing = int(df_global.isnull().sum().sum())

    if method == 'drop':
        df_global = df_global.dropna()

    elif method == 'fill_mean':
        numeric_cols = df_global.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            df_global[col] = df_global[col].fillna(df_global[col].mean())

    elif method == 'fill_mode':
        for col in df_global.columns:
            mode = df_global[col].mode()
            if not mode.empty:
                df_global[col] = df_global[col].fillna(mode.iloc[0])

    elif method == 'remove_duplicates':
        df_global = df_global.drop_duplicates()

    elif method == 'standardize_text':
        _dt = df_global.select_dtypes(include='datetime').columns.tolist()
        cat_cols = [c for c in df_global.select_dtypes(include='object').columns if c not in _dt]
        for col in cat_cols:
            df_global[col] = df_global[col].astype(str).str.strip().str.title()

    elif method == 'standardize_columns':
        df_global.columns = df_global.columns.str.strip().str.lower().str.replace(' ', '_')

    elif method == 'standardize_numeric':
        numeric_cols = df_global.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            mean = df_global[col].mean()
            std = df_global[col].std()
            if std != 0:
                df_global[col] = (df_global[col] - mean) / std

    elif method == 'clean_all':
        numeric_cols = df_global.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            df_global[col] = df_global[col].fillna(df_global[col].mean())
        for col in df_global.columns:
            if df_global[col].isnull().sum() > 0:
                mode = df_global[col].mode()
                if not mode.empty:
                    df_global[col] = df_global[col].fillna(mode.iloc[0])
        df_global = df_global.drop_duplicates()
        df_global.columns = df_global.columns.str.strip().str.lower().str.replace(' ', '_')
        _dt2 = df_global.select_dtypes(include='datetime').columns.tolist()
        cat_cols = [c for c in df_global.select_dtypes(include='object').columns if c not in _dt2]
        for col in cat_cols:
            df_global[col] = df_global[col].astype(str).str.strip().str.title()

    after_missing = int(df_global.isnull().sum().sum())
    after_duplicate = int(df_global.duplicated().sum())
    # ===== Recalculate Outliers =====
    total_outliers = 0
    total_numeric_values = 0

    numeric_cols = df_global.select_dtypes(include=np.number).columns

    for col in numeric_cols:
        data = df_global[col].dropna()

        if len(data) < 4:
            continue

        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1

        outliers = data[
            (data < Q1 - 1.5 * IQR) |
            (data > Q3 + 1.5 * IQR)
        ]

        total_outliers += len(outliers)
        total_numeric_values += len(data)

    outlier_percent = round(
        (total_outliers / total_numeric_values) * 100,
        2
    ) if total_numeric_values > 0 else 0
    is_cleaned = True
    total_cells = df_global.size if df_global.size > 0 else 1
    total_rows  = len(df_global) if len(df_global) > 0 else 1
    return jsonify({
    'status': 'success',
    'before_missing': before_missing,
    'after_missing': after_missing,
    'missing_percent': round(after_missing / total_cells * 100, 2),
    'duplicate_count': after_duplicate,
    'duplicate_percent': round(after_duplicate / total_rows * 100, 2),
    'outlier_count': int(total_outliers),
    'outlier_percent': outlier_percent,
    'rows': int(df_global.shape[0]),
    'preview': df_global.head(10).fillna('NaN').to_dict(orient='records'),
    'full_data': df_global.fillna('NaN').to_dict(orient='records'),
    'numeric_cols': df_global.select_dtypes(include=np.number).columns.tolist(),
    'categorical_cols': [c for c in df_global.select_dtypes(include='object').columns.tolist()
                          if c not in df_global.select_dtypes(include='datetime').columns.tolist()],
    })


@app.route('/save_cleaned', methods=['POST'])
def save_cleaned():
    global df_global, current_filename
    if df_global is None:
        return jsonify({'status': 'error', 'message': 'No dataset'})

    filename = f"cleaned_{current_filename}"
    save_path = os.path.join(CLEANED_FOLDER, filename)

    if filename.endswith('.xlsx'):
        df_global.to_excel(save_path, index=False)
    else:
        df_global.to_csv(save_path, index=False)

    return jsonify({'status': 'success', 'filename': filename})


@app.route('/download_cleaned')
def download_cleaned():
    global current_filename
    filename = f"cleaned_{current_filename}"
    path = os.path.join(CLEANED_FOLDER, filename)
    return send_file(path, as_attachment=True)


@app.route('/undo_cleaning', methods=['POST'])
def undo_cleaning():
    global df_global, df_original, is_cleaned
    if df_original is None:
        return jsonify({'status': 'error', 'message': 'No original dataset found'})

    df_global = df_original.copy()
    is_cleaned = False
    return jsonify({
        'status': 'success',
        'rows': int(df_global.shape[0]),
        'missing_total': int(df_global.isnull().sum().sum()),
        'preview': df_global.head(10).fillna('NaN').to_dict(orient='records'),
        'full_data': df_global.fillna('NaN').to_dict(orient='records')
    })


# ===== TIME SERIES =====

@app.route('/timeseries', methods=['GET'])
def get_timeseries_columns():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    numeric_cols = df_global.select_dtypes(include=np.number).columns.tolist()
    date_cols = df_global.select_dtypes(include=['datetime64']).columns.tolist()

    date_keywords = ['date', 'time', 'tanggal', 'tgl', 'dt', 'bulan', 'tahun', 'year', 'month']
    for col in df_global.columns:
        if col in numeric_cols or col in date_cols:
            continue
        if any(kw in col.lower() for kw in date_keywords):
            try:
                parsed = pd.to_datetime(df_global[col], dayfirst=False, errors='coerce')
                if parsed.notna().mean() > 0.8:
                    date_cols.append(col)
            except:
                pass

    if not date_cols:
        for col in df_global.select_dtypes(include='object').columns:
            if col in numeric_cols:
                continue
            try:
                parsed = pd.to_datetime(df_global[col], dayfirst=False, errors='coerce')
                if parsed.notna().mean() > 0.8:
                    year_check = parsed.dropna().dt.year
                    if year_check.between(1990, 2100).mean() > 0.8:
                        date_cols.append(col)
            except:
                pass

    return jsonify({'date_cols': date_cols, 'numeric_cols': numeric_cols})


@app.route('/generate_timeseries', methods=['POST'])
def generate_timeseries():
    global df_global
    if df_global is None:
        return jsonify({'error': 'No data loaded'})

    try:
        import plotly.graph_objects as go

        data = request.json
        date_col = data['date_col']
        numeric_cols = data['numeric_cols']

        df_ts = df_global.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], dayfirst=False, errors='coerce')
        df_ts = df_ts.dropna(subset=[date_col])
        df_ts[date_col] = df_ts[date_col].dt.to_period('M').dt.to_timestamp()
        df_ts = df_ts.groupby(date_col)[numeric_cols].sum().reset_index()
        df_ts = df_ts.sort_values(date_col)

        charts = []
        insights = []

        for value_col in numeric_cols:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_ts[date_col], y=df_ts[value_col],
                mode='lines+markers', name='Actual',
                line=dict(color='#6c63ff', width=2),
                marker=dict(size=5)
            ))

            if len(df_ts) >= 3:
                ma = df_ts[value_col].rolling(window=3).mean()
                fig.add_trace(go.Scatter(
                    x=df_ts[date_col], y=ma,
                    mode='lines', name='Moving Avg (3)',
                    line=dict(color='#00c864', width=2, dash='dash')
                ))

            if len(df_ts) >= 2:
                rolling = df_ts[value_col].rolling(window=2).mean()
                fig.add_trace(go.Scatter(
                    x=df_ts[date_col], y=rolling,
                    mode='lines', name='Rolling Mean (2)',
                    line=dict(color='#ffd700', width=2, dash='dot')
                ))

            x_num = np.arange(len(df_ts))
            z = np.polyfit(x_num, df_ts[value_col], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=df_ts[date_col], y=p(x_num),
                mode='lines', name='Trend Line',
                line=dict(color='#ff6464', width=2, dash='longdash')
            ))

            fig.update_layout(
                title=dict(
                    text=f'{value_col} Over Time',
                    x=0,
                    xanchor='left',
                    font=dict(size=13)
                ),
                template='plotly_dark',
                legend=dict(
                    orientation='h',
                    yanchor='top',
                    y=-0.2,
                    xanchor='center',
                    x=0.5,
                    font=dict(size=11)
                ),
                margin=dict(l=40, r=20, t=50, b=80)
            )

            mean_val = df_ts[value_col].mean()
            max_val = df_ts[value_col].max()
            min_val = df_ts[value_col].min()
            max_date = df_ts.loc[df_ts[value_col].idxmax(), date_col].strftime('%B %Y')
            min_date = df_ts.loc[df_ts[value_col].idxmin(), date_col].strftime('%B %Y')
            trend = "Naik" if z[0] > 0 else "Turun"

            insight = (
                f"Kolom {value_col} menunjukkan tren {trend}. "
                f"Nilai tertinggi pada {max_date} ({max_val:,.0f}), "
                f"terendah pada {min_date} ({min_val:,.0f}). "
                f"Rata-rata: {mean_val:,.0f}."
            )

            charts.append(fig.to_json())
            insights.append(insight)

        return jsonify({'charts': charts, 'insights': insights})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})


# ===== REPORTING SYSTEM =====
@app.route('/download/pdf')
def download_pdf():
    global df_global, df_original, current_filename, is_cleaned
    if df_global is None:
        return "No data loaded.", 400
        
    use_cleaned = request.args.get('cleaned', 'false').lower() == 'true'
    
    # Blokir jika belum cleaning tapi minta report after cleaning
    if use_cleaned and not is_cleaned:
        return "Data belum di-cleaning. Silakan lakukan cleaning terlebih dahulu.", 400
        
    df = df_global if use_cleaned else (df_original if df_original is not None else df_global)
    label_dataset = "After Cleaning" if use_cleaned else "Before Cleaning"
    
    # Menarik nama user dari session agar tidak anonymous
    username = session.get('user', current_filename or 'User')
    
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Image as RLImage
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import io

    # Pengaturan Ukuran A4 Portrait (Tegak)
    PAGE_W = A4[0]
    CONTENT_W = PAGE_W - 60  # Margin kiri 30, kanan 30
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=30, rightMargin=30,
                            topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    
    # Styles Definition
    title_style = ParagraphStyle('Title', fontSize=18,
        textColor=colors.HexColor('#6c63ff'), spaceAfter=4, fontName='Helvetica-Bold')
    meta_style = ParagraphStyle('Meta', fontSize=8,
        textColor=colors.HexColor('#686868'), spaceAfter=2)
    h2_style = ParagraphStyle('H2', fontSize=12,
        textColor=colors.HexColor('#6c63ff'), spaceBefore=14,
        spaceAfter=6, fontName='Helvetica-Bold')
    h3_style = ParagraphStyle('H3', fontSize=9.5,
        textColor=colors.HexColor('#333333'), spaceBefore=8,
        spaceAfter=4, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('Normal2', fontSize=8,
        textColor=colors.HexColor('#444444'), spaceAfter=2)
    insight_style = ParagraphStyle('Insight', fontSize=8.5,
        textColor=colors.HexColor('#333333'),
        leftIndent=12, spaceBefore=3, spaceAfter=3)
    tag_style = ParagraphStyle('Tag', fontSize=8,
        textColor=colors.HexColor('#00c864') if use_cleaned else colors.HexColor('#f59e0b'),
        spaceAfter=8, fontName='Helvetica-Bold')

    numeric_cols = df.select_dtypes(include='number').columns
    cat_cols     = df.select_dtypes(include='object').columns
    missing_total = int(df.isnull().sum().sum())
    dup_count     = int(df.duplicated().sum())
    
    elements = []
    
    # ── HEADER & META DATA ──
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("Auto EDA Insight", title_style))
    elements.append(Paragraph("Laporan Eksplorasi Data Otomatis", meta_style))
    elements.append(Paragraph(
        f"File: <b>{current_filename}</b>   |   "
        f"Dibuat oleh: <b>{username}</b>   |   "
        f"Generated: <b>{pd.Timestamp.now().strftime('%d %B %Y, %H:%M')}</b>   |   "
        f"Dataset: <b>{label_dataset}</b>",
        meta_style))
    elements.append(Paragraph(f"● {label_dataset}", tag_style))
    elements.append(Table([['']], colWidths=[CONTENT_W],
        style=[('LINEABOVE',(0,0),(-1,0),1,colors.HexColor('#6c63ff')),
               ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
               
    # ── 1. DATA PREVIEW ──
    elements.append(Paragraph("1. Data Preview", h2_style))
    overview_data = [
        ["Metrik","Nilai","Metrik","Nilai"],
        ["Total Baris",       f"{df.shape[0]:,}",    "Missing Values",  f"{missing_total:,}"],
        ["Total Kolom",       str(df.shape[1]),       "Missing %",       f"{round(missing_total/df.size*100,2) if df.size > 0 else 0}%"],
        ["Kolom Numerik",     str(len(numeric_cols)), "Baris Duplikat",  str(dup_count)],
        ["Kolom Kategorikal", str(len(cat_cols)),     "Total Cells",     f"{df.size:,}"],
        ["Baris Lengkap",     str(int(df.dropna().shape[0])),         "Baris Lengkap %",  f"{round(df.dropna().shape[0]/df.shape[0]*100,2) if df.shape[0] > 0 else 0}%"],
    ]
    # Penyesuaian kolom agar pas di A4 Portrait (Lebar total 535)
    t_ov = Table(overview_data, hAlign='LEFT', colWidths=[140,125,140,130])
    t_ov.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6c63ff')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('BACKGROUND',(0,1),(0,-1),colors.HexColor('#f0eeff')),
        ('BACKGROUND',(2,1),(2,-1),colors.HexColor('#f0eeff')),
        ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),
        ('FONTNAME',(2,1),(2,-1),'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(1,1),(-1,-1),[colors.HexColor('#fafafa'),colors.white]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cccccc')),
        ('PADDING',(0,0),(-1,-1),5),
        ('FONTSIZE',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    elements.append(t_ov)
    
    elements.append(Paragraph("Missing Value per Kolom", h3_style))
    mv_data = [["Kolom","Tipe Data","Missing Count","Missing %","Status"]]
    for col in df.columns:
        mc  = int(df[col].isnull().sum())
        pct = round(mc/len(df)*100,2) if len(df) > 0 else 0
        status = "HIGH" if pct>10 else ("MEDIUM" if pct>0 else "OK")
        mv_data.append([str(col)[:25], str(df[col].dtype), str(mc), f"{pct}%", status])
    t_mv = Table(mv_data, hAlign='LEFT', repeatRows=1, colWidths=[165,90,90,90,100])
    t_mv.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6c63ff')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f5f5f5'),colors.white]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cccccc')),
        ('PADDING',(0,0),(-1,-1),4),
        ('FONTSIZE',(0,0),(-1,-1),8),
    ]))
    elements.append(t_mv)
    elements.append(Spacer(1, 8))
    
    # ── 2. DATA TYPE DETECTION ──
    elements.append(Paragraph("2. Data Type Detection", h2_style))
    dt_data = [["Kolom","Tipe Pandas","Tipe Terdeteksi","Contoh Nilai"]]
    for col in df.columns:
        dtype = str(df[col].dtype)
        if 'int' in dtype or 'float' in dtype:
            detected = "Numerik"
        elif 'datetime' in dtype:
            detected = "Datetime"
        elif 'bool' in dtype:
            detected = "Boolean"
        else:
            sample = df[col].dropna()
            try:
                pd.to_datetime(sample[:5])
                detected = "Datetime (string)"
            except:
                try:
                    pd.to_numeric(sample[:5])
                    detected = "Numerik (string)"
                except:
                    detected = "Kategorikal"
        example = str(df[col].dropna().iloc[0])[:30] if df[col].dropna().shape[0] > 0 else '-'
        dt_data.append([str(col)[:25], dtype, detected, example])
    t_dt = Table(dt_data, hAlign='LEFT', repeatRows=1, colWidths=[165,100,120,150])
    t_dt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6c63ff')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f5f5f5'),colors.white]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cccccc')),
        ('PADDING',(0,0),(-1,-1),4),
        ('FONTSIZE',(0,0),(-1,-1),8),
    ]))
    elements.append(t_dt)
    elements.append(Spacer(1, 8))
    
    # ── 3. STATISTIK DESKRIPTIF NUMERIK ──
    if len(numeric_cols) > 0:
        elements.append(Paragraph("3. Statistik Deskriptif Numerik", h2_style))
        num_headers = ["Kolom","Mean","Min","Max","Std Dev","Skewness","Missing","Outliers"]
        num_rows = [num_headers]
        for col in numeric_cols:
            d = df[col].dropna()
            if len(d) > 0:
                Q1, Q3 = d.quantile(0.25), d.quantile(0.75)
                outliers = len(d[(d < Q1 - 1.5 * (Q3 - Q1)) | (d > Q3 + 1.5 * (Q3 - Q1))])
                mean_val, min_val, max_val = d.mean(), d.min(), d.max()
                std_val, skew_val = d.std(), d.skew()
            else:
                outliers, mean_val, min_val, max_val, std_val, skew_val = 0, 0, 0, 0, 0, 0
                
            num_rows.append([
                str(col)[:15], f"{mean_val:.2f}", f"{min_val:.2f}", f"{max_val:.2f}",
                f"{std_val:.2f}", f"{skew_val:.2f}",
                str(int(df[col].isnull().sum())), str(outliers)
            ])
        t_num = Table(num_rows, hAlign='LEFT', repeatRows=1, colWidths=[115,60,60,60,60,60,60,60])
        t_num.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6c63ff')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f5f5f5'),colors.white]),
            ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cccccc')),
            ('PADDING',(0,0),(-1,-1),4),
            ('FONTSIZE',(0,0),(-1,-1),8),
            ('ALIGN',(1,0),(-1,-1),'CENTER'),
        ]))
        elements.append(t_num)
        elements.append(Spacer(1, 8))
        
    # ── 4. STATISTIK KATEGORIKAL ──
    if len(cat_cols) > 0:
        elements.append(Paragraph("4. Statistik Deskriptif Kategorikal", h2_style))
        cat_headers = ["Kolom","Unique","Mode","Mode Freq","Mode %","Missing"]
        cat_rows = [cat_headers]
        for col in cat_cols:
            d = df[col].dropna()
            mode_val  = d.mode()[0] if len(d.mode())>0 else '-'
            mode_freq = int(d.value_counts().get(mode_val,0))
            mode_pct  = round(mode_freq/len(d)*100,2) if len(d)>0 else 0
            cat_rows.append([
                str(col)[:15], str(d.nunique()), str(mode_val)[:20],
                str(mode_freq), f"{mode_pct}%", str(int(df[col].isnull().sum()))
            ])
        t_cat = Table(cat_rows, hAlign='LEFT', repeatRows=1, colWidths=[135,60,140,70,70,60])
        t_cat.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6c63ff')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f5f5f5'),colors.white]),
            ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cccccc')),
            ('PADDING',(0,0),(-1,-1),4),
            ('FONTSIZE',(0,0),(-1,-1),8),
        ]))
        elements.append(t_cat)
        elements.append(Spacer(1, 8))
        
    # ── 5. VISUAL INSIGHTS (CHARTS) ──
    elements.append(Paragraph("5. Visual Insights", h2_style))
    
    # Histogram Kolom Numerik (Max 2 kolom bersandingan agar pas Portrait A4)
    if len(numeric_cols) > 0:
        elements.append(Paragraph("Distribusi Kolom Numerik (Histogram)", h3_style))
        cols_to_plot = list(numeric_cols[:2])
        n = len(cols_to_plot)
        fig_h, axes = plt.subplots(1, n, figsize=(2.6 * n, 2.2))
        if n == 1:
            axes = [axes]
        for ax, col in zip(axes, cols_to_plot):
            data_clean = df[col].dropna()
            ax.hist(data_clean, bins=15, color='#6c63ff', alpha=0.85, edgecolor='white', linewidth=0.5)
            ax.set_title(str(col)[:20], fontsize=7, fontweight='bold', color='#333333')
            ax.tick_params(labelsize=6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        fig_h.tight_layout(pad=0.8)
        img_buf_h = io.BytesIO()
        fig_h.savefig(img_buf_h, format='png', dpi=140, bbox_inches='tight')
        plt.close(fig_h)
        img_buf_h.seek(0)
        elements.append(RLImage(img_buf_h, width=220*n, height=160))
        elements.append(Spacer(1, 6))
        
    # Bar Chart Kolom Kategorikal (Max 2 kolom)
    if len(cat_cols) > 0:
        elements.append(Paragraph("Top Nilai Kolom Kategorikal (Bar Chart)", h3_style))
        cols_cat_plot = list(cat_cols[:2])
        n_c = len(cols_cat_plot)
        fig_b, axes_b = plt.subplots(1, n_c, figsize=(2.7 * n_c, 2.2))
        if n_c == 1:
            axes_b = [axes_b]
        palette = ['#6c63ff','#00c864','#f59e0b','#ff6464','#38bdf8']
        for ax, col in zip(axes_b, cols_cat_plot):
            vc = df[col].value_counts().head(5)
            bars = ax.barh(vc.index.astype(str), vc.values, color=palette[:len(vc)], edgecolor='white', linewidth=0.4)
            ax.set_title(str(col)[:20], fontsize=7, fontweight='bold', color='#333333')
            ax.tick_params(labelsize=6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        fig_b.tight_layout(pad=0.8)
        img_buf_b = io.BytesIO()
        fig_b.savefig(img_buf_b, format='png', dpi=140, bbox_inches='tight')
        plt.close(fig_b)
        img_buf_b.seek(0)
        elements.append(RLImage(img_buf_b, width=220*n_c, height=160))
        elements.append(Spacer(1, 6))
        
    # Heatmap Korelasi
    if len(numeric_cols) >= 2:
        elements.append(Paragraph("Correlation Heatmap", h3_style))
        corr_matrix = df[numeric_cols[:6]].corr()  # batasi max 6 variabel agar teks kebaca
        n_corr = len(corr_matrix.columns)
        fig_c, ax_c = plt.subplots(figsize=(3.5, 2.8))
        cmap = plt.cm.RdYlGn
        im = ax_c.imshow(corr_matrix.values, cmap=cmap, vmin=-1, vmax=1)
        ax_c.set_xticks(range(n_corr))
        ax_c.set_yticks(range(n_corr))
        ax_c.set_xticklabels(corr_matrix.columns, rotation=35, ha='right', fontsize=5.5)
        ax_c.set_yticklabels(corr_matrix.columns, fontsize=5.5)
        
        for i in range(n_corr):
            for j in range(n_corr):
                val = corr_matrix.values[i, j]
                ax_c.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=5,
                          color='black' if abs(val) < 0.6 else 'white')
        fig_c.colorbar(im, ax=ax_c, shrink=0.75)
        ax_c.set_title('Correlation Matrix', fontsize=7, fontweight='bold')
        fig_c.tight_layout()
        img_buf_c = io.BytesIO()
        fig_c.savefig(img_buf_c, format='png', dpi=140, bbox_inches='tight')
        plt.close(fig_c)
        img_buf_c.seek(0)
        elements.append(RLImage(img_buf_c, width=260, height=200))
        elements.append(Spacer(1, 6))
        
    # ── 6. INSIGHTS OTOMATIS ──
    elements.append(Paragraph("6. Insights Otomatis", h2_style))
    insights_list = []
    if len(numeric_cols) > 0:
        hm = df[numeric_cols].mean().idxmax()
        insights_list.append(f"• Variabel dengan rata-rata tertinggi: <b>{hm}</b> = {round(df[hm].mean(),2):,}")
        missing = df.isnull().sum()
        if missing.max() > 0:
            mm = missing.idxmax()
            insights_list.append(f"• Missing value terbanyak: <b>{mm}</b> = {missing.max()} data ({round(missing.max()/len(df)*100,1)}%)")
        else:
            insights_list.append("• Tidak ada missing values ditemukan pada dataset. ✅")
            
        outlier_counts = {}
        for col in numeric_cols:
            d = df[col].dropna()
            if len(d) > 0:
                Q1, Q3 = d.quantile(0.25), d.quantile(0.75)
                outlier_counts[col] = len(d[(d < Q1 - 1.5 * (Q3 - Q1)) | (d > Q3 + 1.5 * (Q3 - Q1))])
            else:
                outlier_counts[col] = 0
        mo = max(outlier_counts, key=outlier_counts.get)
        insights_list.append(f"• Outlier terbanyak terdeteksi pada kolom: <b>{mo}</b> = {outlier_counts[mo]} baris")
        
        if dup_count > 0:
            insights_list.append(f"• Terdapat <b>{dup_count}</b> baris duplikat di dalam dataset.")
        else:
            insights_list.append("• Tidak ada baris duplikat yang terdeteksi. ✅")
            
    for ins in insights_list:
        elements.append(Paragraph(ins, insight_style))
    elements.append(Spacer(1, 6))
    
    # ── 7. TIME SERIES SUMMARY ──
    date_cols = []
    for col in df.columns:
        try:
            parsed = pd.to_datetime(df[col], errors='coerce')
            if parsed.notna().sum() / len(df) > 0.7:
                date_cols.append(col)
        except:
            pass
            
    elements.append(Paragraph("7. Time Series Summary", h2_style))
    if date_cols and len(numeric_cols) > 0:
        ts_col = date_cols[0]
        try:
            df_ts = df.copy()
            df_ts[ts_col] = pd.to_datetime(df_ts[ts_col], errors='coerce')
            df_ts = df_ts.dropna(subset=[ts_col]).sort_values(ts_col)
            
            ts_data = [["Metrik","Nilai"]]
            ts_data.append(["Kolom Tanggal", ts_col])
            ts_data.append(["Rentang Waktu", f"{df_ts[ts_col].min().strftime('%d %b %Y')} — {df_ts[ts_col].max().strftime('%d %b %Y')}"])
            ts_data.append(["Jumlah Periode", str(df_ts[ts_col].nunique())])
            
            t_ts = Table(ts_data, hAlign='LEFT', colWidths=[180,355])
            t_ts.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6c63ff')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('BACKGROUND',(0,1),(0,-1),colors.HexColor('#f0eeff')),
                ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cccccc')),
                ('PADDING',(0,0),(-1,-1),5),
                ('FONTSIZE',(0,0),(-1,-1),8),
            ]))
            elements.append(t_ts)
            
            # Line Chart Time Series (Lebar disesuaikan untuk Portrait A4)
            fig_ts, ax_ts = plt.subplots(figsize=(5.2, 2.0))
            df_ts_plot = df_ts.set_index(ts_col)
            for i, col in enumerate(numeric_cols[:2]):
                col_norm = df_ts_plot[col] / df_ts_plot[col].max() if df_ts_plot[col].max() != 0 else df_ts_plot[col]
                ax_ts.plot(df_ts_plot.index, col_norm, label=col, color=['#6c63ff','#00c864'][i], linewidth=1.2)
            ax_ts.set_title('Time Series Trend (Normalized)', fontsize=7, fontweight='bold')
            ax_ts.legend(fontsize=6)
            ax_ts.tick_params(labelsize=5.5)
            ax_ts.spines['top'].set_visible(False)
            ax_ts.spines['right'].set_visible(False)
            fig_ts.tight_layout()
            
            img_buf_ts = io.BytesIO()
            fig_ts.savefig(img_buf_ts, format='png', dpi=140, bbox_inches='tight')
            plt.close(fig_ts)
            img_buf_ts.seek(0)
            elements.append(Spacer(1, 4))
            elements.append(RLImage(img_buf_ts, width=440, height=150))
        except Exception as e:
            elements.append(Paragraph(f"Time series tidak dapat diproses: {str(e)}", normal_style))
    else:
        elements.append(Paragraph("Tidak ada kolom tanggal terdeteksi pada dataset ini.", normal_style))
        
    # ── FOOTER SYSTEM ──
    elements.append(Spacer(1, 14))
    elements.append(Paragraph(
        f"— Laporan dibuat otomatis oleh Auto EDA Insight | User: {username} | {pd.Timestamp.now().strftime('%d %B %Y %H:%M')} —",
        ParagraphStyle('Footer', fontSize=6.5, textColor=colors.HexColor('#aaaaaa'), alignment=1)))
        
    doc.build(elements)
    buffer.seek(0)
    
    safe_name = (current_filename or 'dataset').replace(' ','_')
    return send_file(buffer, as_attachment=True,
                     download_name=f"eda_report_{label_dataset.replace(' ','_')}_{safe_name}.pdf",
                     mimetype='application/pdf')


@app.route('/download/csv')
def download_csv():
    global df_global, current_filename, is_cleaned
    if df_global is None:
        return "No data loaded.", 400

    buffer = io.StringIO()
    df_global.to_csv(buffer, index=False)
    buffer.seek(0)

    safe_name = (current_filename or 'dataset').replace(' ', '_')
    suffix = 'after_cleaning' if is_cleaned else 'before_cleaning'
    return send_file(
        io.BytesIO(buffer.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=f"data_{safe_name}_{suffix}.csv",
        mimetype='text/csv'
    )


@app.route('/download/excel')
def download_excel():
    global df_global, current_filename, is_cleaned
    if df_global is None:
        return "No data loaded.", 400

    buffer = io.BytesIO()
    df_global.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)

    safe_name = (current_filename or 'dataset').replace(' ', '_')
    suffix = 'after_cleaning' if is_cleaned else 'before_cleaning'
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"data_{safe_name}_{suffix}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ===== JALANKAN APP — HARUS PALING BAWAH =====

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)