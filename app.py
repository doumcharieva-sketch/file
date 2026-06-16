import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
import random
from sklearn.linear_model import LinearRegression
import numpy as np
import os

DB_NAME = "activity_monitor.db"

# ЕСКІ БАЗАНЫ ЖОЮ (әр іске қосқанда жаңа база)
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print(f"Ескі база жойылды: {DB_NAME}")

# ---------- Дерекқор инициализациясы ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT UNIQUE NOT NULL,
        class_name TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        student_id INTEGER, 
        date TEXT, 
        task_title TEXT, 
        task_type TEXT, 
        grade_10 INTEGER, 
        response_time REAL, 
        attendance INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL, 
        password_hash TEXT NOT NULL, 
        role TEXT NOT NULL, 
        student_id INTEGER UNIQUE
    )''')
    teacher_hash = hashlib.sha256("teacher123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)",
              ("teacher", teacher_hash, "teacher"))
    conn.commit()
    conn.close()
    print("Жаңа дерекқор дайын.")

# ---------- Үлгі деректерді қосу (тек 2026) ----------
def insert_sample_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM activities")
    c.execute("DELETE FROM users WHERE role='student'")
    c.execute("DELETE FROM students")
    classes = {"9А": 20, "9Ә": 20, "9В": 20}
    unique_names = [
        "Айбек Төлегенов", "Диана Смағұлова", "Ерасыл Нұржан", "Жансая Әлібекқызы", "Мерей Қайрат",
        "Нұрай Серікқызы", "Санат Бекболат", "Томирис Жанәділ", "Шыңғыс Арман", "Алихан Нұрланұлы",
        "Аружан Қасымова", "Бекжан Ержанұлы", "Гүлназ Тілеуова", "Дамир Сапарғали", "Әсем Жақсылықова",
        "Жандос Мұратұлы", "Камила Есентаева", "Мадина Байғазина", "Назерке Оразова", "Рахым Жанатұлы",
        "Салтанат Серікқызы", "Талғат Мұқанов", "Ұлжан Бекболатова", "Фатима Омарқызы", "Хантөре Нұржанұлы",
        "Шынар Ержанқызы", "Эльмира Төлегенова", "Ясмина Сапарғалиева", "Азамат Қайратұлы", "Әлихан Серікұлы",
        "Бауыржан Жанәділұлы", "Дастан Арманұлы", "Еркебұлан Мұратұлы", "Жанат Қасымов", "Зере Нұрланқызы",
        "Ислам Бекболатұлы", "Кәусар Оразова", "Ләззат Жақсылықова", "Мөлдір Есентаева", "Нұрсұлтан Байғазин",
        "Олжас Тілеуов", "Перизат Қасымова", "Раушан Жанатқызы", "Самал Мұқанова", "Тәуке Серікұлы",
        "Үміт Нұржанқызы", "Фархат Әлібекұлы", "Хадиша Рахымқызы", "Шығыс Төлегенов", "Элина Смағұлова",
        "Ақжол Бекболатұлы", "Баян Нұржанқызы", "Дәулет Қайратұлы", "Ержан Серікұлы", "Жұлдыз Оразова",
        "Зангар Төлеуов", "Инабат Нұрланқызы", "Қуаныш Мұратұлы", "Лаура Серікқызы", "Мұхтар Байғазин"
    ]
    name_index = 0
    for class_name, count in classes.items():
        for i in range(count):
            student_name = unique_names[name_index]
            name_index += 1
            c.execute("INSERT INTO students (name, class_name) VALUES (?,?)", (student_name, class_name))
    c.execute("SELECT id FROM students")
    student_ids = [row[0] for row in c.fetchall()]
    dates = [
        ("2026-04-01", "Алгоритмдер (БЖБ)", "БЖБ"),
        ("2026-04-08", "Циклдер (БЖБ)", "БЖБ"),
        ("2026-04-15", "Шартты оператор (ТЖБ)", "ТЖБ"),
        ("2026-04-22", "Массивтер (формативті)", "Формативті"),
        ("2026-04-29", "Функциялар (ТЖБ)", "ТЖБ")
    ]
    for sid in student_ids:
        for date, task_title, task_type in dates:
            if task_type == "Формативті":
                grade_10 = random.randint(5, 10)
                resp = random.uniform(5, 15)
            elif task_type == "БЖБ":
                score = random.randint(50, 100)
                grade_10 = round(score / 10)
                resp = random.uniform(15, 30)
            else:
                score = random.randint(50, 100)
                grade_10 = round(score / 10)
                resp = random.uniform(30, 45)
            att = 1 if random.random() > 0.1 else 0
            c.execute(
                "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
                (sid, date, task_title, task_type, grade_10, resp, att))
    c.execute("SELECT id FROM students ORDER BY id")
    for idx, (sid,) in enumerate(c.fetchall(), 1):
        username = f"student{idx}"
        pwd_hash = hashlib.sha256(f"{username}123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role, student_id) VALUES (?,?,?,?)",
                  (username, pwd_hash, "student", sid))
    conn.commit()
    conn.close()
    print("2026 жылғы үлгі деректер қосылды!")

# ---------- Көмекші функциялар ----------
def get_students():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, name FROM students", conn)
    conn.close()
    return df

def get_activities(student_id=None, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT a.*, s.name, s.class_name FROM activities a JOIN students s ON a.student_id = s.id"
    params, cond = [], []
    if student_id:
        cond.append("a.student_id = ?")
        params.append(student_id)
    if start_date:
        cond.append("a.date >= ?")
        params.append(start_date)
    if end_date:
        cond.append("a.date <= ?")
        params.append(end_date)
    if cond:
        query += " WHERE " + " AND ".join(cond)
    query += " ORDER BY a.date"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def add_activity(student_id, date, task_title, task_type, grade_10, response_time, attendance):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
        (student_id, date, task_title, task_type, grade_10, response_time, attendance))
    conn.commit()
    conn.close()

def calc_index(row):
    score_norm = row['grade_10'] / 10.0
    att_norm = row['attendance']
    time_norm = max(0, 1 - row['response_time'] / 30)
    return round((score_norm * 0.6 + att_norm * 0.2 + time_norm * 0.2) * 100, 1)

def predict_next_grade(student_id):
    df = get_activities(student_id=student_id)
    if len(df) < 2:
        return None
    df = df.sort_values('date')
    X = np.arange(len(df)).reshape(-1, 1)
    y = df['grade_10'].values
    model = LinearRegression().fit(X, y)
    next_x = np.array([[len(df)]])
    pred = model.predict(next_x)[0]
    return round(np.clip(pred, 1, 10), 1)

def authenticate(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT role, student_id FROM users WHERE username=? AND password_hash=?", (username, pwd_hash))
    row = c.fetchone()
    conn.close()
    return row

def get_student_name(student_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "Оқушы"

def get_student_login_info():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT s.name, u.username FROM students s JOIN users u ON u.student_id = s.id WHERE u.role='student' ORDER BY s.id",
        conn)
    conn.close()
    df['password'] = df['username'] + "123"
    return df

def show_database():
    st.subheader("📁 Дерекқор кестелері")
    conn = sqlite3.connect(DB_NAME)
    for table in ["students", "activities", "users"]:
        st.markdown(f"**{table}**")
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        st.dataframe(df, use_container_width=True)
    conn.close()

# ---------- Деңгейлеу функциясы ----------
def get_level(score):
    if score >= 80:
        return "🟢 Жоғары"
    elif score >= 50:
        return "🟡 Орта"
    else:
        return "🔴 Төмен"

def get_level_short(score):
    if score >= 80:
        return "Жоғары"
    elif score >= 50:
        return "Орта"
    else:
        return "Төмен"

# ---------- STREAMLIT ----------
init_db()
insert_sample_data()  # Автоматты түрде 2026 деректер қосылады

st.set_page_config(layout="wide")

if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.role = None
    st.session_state.sid = None

if not st.session_state.auth:
    st.title("📚 Информатика мониторинг жүйесі")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Логин", key="login_user")
    with col2:
        password = st.text_input("Пароль", type="password", key="login_pass")
    if st.button("Кіру", key="login_btn"):
        user = authenticate(username, password)
        if user:
            st.session_state.auth = True
            st.session_state.role = user[0]
            st.session_state.sid = user[1]
            st.success("Қош келдіңіз!")
            st.rerun()
        else:
            st.error("Логин немесе пароль қате")
    st.stop()

st.title("📊 Информатика пәні бойынша оқу белсенділігін мониторингтеу жүйесі")

# Sidebar
with st.sidebar:
    if st.session_state.role == "teacher":
        st.markdown("### 📌 Басты әрекеттер")
        if st.button("📂 Базаны көрсету", key="db_btn"):
            st.session_state.show_db = True
        if st.button("➕ Үлгі деректерді қосу (2026)", key="sample_btn"):
            insert_sample_data()
            st.success("2026 жылғы үлгі деректер қосылды!")
            st.rerun()
        st.markdown("---")
        st.markdown("### 📊 Графиктер")
        if st.button("📊 Белсенділік", key="sidebar_act"):
            st.session_state.show_act = True
        if st.button("🔮 Болжам", key="sidebar_pred"):
            st.session_state.show_pred = True
        if st.button("⚠️ Ескертулер", key="sidebar_warn"):
            st.session_state.show_warn = True
        if st.button("📈 Сызықтық салыстыру", key="sidebar_line"):
            st.session_state.show_line = True
        if st.button("🔥 Жылу картасы", key="sidebar_heat"):
            st.session_state.show_heat = True
        if st.button("🏆 Үздік оқушылар", key="sidebar_top"):
            st.session_state.show_top = True
    st.markdown("---")
    if st.button("🚪 Шығу", key="logout_btn"):
        for k in ['auth', 'role', 'sid', 'show_db', 'show_act', 'show_pred', 'show_warn', 'show_line', 'show_heat']:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

if st.session_state.get("show_db", False):
    show_database()
    if st.button("Жабу", key="close_db"):
        st.session_state.show_db = False
        st.rerun()
    st.markdown("---")

# ---------- Мұғалім интерфейсі ----------
if st.session_state.role == "teacher":
    students_df = get_students()
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Басталу күні", datetime(2026, 4, 1), key="start")
    with col2:
        end_date = st.date_input("Аяқталу күні", datetime(2026, 5, 1), key="end")
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    tabs = st.tabs(["📈 Мониторинг", "✏️ Деректерді енгізу", "📉 Жеке графиктер", "📊 Сыныптық талдау", "🔑 Оқушы логиндері", "📂 Импорт / API"])

    with tabs[0]:
        conn = sqlite3.connect(DB_NAME)
        classes_df = pd.read_sql_query("SELECT DISTINCT class_name FROM students ORDER BY class_name", conn)
        conn.close()
        class_list = classes_df['class_name'].tolist() if not classes_df.empty else ["9А", "9Ә", "9В"]
        selected_class = st.selectbox("📚 Сыныпты таңдаңыз", class_list, key="class_selector")

        df = get_activities(start_date=start_str, end_date=end_str)
        df = df[df['class_name'] == selected_class]

        if df.empty:
            st.info(f"{selected_class} сыныбы үшін берілген күн аралығында деректер жоқ.")
        else:
            df['Белсенділік'] = df.apply(calc_index, axis=1)
            task_type_filter = st.selectbox("Тапсырма түрін таңдаңыз", ["Формативті", "БЖБ", "ТЖБ"], key="task_type_filter")
            df_filtered = df[df['task_type'] == task_type_filter].copy()

            if df_filtered.empty:
                st.info(f"Бұл күн аралығында {task_type_filter} түрі бойынша деректер жоқ.")
            else:
                # Соңғы тапсырма бойынша әр оқушының көрсеткіштері
                latest_filtered = df_filtered.sort_values('date').groupby('student_id').last().reset_index()
                predictions = []
                warnings = []
                for _, row in latest_filtered.iterrows():
                    sid = row['student_id']
                    pred = predict_next_grade(sid)
                    predictions.append(pred if pred is not None else "—")
                    # Ескерту тек төменгі деңгей үшін (қызыл)
                    if row['Белсенділік'] < 50:
                        warnings.append("🔴 Төмен деңгей")
                    else:
                        warnings.append("")

                full_df = pd.DataFrame({
                    'Оқушы': latest_filtered['name'],
                    'Баға (1-10)': latest_filtered['grade_10'],
                    'Уақыт (мин)': latest_filtered['response_time'],
                    'Қатысу': latest_filtered['attendance'],
                    'Белсенділік (0-100)': latest_filtered['Белсенділік'],
                    'Келесі болжам': predictions,
                    'Ескерту': warnings
                })

                # ----- ҮШ ДЕҢГЕЙЛІ КЕРІ БАЙЛАНЫС (ЖАСЫЛ, САРЫ, ҚЫЗЫЛ) -----
                full_df['Деңгей'] = full_df['Белсенділік (0-100)'].apply(get_level)
                # Деңгейдің қысқаша атауы (педагогикалық ұсыныстар үшін)
                full_df['Ұсыныс'] = full_df['Белсенділік (0-100)'].apply(
                    lambda x: '🏆 Жоғары деңгей – мадақтау, күрделі тапсырмалар' if x >= 80 else
                              '📚 Орта деңгей – қосымша жаттығулар, жеке көмек' if x >= 50 else
                              '⚠️ Төмен деңгей – себебін анықтау, ата-анамен байланыс'
                )

                # Статистика: деңгейлер бойынша бөліну
                level_counts = full_df['Деңгей'].value_counts()
                total = len(full_df)
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    green = level_counts.get('🟢 Жоғары', 0)
                    st.metric("🟢 Жоғары деңгей", f"{green} ({green/total*100:.1f}%)")
                with col_stats2:
                    yellow = level_counts.get('🟡 Орта', 0)
                    st.metric("🟡 Орта деңгей", f"{yellow} ({yellow/total*100:.1f}%)")
                with col_stats3:
                    red = level_counts.get('🔴 Төмен', 0)
                    st.metric("🔴 Төмен деңгей", f"{red} ({red/total*100:.1f}%)")

                st.subheader(f"📋 {selected_class} сыныбының оқушылар кестесі (деңгейлер бойынша)")
                # Кестені түспен көрсету (деңгей бағаны бойынша)
                styled_df = full_df.style.applymap(
                    lambda v: 'background-color: #c8e6c9' if v == '🟢 Жоғары' else
                              'background-color: #fff9c4' if v == '🟡 Орта' else
                              'background-color: #ffcdd2' if v == '🔴 Төмен' else '',
                    subset=['Деңгей']
                )
                st.dataframe(styled_df, use_container_width=True)

                # ----- Графиктер (бұрынғыдай, бірақ деңгейлер қосылды) -----
                if st.session_state.get("show_act", False):
                    st.subheader("📊 Белсенділік индексі (гистограмма) – деңгейлер бойынша")
                    fig_act = px.bar(full_df, x='Оқушы', y='Белсенділік (0-100)',
                                     color='Деңгей', title="Белсенділік индексі",
                                     color_discrete_map={'🟢 Жоғары':'green', '🟡 Орта':'gold', '🔴 Төмен':'red'})
                    fig_act.update_layout(height=400)
                    st.plotly_chart(fig_act, use_container_width=True)
                    st.session_state.show_act = False

                if st.session_state.get("show_pred", False):
                    st.subheader("🔮 Келесі тапсырмаға болжамды бағалар")
                    fig_pred = px.bar(full_df, x='Оқушы', y='Келесі болжам',
                                      title="Болжамды бағалар (1-10)",
                                      color='Келесі болжам', color_continuous_scale='Blues')
                    fig_pred.update_layout(height=400)
                    st.plotly_chart(fig_pred, use_container_width=True)
                    st.session_state.show_pred = False

                if st.session_state.get("show_warn", False):
                    st.subheader("⚠️ Ескерту қажет оқушылар (Төмен деңгей)")
                    warns = full_df[full_df['Деңгей'] == '🔴 Төмен']
                    if not warns.empty:
                        st.warning("Төмендегі оқушыларға назар аударыңыз (ОБИ < 50):")
                        st.dataframe(warns[['Оқушы', 'Белсенділік (0-100)', 'Келесі болжам', 'Ұсыныс']],
                                     use_container_width=True)
                    else:
                        st.success("Төмен деңгейдегі оқушы жоқ.")
                    st.session_state.show_warn = False

                if st.session_state.get("show_line", False):
                    st.subheader("📈 Белсенділік пен болжамның сызықтық салыстыруы")
                    fig_line = px.line(full_df, x='Оқушы',
                                       y=['Белсенділік (0-100)', 'Келесі болжам'],
                                       title="Салыстыру", markers=True,
                                       color_discrete_sequence=['#2ed573', '#4a9eff'])
                    fig_line.update_layout(height=400)
                    st.plotly_chart(fig_line, use_container_width=True)
                    st.session_state.show_line = False

                if st.session_state.get("show_heat", False):
                    st.subheader("🔥 Жылу картасы (оқушылар × күндер)")
                    pivot = df_filtered.pivot_table(index='name', columns='date', values='grade_10', aggfunc='first')
                    if not pivot.empty:
                        fig_heat = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale='Blues',
                                             title="Бағалар")
                        fig_heat.update_layout(height=400)
                        st.plotly_chart(fig_heat, use_container_width=True)
                    else:
                        st.info("Жылу картасы үшін деректер жоқ.")
                    st.session_state.show_heat = False

                st.caption("🟢 Жоғары (ОБИ≥80) | 🟡 Орта (50-79) | 🔴 Төмен (<50)")

                if st.session_state.get("show_top", False):
                    st.subheader("🏆 Үздік оқушылар")
                    top_by_grade = full_df.nlargest(5, 'Баға (1-10)')[['Оқушы', 'Баға (1-10)', 'Деңгей']]
                    st.write("**Ең жоғары балл алған 5 оқушы:**")
                    st.dataframe(top_by_grade, use_container_width=True)
                    top_by_activity = full_df.nlargest(5, 'Белсенділік (0-100)')[['Оқушы', 'Белсенділік (0-100)', 'Деңгей']]
                    st.write("**Ең белсенді 5 оқушы:**")
                    st.dataframe(top_by_activity, use_container_width=True)
                    st.session_state.show_top = False

    # Қалған қойындылар (өзгеріссіз)
    with tabs[1]:
        if students_df.empty:
            st.warning("Оқушылар жоқ")
        else:
            task_type = st.selectbox("Тапсырма түрі", ["Формативті", "БЖБ", "ТЖБ"], key="add_task_type")
            default_title = f"{task_type} тапсырмасы"
            task_title = st.text_input("Тапсырма атауы", value=default_title, key="task_title")
            if task_type == "Формативті":
                max_grade = 10
                grade_label = "Баға (1-10)"
                default_time = 10.0
                time_help = "5-15 мин"
            else:
                max_grade = 100
                grade_label = "Баға (0-100)"
                default_time = 25.0 if task_type == "БЖБ" else 40.0
                time_help = "20-30 мин" if task_type == "БЖБ" else "40 мин"
            student = st.selectbox("Оқушы", students_df['name'].tolist(), key="add_student")
            sid = students_df[students_df['name'] == student]['id'].values[0]
            date = st.date_input("Күн", datetime.today(), key="add_date")
            if max_grade == 10:
                grade = st.slider(grade_label, 1, max_grade, 5, key="add_grade")
                grade_10 = grade
            else:
                score_100 = st.slider(grade_label, 0, max_grade, 70, key="add_grade")
                grade_10 = round(score_100 / 10)
                st.caption(f"1-10 балдық баға: {grade_10}")
            rt = st.number_input(f"Жауап уақыты (мин) - {time_help}", 0.0, 120.0, default_time, 0.5, key="add_time")
            att = 1 if st.radio("Қатысу", ["Келді", "Келмеді"], horizontal=True, key="add_att") == "Келді" else 0
            if st.button("💾 Сақтау", key="add_save"):
                add_activity(sid, date.strftime("%Y-%m-%d"), task_title, task_type, grade_10, rt, att)
                st.success("Сақталды!")
                st.rerun()

    with tabs[2]:
        if not students_df.empty:
            selected = st.selectbox("Оқушыны таңдаңыз", students_df['name'].tolist(), key="chart_student")
            all_activities = get_activities(start_date=start_str, end_date=end_str)
            df_stu = all_activities[all_activities['name'] == selected]
            if df_stu.empty:
                st.info(f"Бұл оқушыға {start_str} мен {end_str} аралығында деректер жоқ")
            else:
                df_stu['Белсенділік'] = df_stu.apply(calc_index, axis=1)
                df_stu = df_stu.sort_values('date')
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.line(df_stu, x='date', y='grade_10', markers=True, color='task_type', title="Балл өзгерісі"), use_container_width=True)
                with c2:
                    st.plotly_chart(px.line(df_stu, x='date', y='response_time', markers=True, color='task_type', title="Уақыт динамикасы"), use_container_width=True)
                st.plotly_chart(px.bar(df_stu, x='date', y='Белсенділік', color='task_type', title="Белсенділік индексі"), use_container_width=True)

    with tabs[3]:
        df_class = get_activities(start_date=start_str, end_date=end_str)
        if not df_class.empty:
            df_class['Белсенділік'] = df_class.apply(calc_index, axis=1)
            avg_grade = df_class.groupby('date')['grade_10'].mean().reset_index()
            avg_idx = df_class.groupby('date')['Белсенділік'].mean().reset_index()
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.line(avg_grade, x='date', y='grade_10', markers=True, title="Сыныптың орташа бағасы"), use_container_width=True)
            with c2:
                st.plotly_chart(px.line(avg_idx, x='date', y='Белсенділік', markers=True, title="Сыныптың орташа белсенділігі"), use_container_width=True)
            pivot = df_class.pivot_table(index='name', columns='date', values='grade_10')
            if not pivot.empty:
                st.plotly_chart(px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale='Blues', title="Жылу картасы"), use_container_width=True)
        else:
            st.info("Деректер жоқ")

    with tabs[4]:
        df_login = get_student_login_info()
        if not df_login.empty:
            st.dataframe(df_login, use_container_width=True)
            st.info("Пароль: логин + '123' (мысалы, student1 → student1123)")

    with tabs[5]:
        st.subheader("📂 Файлдан импорттау (CSV, XLSX)")
        uploaded_file = st.file_uploader("Деректері бар файлды таңдаңыз", type=['csv', 'xlsx'])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded_file)
                else:
                    df_import = pd.read_excel(uploaded_file, engine='openpyxl')
                df_import.columns = df_import.columns.str.strip().str.lower()
                column_mapping = {
                    'оқушы': 'student_name', 'оқушы аты': 'student_name', 'student_name': 'student_name',
                    'күн': 'date', 'date': 'date',
                    'тапсырма атауы': 'task_title', 'тапсырма': 'task_title', 'task_title': 'task_title',
                    'тапсырма түрі': 'task_type', 'түрі': 'task_type', 'task_type': 'task_type',
                    'баға(1-10)': 'grade_10', 'баға': 'grade_10', 'grade_10': 'grade_10',
                    'уақыт': 'response_time', 'жауап уақыты': 'response_time', 'response_time': 'response_time',
                    'қатысу': 'attendance', 'attendance': 'attendance'
                }
                df_import.rename(columns=column_mapping, inplace=True)
                if 'date' in df_import.columns:
                    df_import['date'] = pd.to_datetime(df_import['date']).dt.strftime('%Y-%m-%d')
                required_cols = ['student_name', 'date', 'task_title', 'task_type', 'grade_10', 'response_time', 'attendance']
                missing_cols = [col for col in required_cols if col not in df_import.columns]
                if missing_cols:
                    st.error(f"Қажетті бағандар табылмады: {missing_cols}")
                else:
                    st.dataframe(df_import.head())
                    students_df_local = get_students()
                    name_to_id = dict(zip(students_df_local['name'], students_df_local['id']))
                    import_rows = []
                    for _, row in df_import.iterrows():
                        if row['student_name'] in name_to_id:
                            import_rows.append((name_to_id[row['student_name']], row['date'], row['task_title'], row['task_type'], int(row['grade_10']), float(row['response_time']), int(row['attendance'])))
                    if st.button("Импорттау"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.executemany("INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)", import_rows)
                        conn.commit()
                        conn.close()
                        st.success(f"{len(import_rows)} жол импортталды")
                        st.rerun()
            except Exception as e:
                st.error(f"Қате: {e}")

# ---------- Оқушы интерфейсі ----------
else:
    name = get_student_name(st.session_state.sid)
    st.subheader(f"Қош келдің, {name}!")
    df = get_activities(student_id=st.session_state.sid)
    if df.empty:
        st.info("Сізге әлі баға енгізілмеген")
    else:
        df['Белсенділік'] = df.apply(calc_index, axis=1)
        # Оқушының деңгейін есептеу (соңғы белсенділік бойынша)
        latest_score = df.sort_values('date').iloc[-1]['Белсенділік']
        level = get_level(latest_score)
        st.info(f"Сіздің ағымдағы деңгейіңіз: **{level}** (ОБИ = {latest_score})")
        st.dataframe(df[['date', 'task_title', 'task_type', 'grade_10', 'response_time', 'attendance', 'Белсенділік']], use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.line(df, x='date', y='grade_10', markers=True, color='task_type', title="Менің бағаларым"), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df, x='date', y='Белсенділік', color='task_type', title="Менің белсенділік индексім"), use_container_width=True)
