import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
import random
from sklearn.linear_model import LinearRegression
import numpy as np

DB_NAME = "activity_monitor.db"


# ---------- Дерекқор инициализациясы ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, task_title TEXT, task_type TEXT, grade_10 INTEGER, response_time REAL, attendance INTEGER)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, student_id INTEGER UNIQUE)''')

    students = ["Айбек Төлегенов", "Диана Смағұлова", "Ерасыл Нұржан", "Жансая Әлібекқызы", "Мерей Қайрат",
                "Нұрай Серікқызы", "Санат Бекболат", "Томирис Жанәділ", "Шыңғыс Арман"]
    for name in students:
        c.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))

    teacher_hash = hashlib.sha256("teacher123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)",
              ("teacher", teacher_hash, "teacher"))

    c.execute("SELECT id FROM students")
    for idx, (sid,) in enumerate(c.fetchall(), 1):
        username = f"student{idx}"
        pwd_hash = hashlib.sha256(f"{username}123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role, student_id) VALUES (?,?,?,?)",
                  (username, pwd_hash, "student", sid))
    conn.commit()
    conn.close()
    print("Дерекқор дайын")


# ---------- Үлгі деректерді қосу ----------
def insert_sample_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM activities")
    students_df = get_students()
    sids = students_df['id'].tolist()
    for sid in sids:
        # Формативті (3 тапсырма)
        for i in range(1, 4):
            grade = random.randint(5, 10)
            rt = random.uniform(5, 12)
            att = 1 if random.random() > 0.1 else 0
            date = f"2025-04-{10 + i}"
            c.execute(
                "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
                (sid, date, f"Формативті {i}", "Формативті", grade, rt, att))
        # БЖБ (2 тапсырма)
        for i in range(4, 6):
            score_100 = random.randint(50, 100)
            grade = round(score_100 / 10)
            rt = random.uniform(20, 30)
            att = 1 if random.random() > 0.1 else 0
            date = f"2025-04-{10 + i}"
            c.execute(
                "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
                (sid, date, f"БЖБ {i - 3}", "БЖБ", grade, rt, att))
        # ТЖБ (1 тапсырма)
        score_100 = random.randint(50, 100)
        grade = round(score_100 / 10)
        rt = random.uniform(35, 45)
        att = 1 if random.random() > 0.1 else 0
        date = "2025-04-16"
        c.execute(
            "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
            (sid, date, "ТЖБ", "ТЖБ", grade, rt, att))
    conn.commit()
    conn.close()


# ---------- Көмекші функциялар ----------
def get_students():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, name FROM students", conn)
    conn.close()
    return df


def get_activities(student_id=None, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT a.*, s.name FROM activities a JOIN students s ON a.student_id = s.id"
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


# ---------- STREAMLIT ----------
init_db()
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

with st.sidebar:
    if st.session_state.role == "teacher":
        if st.button("📂 Базаны көрсету", key="db_btn"):
            st.session_state.show_db = True
        if st.button("➕ Үлгі деректерді қосу", key="sample_btn"):
            insert_sample_data()
            st.success("Үлгі деректер қосылды! Бетті жаңартыңыз.")
            st.rerun()
        st.markdown("---")
    if st.button("🚪 Шығу", key="logout_btn"):
        for k in ['auth', 'role', 'sid', 'show_db']:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

if st.session_state.get("show_db", False):
    show_database()
    if st.button("Жабу", key="close_db"):
        st.session_state.show_db = False
        st.rerun()
    st.markdown("---")

# ---------- МҰҒАЛІМ ИНТЕРФЕЙСІ ----------
if st.session_state.role == "teacher":
    students_df = get_students()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Басталу күні", datetime(2025, 4, 1), key="start")
    with col2:
        end_date = st.date_input("Аяқталу күні", datetime(2025, 5, 1), key="end")
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    tabs = st.tabs(
        ["📈 Мониторинг", "✏️ Деректерді енгізу", "📉 Жеке графиктер", "📊 Сыныптық талдау", "🔑 Оқушы логиндері",
         "📂 Импорт / API"])

    with tabs[0]:
        df = get_activities(start_date=start_str, end_date=end_str)
        if df.empty:
            st.info("Берілген күн аралығында деректер жоқ. «Үлгі деректерді қосу» арқылы қосыңыз.")
        else:
            df['Белсенділік'] = df.apply(calc_index, axis=1)
            task_type_filter = st.selectbox("Тапсырма түрін таңдаңыз", ["Формативті", "БЖБ", "ТЖБ"],
                                            key="task_type_filter")
            df_filtered = df[df['task_type'] == task_type_filter].copy()
            if df_filtered.empty:
                st.info(f"Бұл күн аралығында {task_type_filter} түрі бойынша деректер жоқ.")
            else:
                latest_filtered = df_filtered.sort_values('date').groupby('student_id').last().reset_index()
                predictions = []
                warnings = []
                for _, row in latest_filtered.iterrows():
                    sid = row['student_id']
                    pred = predict_next_grade(sid)
                    predictions.append(pred if pred is not None else "—")
                    if row['Белсенділік'] < 50 or row['grade_10'] < 4:
                        warnings.append("⚠️")
                    else:
                        warnings.append("")
                display_df = pd.DataFrame({
                    'Оқушы': latest_filtered['name'],
                    'Баға (1-10)': latest_filtered['grade_10'],
                    'Уақыт (мин)': latest_filtered['response_time'],
                    'Қатысу': latest_filtered['attendance'],
                    'Белсенділік (0-100)': latest_filtered['Белсенділік'],
                    'Келесі болжам': predictions,
                    'Ескерту': warnings
                })
                st.dataframe(display_df, use_container_width=True)
                fig = px.bar(display_df, x='Оқушы', y='Белсенділік (0-100)',
                             title=f"{task_type_filter} түрі бойынша соңғы белсенділік индексі")
                st.plotly_chart(fig, use_container_width=True)

    # ---------- 2. Деректерді енгізу ----------
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

    # ---------- 3. Жеке графиктер ----------
    with tabs[2]:
        if not students_df.empty:
            selected = st.selectbox("Оқушыны таңдаңыз", students_df['name'].tolist(), key="chart_student")
            sid = students_df[students_df['name'] == selected]['id'].values[0]
            df = get_activities(student_id=sid, start_date=start_str, end_date=end_str)
            if df.empty:
                st.info("Бұл оқушыға деректер жоқ")
            else:
                df['Белсенділік'] = df.apply(calc_index, axis=1)
                df = df.sort_values('date')
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(
                        px.line(df, x='date', y='grade_10', markers=True, color='task_type', title="Балл өзгерісі"),
                        use_container_width=True)
                with c2:
                    st.plotly_chart(px.line(df, x='date', y='response_time', markers=True, color='task_type',
                                            title="Уақыт динамикасы"), use_container_width=True)
                st.plotly_chart(px.bar(df, x='date', y='Белсенділік', color='task_type', title="Белсенділік индексі"),
                                use_container_width=True)

    # ---------- 4. Сыныптық талдау ----------
    with tabs[3]:
        df = get_activities(start_date=start_str, end_date=end_str)
        if not df.empty:
            df['Белсенділік'] = df.apply(calc_index, axis=1)
            avg_grade = df.groupby('date')['grade_10'].mean().reset_index()
            avg_idx = df.groupby('date')['Белсенділік'].mean().reset_index()
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(
                    px.line(avg_grade, x='date', y='grade_10', markers=True, title="Сыныптың орташа бағасы"),
                    use_container_width=True)
            with c2:
                st.plotly_chart(
                    px.line(avg_idx, x='date', y='Белсенділік', markers=True, title="Сыныптың орташа белсенділігі"),
                    use_container_width=True)
            pivot = df.pivot_table(index='name', columns='date', values='grade_10')
            if not pivot.empty:
                st.plotly_chart(px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale='Blues',
                                          title="Жылу картасы (бағалар)"), use_container_width=True)
        else:
            st.info("Деректер жоқ")

    # ---------- 5. Оқушы логиндері ----------
    with tabs[4]:
        df_login = get_student_login_info()
        if not df_login.empty:
            st.dataframe(df_login, use_container_width=True)
            st.info("Пароль: логин + '123' (мысалы, student1 → student1123)")

    # ---------- 6. Импорт / API ----------
    with tabs[5]:
        st.subheader("CSV импорт (әзірлену үстінде)")
        st.info("Бұл функция келесі нұсқада қосылады.")
        st.subheader("Kundelik.kz API (тәжірибелік)")
        st.info("API интеграциясы әзірленуде.")

# ---------- ОҚУШЫ ИНТЕРФЕЙСІ ----------
else:
    name = get_student_name(st.session_state.sid)
    st.subheader(f"Қош келдің, {name}!")
    df = get_activities(student_id=st.session_state.sid)
    if df.empty:
        st.info("Сізге әлі баға енгізілмеген")
    else:
        df['Белсенділік'] = df.apply(calc_index, axis=1)
        st.dataframe(df[['date', 'task_title', 'task_type', 'grade_10', 'response_time', 'attendance', 'Белсенділік']],
                     use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                px.line(df, x='date', y='grade_10', markers=True, color='task_type', title="Менің бағаларым"),
                use_container_width=True)
        with c2:
            st.plotly_chart(
                px.bar(df, x='date', y='Белсенділік', color='task_type', title="Менің белсенділік индексім"),
                use_container_width=True)