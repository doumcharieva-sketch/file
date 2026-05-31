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


# ---------- Дерекқор инициализациясы (тек кестелер мен мұғалім) ----------
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
    print("Дерекқор құрылымы дайын.")


# ---------- Үлгі деректерді қосу (батырма арқылы) ----------
def insert_sample_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Барлық ескі деректерді өшіру (қайталануды болдырмау үшін)
    c.execute("DELETE FROM activities")
    c.execute("DELETE FROM users WHERE role='student'")
    c.execute("DELETE FROM students")

    # 2. Сыныптар мен оқушылар саны
    classes = {
        "9А": 20,
        "9Ә": 20,
        "9В": 20
    }

    # 3. 60 бірегей есім тізімі (қайталанбайтын)
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
    ]  # Дәл 60 есім

    # 4. Оқушыларды қосу (әр сыныпқа 20 бірегей есім)
    name_index = 0
    for class_name, count in classes.items():
        for i in range(count):
            student_name = unique_names[name_index]
            name_index += 1
            c.execute("INSERT INTO students (name, class_name) VALUES (?,?)", (student_name, class_name))

    # 5. Барлық оқушы ID-лерін алу
    c.execute("SELECT id FROM students")
    student_ids = [row[0] for row in c.fetchall()]

    # 6. Әр оқушыға бағалар енгізу (5 тапсырма)
    dates = [
        ("2025-04-01", "Алгоритмдер (БЖБ)", "БЖБ"),
        ("2025-04-08", "Циклдер (БЖБ)", "БЖБ"),
        ("2025-04-15", "Шартты оператор (ТЖБ)", "ТЖБ"),
        ("2025-04-22", "Массивтер (формативті)", "Формативті"),
        ("2025-04-29", "Функциялар (ТЖБ)", "ТЖБ")
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
            else:  # ТЖБ
                score = random.randint(50, 100)
                grade_10 = round(score / 10)
                resp = random.uniform(30, 45)
            att = 1 if random.random() > 0.1 else 0
            c.execute(
                "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
                (sid, date, task_title, task_type, grade_10, resp, att))

    # 7. Оқушылардың логиндерін жасау (student1, student2, ..., student60)
    c.execute("SELECT id FROM students ORDER BY id")
    for idx, (sid,) in enumerate(c.fetchall(), 1):
        username = f"student{idx}"
        pwd_hash = hashlib.sha256(f"{username}123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username, password_hash, role, student_id) VALUES (?,?,?,?)",
                  (username, pwd_hash, "student", sid))

    conn.commit()
    conn.close()
    print("Үлгі деректер сәтті қосылды!")


# ---------- Қалған функциялар ----------
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

# Бүйірлік панель
with st.sidebar:
    if st.session_state.role == "teacher":
        st.markdown("### 📌 Басты әрекеттер")
        if st.button("📂 Базаны көрсету", key="db_btn"):
            st.session_state.show_db = True
        if st.button("➕ Үлгі деректерді қосу", key="sample_btn"):
            insert_sample_data()
            st.success("Үлгі деректер қосылды! Бетті жаңартыңыз.")
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

# Мұғалім интерфейсі
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
        # ----- Сынып таңдау селекторы (басында) -----
        # Барлық сыныптарды алу
        conn = sqlite3.connect(DB_NAME)
        classes_df = pd.read_sql_query("SELECT DISTINCT class_name FROM students ORDER BY class_name", conn)
        conn.close()
        class_list = classes_df['class_name'].tolist() if not classes_df.empty else ["9А", "9Ә", "9В"]
        selected_class = st.selectbox("📚 Сыныпты таңдаңыз", class_list, key="class_selector")

        # Деректерді жүктеу
        df = get_activities(start_date=start_str, end_date=end_str)
        # Таңдалған сынып бойынша сүзу
        df = df[df['class_name'] == selected_class]

        if df.empty:
            st.info(
                f"{selected_class} сыныбы үшін берілген күн аралығында деректер жоқ. «Үлгі деректерді қосу» арқылы қосыңыз.")
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

                full_df = pd.DataFrame({
                    'Оқушы': latest_filtered['name'],
                    'Баға (1-10)': latest_filtered['grade_10'],
                    'Уақыт (мин)': latest_filtered['response_time'],
                    'Қатысу': latest_filtered['attendance'],
                    'Белсенділік (0-100)': latest_filtered['Белсенділік'],
                    'Келесі болжам': predictions,
                    'Ескерту': warnings
                })
                st.subheader(f"📋 {selected_class} сыныбының оқушылар кестесі")
                st.dataframe(full_df, use_container_width=True)

                if st.session_state.get("show_act", False):
                    st.subheader("📊 Белсенділік индексі (гистограмма)")
                    fig_act = px.bar(full_df, x='Оқушы', y='Белсенділік (0-100)',
                                     title="Белсенділік индексі (0-100)",
                                     color='Белсенділік (0-100)', color_continuous_scale='Viridis')
                    fig_act.update_layout(height=400, autosize=True)
                    st.plotly_chart(fig_act, use_container_width=True)
                    st.session_state.show_act = False

                if st.session_state.get("show_pred", False):
                    st.subheader("🔮 Келесі тапсырмаға болжамды бағалар")
                    fig_pred = px.bar(full_df, x='Оқушы', y='Келесі болжам',
                                      title="Болжамды бағалар (1-10)",
                                      color='Келесі болжам', color_continuous_scale='Blues')
                    fig_pred.update_layout(height=400, autosize=True)
                    st.plotly_chart(fig_pred, use_container_width=True)
                    st.session_state.show_pred = False

                if st.session_state.get("show_warn", False):
                    st.subheader("⚠️ Ескерту қажет оқушылар")
                    warns = full_df[full_df['Ескерту'] == "⚠️"]
                    if not warns.empty:
                        st.warning("Төмендегі оқушыларға назар аударыңыз:")
                        st.dataframe(warns[['Оқушы', 'Белсенділік (0-100)', 'Келесі болжам']],
                                     use_container_width=True)
                    else:
                        st.success("Ескерту қажет оқушы жоқ.")
                    st.session_state.show_warn = False

                if st.session_state.get("show_line", False):
                    st.subheader("📈 Белсенділік пен болжамның сызықтық салыстыруы")
                    fig_line = px.line(full_df, x='Оқушы',
                                       y=['Белсенділік (0-100)', 'Келесі болжам'],
                                       title="Белсенділік пен болжамның салыстыруы (сызықтық)",
                                       markers=True,
                                       color_discrete_sequence=['#2ed573', '#4a9eff'])
                    fig_line.update_layout(height=400, autosize=True)
                    st.plotly_chart(fig_line, use_container_width=True)
                    st.session_state.show_line = False

                if st.session_state.get("show_heat", False):
                    st.subheader("🔥 Жылу картасы (оқушылар × күндер)")
                    pivot = df_filtered.pivot_table(index='name', columns='date', values='grade_10', aggfunc='first')
                    if not pivot.empty:
                        fig_heat = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale='Blues',
                                             title="Бағалардың жылу картасы")
                        fig_heat.update_layout(height=400, autosize=True)
                        st.plotly_chart(fig_heat, use_container_width=True)
                    else:
                        st.info("Жылу картасы үшін деректер жоқ.")
                    st.session_state.show_heat = False

                st.caption("⚠️ - белсенділік 50-ден төмен немесе баға 4-тен төмен оқушылар")

                if st.session_state.get("show_top", False):
                    st.subheader("🏆 Үздік оқушылар")

                    # Бағасы бойынша ең жоғары 5 оқушы
                    top_by_grade = full_df.nlargest(5, 'Баға (1-10)')[['Оқушы', 'Баға (1-10)', 'Белсенділік (0-100)']]
                    st.write("**Ең жоғары балл алған 5 оқушы:**")
                    st.dataframe(top_by_grade, use_container_width=True)

                    # Белсенділігі бойынша ең жоғары 5 оқушы
                    top_by_activity = full_df.nlargest(5, 'Белсенділік (0-100)')[
                        ['Оқушы', 'Белсенділік (0-100)', 'Баға (1-10)']]
                    st.write("**Ең белсенді 5 оқушы:**")
                    st.dataframe(top_by_activity, use_container_width=True)

                    # Біріктірілген (бағасы да, белсенділігі де жоғары)
                    top_both = full_df[(full_df['Баға (1-10)'] >= 9) & (full_df['Белсенділік (0-100)'] >= 80)]
                    if not top_both.empty:
                        st.write("**Бағасы ≥ 9 ЖӘНЕ Белсенділігі ≥ 80 оқушылар:**")
                        st.dataframe(top_both[['Оқушы', 'Баға (1-10)', 'Белсенділік (0-100)']],
                                     use_container_width=True)
                    else:
                        st.info("Жоғары балл мен белсенділікті біріктірген оқушы жоқ.")

                    st.session_state.show_top = False  # бір рет көрсетіп, батырманы қайтару

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
            df = all_activities[all_activities['name'] == selected]
            if df.empty:
                st.info(f"Бұл оқушыға {start_str} мен {end_str} аралығында деректер жоқ")
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
                # 1. Файлды оқу
                if uploaded_file.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded_file)
                else:
                    df_import = pd.read_excel(uploaded_file, engine='openpyxl')

                # 2. Баған атауларын қалыпқа келтіру (бос орындарды өшіру, кіші әріпке түрлендіру)
                df_import.columns = df_import.columns.str.strip().str.lower()

                # 3. Баған атауларын ағылшыншаға түрлендіру (қазақша болса)
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

                # 4. Күнді дұрыс форматқа келтіру (YYYY-MM-DD)
                if 'date' in df_import.columns:
                    # Тек күн бөлігін алу (уақытты алып тастау)
                    df_import['date'] = pd.to_datetime(df_import['date']).dt.strftime('%Y-%m-%d')

                # 5. Тапсырма түрін түзету
                if 'task_type' in df_import.columns:
                    df_import['task_type'] = df_import['task_type'].replace({
                        'Форматитеті': 'Формативті',
                        'Форматтвті': 'Формативті',
                        'формативті': 'Формативті'
                    })

                # 6. Қажетті бағандарды тексеру
                required_cols = ['student_name', 'date', 'task_title', 'task_type', 'grade_10', 'response_time',
                                 'attendance']
                missing_cols = [col for col in required_cols if col not in df_import.columns]

                if missing_cols:
                    st.error(f"Қажетті бағандар табылмады: {missing_cols}")
                    st.info("Файлдың баған атаулары: " + ", ".join(df_import.columns))
                else:
                    st.subheader("🔍 Жүктелген файлдың алғашқы 5 жолы")
                    st.dataframe(df_import.head(), use_container_width=True)

                    # 7. Оқушы атын ID-ге түрлендіру
                    students_df = get_students()
                    name_to_id = dict(zip(students_df['name'], students_df['id']))

                    # 8. Деректерді дайындау
                    import_rows = []
                    errors = []
                    for idx, row in df_import.iterrows():
                        student_name = row['student_name']
                        if student_name not in name_to_id:
                            errors.append(f"{idx + 1}. жол: '{student_name}' оқушысы табылмады")
                            continue
                        student_id = name_to_id[student_name]
                        date = row['date']  # қазір қарапайым жол форматында
                        task_title = str(row['task_title'])
                        task_type = str(row['task_type'])
                        grade_10 = int(float(row['grade_10']))  # кейде сандық мән float болуы мүмкін
                        response_time = float(row['response_time'])
                        attendance = int(float(row['attendance']))
                        import_rows.append(
                            (student_id, date, task_title, task_type, grade_10, response_time, attendance))

                    if errors:
                        st.warning("Келесі қателер орын алды:")
                        for err in errors[:10]:
                            st.write(err)

                    if import_rows:
                        if st.button("📥 Импорттау (жаңа деректер қосылады, ескілер сақталады)", key="import_btn"):
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.executemany(
                                "INSERT INTO activities (student_id, date, task_title, task_type, grade_10, response_time, attendance) VALUES (?,?,?,?,?,?,?)",
                                import_rows)
                            conn.commit()
                            conn.close()
                            st.success(f"✅ {len(import_rows)} жазба сәтті импортталды!")
                            st.balloons()
                            st.rerun()
                    else:
                        st.error("Импорттау үшін ешқандай деректер жоқ")

            except Exception as e:
                st.error(f"Қате орын алды: {str(e)}")
                st.info(
                    "Файл форматын тексеріңіз. Керекті бағандар: student_name, date, task_title, task_type, grade_10, response_time, attendance")

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
